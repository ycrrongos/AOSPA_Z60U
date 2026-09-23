# 0008 — CneApp JNI vendor symlink

## 问题

Soong 通过后 kati 失败：

```
TARGET module CneApp requires non-existent TARGET module:
CneApp.libvndfwk_detect_jni.qti_vendor_symlink
```

不要设 `BUILD_BROKEN_MISSING_REQUIRED_MODULES`。

## 决策

nubia extract-utils 给 `CneApp` 写了 `required: ["CneApp.libvndfwk_detect_jni.qti_vendor_symlink"]`。
AOSPA CLO `device/qcom/common/vendor/telephony/Android.bp` 里同功能模块叫 `CneApp.libvndfwk_detect_jni.qti_symlink`，且在独立 `soong_namespace`，vendor blob 看不见。

在 overlay `device/nubia/sm8650-common/Android.bp` 按 Lineage 名字加一份 `install_symlink`（vendor 树已 import 该 DT namespace）。指向 `/vendor/lib64/libvndfwk_detect_jni.qti.so`（CLO `core-utils` 会装这份 so）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
