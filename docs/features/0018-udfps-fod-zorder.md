# 0018 — UDFPS 内联 `FOD_PRESSED_LAYER_ZORDER`（不要空的 generated_kernel_headers）

## 问题

```
fingerprint/UdfpsExtension.cpp: fatal error: 'display/drm/sde_drm.h' file not found
```

`libudfps_extension.sm8650` 依赖 `generated_kernel_headers`，再 `#include <display/drm/sde_drm.h>`。AOSPA 这份 header lib 仍是 0002/0003 的空 stub；真正的 UAPI 在

`kernel/nubia/sm8650-modules/qcom/opensource/display-drivers/include/uapi/display/drm/sde_drm.h`

该头还会 `#include <drm/drm.h>`，不能只加 display-drivers 这一层路径。

## 决策

`UdfpsExtension.cpp` 只用 `FOD_PRESSED_LAYER_ZORDER`（`0x20000000u`）。overlay 里内联该宏，去掉对 stub `generated_kernel_headers` 的依赖。不要为此去 overlay 整份 display-drivers UAPI，也不要现在接 Voltage 的 `headers_install`。

Display HAL（composer / sde-drm）仍走 stub `qti_kernel_headers`，缺 `sde_drm.h` 时另做（真正 `generated_kernel_includes`）。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
