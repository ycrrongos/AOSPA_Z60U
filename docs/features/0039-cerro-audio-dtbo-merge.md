# 0039 — cerro 无声：DTBO merge 后 MTP audio 盖掉 Lineage zte 声卡配置

## 问题

开机无声卡：`/proc/asound/cards` 空，只剩 `/dev/snd/timer`；`soc:spf_core_platform:sound` deferred。
AW882xx I2C 能 probe，HAL/audioserver 在跑，但 ASoC card 未注册。

## 根因（不是 Android device-tree audio XML）

`device/nubia/*/audio/*.xml` 已与 Lineage `lineage-23.2` 一致；真正坏在 **kernel DTBO merge**：

1. `merge_dtbs.py` 用 `fdtoverlaymerge` 把 `pineapple-audio*.dtbo`（MTP）和 `zte-cerro-overlay.dtbo` 并进同一 DTBO。
2. ABL 按 fragment 顺序应用时，**MTP 的 sound / lpass-cdc 属性后写覆盖 zte**：
   - `qcom,num-macros = 4`，但 zte 已 `status=disabled` 掉 `wsa_macro` / `wsa2-macro` → 只有 3 个 macro 注册 → `lpass-cdc` 永远不 `snd_soc_register_component`
   - `qcom,wsa-max-devs = 2` → machine 挂 WSA BE
   - `qcom,audio-routing` 含 `HAP_IN` / `WSA_*` → `snd_soc_register_card` 失败 **-ENODEV**
3. Lineage `zte-pineapple-common-overlay.dtsi` 里已有正确值（`num-macros=3`、`wsa-max-devs=0`、无 WSA routing），只是赢不过 MTP。

**不要**整份跳过 `pineapple-audio` techpack：zte overlay 依赖其中的 `__symbols__`（如 `wsa_spkr_en*`），跳过后易软砖。

**不要**对合并后的 DTBO 做 `dtc` 反编译再编译：会把 `qcom,cdc-vdd-*-voltage` 等 u32 误当成字符串，导致 `wcd939x` probe -EINVAL。

## 解决

1. `device-overlay/.../build/tools/fix-cerro-audio-dtbo.py`  
   对 `*zte-cerro*.dtbo` **原地**改 MTP 副本（**跨 FDT**：用 zte 干净 routing 盖 MTP）：
   - `qcom,wsa-max-devs` 2→0
   - `qcom,num-macros` 4→3
   - 含 `WSA`/`HAP` 的 `qcom,audio-routing` → 同长度填干净模板
   - `asoc-codec-names` 去掉 `wsa-codec*` / `swr-haptics`（pad stub，**不缩短**）
2. `merge_dtbs.py` 在写出 merged DTBO 后调用上述脚本（已去掉跳过 audio techpack 的逻辑）。

**禁止**把 `asoc-codec` phandle 改成 `0`（旧试验包 `dtbo-WORKING-asoc2.img`）：会 USB 断连 / 起不来。急救只用 **fill-v3**。

现场急救（不必整编）：

```bash
python3 device-overlay/nubia/sm8650-common/build/tools/fix-cerro-audio-dtbo.py -v \
  source/out/target/product/cerro/obj/DTB_OBJ/out/*zte-cerro*.dtbo
# 再 mkdtboimg 打成 dtbo.img，fastboot flash dtbo_<slot>
# 或直接：
fastboot flash dtbo_a prebuilts-cerro/dtbo/dtbo-WORKING-fill-v3.img
fastboot flash dtbo_b prebuilts-cerro/dtbo/dtbo-WORKING-fill-v3.img
```

已打好的试验包：`prebuilts-cerro/dtbo/dtbo-WORKING-fill-v3.img` / `dtbo-cerro-audio-fill.img`

## 验收

```text
xxd .../lpass-cdc/qcom,num-macros     → 00000003
xxd .../sound/qcom,wsa-max-devs       → 00000000
routing 无 WSA/HAP
/proc/asound/cards 有 pineapple 卡
/sys/kernel/debug/asoc/components 含 lpass-cdc、wcd939x-codec
dmesg: Sound card ... registered
```

## 相关

- DT：`kernel/.../zte-pineapple-common-overlay.dtsi`、`cerro/zte-cerro-overlay.dtsi`
- 驱动：`lpass-cdc.c`（`num_macros_registered == num_macros` 才注册 component）
