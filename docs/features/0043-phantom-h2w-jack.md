# 0043 — 无 3.5mm 插孔：清 phantom h2w / LINE

## 问题

开机 `pineapple-mtp-snd-card Headset Jack` 的 `SW_LINEOUT_INSERT` / `SW_JACK_PHYSICAL_INSERT` 卡在插入 →
`setWiredDeviceConnectionState(LINE/h2w AVAILABLE)` → 媒体路由到幽灵有线耳机，扬声器无声。

## 做法

1. RRO：`config_useDevInputEventForAudioJack=false`（USB-C 音频仍走 USB HAL）
2. `init.cerro.audio_jack.rc` + `cerro_clear_audio_jack.sh`：boot 后 `sendevent` 清 SW 位（备份）
3. `vendor.prop`：`persist.vendor.radio.5g_mode_pref=1`（与联通 5G 一并修正 overlay 默认 0）

## 验证

```bash
getevent -i /dev/input/event8   # SW 位无 *
dumpsys audio | grep "Devices:" # 应为 speaker，不是 line
```

## 重放

`bash scripts/apply-device-overlay.sh` 后重编 / 刷 vendor+system RRO。

## 附加：mixer HPH 默认

MTP `mixer_paths` 初始 `RX_HPH PCM=1`。cerro 扬声器走 AW882 MI2S，应关 HPH：

- 文件头 ctl 改为 `0`
- `path name="speaker"` 内显式 `RX_HPH PCM` / `HPH PCM Enable` = 0
