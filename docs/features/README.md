# Features

每个功能一篇开发文档：`docs/features/<id>-<slug>.md`。

索引：

| ID | 文档 | 状态 |
|----|------|------|
| 0001 | [cerro-hals-caf](0001-cerro-hals-caf.md) | lunch 缺 `hardware/qcom-caf`；已写精简 local_manifest |
| 0002 | [soong-isolate-caf-common](0002-soong-isolate-caf-common.md) | soong 重复模块；删 CAF rfs/mount/hidl 副本，stub health |
| 0003 | [soong-display-namespaces](0003-soong-display-namespaces.md) | CLO vendor 引用缺失的 `hardware/qcom/display` |
| 0004 | [protobuf-21.7-nubiaparts](0004-protobuf-21.7-nubiaparts.md) | nubia blob 要 protobuf 21.7 full/lite；NubiaParts 改用 `co.aospa.resources` |
| 0005 | [vibrator-headers](0005-vibrator-headers.md) | CLO vibrator 补 `libqtivibratoreffect_headers`（不整仓覆盖 Lineage vibrator） |
| 0006 | [tinyxml2-qcwcn-namespace](0006-tinyxml2-qcwcn-namespace.md) | compat 补 `libtinyxml2-v34`；hostapd 用 CLO qcwcn 限定名 |
| 0007 | [libinput-shim](0007-libinput-shim.md) | compat 补 `libinput_shim`（nubia `libwfdnative`） |
| 0008 | [cneapp-vndfwk-symlink](0008-cneapp-vndfwk-symlink.md) | CneApp 要 Lineage 名的 `libvndfwk_detect_jni.qti` vendor symlink |
| 0009 | [telephony-ext-bootjar](0009-telephony-ext-bootjar.md) | 去掉与 `aospa-target.mk` 重复的 `telephony-ext` boot jar |
| 0010 | [nxp-authsecret-collision](0010-nxp-authsecret-collision.md) | 关掉与 AOSP 撞 init_rc 的 NXP QTI authsecret |
| 0011 | [mountpoint-mkdir-dup](0011-mountpoint-mkdir-dup.md) | 去掉与 AndroidBoardCommon 重复的 soong mkdir 挂载点 |
| 0012 | [in-tree-kernel](0012-in-tree-kernel.md) | 关掉 pineapple-kernel 预编译，用 Lineage kernel.mk 编 `kernel/nubia/sm8650` |
| 0013 | [nubia-elf-check](0013-nubia-elf-check.md) | nubia blob 的 make check_elf 看不见 namespaced `libgralloc.qti` |
| 0014 | [ufs-bsg-headers](0014-ufs-bsg-headers.md) | recovery-ext 用 BSG 内联头，避开 stub `qti_kernel_headers` |
| 0015 | [lineage-touch-sepolicy](0015-lineage-touch-sepolicy.md) | overlay 补 `hal_lineage_touch`；不要 inherit 整份 Lineage common sepolicy |
| 0016 | [platform-app-36-sepolicy](0016-platform-app-36-sepolicy.md) | 去掉 recovery 没有的 Plasma `platform_app_36` |
| 0017 | [fdt-overlay-merge](0017-fdt-overlay-merge.md) | Lineage `fdt_overlay_merge` 进 AOSPA libfdt，供 `fdtoverlaymerge` |
| 0018 | [udfps-fod-zorder](0018-udfps-fod-zorder.md) | UDFPS 内联 `FOD_PRESSED_LAYER_ZORDER`，避开 stub kernel headers |
| 0019 | [kernel-clang-path](0019-kernel-clang-path.md) | 内核用 Soong 默认 clang；AOSPA `clang-stable` 没有编译器 |
| 0020 | [libinput-shim-aospa-flags](0020-libinput-shim-aospa-flags.md) | libinput_shim 对齐 AOSPA `int32_t` flags，不要 `MotionFlag` |
| 0021 | [kernel-system-perl](0021-kernel-system-perl.md) | 内核 PERL 用系统 perl；tools-lineage perl 要 libcrypt.so.1 |
| 0022 | [vendor-git-lfs](0022-vendor-git-lfs.md) | `git lfs pull` 拉 NubiaCamera / radio，否则 signapk 不是 zip |
| 0023 | [kernel-board-platform](0023-kernel-board-platform.md) | 外部模块 make 传入 `TARGET_BOARD_PLATFORM`，否则 audio 缺 snd_event/swr |
| 0024 | [radio-sha1-checked](0024-radio-sha1-checked.md) | 补 Lineage `add-radio-file-sha1-checked`，否则 target_files 找不到 aop.img |
| 0025 | [prebuilt-dtboimage](0025-prebuilt-dtboimage.md) | BoardConfig 提早设 `BOARD_PREBUILT_DTBOIMAGE`，否则没有 dtbo.img |
| 0026 | [lineage-hal-fcm](0026-lineage-hal-fcm.md) | FCM 声明 livedisplay / high-touch HAL，否则 OTA VINTF 失败 |
| 0027 | [ramoops-console-pstore](0027-ramoops-console-pstore.md) | pineapple ramoops 划出 console；DTB 在 vendor_boot |
| 0028 | [bootdiag-metadata-soft-recovery](0028-bootdiag-metadata-soft-recovery.md) | 首启 dmesg 落 /metadata；超时软重启 recovery 保 pstore |
| 0029 | [bringup-disable-metadata-encryption](0029-bringup-disable-metadata-encryption.md) | 临时去掉 userdata wrappedkey/metadata_encryption 做 bringup |
| 0030 | [generated-kernel-headers](0030-generated-kernel-headers.md) | Voltage 式 headers_install，替换空 stub `qti_kernel_headers` |
| 0031 | [gralloc-root-elf-check](0031-gralloc-root-elf-check.md) | 去嵌套 gralloc NS + import 父 NS；nubia prebuilt 批量关 elf-check |
| 0032 | [nxp-qti-rc-rename](0032-nxp-qti-rc-rename.md) | NXP eSE rc/xml 改 `*-qti`，不再永久 disable |
| 0033 | [mkdir-mk-product-packages](0033-mkdir-mk-product-packages.md) | mkdir.mk 按 PACKAGES 建目录；重开 soong mkdir |
| 0034 | [aospa-version-calcite](0034-aospa-version-calcite.md) | zip/version 前缀改 calcite |
| 0035 | [host-imgdiff-deprecated-ota](0035-host-imgdiff-deprecated-ota.md) | 拉 deprecated-ota 编 imgdiff；去掉 FULL_RECOVERY |
| 0036 | [qseecomd-libdisplayconfig](0036-qseecomd-libdisplayconfig.md) | qseecomd 缺 `libdisplayconfig.qti`；late-fs 启动 |
| 0037 | [caf-display-hwc](0037-caf-display-hwc.md) | CAF HWC：soong NS + qtidisplay soong_config；编 composer/mapper |
| 0038 | [mediaserver-64b-setupwizard](0038-mediaserver-64b-setupwizard.md) | 缺 `ro.mediaserver.64b.enable` → 无 media.player；SetupWizard ANR |
| 0039 | [cerro-audio-dtbo-merge](0039-cerro-audio-dtbo-merge.md) | MTP audio DTBO 盖掉 Lineage zte 声卡；merge 后原地修 num-macros/routing |
| 0040 | [ir-hal-sepolicy](0040-ir-hal-sepolicy.md) | Lineage IR HAL 缺 file_contexts → system_server 死等 ConsumerIr |
| 0042 | [vibrator-effect-stream](0042-vibrator-effect-stream.md) | USE_EFFECT_STREAM + richtap FIFO；CLO oneshot 改走 effect_stream |
| 0043 | [phantom-h2w-jack](0043-phantom-h2w-jack.md) | 无 3.5mm；MTP Headset Jack 幽灵 h2w/LINE 抢路由 |
| 0044 | [haptic-custom-fifo-alloc](0044-haptic-custom-fifo-alloc.md) | haptic_hv custom FIFO 少分配 `sizeof(int)` → 修 kvzalloc |
| 0045 | [haptic-reset-gpio-dtbo](0045-haptic-reset-gpio-dtbo.md) | cerro reset-gpio=120 须整节点重写，否则 DTBO phandle 失效停在 90 |
| 0046 | [unicom-cu-openmkt-mbn](0046-unicom-cu-openmkt-mbn.md) | mbn_sw 列了 CU OpenMkt 但 modem.img 无文件 → 联通停 LTE |
| 0047 | [awinic-haptic-hv-module](0047-awinic-haptic-hv-module.md) | Voltage `haptic.ko`（AWINIC_HAPTIC_HV）；无模块则 HAL 空转无触感 |
| 0048 | [github-version-snapshots](0048-github-version-snapshots.md) | 每版 `github-snapshot` 推 GitHub + 镜像 Cursor 聊天，可回滚 |
