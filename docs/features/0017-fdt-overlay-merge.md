# 0017 — Lineage `fdt_overlay_merge` 进 AOSPA libfdt（fdtoverlaymerge 要用）

## 问题

```
external/dtc/fdtoverlaymerge.c:131: error: use of undeclared identifier 'fdt_overlay_merge'
```

0012 只拷了 `fdtoverlaymerge.c` 并加了 host 二进制。QCOM `merge_dtbs.py` 对 `.dtbo` 调 `fdtoverlaymerge`，它调用 CAF/Lineage 的 `fdt_overlay_merge()`（把两个 overlay blob 合成一个）。上游 dtc / AOSPA libfdt 只有 `fdt_overlay_apply()`。

## 决策

不要整仓覆盖 `external/dtc`。从 Lineage `android_external_dtc` @ **lineage-23.2** 只拷 `libfdt/fdt_overlay.c`（含 merge 实现；`overlay_merge` / `overlay_fixup_phandles` 签名也改了，不能只 append）。

`scripts/patch-soong-dtc-fdt-tools.py`：

- 安装 `prebuilts-cerro/dtc/fdt_overlay.c` → `external/dtc/libfdt/fdt_overlay.c`
- 在 `libfdt.h` 声明 `fdt_overlay_merge`
- `version.lds` 导出该符号

不要改 `fdt_rw.c`（AOSPA 已有 `fdt_add_subnode_namelen` / `fdt_setprop_u32`）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
