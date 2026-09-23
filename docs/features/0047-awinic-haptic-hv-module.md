# 0047 — Voltage 式 awinic haptic_hv（`haptic.ko`）

## 问题

触感全无：HAL 能跑 oneshot 日志，但 I2C `haptic_hv@5A` **无驱动绑定**。
实机只有 `qcom-hv-haptics` / `swr_haptics`，没有 Voltage 的 `haptic.ko`（`CONFIG_AWINIC_HAPTIC_HV=m`）。

## Voltage 对照

- 源码：`kernel/nubia/sm8650/drivers/misc/haptic_hv/`（产物名 `haptic.ko`）
- 配置：`arch/arm64/configs/oem/pineapple_diff.config` → `CONFIG_AWINIC_HAPTIC_HV=m`
- `modules.load` 已列 `haptic.ko`
- `ueventd`：`firmware_directories` 需含 `/vendor/firmware/`（`haptic_ram.bin`）

## 做法（可重放）

1. `prebuilts-cerro/vibrator-voltage/`：从 Voltage 抽出的 `haptic_hv/` 源、`pineapple_diff.config`、`haptic.ko`
2. `scripts/patch-kernel-awinic-haptic.py`：保证 oem fragment 有 `CONFIG_AWINIC_HAPTIC_HV=m`；缺源则从 prebuilts 拷入
3. `apply-device-overlay.sh` 已挂该脚本
4. 0042 effect-stream + 0044 FIFO alloc + 0045 reset-gpio=120 仍需要

## 热修（vendor_dlkm 有空时）

```bash
adb root; adb remount
adb push prebuilts-cerro/vibrator-voltage/haptic.ko /vendor_dlkm/lib/modules/haptic.ko
# modules.load 已有 haptic.ko
adb reboot
```

**不要**在 `vendor_dlkm` 100% 时 `cp`（会写成 0 字节 → `insmod Invalid argument`）。

## 验证

```text
lsmod | grep '^haptic '
dmesg | grep awinic_haptic
# input: awinic_haptic as .../1-005a/input/inputN
cmd vibrator_manager synced oneshot -a 400 255
```

## Voltage 对照补遗（2026-09-23 调研）

- **不是** AAC RichTap AIDL；是 QTI FF + `haptic.ko` + `libqtivibratoreffect.nubia_sm8650-richtap`。Plasma `cerro-opt` **无**振动。
- `haptic_ram.bin` 在 extract 的 `/vendor/firmware/`；Voltage `ueventd` 默认只搜 `firmware_mnt/image/` → 须加 `/vendor/firmware/`，或 init  staged 后再 `restart vendor.qti.vibrator`。FW 未就绪时常见 `EVIOCSFF` **-19** / FW **-13**。
- `isVibratorControllerRegistered=false` **不**代表马达坏（那是 adaptive IVibratorController）。
- Penguin `apply-keep-wiring.sh` 若不 rsync `vibrator/`，下一轮干净 apply 会丢 effect 源；AOSPA 全树 overlay 已有该目录。

开机恢复前不要热推模块（见 TROUBLESHOOTING「vendor 写满 0 字节」）。

## 相关

- [0042](0042-vibrator-effect-stream.md) / [0044](0044-haptic-custom-fifo-alloc.md) / [0045](0045-haptic-reset-gpio-dtbo.md)
