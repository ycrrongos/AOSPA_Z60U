# 0002 — Soong 隔离 CAF common / Lineage health 重复模块

## 问题

`./rom-build.sh cerro -j 4` 在 soong bootstrap 失败：

- `hardware/qcom-caf/common/Android.bp` 与 `device/qcom/common/Android.bp` 重复 `rfs_*_symlink`、`vendor_*_mountpoint`、部分 `prebuilt_hidl_interfaces`
- `hardware/qcom-caf/common/fwk-detect` 与 `vendor/qcom/opensource/core-utils/fwk-detect` 重复
- `hardware/qcom-caf/common/memtrack` 与 `device/qcom/vendor-common/memtrack` 重复
- `hardware/lineage/interfaces/health` 与 `vendor/aospa/interfaces/health` 重复 `vendor.lineage.health` / `vendor.lineage.health-service.default`

DT 仍需要 CAF common 里的 **内核头**（`qti_kernel_headers`、`audio_kernel_headers` 等）和 **libqti-perfd-client**（已有独立 `soong_namespace` + `PRODUCT_SOONG_NAMESPACES`）。触控 / LiveDisplay 仍走 `hardware/lineage/interfaces`，不要整仓丢掉。

## 决策

不要把 `hardware/qcom-caf/common/Android.bp` 整文件换成 Lineage `os_pickup.bp`，也不要在文件头加 `soong_namespace {}`：

1. Soong 规定 **namespace 必须是该 Android.bp 的第一个模块**。
2. `hardware/qcom-caf/sm8650` 的 `Android.bp` 已是 `os_pickup_qssi.bp` namespace，只隐式看见 **root** namespace。把头文件放进 CAF common namespace 后，display/audio 会找不到 `qti_kernel_headers`。

做法：`scripts/patch-soong-isolate-caf-common.py`（挂在 `apply-device-overlay.sh` 末尾）

- CAF `Android.bp`：删除全部 `install_symlink` / `mkdir`，以及与 CLO 同名的三个 HIDL（`iop` / `limits` / `sigma_miracast`）。其余 HIDL 名与 CLO 不同，保留。
- `fwk-detect/Android.bp`、`memtrack/Android.bp`、Lineage health 两份 `Android.bp`：换成一行 stub。不要用 `/* ... */` 包原文（内层版权 `*/` 会提前结束注释，模块仍会被解析）。

`PRODUCT_PACKAGES += vendor.lineage.health-service.default` 保留，改用 AOSPA 那份实现。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```

`repo sync` 会还原 CAF / lineage interfaces 的 git 文件；sync 后必须再跑 apply（`scripts/sync-calcite.sh` 已调用）。

## 验证

- `hardware/qcom-caf/common/Android.bp` 含 `qti_kernel_headers`，不含 `rfs_apq_gnss_hlos_symlink`
- `hardware/lineage/interfaces/health/aidl/Android.bp` 只有 `// AOSPA cerro:` stub
- soong bootstrap 不再报这些 `already defined`
