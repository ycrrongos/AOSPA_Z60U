# 0026 — FCM 声明 Lineage livedisplay / touch HAL

## 问题

`dtbo.img`（0025）和 radio（0024）已进 target_files。打 OTA：

```
VINTF compatibility check failed
vendor.lineage.livedisplay.ISunlightEnhancement/default (@1)
vendor.lineage.touch.IHighTouchPollingRate/default (@1)
```

设备 manifest 有这两项（`livedisplay-service.sysfs` SE、`touch-service.nubia_sm8650`），AOSPA 框架兼容矩阵没有。Lineage 写在 `hardware/lineage/interfaces/compatibility_matrices/compatibility_matrix.lineage.xml`，官方机型靠 inherit Lineage 产品层带上。

## 决策

把这两项 **optional AIDL** 写进 overlay `device_framework_matrix.xml`（已在 `DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE`）。不要 inherit 整份 Lineage FCM / 产品层。0015 已补 touch sepolicy。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
