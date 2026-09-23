# 0036 — qseecomd exit 255：缺 `libdisplayconfig.qti`

## 症状

卡努比亚 logo。bootdiag：`zygote` 空、`crypto=unsupported`；dmesg 里 `vendor.qseecomd` 反复 **exit 255**，vold 死等 `android.security.maintenance`。

## 根因（strace）

1. RPMB / `/dev/0:0:0:49476` / `smcinvoke` **正常**；AVC 扫 `/dev/0:0:0:0` 是 GPT listener，不是死因（permissive 下 ioctl 成功）。
2. qseecomd 加载 `libops.so`（OPS listener）时 `dlopen` **`libdisplayconfig.qti.so`** → `ENOENT` → `exit_group(-1)`。
3. CAF `libdisplayconfig.qti` 在 `hardware/qcom-caf/sm8650` **空 soong_namespace** 里（0031 `os_pickup_qssi`），且该 NS **未**进 `PRODUCT_SOONG_NAMESPACES` → `m libdisplayconfig.qti` = unknown target；composer 等同理未装上。

日志：`cerro-bootdiag-pull5/qseecomd.strace`。

## 修复

1. **prebuilt** `device-overlay/nubia/sm8650-common/prebuilt/`：`libdisplayconfig.qti.so`（从 `libdisplayconfig.system.qti` 改 SONAME）+ `Android.bp`；`common.mk` `PRODUCT_PACKAGES += libdisplayconfig.qti`。
2. **`qseecomd.rc`**：改 `disabled` + `on late-fs` 再 `start`（persist 已挂）；`cerro/device.mk` `PRODUCT_COPY_FILES`；从 `proprietary-files.txt` 去掉原 rc 避免撞路径。

## 验证

刷 vendor（fastbootd）后：qseecomd **不再** exit 255；zygote 会起来。随后卡在 **surfaceflinger SIGABRT**（缺 HWC/composer，另案）。见 `cerro-bootdiag-pull6/`。

## 后续

0037：CAF display（composer / `libdisplayconfig.qti`）已在 soong 可编并装入 vendor；实机 `boot_completed`。见 `docs/features/0037-caf-display-hwc.md`。
