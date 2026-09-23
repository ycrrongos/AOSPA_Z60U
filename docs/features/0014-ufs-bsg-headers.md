# 0014 — recovery-ext UFS 走 BSG 内联头（不要空的 qti_kernel_headers）

## 问题

```
recovery-ufs-bsg.cpp: fatal error: 'scsi/ufs/ioctl.h' file not found
```

`vendor/qcom/opensource/recovery-ext` 的 soong 模块 `librecovery_updater` 依赖 `qti_kernel_headers`。AOSPA cerro 的这份是 stub（0002/0003，真正的 `headers_install` 还没接）。未设 `soong_config` `ufsbsg.ufsframework=bsg` 时会 `#include <scsi/ufs/ioctl.h>`。

## 决策

overlay `BoardConfigCommon.mk`：

```
$(call soong_config_set,ufsbsg,ufsframework,bsg)
```

走 `recovery-ufs-bsg.h` 里的 `_BSG_FRAMEWORK_KERNEL_HEADERS` 内联定义。官方 pineapple 也是 bsg。不要为此去 overlay 整份 kernel UAPI。

真正 UAPI 仍待 `generated_kernel_includes`（对照 Voltage soong generator）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
