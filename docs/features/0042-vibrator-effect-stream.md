# 0042 — Voltage-style vibrator effect stream (richtap FIFO)

## 问题

`awinic_haptic` / `haptic_hv` 的 custom 路径要求 `custom_len == sizeof(custom_fifo_data)`（与 `effect_stream` 布局一致）。
AOSPA CLO `vendor.qti.hardware.vibrator.impl` 硬链默认 `libqtivibratoreffect`，且不定义 `USE_EFFECT_STREAM`。
oneshot 默认 `FF_CONSTANT`（驱动 **接受** CONSTANT→RAM_LOOP）；perform/richtap 波形需要 FIFO。

> 早期误判“awinic 拒 FF_CONSTANT”。CONSTANT 可用；FIFO 拒包是 `custom_len` 不对。内核 custom 分配见 [0044](0044-haptic-custom-fifo-alloc.md)。

## 做法（Voltage / Lineage soong_config，不整仓覆盖 AIDL）

1. `common.mk` 已有：
   - `soong_config_set qti_vibrator effect_lib libqtivibratoreffect.nubia_sm8650-richtap`
   - `soong_config_set_bool qti_vibrator use_effect_stream true`
2. `scripts/patch-soong-vibrator-headers.py`：补 `libqtivibratoreffect_headers`
3. **新增** `scripts/patch-soong-vibrator-effect-stream.py`：
   - `aidl/Android.bp`：`select(use_effect_stream)` → `-DUSE_EFFECT_STREAM`；`select(effect_lib)` 链 richtap
   - `Vibrator.cpp`：oneshot 在 `USE_EFFECT_STREAM` 下改用 `get_effect_stream(0)` + `FF_CUSTOM`（不用 `FF_CONSTANT`）
4. `apply-device-overlay.sh` 已挂上该脚本

## 验证

```bash
# 编完推 vendor（或 /data bind）后：
setprop ctl.restart vendor.qti.vibrator
cmd vibrator_manager synced oneshot 300
# dmesg 不应再刷 Only support custom FIFO data
# logcat -s vendor.qti.vibrator:D 可见 perform / on complete
```

## 重放

```bash
bash scripts/apply-device-overlay.sh
# lunch 后：
m vendor.qti.hardware.vibrator.impl libqtivibratoreffect.nubia_sm8650-richtap vendor.qti.hardware.vibrator.service
```
