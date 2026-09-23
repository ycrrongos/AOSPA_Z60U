# 0005 — CLO vibrator 补 libqtivibratoreffect_headers

## 问题

soong：`libqtivibratoreffect.nubia_sm8650-richtap` 依赖 `libqtivibratoreffect_headers`。
Lineage / Voltage 的 `vendor/qcom/opensource/vibrator/effect/Android.bp` 有这份 `cc_library_headers`。
AOSPA CLO 同仓只有 `libqtivibratoreffect` 共享库（`export_include_dirs`），没有 headers 模块名。

## 决策

**禁止**整份覆盖 Lineage vibrator：Voltage/Lineage AIDL 已拆成 `vibratorOL` / `vibratorSel` 等，AOSPA calcite 仍是单份 `vendor.qti.hardware.vibrator.impl`，并硬链 `libqtivibratoreffect`。
只在 CLO `effect/Android.bp` 插入 headers 模块，脚本 `scripts/patch-soong-vibrator-headers.py`。overlay 的 richtap `Android.bp` 保持 Plasma 原样（下次从 229 rsync 不会丢补丁）。

AOSPA AIDL **已**通过 `scripts/patch-soong-vibrator-effect-stream.py` 消费 `soong_config qti_vibrator`（见 [0042](0042-vibrator-effect-stream.md)）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```

`repo sync` 会还原 `vendor/qcom/opensource/vibrator`；必须再跑 apply。
