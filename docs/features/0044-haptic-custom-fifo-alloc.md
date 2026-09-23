# 0044 — haptic_hv custom FIFO 堆分配修正

## 问题

`awinic` `haptic_hv` 的 `upload_custom_effect` 用 `kcalloc(length)` 分配
`struct aw_haptic_container { int len; uint8_t data[]; }`，少了 `sizeof(int)`。
Voltage/Artist 同源也有此 bug；固件 RTP 路径用的是 `vmalloc(size + sizeof(int))`。

richtap / `USE_EFFECT_STREAM` 的 oneshot/perform 都走 custom FIFO。少分配会导致堆越界，
RTP_GO 可能根本起不来（用户空间 `EVIOCSFF` 仍返回 0）。

## 做法

`scripts/patch-kernel-haptic-custom-alloc.py`：改成

```c
aw_rtp = kvzalloc(sizeof(*aw_rtp) + custom_data.length, GFP_KERNEL);
```

挂进 `apply-device-overlay.sh`。需重编 `haptic.ko` / vendor_dlkm / 整核后刷机。

## 验证

```bash
# 停 HAL 后直接打 FF：
/data/local/tmp/fftest2 f   # custom FIFO
dmesg | grep -iE 'RTP_GO|failed to enter RTP'
cmd vibrator_manager synced oneshot 500
```

## 与 0042 的关系

0042 把 CLO vibrator 接到 richtap effect_stream。本补丁修内核消费侧。
Voltage `on()` 仍用 `FF_CONSTANT`（RAM_LOOP）；awinic **接受** CONSTANT（不是“只认 FIFO”）。
此前 FIFO 拒包是 `custom_len != sizeof(custom_fifo_data)`，不是 CONSTANT。
