# 0050 — 暂时关闭库存指纹伪装 + userdebug 默认 adb root

## 背景

关于本机显示 `release-keys`，是产品 mk 用库存 `BuildDesc` / `BuildFingerprint` 伪装的，不是编成了 user。  
AOSPA Settings 也没有 Lineage 式「ADB root」菜单；userdebug 需电脑执行 `adb root`。

用户要求 bringup 阶段：**先关掉伪装**（以后可开），并 **系统默认 adb root**。

## 改动

| 项 | 做法 |
|----|------|
| 指纹伪装 | `AOSPA_CERRO_SPOOF_STOCK_FINGERPRINT ?= false`；为 `true` 时才设 PQ83A01 BuildDesc/Fingerprint/DeviceName |
| 默认 adb root | `init.cerro.adb_root.rc`：`ro.debuggable=1` → `setprop service.adb.root 1` |
| USB / 免配对 | userdebug：`persist.sys.usb.config=adb`、`ro.adb.secure=0` |

真相源：

- `device-overlay/vendor-aospa/products/cerro/aospa_cerro.mk`（lunch 实际用）
- `device-overlay/nubia/cerro/aospa_cerro.mk`（保持同步）
- `device-overlay/nubia/cerro/device.mk`
- `device-overlay/nubia/cerro/rootdir/etc/init.cerro.adb_root.rc`
- 开关表：`docs/aospa-cerro-patch-toggles.md`

## 重新打开伪装

```makefile
AOSPA_CERRO_SPOOF_STOCK_FINGERPRINT := true
```

写在产品 mk 继承前，或编包时传入。

## 验证（刷含本改动的 userdebug 后）

```bash
adb shell getprop ro.build.description   # 不应再带库存 release-keys 文案
adb shell getprop ro.build.tags          # test-keys
adb shell getprop service.adb.root       # 1（adbd 已 root 时）
adb shell id                             # 无需先 adb root 即为 uid=0（若 adbd 已按 root 起）
```

## 重放

```bash
bash scripts/apply-device-overlay.sh
# 重编 system/product 或整包后刷机
```
