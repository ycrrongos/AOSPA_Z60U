# 0032 — NXP eSE rc/xml 改 `*-qti` 名（不再永久 disable）

## 问题

QTI binary 已是 `*-qti` / `strongbox-nxp`，但 `init_rc` / vintf 仍用 AOSP 文件名，和 `hardware/nxp` 撞 install。0010 用 `enabled: false`。

## 决策

`scripts/patch-soong-nxp-authsecret.py`：复制并改名为 `*-qti.rc` / `*-qti.xml`（含 strongbox **vintf**，避免与 `external/libese` Google strongbox 抢同一 install 路径），更新 Android.bp，去掉 `enabled: false`。cerro 仍不包装 eSE（`TARGET_USES_ESE_KEYMINT=false`）；需要时打开即可，无文件名冲突。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
