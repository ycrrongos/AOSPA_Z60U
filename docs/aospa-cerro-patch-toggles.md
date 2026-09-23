# AOSPA cerro patch / product toggles

在对应 `.mk` 里用 `?=` 默认值；需要打开时在 `device.mk` / 产品 mk 之前设 `:= true`，或：

```bash
# 单次编包
make AOSPA_CERRO_SPOOF_STOCK_FINGERPRINT=true ...
```

| 开关 | 默认 | 作用 | 真相源 |
|------|------|------|--------|
| `AOSPA_CERRO_SPOOF_STOCK_FINGERPRINT` | **false** | 库存 PQ83A01 fingerprint / BuildDesc（`release-keys` 伪装） | `device-overlay/vendor-aospa/products/cerro/aospa_cerro.mk` |
| （固定）userdebug adb root | on（userdebug） | `service.adb.root=1` + `persist.sys.usb.config=adb` + `ro.adb.secure=0` | `device.mk` + `init.cerro.adb_root.rc` |

细节：[`docs/features/0050-disable-fingerprint-spoof-default-adb-root.md`](features/0050-disable-fingerprint-spoof-default-adb-root.md)。
