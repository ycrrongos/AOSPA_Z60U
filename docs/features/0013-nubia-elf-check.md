# 0013 — nubia vendor 预编译关掉 make check_elf（namespaced libgralloc.qti）

## 问题

ninja 编到约 35%：

```
libcommonchiutils.so: error: DT_NEEDED "libgralloc.qti.so" is not specified in shared_libs.
```

`vendor/nubia/sm8650-common/Android.bp` 里该模块 **已经** `shared_libs: ["libgralloc.qti", ...]`，并 import 了 `hardware/qcom-caf/sm8650/display/gralloc`。Soong 分析能过。失败的是 **make 侧** `check_elf_file`：`--shared-lib` 白名单只有 root namespace 的 `.so` 路径，namespaced CAF 模块只有 `meta_lic`，没有进 allowlist。

## 决策

不要整仓覆盖 `vendor/nubia`（local_manifest 的 extract-utils 树）。`scripts/patch-soong-nubia-elf-check.py` 给 `vendor/nubia/{sm8650-common,cerro}/Android.bp` 里所有 `cc_prebuilt_*` 加 `check_elf_files: false`。blob 的 DT_NEEDED 仍由 soong `shared_libs` 在分析期约束。

不要 `BUILD_BROKEN_*`。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```

`repo sync` 会还原 vendor Android.bp，必须再跑 apply。
