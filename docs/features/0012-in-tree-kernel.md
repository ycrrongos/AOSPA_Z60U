# 0012 — 源码编译 kernel/nubia/sm8650（关掉 QCOM kernel-platform 预编译）

## 问题

kati 通过后 ninja 立刻失败：

```
ninja: 'device/qcom/pineapple-kernel/Image', needed by 'out/target/product/cerro/kernel', missing and no known rule to make it
```

官方 AOSPA 机型用预编译 `device/qcom/<platform>-kernel`。`device/qcom/common/dlkm/kernel-platform.mk` 在 `TARGET_FWK_SUPPORTS_FULL_VALUEADDS` + pineapple 6.1 时被 include，默认：

```
TARGET_USES_KERNEL_PLATFORM ?= true
TARGET_PREBUILT_KERNEL := device/qcom/pineapple-kernel/Image
PRODUCT_COPY_FILES += .../Image:kernel
```

AOSPA 没有 `vendor/aospa/build/tasks/kernel.mk`，也没有 `TARGET_KERNEL_SOURCE` 的编译配方。cerro 的内核在 `kernel/nubia/sm8650`（local_manifest `cerro.xml`），229 上 Voltage 用 Lineage `vendor/voltage/build/tasks/kernel.mk` 编。229 也没有现成的 `pineapple-kernel` 预编译树。

## 决策

按 AGENTS：`TARGET_KERNEL_SOURCE := kernel/nubia/sm8650`，不要 `kernel_platform/` / bazel。

1. **产品 makefile 在 inherit `aospa-target.mk` 之前** 设 `TARGET_USES_KERNEL_PLATFORM := false`（`aospa_cerro.mk` + `sm8650-common/common.mk`）。`kernel-platform.mk` 用 `?=`，BoardConfig 太晚。
2. 把 Voltage/Lineage `kernel.mk` 放进 overlay `device/nubia/sm8650-common/build/tasks/kernel.mk`。AOSP `build/make/core/Makefile` 会 `-include device/*/*/build/tasks/*.mk`。
3. `build/BoardConfigKernel.mk` 从 Voltage `vendor/voltage/config/BoardConfigKernel.mk` 改写：不 inherit `vendor/voltage`；clang 用 `clang-stable`；rust 用 AOSPA `prebuilts/rust`；`merge_dtbs.py` 拷到 overlay `build/tools/`。由 **kernel.mk 在 tasks 阶段 include**（这时才有 `TARGET_OUT_INTERMEDIATES`）。
4. 缺的宿主工具用 local_manifest `cerro-kernel-tools.xml`：`prebuilts/kernel-build-tools`（AOSP `kernel/prebuilts/build-tools` @ `main-kernel-2025`）和 `prebuilts/tools-lineage`（Lineage @ `lineage-24.0`）。不要整仓 Voltage。
5. `TARGET_AUTO_COLLECT_KERNEL_MODULE_DEPS` 未接（cerro DT 也没开）。`TARGET_KERNEL_PLATFORM_TARGET` 保持空，不走 bazel `kernel/platform`。
6. CLO `vendor/qcom/build/tasks/kernel_definitions.mk` 在 `TARGET_PREBUILT_KERNEL` 为空时也会编内核，和 Lineage `kernel.mk` 抢 `dtb.img`。BoardConfig 把 `TARGET_PREBUILT_KERNEL` 指到 Lineage 将生成的 `obj/KERNEL_OBJ/arch/arm64/boot/Image`（**不要**设 `TARGET_FORCE_PREBUILT_KERNEL`，否则会真的走预编译、源码不编）。
7. `merge_dtbs.py` 需要 host `fdtput` / `fdtoverlaymerge`。AOSPA dtc 缺这两项；`scripts/patch-soong-dtc-fdt-tools.py` 补 `cc_binary_host`，`fdtoverlaymerge.c` 放 `prebuilts-cerro/dtc/`。

## 重放

```bash
source scripts/proxy-env.sh
# 若 prebuilts/kernel-build-tools 还不在树里：
# bash scripts/sync-calcite.sh
bash scripts/apply-device-overlay.sh
cd source && source build/envsetup.sh && lunch aospa_cerro-userdebug
./rom-build.sh cerro
```

`apply-device-overlay.sh` 会把 `local_manifests/cerro-kernel-tools.xml` 拷进 `.repo/local_manifests/`；真正拉预编译树要再 `repo sync` 这两条。本机也可从 229 只读 rsync 这两份 prebuilts（不含 `.git`）。

## 验证

- `get_build_var TARGET_USES_KERNEL_PLATFORM` 为 `false`
- ninja 不再要 `device/qcom/pineapple-kernel/Image`
- `out/target/product/cerro/obj/KERNEL_OBJ/arch/arm64/boot/Image` 由 `kernel/nubia/sm8650` 生成
