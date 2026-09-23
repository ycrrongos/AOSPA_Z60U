# 0011 — 去掉与 AndroidBoardCommon 重复的 soong mkdir 挂载点

## 问题

kati：`overriding commands for target out/target/product/cerro/vendor/firmware_mnt`

- AOSPA `vendor/aospa/build/core/mkdir.mk`（soong `vendor_firmware_mnt_mountpoint`）
- QCOM `vendor/qcom/opensource/core-utils/build/AndroidBoardCommon.mk`（`$(FIRMWARE_MOUNT_POINT)`）

`device/qcom/common/Android.mk` 在 `TARGET_FWK_SUPPORTS_FULL_VALUEADDS=true` 时 include 后者。AOSPA `build/make/core/config.mk` **全局**设了这个变量。

## 决策

官方 AOSPA **不**把这三个 soong mkdir 加进 `PRODUCT_PACKAGES`，但 `mkdir.mk` **仍然**会给模块写 `$(LOCAL_SOONG_INSTALL_DIR)` 配方，所以只从 DT 拿掉 PRODUCT_PACKAGES 不够。

`scripts/patch-soong-qcom-mkdir-mountpoints.py` 对

- `vendor_bt_firmware_mountpoint`
- `vendor_dsp_mountpoint`
- `vendor_firmware_mnt_mountpoint`

设 `enabled: false`。挂载点由 AndroidBoardCommon.mk 创建（含 `/firmware` 等 root symlink）。不要 `BUILD_BROKEN_DUP_RULES`。overlay `common.mk` 也不再 PACKAGE 这三项。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
