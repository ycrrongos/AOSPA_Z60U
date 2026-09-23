# 0010 — 关掉与 AOSP 撞 init_rc 的 NXP QTI eSE HAL

## 问题

kati 连续撞 install 路径（QTI binary 改了模块名，**rc/xml 文件名没改**）。扫过 `hardware/nxp` vs `vendor/nxp` 的 `init_rc`，撞名只有这三份：

- `android.hardware.authsecret-service.nxp.rc`：AOSP KM300 vs QTI `*-qti`
- `android.hardware.security.keymint-service.strongbox.nxp.rc`：AOSP KM200 vs QTI KM300 `strongbox-nxp`
- `android.hardware.weaver-service.nxp.xml`：AOSP weaver `vintf_fragments` vs QTI `prebuilt_etc`

## 决策

cerro 是 pineapple，`keymint_vendor_board.mk` 已 `TARGET_USES_ESE_KEYMINT := false`（用 QTI TEE `keymint-service-qti`，不是 NXP strongbox）。
Soong 仍会给未 `enabled: false` 的 vendor binary 生成 install 规则。

`scripts/patch-soong-nxp-authsecret.py` 给这三份 QTI HAL 以及 weaver 那份 `prebuilt_etc` xml `enabled: false`。不要整仓覆盖 `vendor/nxp`。若以后真要 eSE，应给 QTI 的 rc/xml 改独立文件名再打开。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
