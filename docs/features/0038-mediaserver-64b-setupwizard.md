# 0038 — SetupWizard 黑屏 ANR：缺 `media.player`（mediaserver 未起）

## 症状

`boot_completed=1` 后卡在 Pixel SetupWizard 欢迎页：黑屏、「应用无响应」。

## 根因

ANR：`WelcomeActivity.onCreate` → `RingtoneManager.getRingtone` → `MediaPlayer.setDataSource` → **永久等待** `media.player`（`waitForService`）。

设备上：

- 有 `/system/bin/mediaserver64`，**没有** `mediaserver32`
- `mediaserver_dynamic.rc` 按 `ro.mediaserver.64b.enable`（默认 false）import `mediaserver.64bit_false.rc` → `service media /system/bin/mediaserver32`
- `media` 服务起不来 → binder 无 `media.player` / `media.resource_manager`

为何会这样：`device/qcom/common` 打开了 `TARGET_DYNAMIC_64_32_MEDIASERVER`；`qti-media.mk` 本会设 `ro.mediaserver.64b.enable=true`，但 cerro **未**把 `media` 放进 `TARGET_COMMON_QTI_COMPONENTS`，属性缺失。cerro 又是 `core_64_bit_only`，本来就没有 32-bit mediaserver。

## 修复

两处同时钉死（避免只改 `vendor.prop` 却刷了旧 `vendor.img`）：

1. `device-overlay/nubia/sm8650-common/vendor.prop` → `TARGET_VENDOR_PROP`
2. `device-overlay/nubia/sm8650-common/common.mk` → `PRODUCT_VENDOR_PROPERTIES`

```properties
ro.mediaserver.64b.enable=true
```

与 AOSPA `qti-media.mk` 一致。

### 刷机（已验证路径）

`m vendorimage` 新产物曾直接掉 bootloader；在修好该回归前，用 **已知能开机的 vendor 底包** 注入属性：

```bash
bash scripts/inject-vendor-mediaserver-ir-label.sh \
  source/out/target/product/cerro/vendor.img.sparse
# fastbootd:
fastboot flash vendor_a source/out/target/product/cerro/vendor-WORKING-0038-0040.img
fastboot --set-active=a && fastboot reboot
```

底包默认是 `vendor.img.sparse`（2026-08-25 22:51 HWC 包）。脚本同时打上 IR 二进制 SELinux 标签（0040）。

冷启动后 init 应 import `mediaserver.64bit_true.rc`，起 `mediaserver64`，注册 `media.player`。

## 验证

```bash
getprop ro.mediaserver.64b.enable   # true
getprop init.svc.media              # running
service list | grep media.player
```

SetupWizard Welcome 窗口应有 surface、可点；不应再 ANR 等 media.player。
