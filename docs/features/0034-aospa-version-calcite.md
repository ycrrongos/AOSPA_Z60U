# 0034 — `AOSPA_MAJOR_VERSION := calcite`

## 问题

calcite 树但 `vendor/aospa/target/product/version.mk` 仍 `beryl` → zip 名 `aospa-beryl-…`。

## 决策

`scripts/patch-aospa-version-calcite.py` 在 apply 时改成 `calcite`（带 MARKER，幂等）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
