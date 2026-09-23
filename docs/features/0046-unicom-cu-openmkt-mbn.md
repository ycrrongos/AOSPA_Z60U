# 0046 — 联通 CU OpenMkt MBN 缺失

## 问题

`mbn_sw.txt` 列有：

```
mcfg_sw/generic/China/CU/Commercial/OpenMkt/mcfg_sw.mbn
mcfg_sw/generic/China/CU/Commercial/VoLTE/mcfg_sw.mbn
```

但 `modem.img` / 实机 `firmware_mnt` **只有 VoLTE**（无 OpenMkt 目录）。
移动有 `Volte_OpenMkt` → `NR_SA`；联通停 `LTE`，偶发 `isEnDcAvailable=true` 仍不升 5G。
飞机模式恢复时联通能扫到 NR n78（紧急），正常驻网仍回 LTE。

## 已做（不够）

- `persist.vendor.radio.5g_mode_pref=3`（NSA+SA）
- CarrierConfig 联通 `hide_enabled_5g_bool=false` + `carrier_nr` SA+NSA
- `cmd phone set-allowed-network-types-for-users -s 1 …NR`

## 还需

从 **同平台厂包 / OP12 / 能出联通 5G 的 modem** 取出：

`China/CU/Commercial/OpenMkt/mcfg_sw.mbn`

放入：

```
device-overlay/.../radio/mcfg/... 或 vendor 注入脚本
→ 刷入 modem / 开机 copy 到 firmware_mnt
```

`firmware_mnt` 现约 93MB 空闲，可热测 mkdir+push 后重载 MBN（需重启 modem/`airplane`）。

### 已排除的来源（2026-09-23）

- Voltage / ArtistAOSP `vendor/nubia/cerro/radio/modem.img`：CU 下 **只有 VoLTE**（无 OpenMkt 目录）
- 本机 `mbn_sw.txt` 列名存在 ≠ 分区里有文件

## 不要

用 CMCC/CT OpenMkt 顶替 CU（ICCID/PLMN 策略不对）。
