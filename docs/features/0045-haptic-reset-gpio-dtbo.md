# 0045 — haptic reset-gpio 必须是 TLMM 120（改 common 全节点）

## 问题

common `zte-pineapple-common-overlay.dtsi` 里 `haptic_hv@5A` 的 `reset-gpio=<&tlmm 90>`。
cerro 硬件要用 **120**。只在 `zte-cerro-overlay.dtsi` 覆盖该属性时，DTBO 片段里
`&tlmm` **fixup 失败**（`0xffffffff`），实机仍读到 **90** → HAL/驱动都在跑但马达不振。

曾试 `/delete-node/` 整节点重建，合并 DTBO 后出现 Watchdog/相机 HAL 崩、boot 卡死，已回退。

## 做法

`scripts/patch-kernel-haptic-reset-gpio.py`：把 common 全节点里的 `90` 改成 `120`（挂 apply 链）。
另：`patch-kernel-haptic-custom-alloc.py`（0044）修 FIFO 堆分配。

## 验证

```bash
xxd .../haptic_hv@5A/reset-gpio   # 第二 cell = 0x78
cmd vibrator_manager synced oneshot -a 800 255
```

## 重放

```bash
bash scripts/apply-device-overlay.sh
# 重编刷 dtbo（+ vendor_dlkm 含新 haptic.ko）
```
