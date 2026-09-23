# 0027 — ramoops 留给 console，卡 logo 后能从 recovery 读 pstore

## 问题

卡努比亚第一屏时没有 adb。舵机夹具可 Power+Vol+ ~17s 进 recovery，但 `/sys/fs/pstore` 一直空：

- dmesg：`ramoops: using 0x200000@0xbffdff000`
- sysfs：`console_size=0`、`record_size=0`、`pmsg_size=2097152`
- 另有 `pstore: Invalid compression size for deflate: 0`

## 根因

`pineapple.dtsi` 的 `ramoops_region` 把整段 2MiB 都给了 `pmsg-size`，没有 `console-size` / `record-size`。内核 `CONFIG_PSTORE_CONSOLE=y` 也写不进 RAM。强制进 recovery 抓不到上次开机 console。

## 决策

在 `pineapple.dtsi` 划出：

| 区 | 大小 |
|----|------|
| console | 512KiB (`0x80000`) |
| record (oops) | 128KiB (`0x20000`) |
| pmsg | 1.375MiB (`0x160000`) |

由 `scripts/patch-kernel-ramoops-console.py` 幂等改 `source/kernel/.../pineapple.dtsi`（kernel 不在 `device-overlay/`）。

## 夹具进 recovery

```bash
# 串口需 dialout 或 sudo；角度见 press-angles.env
HOLD_S=17 bash clo-agent-kit/tools/edl-tools/enter-recovery-hand.sh
# 或
sudo .../venv/bin/python clo-agent-kit/tools/agent-phone/servo_cli.py hold-recovery --seconds 17
```

流程：卡 logo → 夹具 17s → **再短按一次 Power**（解锁提示把松手当成一次按键）→ `adb root` → `ls /sys/fs/pstore`。

## 重放

```bash
bash scripts/apply-device-overlay.sh
# DTB 在 vendor_boot，不是只刷 boot/dtbo
m bootimage dtboimage vendorbootimage
fastboot flash vendor_boot vendor_boot.img
fastboot flash boot boot.img
fastboot flash dtbo dtbo.img
```

夹具长按进 recovery 会**硬断电清 RAM**，pstore 仍可能空；配合 0028 软重启才能稳定抓 console。

## 验证

刷入新 boot/dtbo 后：开机卡 logo → `enter-recovery-hand.sh` →

```bash
adb root
adb shell 'ls -la /sys/fs/pstore'
adb shell 'cat /sys/module/ramoops/parameters/console_size'   # 期望 524288
```
