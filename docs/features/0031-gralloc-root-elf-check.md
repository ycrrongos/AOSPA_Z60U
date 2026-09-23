# 0031 — CAF gralloc 可见性 + 选择性 check_elf

## 问题

0003 给 `display/gralloc`、`libdebug` 加了**嵌套** `soong_namespace`，CLO 才能 `import` 路径。副作用：嵌套 NS 里的 `libgralloc.qti` **不向 make 导出** → 0013 批量 `check_elf_files: false`。

误判：「去掉嵌套 NS = 回 root」。`hardware/qcom-caf/sm8650/Android.bp` → `os_pickup_qssi.bp`，整棵 CAF 仍在父 NS。把该 NS 丢进 `PRODUCT_SOONG_NAMESPACES` 会导出过多模块并撞 install（如 strongbox vintf）。

## 决策

1. 去掉 gralloc/libdebug **嵌套** NS。
2. `os_pickup_qssi.bp` 空 namespace（无 `vendor/qcom/opensource/display` NS）。
3. 依赖 `libgralloc.qti` 的 `vendor/qcom/common` BP `import "hardware/qcom-caf/sm8650"`。
4. **不对**整棵 CAF 开 `PRODUCT_SOONG_NAMESPACES`。
5. `patch-soong-nubia-elf-check.py`：nubia extract 的 `cc_prebuilt_*` **批量** `check_elf_files: false`（Make 仍看不见 CAF-NS 的 DT_NEEDED；点关会无限打地鼠）。Soong import 修复保留。

FM 仍 `enabled: false`（system_ext 同名 HIDL）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
