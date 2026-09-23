# 0006 — tinyxml2-v34 + hostapd qcwcn namespace

## 问题

vibrator / protobuf lite 修完后 soong：

- `libsnapdragoncolor-manager` → `libtinyxml2-v34`
- `hostapd` → `lib_driver_cmd_qcwcn`（模块在 namespace `hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib`，root 看不见）

## 决策

**tinyxml2-v34**：又一份 Lineage compat 预编译 SONAME。AOSPA `vndk/v34` 只有 `libaudioroute-v34` / `libui-v34`。从 229 只拷 `.so` 到 `prebuilts-cerro/libtinyxml2-v34/`，`scripts/patch-lineage-compat-tinyxml2-v34.py` 装进 compat。不要整仓覆盖。

**qcwcn**：不要拉 `hardware/qcom-caf/wlan`（AOSPA 已有 `hardware/qcom/wlan`）。Lineage DT 写 `BOARD_HOSTAPD_PRIVATE_LIB := lib_driver_cmd_qcwcn`；CLO 同模块在 nested `soong_namespace`。官方 `device/qcom/wlan/vendor_board_common.mk` 用 fully-qualified：

```
//hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib:lib_driver_cmd_qcwcn
```

overlay `BoardConfigCommon.mk` 改成同样写法。从 229 再 rsync DT 后要重做这一行（或跑 apply 前检查 overlay）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
