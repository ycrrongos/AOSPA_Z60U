# 0039 — cerro 无声：DTBO merge 后 MTP audio 盖掉 Lineage zte 声卡配置

## 状态：**已整段撤回（2026-09-23）**

用户要求声音相关修补全部删除、从头重做。下列产物已从真相源移除，**sync/apply 后不应再出现**：

- ~~`build/tools/fix-cerro-audio-dtbo.py`~~（已删）
- ~~`merge_dtbs.py` 里 `_cerro_fix_merged_audio_dtbos` 调用~~（已去掉）
- 试验包 `dtbo-WORKING-fill-v*` / `asoc2` **不要再刷**（曾导致卡第一屏 / 软砖）

当前策略：先编**无声音修补**的整包验证开机；声音另开功能重做。

---

## 原问题（保留作背景，勿当现行方案）

开机无声卡：`/proc/asound/cards` 空；根因是 DTBO merge 后 MTP `pineapple-audio` 盖掉 Lineage zte 的 `num-macros` / `wsa-max-devs` / routing。详见 git 历史 `docs/features/0039` 旧版与 `snapshot-*` 标签。
