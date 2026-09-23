# 0028 — 首启卡 logo：metadata 落盘 + 软重启进 recovery（保 pstore）

## 问题

卡努比亚第一屏无 adb。夹具 Power+Vol+ ~17s 能进 recovery，但那是**硬断电**，会清掉 RAM，ramoops console（0027）抓不到上次开机日志。

## 根因（曾失效）

`init.cerro.bootdiag.{sh,rc}` 写在 `rootdir/`，但 **未加入 `device.mk` 的 `PRODUCT_COPY_FILES`**，vendor 镜像里没有这两个文件，服务从未跑过 → `/metadata` 无 `cerro-boot-*.txt`。

## 决策

1. **0027**：`pineapple.dtsi` 划出 console；**DTB 在 `vendor_boot`**（不只 boot/dtbo）。
2. **本功能**：`init.cerro.bootdiag`（vendor）
   - `device.mk` **必须** COPY 进 `/vendor/bin` + `/vendor/etc/init`
   - `on post-fs` / `on early-boot` 启动（`/metadata` 已挂，不依赖 `/data`）
   - 每 2s 写 `dmesg` / logcat → `/metadata/cerro-boot-*.txt`；同时 `echo` 到 `/dev/kmsg`（metadata 写失败时 soft reboot 后仍可从 pstore 看到心跳）
   - 约 90s 无 `sys.boot_completed=1` → `sys.powerctl reboot,recovery`（**软重启**，保留 ramoops）
   - `seclabel u:r:su:s0`（userdebug，免单独 TE）

夹具长按仍可手动进 recovery；有 bootdiag 后优先**等 ~90s 自动进 recovery**再拉日志。

## 重放

```bash
bash scripts/apply-device-overlay.sh
# lunch 后 — 至少要编 vendor（含 bootdiag）
m vendorimage
# 若 ramoops DTB 也要刷：
m vendorbootimage bootimage dtboimage
# fastbootd：
fastboot flash vendor vendor.img
# 按需：
fastboot flash vendor_boot vendor_boot.img
fastboot flash boot boot.img
fastboot flash dtbo dtbo.img
```

## 刷机（当前可用产物）

```text
source/out/target/product/cerro/vendor.img   # 已含 bootdiag（ext4 raw）
```

```bash
# fastbootd / userspace fastboot
fastboot flash vendor out/target/product/cerro/vendor.img
fastboot reboot
# 卡 logo → 等约 90s 应软进 recovery（不要夹具硬断电）
bash scripts/pull-bootdiag-from-recovery.sh ./cerro-bootdiag-pull
```

若 `m vendorimage` 因 `imgdiff` recovery_from_boot 失败，可对已装好的 `out/.../vendor/` 直接跑 `build_image`（见 TROUBLESHOOTING）。

## 验证

等自动进 recovery（或夹具），然后：

```bash
bash scripts/pull-bootdiag-from-recovery.sh ./cerro-bootdiag-pull
# 或手动：
adb root
adb shell 'cat /sys/module/ramoops/parameters/console_size'   # 524288
mkdir -p /tmp/m && adb shell 'mount -t f2fs -o ro /dev/block/by-name/metadata /tmp/m'
adb pull /tmp/m/cerro-boot-dmesg.txt .
adb pull /tmp/m/cerro-boot-status.txt .
adb shell 'ls -la /sys/fs/pstore; grep cerro_bootdiag /sys/fs/pstore/console-ramoops-0'
```
