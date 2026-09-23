# 0001 — cerro Lineage CAF HAL 缺口

## 问题

AOSPA calcite 是 CLO 树：QCOM HAL 在 `hardware/qcom/` 和 `vendor/qcom/opensource/`。
cerro 设备树（nubia-sm8650-devs lineage-23.2）硬编码 `hardware/qcom-caf/{common,sm8650/...}`。
`lunch aospa_cerro-userdebug` 立刻失败：`hardware/qcom-caf/common/common.mk does not exist`。

## 决策

对照 229 OnlyAOSP `cerro-hals.xml` **按缺项补**，禁止整份 overlay：

**不拉（AOSPA 已有）**

- `hardware/qcom/bootctrl`、`hardware/qcom/wlan`
- `device/qcom/sepolicy_vndr`（CLO 路径；OnlyAOSP 的 `sm8650` 子路径会顶掉）
- `vendor/qcom/opensource/{usb,power,vibrator,data-ipa-cfg-mgr,dataipa,commonsys*}`
- `hardware/lineage/compat`（AOSPA 自己的；21.7 protobuf 另拷，见 [0004](0004-protobuf-21.7-nubiaparts.md)）

**要拉（DT 硬编码缺失）**

见仓库根 `local_manifests/cerro-hals.xml`（apply 会拷进 `source/.repo/local_manifests/`，避免 `source/` 重下后丢失）。

**不要 inherit** `hardware/qcom-caf/common/common.mk`：会与 AOSPA `device/qcom/common` 重复定义 RFS/mountpoint Soong 模块。overlay 的 `sm8650-common/common.mk` 已去掉该行。Soong 仍会扫描 CAF `Android.bp`，见 [0002](0002-soong-isolate-caf-common.md)。

`device/lineage/sepolicy` 用 **lineage-24.0**（与 229 VoltageOS 17 一致），其余 CAF 用 lineage-23.2 / `lineage-23.2-caf-sm8650`。

## 重放

```bash
source scripts/proxy-env.sh
repo sync --current-branch --no-tags -j4 \
  hardware/qcom-caf/common \
  hardware/qcom-caf/sm8650/audio/agm \
  hardware/qcom-caf/sm8650/audio/graphservices \
  hardware/qcom-caf/sm8650/audio/pal \
  hardware/qcom-caf/sm8650/audio/primary-hal \
  hardware/qcom-caf/sm8650/data-ipa-cfg-mgr \
  hardware/qcom-caf/sm8650/dataipa \
  hardware/qcom-caf/sm8650/display \
  hardware/lineage/interfaces \
  device/lineage/sepolicy \
  vendor/qcom/opensource/audio-hal/st-hal-ar-legacy \
  vendor/qcom/opensource/libvmmem
```

`packages/resources/devicesettings` 用 AOSPA 自带的，不要覆盖。

`linkfile`：`hardware/qcom-caf/common` 的 `os_pickup_qssi.bp` → `hardware/qcom-caf/sm8650/Android.bp`。
**不要**用 OnlyAOSP 那两条会覆盖 `hardware/qcom/Android.mk` / `device/qcom/sepolicy_vndr/SEPolicy.mk` 的 linkfile。
