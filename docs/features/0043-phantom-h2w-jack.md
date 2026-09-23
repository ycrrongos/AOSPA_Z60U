# 0043 — 无 3.5mm 插孔：清 phantom h2w / LINE

## 状态：**已整段撤回（2026-09-23）**

声音修补清零的一部分。已删除 / 恢复 Lineage 默认：

- ~~`init.cerro.audio_jack.rc` / `cerro_clear_audio_jack.sh`~~（已删）
- ~~`config_useDevInputEventForAudioJack=false`~~ → 恢复 **`true`**
- ~~`mixer_paths` 强制 `RX_HPH PCM=0`~~ → 恢复 Lineage **`1`**；speaker path 去掉 HPH 覆盖

声音功能将另开文档重做；本篇勿再当 apply 依据。
