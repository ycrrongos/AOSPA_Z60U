# 0019 — 内核编译用 Soong 默认 clang（AOSPA `clang-stable` 没有编译器）

## 问题

```
Building Kernel Config
HOSTCC scripts/basic/fixdep
/bin/sh: clang: 未找到命令
```

0012 把 Lineage `kernel.mk` 的 clang 指到 `prebuilts/clang/host/linux-x86/clang-stable`。Voltage/Lineage 这份是完整工具链（或指向当前 clang 的 symlink）。AOSPA calcite 的 `clang-stable/bin` 只有 `clang-format` / `git-clang-format`。真正的编译器在 Soong 默认 `clang-r547379`（`LLVM_PREBUILTS_VERSION`）。

另外 `TARGET_KERNEL_NO_GCC=true` 分支没设 `HOSTCC=` 绝对路径，`LLVM=1` 会用 PATH 里的 `clang`；`KERNEL_CC` 在 `CCACHE_BIN` 为空时变成 `CC=" clang"`（前导空格）。

## 决策

overlay `build/BoardConfigKernel.mk`：

- `clang-stable/bin/clang` 存在才用它
- 否则用 `LLVM_PREBUILTS_VERSION`，再否则 `clang-r547379`
- `KERNEL_NO_GCC` 分支同样设 `HOSTCC`/`HOSTCXX`/`HOSTAR`/`HOSTLD`/`LD`/`AR` 绝对路径

`build/tasks/kernel.mk`：`KERNEL_CC` 用 `$(TARGET_KERNEL_CLANG_PATH)/bin/clang`，不要空 ccache 前缀。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
