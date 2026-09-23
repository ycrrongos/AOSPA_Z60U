# 0009 — 去掉重复的 telephony-ext boot jar

## 问题

kati：`overriding commands for target boot-telephony-ext.art`。

## 决策

`aospa-target.mk` 已 `PRODUCT_BOOT_JARS += telephony-ext`。Lineage/Plasma `sm8650-common/common.mk` 又加一次。overlay 删掉 DT 这份 `PRODUCT_BOOT_JARS`，保留 `PRODUCT_PACKAGES`（重复包名无害）。

从 229 rsync DT 后要再删这一段。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
