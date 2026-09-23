# 0049 — 声音修补清零 + 无音频修整包基线

## 背景

卡第一屏 / 上下文丢失后无法定位哪版音频试验改坏开机。用户要求：

1. **删除全部声音修复**（0039 DTBO fill、0043 phantom h2w/jack、mixer HPH 覆盖）
2. **重新 sync**，**先不修声音**
3. **编译整包**，只验证能否开机
4. 参考包 `/home/rong/Downloads/aospa_cerro-ota.zip`（卡第二屏/开机动画）**只查阅，不刷机、不全量替换**

## 已删除 / 恢复

| 项 | 动作 |
|----|------|
| `fix-cerro-audio-dtbo.py` | 删除 |
| `merge_dtbs.py` cerro audio hook | 已无（确认） |
| `init.cerro.audio_jack.rc` / `cerro_clear_audio_jack.sh` | 删除 |
| `common.mk` / `rootdir/Android.bp` jack 包 | 已无 |
| `config_useDevInputEventForAudioJack` | `true`（Lineage） |
| `mixer_paths_pineapple_mtp.xml` HPH | Lineage 默认 `1`，speaker 无 HPH 覆盖 |
| 功能文 0039 / 0043 | 标为已撤回 |

**未动**：触感（0042/0044/0045/0047）、IR、bootdiag、其它非声音功能；`stage-audio-kernel-uapi`（编内核头，非扬声器“修复”）。

## 编译树

本机 `AOSPA_Z60U/source` → 符号链接到已有 `PenguinOS_cerro/source`（aospa-shadedark `calcite`，避免再占 400G）。

## 流程

```bash
source scripts/proxy-env.sh
bash scripts/sync-calcite.sh          # sync + apply-device-overlay + LFS
cd source && source build/envsetup.sh && lunch aospa_cerro-userdebug
./rom-build.sh cerro                  # 整包；不修声音、不刷机
bash scripts/github-snapshot.sh "0049 audio fixes removed; full build baseline"
```

## 验收

- 出包：`out/target/product/cerro/*.zip` / images
- 开机与否由用户刷测；本版**故意无声音修补**
