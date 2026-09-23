# 0024 — 补 Lineage `add-radio-file-sha1-checked`（radio 进 target_files）

## 问题

内核/分区镜像都编过，打包 `aospa_cerro-target_files` 时：

```
++++ radio  ++++
AssertionError: Failed to find aop.img
```

`vendor/nubia/cerro/radio/*.img` 已是真实 LFS blob（0022），`BoardConfigVendor.mk` 也把 `aop` 等写进 `AB_OTA_PARTITIONS`。`add_img_to_target_files.py` 的 `CheckAbOtaImages` 要在 `PRODUCT_OUT` 找到对应 `.img`。

## 决策

Lineage `extract-utils` 生成的 `vendor/nubia/cerro/Android.mk` 调用 `add-radio-file-sha1-checked`。宏在 `vendor/lineage/build/core/utils.mk`。AOSPA 只有 `add-radio-file`；未定义的 `$(call …)` 被吃掉，radio 不会拷到 `PRODUCT_OUT`。

overlay `build/radio-sha1.mk` 从 BoardConfig include（**不要**放 `build/tasks/`，tasks 在 Android.mk 之后才加载）。不要改 vendor 仓、不要 inherit `vendor/lineage`。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
