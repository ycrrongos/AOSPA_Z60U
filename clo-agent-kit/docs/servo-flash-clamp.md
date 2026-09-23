# 舵机刷机夹（agent-phone 硬件）

> **用途**：无人值守把 Nubia Z60 Ultra（cerro / NX721J）按进 **9008**，配合 `tools/edl-tools/enter-9008-hand.sh` 与 `auto-flash-watch.sh`。  
> **原则**：舵机 **见到 `05c6:9008` 再松**；串口用 Espressif **by-id**，勿占裸 `/dev/ttyACM0`（常是舵机，手机 ACM 是另一条）。

---

## 1. 本包文件

| 路径 | 说明 |
|------|------|
| `hardware/servo-flash-clamp/nubia-z60u-clamp-v1.stl` | 刷机夹 3D 打印件（ZWCAD 导出，约 **184×194×30 mm**） |
| `tools/agent-phone/` | 固件源码、`servo_cli.py`、网页校准、`press-angles.env` |
| `tools/edl-tools/enter-9008-hand.sh` | 按住三键 + 可选 ACM reboot，直到 9008 |

母机原件：`~/模型001.stl`（与本包 STL 同源）。

---

## 2. BOM（参考）

| 部件 | 型号 / 说明 |
|------|-------------|
| 主控 | **DFRobot FireBeetle 2 ESP32-S3 V1.0**（USB CDC，`303A:1001` / `3343:83CF`） |
| 舵机 ×3 | 9g 金属齿或 SG90 级（Vol+ / Vol− / Power 各一） |
| 舵机电源 | **独立 5V ≥2A**（勿从板子 3V3/USB 拖大电流；曾导致 ESP32 掉线） |
| 共地 | 舵机 GND 与 FireBeetle GND 必须相连 |
| 打印件 | PLA/PETG，`nubia-z60u-clamp-v1.stl`，层高 0.2mm，20% 填充即可 |
| USB | 手机数据线接主机；FireBeetle 另接 USB 到主机（与手机 **两条线**） |

### 接线（Cerro 实机标定后）

FireBeetle 顶面丝印（用户接线对调后固件已对齐）：

| 丝印 | 功能 | GPIO |
|------|------|------|
| **A2** | Vol+ | 6 |
| **A1** | Vol− | 5 |
| **A0** | Power | 4 |

信号线接舵机 PWM；舵机 VCC 接 **外置 5V**，不要接 FireBeetle 5V 针脚扛三台舵机峰值电流。

---

## 3. 组装要点

1. 打印 `nubia-z60u-clamp-v1.stl`，清理支撑；手机侧贴薄泡棉防刮。
2. 三台舵机臂对准 **音量+、音量−、电源** 键位；先不拧紧，留校准余量。
3. FireBeetle 固定在夹具侧面，USB 朝外方便常插。
4. 手机竖放、底部 USB 朝主机；夹具应保证按键行程垂直下压，避免侧向蹭键。
5. 上电串口应打印：`READY agent_phone_tool` + `BOARD firebeetle2_esp32s3 silk A2=VOL+ ...`

---

## 4. 固件烧录

```bash
cd tools/agent-phone/firmware
# 需 PlatformIO：pip install platformio  或系统包 platformio
pio run -e firebeetle2_esp32s3 -t upload --upload-port /dev/serial/by-id/usb-Espressif_*
pio device monitor -b 115200
```

其他板型见 `tools/agent-phone/README.md`（STM32 Blue Pill 等）。

---

## 5. 角度校准

板子 **不保存** PRESS/REST 到 Flash；每次换舵机/改机械结构都要重校。

### 网页（推荐）

```bash
cd tools/agent-phone
pip install -r server/requirements.txt
uvicorn server.app:app --host 127.0.0.1 --port 8787
# 浏览器 http://127.0.0.1:8787
```

拖滑块设 `REST*`（松开）与 `PRESS*`（按下），点「同步到板子」，再单键试按确认行程。

### CLI

```bash
# 串口常属 dialout；本机可用 sudo + edl-tools venv（含 pyserial）
PY=tools/edl-tools/venv/bin/python
sudo $PY tools/agent-phone/servo_cli.py ping
sudo $PY tools/agent-phone/servo_cli.py angles
sudo $PY tools/agent-phone/servo_cli.py hold-edl --seconds 60 --min-hold 8
# 卡 logo → recovery：Power+Vol+ ~17s，松手后再短按一次 Power
# （解锁提示页会把松手当成一次电源键，需再按才继续）
HOLD_S=17 ./tools/edl-tools/enter-recovery-hand.sh
# 或：sudo $PY tools/agent-phone/servo_cli.py hold-recovery --seconds 17
```

### 写入 `press-angles.env`

母机 cerro 当前值（2026-08-16 标定，**换夹具后需重校**）：

```
PRESSU=81
PRESSD=98
PRESSP=97
RESTU=90
RESTD=90
RESTP=90
```

`enter-9008-hand.sh` 启动前会 `source` 该文件并下发到板子。

---

## 6. 进 9008（自动化）

```bash
# 在 kit 根目录
HOLD_S=90 MIN_HOLD_S=8 ./tools/edl-tools/enter-9008-hand.sh
lsusb | grep 05c6:9008
```

- 若手机在 **Linux ACM**（`1d6b:0104`），脚本默认 `REBOOT_ACM=1`：按住 2s 后从 Nubia by-id 发 reboot，按键在复位窗口内吃进 EDL。
- 成功判据：**精确** `05c6:9008`，不是 `19d2:0112`（MemoryDump）。
- 失败：检查 PRESS 幅度、5V 供电、USB 线；可 `NO_HAND=1` 改用手动进 9008。

与刷机监听联动：

```bash
./tools/edl-tools/auto-flash-watch.sh --daemon /path/to/boot.img
```

---

## 7. 常见坑（母仓库实测）

| 现象 | 原因 / 处理 |
|------|-------------|
| `ttyACM0` 写到手机 | ACM 编号会变；**舵机常在 ACM0**，手机用 `by-id/*nubia*` |
| 按住仍不进 9008 | PRESS 不够 / 手机没电；加大 PRESSP 或先充电 |
| ESP32 掉线 | 3V3 供舵机 → 改 **5V 外电** |
| 松手太早 | 已改为 **until 9008**；勿用固定 12s 松手 |
| KDE 休眠后 ACM 假死 | 舵机短按 Power 可唤醒手机 USB |

---

## 8. 可选：夹具内看屏

母仓库有 `tools/cerro-screen-server.py`（USB ECM MJPEG），帧率约 1–2 fps，够看夹具里是否亮屏/卡 logo；**未打进本 zip**（在 `LOA_Nubia_Z60U/tools/`）。
