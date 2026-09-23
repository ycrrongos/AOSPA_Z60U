# 0035 — host `imgdiff`（`bootable/deprecated-ota`）

## 问题

编 `vendorimage` / recovery_from_boot 需要 `HOST_OUT_EXECUTABLES/imgdiff`。AOSPA calcite 未带 `bootable/deprecated-ota`；曾用 `BOARD_USES_FULL_RECOVERY_IMAGE` 绕过。

## 决策

- `local_manifests/cerro-imgdiff.xml` → `VoltageOS/bootable_deprecated-ota` @ `17`
- 本机可从 229 只读 rsync 同路径应急
- overlay **去掉** `BOARD_USES_FULL_RECOVERY_IMAGE`
- `scripts/patch-soong-deprecated-ota-imgdiff.py`：关掉 `non_ab_unit_tests`（calcite 上 health V4+V5 同图冲突）；只保留 host `imgdiff`

```bash
source scripts/proxy-env.sh
# 若尚无树：
repo sync bootable/deprecated-ota
bash scripts/apply-device-overlay.sh
m imgdiff
```

## 验证

`out/host/linux-x86/bin/imgdiff` 存在；BoardConfig 无 `BOARD_USES_FULL_RECOVERY_IMAGE`。
