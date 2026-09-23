# 0023 — 内核外部模块传入 TARGET_BOARD_PLATFORM

## 问题

内核 `Image` 已编过（0019/0021）。`TARGET_KERNEL_EXT_MODULES` 编 `audio-kernel` 时 modpost：

```
ERROR: modpost: "snd_event_client_register" [.../ipc/gpr_dlkm.ko] undefined!
ERROR: modpost: "swr_driver_register" [.../asoc/codecs/swr_dmic_dlkm.ko] undefined!
```

实际命令是 `BOARD_PLATFORM=`（空）。`audio-kernel/Makefile` 写 `BOARD_PLATFORM=$(TARGET_BOARD_PLATFORM)`，Lineage `kernel.mk` 的 `make-external-module-target` 原先不传这个变量。

## 决策

`soc/Kbuild` / `asoc/Kbuild` 用 `ifeq ($(BOARD_PLATFORM), pineapple)` 才 include `pineappleauto.conf`（`CONFIG_SND_EVENT=m`、`CONFIG_SOUNDWIRE=m`）。`ipc/` 和部分 codec 用 `CONFIG_ARCH_PINEAPPLE`（GKI `.config` 已是 y），所以 `gpr_dlkm` / `swr_dmic` 会编，`snd_event_dlkm` / `swr_dlkm` 不会。

在 overlay `BoardConfigKernel.mk` 加 `KERNEL_MAKE_FLAGS += TARGET_BOARD_PLATFORM=$(TARGET_BOARD_PLATFORM)`。不要改 sm8650-modules 源码（会被 sync 覆盖）。display/camera/bt 的 Makefile 同样读这个变量。

## 重放

```bash
bash scripts/apply-device-overlay.sh
```
