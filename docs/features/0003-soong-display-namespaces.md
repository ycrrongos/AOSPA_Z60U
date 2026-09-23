# 0003 — Soong display namespace（CLO vendor vs CAF sm8650）

## 问题

0002 去掉 CAF/health 重复模块后，soong 继续报：

- `vendor/qcom/common/vendor/*/Android.bp`：`namespace hardware/qcom/display{,/gralloc,/libdebug} does not exist`
- `hardware/qcom-caf/sm8650/Android.bp`（`os_pickup_qssi.bp`）：`namespace vendor/qcom/opensource/display does not exist`

官方 AOSPA 机型用 `vendor/aospa/products/platforms/*.xml` 拉 `hardware/qcom/display`。calcite **没有** pineapple/sm8650 这份；cerro 显示 HAL 在 `hardware/qcom-caf/sm8650/display`。

229 OnlyAOSP `cerro-hals.xml` 同样只有 `os_pickup_qssi.bp` → `hardware/qcom-caf/sm8650/Android.bp`，另两条 `os_pickup_aosp.mk` / `os_pickup_sepolicy_vndr.mk` **不要**用（会盖 CLO）。OnlyAOSP 还多拉 Lineage `commonsys/display`，AOSPA 已有 `commonsys-intf/display`，缺的是 `vendor/qcom/opensource/display`。

## 决策

不要整份搬 OnlyAOSP HAL overlay，也不要空 stub `hardware/qcom/display`（`soong_namespace` 的 import **不传递**，Adreno 预编译库找不到 `libgralloc.qti`）。

`scripts/patch-soong-display-namespaces.py`（挂在 `apply-device-overlay.sh`）：

1. 在 CAF `display/gralloc`、`display/libdebug` 的 `Android.bp` **文件头**加 `soong_namespace`，并 **import 父 namespace** `hardware/qcom-caf/sm8650`（否则看不见 `qtidisplay_common_defaults`）。
2. `os_pickup_qssi.bp` 去掉不存在的 `vendor/qcom/opensource/display`，改为 import 上面两个 CAF namespace，让 composer/sdm 仍能看见 `libdisplaydebug`。
3. `vendor/qcom/common/**/Android.bp` 里 `hardware/qcom/display/gralloc|libdebug` → 对应 CAF 路径；`hardware/qcom/display` → `hardware/qcom-caf/sm8650`（父 namespace，含 display 其余模块）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```

`repo sync` 会还原 CAF display / `os_pickup_qssi.bp` / `vendor/qcom/common` / `vendor/nubia/*/Android.bp` / lineage interfaces，必须再跑 apply。

Voltage 的 `vendor/voltage/build/soong/Android.bp` 定义 `generated_kernel_header_defaults` + `generated_kernel_includes`（`headers_install`）。AOSPA 原先用空 stub；**0030** 已在设备树接 `cerro_generator`，CAF defaults 挂 `generated_kernel_includes`。

`vendor/qcom/common/vendor/gps-legacy` 依赖 `libgps.utils`，该模块在 cerro DT 的 `soong_namespace`（`device/nubia/sm8650-common`）里。脚本给 gps-legacy 补上这条 import。
