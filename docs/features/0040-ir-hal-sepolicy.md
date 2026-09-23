# 0040 — Lineage IR HAL SELinux（卡 logo / system_server 死等 ConsumerIr）

## 症状

`boot_completed` 起不来或极慢：`system_server` Watchdog，主线程卡在
`ServiceManager.waitForService(android.hardware.ir.IConsumerIr/default)`。

init：

```text
Could not start service 'vendor.ir-default' ... labeled "u:object_r:vendor_file:s0"
has incorrect label or no domain transition
```

## 根因

`common.mk` 打了 `android.hardware.ir-service.lineage`，但 AOSPA 未 inherit
Lineage `device/lineage/sepolicy/common/sepolicy.mk`，缺：

- `file_contexts` → `hal_ir_default_exec`
- `lirc_device` + `hal_ir_default` 对 `/dev/lirc0` 的 allow
- `vendor_ir_prop`

二进制落成 `vendor_file`，init 拒绝 domain transition → HAL 永不注册 →
framework 永久等 IR。

（同 0015 touch：只补需要的 sepolicy，不整份 inherit Lineage common。）

## 修复（overlay，可重放）

| 路径 | 内容 |
|------|------|
| `sepolicy/vendor/device.te` | `type lirc_device, dev_type;` |
| `sepolicy/vendor/file_contexts` | `/dev/lirc0`、`android.hardware.ir-service.lineage` → `hal_ir_default_exec` |
| `sepolicy/vendor/hal_ir_default.te` | `allow` lirc + `get_prop(vendor_ir_prop)` |
| `sepolicy/vendor/property.te` / `property_contexts` | `vendor_ir_prop` |

`hal_ir_default` / `_exec` 类型已在 AOSP `system/sepolicy/vendor/hal_ir_default.te`。
平台策略已有 `init` → `hal_ir_default_exec` 的 domain transition；**开机卡死的充要条件是二进制标签**。

### 刷机（已验证路径）

不要整份替换旧 vendor 里的 `vendor_sepolicy.cil`（易软砖）。在已知能开机的 vendor 上只做：

1. `ro.mediaserver.64b.enable=true`（0038）
2. 给 IR 二进制打上 `u:object_r:hal_ir_default_exec:s0` xattr

```bash
bash scripts/inject-vendor-mediaserver-ir-label.sh
fastboot flash vendor_a source/out/target/product/cerro/vendor-WORKING-0038-0040.img
```

实测：`Enforcing` 下 `vendor.ir-default` running，`IConsumerIr/default` 与 `media.player` 均在，`WelcomeActivity` 可起来。lirc allow 仍留在 overlay，供日后干净 `vendorimage` 使用。

## 验证

```bash
# 冷启动、enforcing
getenforce                                          # Enforcing
getprop init.svc.vendor.ir-default                  # running
ls -Z /vendor/bin/hw/android.hardware.ir-service.lineage
# u:object_r:hal_ir_default_exec:s0
getprop sys.boot_completed                          # 1
service list | grep -E 'media.player|IConsumerIr'
```

勿用 `setenforce 0` / 手起 HAL 当正式方案。
