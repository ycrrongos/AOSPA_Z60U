# 0030 — Voltage 式 `headers_install`（替换空 stub `qti_kernel_headers`）

## 问题

0002/0003 在 CAF `Android.bp` 里放了空的 `generated_kernel_header_defaults`，只为过 soong。`qti_kernel_headers` / `generated_kernel_headers` 没有 UAPI，于是：

- recovery-ext 只能走 BSG 内联（0014）
- UDFPS 只能内联 `FOD_PRESSED_LAYER_ZORDER`（0018）
- 其它依赖内核头的模块会缺 `linux/*.h` / audio UAPI

229 Voltage 用 `vendor/voltage/build/soong` 的 `voltage_generator` 真跑 `headers_install`，再 `clean_headers.sh`，并用脚本灌 SM8650 out-of-tree audio UAPI。

## 决策

不整仓 Voltage。在 cerro 设备树里接同款流水线：

| 路径 | 作用 |
|------|------|
| `device/.../build/soong/` | `cerro_generator` + `generated_kernel_includes` |
| `build/BoardConfigKernel.mk` | 早 include（BoardConfigCommon），供 soong 看见 `KERNEL_*` |
| `build/BoardConfigSoong.mk` | `cerroVarsPlugin` 导出 make→soong |
| `build/tools/run-headers-install.sh` | 实际跑 `headers_install`（不把 `KERNEL_MAKE_FLAGS` 塞进 soong.variables，避免引号弄坏 JSON） |
| `build/tools/clean_headers.sh` | 同 Voltage |
| `build/tools/stage-audio-kernel-uapi.sh` | 灌 audio-kernel UAPI + strip `__user` 等 |
| `scripts/patch-soong-isolate-caf-common.py` | CAF defaults 挂 `generated_headers: ["generated_kernel_includes"]` |

不设 `TARGET_KERNEL_PLATFORM_TARGET`（不走 bazel）。`TARGET_KERNEL_NO_GCC` 下 `KERNEL_CROSS_COMPILE` 可为空（与 Voltage 一致）。

0014 / 0018 的内联 workaround **先保留**（仍正确）；真正头文件齐后可再考虑改回依赖 header lib。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```

## 验证

- `hardware/qcom-caf/common/Android.bp` 的 defaults 含 `generated_kernel_includes`
- soong 能解析 `device/nubia/sm8650-common/build/soong` 的 `cerro_generator`
- ninja 会生成 `generated_kernel_includes`；产物里有 `usr/include/...`，audio 有 `usr/include/audio/linux/msm_audio.h`（需已 sync `kernel/nubia/sm8650-modules`）

## 对照

本机只读镜像：`ref-229/source/vendor/voltage/build/soong/`。
