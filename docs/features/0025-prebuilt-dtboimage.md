# 0025 — 提早定义 BOARD_PREBUILT_DTBOIMAGE（target_files 要 dtbo.img）

## 问题

radio（0024）已进 `RADIO/`。打包继续失败：

```
AssertionError: Failed to find dtbo.img
```

`AB_OTA_PARTITIONS` 有 `dtbo`，`out/target/product/cerro/` 没有 `dtbo.img`。`TARGET_NEEDS_DTBOIMAGE := true`，merge_dtbs 已产出 `DTB_OBJ/out/*.dtbo`。

## 决策

AOSP `build/make/core/Makefile` 只在 **`ifdef BOARD_PREBUILT_DTBOIMAGE`** 时生成 `$(PRODUCT_OUT)/dtbo.img`（拷贝 + AVB footer）。这发生在 `device/*/build/tasks/*.mk` **之前**。

0012 把 Lineage `BoardConfigKernel.mk` 放到 kernel.mk（tasks）里 include，因为当时还没有 `TARGET_OUT_INTERMEDIATES`。于是 `BOARD_PREBUILT_DTBOIMAGE ?= …/DTBO_OBJ/…/dtbo.img` 设得太晚，Makefile 看不到。

AOSPA 官方 `vendor/aospa/target/board/BoardConfigKernel.mk` 用 `$(PRODUCT_OUT)/prebuilt_dtbo.img`，但只在 `BOARD_KERNEL_SEPARATED_DTBO` 时设置。cerro 用的是 `TARGET_NEEDS_DTBOIMAGE`，没有那个开关。

在 overlay `BoardConfigCommon.mk`（BoardConfig 阶段已有 `PRODUCT_OUT`）设：

```
BOARD_PREBUILT_DTBOIMAGE := $(PRODUCT_OUT)/prebuilt_dtbo.img
```

kernel.mk 的 merge_dtbs 配方会生成这个文件。不要开 `BOARD_KERNEL_SEPARATED_DTBO`（会和 QCOM `generate_extra_images.mk` 抢规则）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
