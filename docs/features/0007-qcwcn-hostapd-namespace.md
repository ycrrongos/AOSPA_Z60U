# 0007 — hostapd / qcwcn soong namespace

## 问题

soong：`hostapd` 依赖 `lib_driver_cmd_qcwcn`。模块其实存在，但在 namespace
`hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib` 里。hostapd 在 root namespace，
Lineage DT 写的是裸模块名，所以报 undefined。

## 决策

AOSPA CLO `device/qcom/wlan/vendor_board_common.mk` 已经用限定名：

```
BOARD_HOSTAPD_PRIVATE_LIB := //hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib:lib_driver_cmd_qcwcn
BOARD_WPA_SUPPLICANT_PRIVATE_LIB := //hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib:lib_driver_cmd_qcwcn
```

cerro overlay 的 `BoardConfigCommon.mk` 改成同样写法。另外 `common.mk` 按 AOSPA volcano wlan.mk 加上：

```
PRODUCT_SOONG_NAMESPACES += hardware/qcom/wlan hardware/qcom/wlan/qcwcn
```

不要拉 Lineage `hardware/qcom-caf/wlan` 顶掉 AOSPA `hardware/qcom/wlan`。

从 229 刷新 overlay 后这两处会回到 Lineage 裸名，apply 前要再改（或记住本文件）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
