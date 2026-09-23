# 0033 — mkdir.mk 按 PRODUCT_PACKAGES 建目录（重开 soong mkdir）

## 问题

AOSPA `mkdir.mk` 给所有 soong mkdir 写 `$(LOCAL_SOONG_INSTALL_DIR)` 配方；QCOM `AndroidBoardCommon.mk` 也建同一路径 → kati overriding。0011 对三个模块 `enabled: false`。

## 决策

补丁 `vendor/aospa/build/core/mkdir.mk`：仅当模块在 `PRODUCT_PACKAGES` 时才定义 mkdir 配方。然后重新 `enabled` 那三个 CLO mkdir 模块。cerro 不 PACKAGE 它们，挂载点仍由 AndroidBoardCommon 创建。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
