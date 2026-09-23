# 0037 — CAF display HWC：composer / mapper / libdisplayconfig

## 症状

0036 修好 qseecomd 后，zygote 起得来，但 **surfaceflinger SIGABRT** 循环，init 杀 zygote，仍无 `boot_completed`。vendor 里没有 `vendor.qti.hardware.display.composer-service`（及 QTI mapper/allocator）。

日志：`cerro-bootdiag-pull6/`。

## 根因

1. CAF display 整树在 `hardware/qcom-caf/sm8650` 的 soong_namespace 里；0031 把 `os_pickup_qssi.bp` 抽空后，composer / `libdisplayconfig.qti` **不进**产品图。
2. AOSPA calcite **没有** `vendor/qcom/opensource/display`（Voltage 有）；只能 import 已有的 `commonsys-intf/display`。
3. 即便把 `hardware/qcom-caf/sm8650` 加进 `PRODUCT_SOONG_NAMESPACES`，编译 `libsdmdal` 仍缺头文件：Voltage 经 `hardware/qcom-caf/common/BoardConfigQcom.mk` 设 `SOONG_CONFIG_qtidisplay_default=true`，AOSPA 走 `device/qcom/common/BoardConfigQcom.mk` **没有** qtidisplay 变量 → `qtidisplay_defaults` 不挂 `display_headers`。

## 修复（可重放）

### Overlay

- `device-overlay/nubia/sm8650-common/common.mk`
  - `PRODUCT_SOONG_NAMESPACES += hardware/qcom-caf/sm8650` + `commonsys-intf/display`
  - `soong_config_set_bool`：`default` / `drmpp` / `gralloc4` / `displayconfig_enabled` / `ubwcp_headers` / `udfps` / `legacy_pphwresourceinfo`
  - `soong_config_set`：`composer_version=v3`
  - 保留 `PRODUCT_PACKAGES`：composer / allocator / demura / mapper@4.0-impl
- `BoardConfigCommon.mk`：`include hardware/qcom-caf/sm8650/display/config/display-board.mk`（勿用 `hardware/qcom/display/...`）

### 脚本

`scripts/patch-soong-display-namespaces.py`（`apply-device-overlay.sh` 已挂）：

1. `commonsys-intf/display` 加空 `soong_namespace`
2. `os_pickup_qssi.bp` import 该 NS（不 import 缺失的 `opensource/display`）
3. 去掉嵌套 gralloc/libdebug NS（0031）
4. `vendor/qcom/common` + nubia prebuilt：凡引用 `display.config-V*` 的 `Android.bp`，import commonsys-intf
5. FM `@1.0` vendor prebuilt `enabled: false`（与 AOSPA system_ext 撞名；`--fm-only` 在 elf-check 之后再跑）

不要再装 0036 的 SONAME 权宜 prebuilt `libdisplayconfig.qti`（改由 CAF 编出）。

## 验证

```bash
bash scripts/apply-device-overlay.sh
cd source && lunch aospa_cerro-userdebug
m vendor.qti.hardware.display.composer-service libdisplayconfig.qti \
  android.hardware.graphics.mapper@4.0-impl-qti-display \
  vendor.qti.hardware.display.allocator-service
# m vendorimage 若卡 imgdiff → build_image 打 vendor.img；fastbootd 刷 vendor
```

**2026-08-25 实机**：刷含 HWC 的 vendor 后约 **38s** `sys.boot_completed=1`；`surfaceflinger` / zygote / qseecomd 均 running；HWC display id 正常。日志：`cerro-bootdiag-pull7/`。

装上后 vendor 应有：

- `vendor/bin/hw/vendor.qti.hardware.display.composer-service`
- `vendor/lib64/libdisplayconfig.qti.so`
- `vendor/lib64/hw/android.hardware.graphics.mapper@4.0-impl-qti-display.so`

## 注意

- 动态分区 **vendor** 只在 **fastbootd** 刷（bootloader `flash vendor` → Partition not found）。
- 不要整份 inherit `display-product.mk`（里面 `hardware/qcom/display/config` 路径在 AOSPA 不存在）；只要 board 片段 + soong_config。
- 勿在 229 上 sync；对照只读。
- bringup 仍为 `androidboot.selinux=permissive`；后续再收紧。
