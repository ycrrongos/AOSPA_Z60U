# 0007 — libinput_shim for libwfdnative

## 问题

soong：`libwfdnative`（nubia system_ext blob）依赖 `libinput_shim`。AOSPA `hardware/lineage/compat` 没有这份 shim。

## 决策

Lineage 源码在 `compat/libinput/{Input.cpp,android_view_KeyEvent.cpp}`，模块 `system_ext_specific: true`（与 blob 分区一致）。**禁止**整仓覆盖 compat。从 229 只拷这两个 cpp 到 `prebuilts-cerro/libinput_shim/`，`scripts/patch-lineage-compat-libinput-shim.py` 装进 AOSPA compat。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
