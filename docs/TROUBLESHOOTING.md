# TROUBLESHOOTING

固定排障日志。每次卡住、踩坑、误判必须记在这里（症状 → 试过什么 → 根因 → 解决办法）。不要只记在聊天里。

## 模板

```markdown
### YYYY-MM-DD — 简短标题

- **症状**：
- **环境**：（分支 / lunch / 命令）
- **试过**：
- **根因**：
- **解决**：
```

---

### 2026-08-24 — lunch 缺 hardware/qcom-caf/common/common.mk

- **症状**：`lunch aospa_cerro-userdebug` 失败，`device/nubia/sm8650-common/common.mk:9` inherit 不到 `hardware/qcom-caf/common/common.mk`。
- **环境**：AOSPA calcite 已 `repo sync`；overlay 已打上 Plasma 剥品牌 DT。
- **试过**：对照 229 Voltage 主 manifest（CAF 编进 Voltage 官方 xml）、OnlyAOSP 整份 `cerro-hals.xml`。
- **根因**：AOSPA 是 CLO，没有 Lineage 的 `hardware/qcom-caf/*` 路径；cerro DT 仍按 Lineage 路径 inherit。不能把 OnlyAOSP 整份 HAL overlay 盖掉 CLO 的 `device/qcom/sepolicy_vndr` / `hardware/qcom/bootctrl`。
- **解决**：新增 `source/.repo/local_manifests/cerro-hals.xml`，只拉缺失的 qcom-caf + lineage sepolicy/interfaces + st-hal。**不要**覆盖 AOSPA 已有的 `packages/resources/devicesettings`。文档：`docs/features/0001-cerro-hals-caf.md`。

### 2026-08-24 — lunch TARGET_BOARD_PLATFORM / beans / inherit-product-if-exists

- **症状**：CAF 补齐后 `lunch aospa_cerro-userdebug` 报 `No beans found for the device (cerro)`，随后 `device/qcom/common/common.mk`：`TARGET_BOARD_PLATFORM is not defined yet`。
- **根因**：1) `aospa-target.mk` 在 BoardConfig 之前 inherit QCOM common，product mk 必须提前设 `TARGET_BOARD_PLATFORM := pineapple`。2) `vendor/aospa/products/AndroidProducts.mk` 用 `inherit-product-if-exists` 挂 cerro，会在解析全部产品时提前 inherit；官方机型用 `PRODUCT_MAKEFILES` + `ifeq (aospa_xxx,$(TARGET_PRODUCT))`。
- **解决**：`aospa_cerro.mk` 加 ifeq 与 pineapple；apply 脚本改成 `PRODUCT_MAKEFILES += device/nubia/cerro/aospa_cerro.mk`。

  `No beans found` 来自 `vendor/aospa/build/tools/barista.py`（官方机型才有 `beans.xml`）。cerro 用 local_manifest，可忽略。

  lunch 成功后 `AOSPA_VERSION=beryl-...`、`PLATFORM_VERSION=16`：`repo` 确认在 `calcite`（`.repo/manifests.git` merge=`refs/heads/calcite`）。官方 calcite 的 `vendor/aospa/target/product/version.mk` 仍写 `AOSPA_MAJOR_VERSION := beryl`，`default.xml` 的 aospa remote 也仍是 `revision="beryl"`。这是上游命名滞后，不是 init 错分支。

### 2026-08-25 — soong: rfs_* already defined (qcom-caf vs device/qcom/common)

- **症状**：`rom-build.sh cerro -j 4` 在 soong bootstrap 失败，大量 `hardware/qcom-caf/common/Android.bp` 模块与 `device/qcom/common/Android.bp` 重复（`rfs_*_symlink`、`vendor_*_mountpoint`、memtrack、fwk-detect）。
- **根因**：cerro DT（Lineage）inherit `hardware/qcom-caf/common/common.mk`；AOSPA `aospa-target.mk` 已经 inherit `device/qcom/common/common.mk`。两边定义同一批 RFS/mountpoint Soong 模块。CAF 源码树仍需要（audio/display HAL），但不能 inherit 那份 common.mk。
- **解决**：`device-overlay/nubia/sm8650-common/common.mk` 去掉该 inherit。Soong **仍会扫描**整份 `hardware/qcom-caf/common/Android.bp`，不能整文件套 `soong_namespace {}`：Soong 要求 namespace 必须是该文件第一个模块，那样会把 `qti_kernel_headers` / `audio_kernel_headers` 藏进 namespace，而 `hardware/qcom-caf/sm8650` 自己已是 `os_pickup_qssi.bp` namespace，跨 namespace 找不到这些头。正确做法是从 CAF `Android.bp` **删掉**与 CLO 重复的 `install_symlink` / `mkdir` / 三个 HIDL 名，内核头留在 root；再把 `fwk-detect`、`memtrack` 和 Lineage `health` 的 `Android.bp` 换成 stub。`/* */` 包一整份 bp 不可行（版权块里的 `*/` 会提前闭合）。脚本：`scripts/patch-soong-isolate-caf-common.py`。

### 2026-08-25 — soong: hardware/qcom/display namespace does not exist

- **症状**：重复模块修好后，`rom-build.sh cerro -j 4` 报 `namespace hardware/qcom/display{,/gralloc,/libdebug} does not exist`，以及 `vendor/qcom/opensource/display does not exist`。
- **环境**：AOSPA calcite + Lineage CAF sm8650 display；对照 229 OnlyAOSP `cerro-hals.xml`（密码 SSH，未写入仓库）。
- **试过**：OnlyAOSP 同样只 link `os_pickup_qssi.bp`，另两条 os_pickup mk 会盖 CLO，不用。空 stub `hardware/qcom/display` 不够：import 不传递，Adreno 看不到 `libgralloc.qti`。
- **根因**：`vendor/qcom/common` 按官方 AOSPA 平台 xml 的 `hardware/qcom/display` 写 import；calcite 无 pineapple 这份。cerro 显示 HAL 在 `hardware/qcom-caf/sm8650/display`。`os_pickup_qssi.bp` 还 import 了树里没有的 `vendor/qcom/opensource/display`。
- **解决**：CAF gralloc/libdebug 文件头加 `soong_namespace` 并 import 父 namespace `hardware/qcom-caf/sm8650`；vendor/qcom/common import 改到 CAF 路径；`os_pickup_qssi.bp` 改 import 这两个 namespace。`vendor/nubia/sm8650-common/Android.bp` 丢掉不存在的 Lineage namespace（wlan/display/dataservices）；CLO 对应模块在 root，仍能看见。`hardware/lineage/interfaces/power-libperfmgr` import 缺失的 `hardware/google/pixel`，cerro 不用该 HAL，stub 掉。nubia 的 `vendor.qti.hardware.fm@1.0` 预编译与 AOSPA system_ext 分区冲突，对该模块 `enabled: false`。脚本：`scripts/patch-soong-display-namespaces.py`、`scripts/patch-soong-isolate-caf-common.py`。文档：`docs/features/0003-soong-display-namespaces.md`。

### 2026-08-25 — soong: libprotobuf-cpp-full-21.7 / org.lineageos.settings.resources

- **症状**：display/FM 修完后 soong 报 `undefined module "libprotobuf-cpp-full-21.7"`（nubia vendor bp）和 `org.lineageos.settings.resources`（NubiaParts）。
- **根因**：Lineage extract-utils blob 依赖 compat 里的 protobuf 21.7 SONAME；AOSPA `hardware/lineage/compat` 只有 3.9.1/v29。AOSPA 把 `packages/resources/devicesettings` 模块改名为 `co.aospa.resources`。不能整份覆盖 Lineage compat。
- **解决**：从 229 Voltage compat 只拷 21.7 `.so` 到 `prebuilts-cerro/`，`scripts/patch-lineage-compat-protobuf.py` 装进 AOSPA compat。overlay `parts/Android.bp` 改用 `co.aospa.resources`。文档：`docs/features/0004-protobuf-21.7-nubiaparts.md`。

### 2026-08-25 — soong: libvmmem missing

- **症状**：`libcpion` 依赖 `libvmmem`，树里没有 `vendor/qcom/opensource/libvmmem`。
- **根因**：OnlyAOSP cerro-hals 有这份 Lineage 工程；AOSPA CLO 没有。按缺项补，不是整份 overlay。
- **解决**：`cerro-hals.xml` 增加 `LineageOS/android_vendor_qcom_opensource_libvmmem` @ lineage-23.2，`repo sync` 该路径。清单真相源改到仓库根 `local_manifests/`，apply 时拷回 `.repo/local_manifests/`。

### 2026-08-25 — soong: libprotobuf-cpp-lite-21.7 / libqtivibratoreffect_headers

- **症状**：`libvmmem` 补上后 soong 报 `liblocation_api_msg` 依赖 `libprotobuf-cpp-lite-21.7`；`libqtivibratoreffect.nubia_sm8650-richtap` 依赖 `libqtivibratoreffect_headers`。
- **根因**：0004 只拷了 protobuf **full** 21.7；lite 是另一份 SONAME。AOSPA CLO vibrator 没有 Lineage 的 headers 模块名；不能整仓覆盖 Lineage vibrator（AIDL 布局不同）。
- **解决**：同样从 229 只拷 lite `.so`，`patch-lineage-compat-protobuf.py` 一并安装。`scripts/patch-soong-vibrator-headers.py` 只给 CLO `effect/Android.bp` 加 headers 模块。文档：`docs/features/0004-protobuf-21.7-nubiaparts.md`、`docs/features/0005-vibrator-headers.md`。

### 2026-08-25 — soong: libtinyxml2-v34 / lib_driver_cmd_qcwcn namespace

- **症状**：`libsnapdragoncolor-manager` 依赖 `libtinyxml2-v34`；`hostapd` 依赖 `lib_driver_cmd_qcwcn`，Soong 提示该模块在 `hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib`。
- **试过**：不要为此去拉 OnlyAOSP 的 `hardware/qcom-caf/wlan`（AOSPA 已有 CLO `hardware/qcom/wlan`）。
- **根因**：AOSPA lineage compat 的 vndk/v34 缺 tinyxml2；Lineage DT 用无 namespace 的 `BOARD_*_PRIVATE_LIB`，CLO 把 qcwcn 放进 nested soong_namespace。
- **解决**：只拷 `libtinyxml2-v34.so` 进 compat。overlay `BoardConfigCommon.mk` 改成 `//hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib:lib_driver_cmd_qcwcn`（同 `device/qcom/wlan/vendor_board_common.mk`）。文档：`docs/features/0006-tinyxml2-qcwcn-namespace.md`。

### 2026-08-25 — soong: libinput_shim missing

- **症状**：`libwfdnative` 依赖 `libinput_shim`。
- **根因**：Lineage compat 有 `libinput/` shim；AOSPA 这份 compat 没有。不能整仓覆盖。
- **解决**：从 229 只拷 `Input.cpp` / `android_view_KeyEvent.cpp`，`scripts/patch-lineage-compat-libinput-shim.py`。文档：`docs/features/0007-libinput-shim.md`。

### 2026-08-25 — kati: CneApp.libvndfwk_detect_jni.qti_vendor_symlink

- **症状**：soong 通过后 ckati 报 `CneApp` required 模块不存在；提示可设 `BUILD_BROKEN_MISSING_REQUIRED_MODULES`。
- **试过**：不要开 BUILD_BROKEN。CAF isolate 删的是 CAF common 里重复的 rfs/mount symlink，不是这份。
- **根因**：extract-utils 模块名带 `_vendor_symlink`；CLO telephony 叫 `_symlink` 且在别的 soong_namespace。
- **解决**：overlay DT `Android.bp` 用 Lineage 名字加 `install_symlink`。vendor bp 已 import `device/nubia/sm8650-common`。文档：`docs/features/0008-cneapp-vndfwk-symlink.md`。

### 2026-08-25 — kati: boot-telephony-ext.art override

- **症状**：CneApp symlink 修好后，ckati `overriding commands for target boot-telephony-ext.art`。
- **根因**：`aospa-target.mk` 已 `PRODUCT_BOOT_JARS += telephony-ext`，Plasma DT `common.mk` 又加一次。
- **解决**：overlay 删掉 DT 的 `PRODUCT_BOOT_JARS += telephony-ext`。文档：`docs/features/0009-telephony-ext-bootjar.md`。

### 2026-08-25 — kati: authsecret-service.nxp.rc override

- **症状**：`overriding commands for target vendor/etc/init/android.hardware.authsecret-service.nxp.rc`（AOSP `hardware/nxp` vs QTI `vendor/nxp`，vintf 同样撞名）。
- **根因**：QTI binary 改名为 `*-qti`，init_rc/vintf 仍用 AOSP 文件名。Soong 即使没 PACKAGE 也会给 vendor binary 写 install 规则。cerro 不用 NXP eSE keymint。
- **解决**：`scripts/patch-soong-nxp-authsecret.py` 关掉 QTI `authsecret-service.nxp-qti`、`keymint-service.strongbox-nxp`、`weaver-service.nxp-qti` 以及 weaver 那份 `prebuilt_etc` xml。文档：`docs/features/0010-nxp-authsecret-collision.md`。

### 2026-08-25 — kati: vendor/firmware_mnt mkdir override

- **症状**：`overriding commands for target vendor/firmware_mnt`（aospa mkdir.mk vs AndroidBoardCommon.mk）。
- **根因**：AOSPA 全局 `TARGET_FWK_SUPPORTS_FULL_VALUEADDS := true`，会 include QCOM AndroidBoardCommon 的 make mkdir；Lineage DT 又 PRODUCT_PACKAGES 了 soong `vendor_*_mountpoint`。
- **解决**：DT 去掉 PRODUCT_PACKAGES 仍不够（mkdir.mk 无条件写配方）。`scripts/patch-soong-qcom-mkdir-mountpoints.py` 关掉那三个 soong mkdir。文档：`docs/features/0011-mountpoint-mkdir-dup.md`。

### 2026-08-25 — ninja: device/qcom/pineapple-kernel/Image missing

- **症状**：soong/kati 通过后 ninja：`device/qcom/pineapple-kernel/Image` needed by `out/target/product/cerro/kernel`，没有规则。
- **根因**：AOSPA `kernel-platform.mk` 默认 `TARGET_USES_KERNEL_PLATFORM=true`，把官方预编译 Image 拷到 `$(PRODUCT_OUT)/kernel`。AOSPA 没有 Lineage `kernel.mk`；cerro 内核源在 `kernel/nubia/sm8650`。229 也没有 pineapple-kernel 预编译。
- **试过**：不要改用 `kernel_platform/` bazel。BoardConfig 里设 `TARGET_USES_KERNEL_PLATFORM` 太晚（product 已经 `?=` 成 true）。
- **解决**：`aospa_cerro.mk` / `common.mk` 在 inherit `aospa-target.mk` 前设 `TARGET_USES_KERNEL_PLATFORM := false`。overlay `build/tasks/kernel.mk` + `build/BoardConfigKernel.mk` 编源码树；`merge_dtbs.py` 放 overlay。`prebuilts/kernel-build-tools` 与 `prebuilts/tools-lineage` 走 `local_manifests/cerro-kernel-tools.xml`。文档：`docs/features/0012-in-tree-kernel.md`。

### 2026-08-25 — kati: dtb.img override (Lineage kernel.mk vs CLO kernel_definitions.mk)

- **症状**：`device/nubia/sm8650-common/build/tasks/kernel.mk` overriding `out/target/product/cerro/dtb.img`，先前在 `vendor/qcom/build/tasks/kernel_definitions.mk`。
- **根因**：AOSPA `BoardConfigKernel.mk` 在 `TARGET_PREBUILT_KERNEL` 为空时设 `TARGET_COMPILE_WITH_MSM_KERNEL`；CLO `kernel_definitions.mk` 同样在变量为空时编 QGKI，和 Lineage `kernel.mk` 抢 `dtb.img`。CLO 还用错相对路径 grep `vendor/pineapple_GKI.config`。
- **解决**：BoardConfig 给 `TARGET_PREBUILT_KERNEL` 填 Lineage 将要生成的 Image 路径（`$(PRODUCT_OUT)/obj/KERNEL_OBJ/arch/arm64/boot/Image`）。CLO 任务整份跳过；Lineage `kernel.mk` 只有 `TARGET_FORCE_PREBUILT_KERNEL` 才会改用预编译，源码仍会编。不要打 `BUILD_BROKEN_DUP_RULES`。

### 2026-08-25 — ninja: host fdtput missing for dtb.img

- **症状**：kati 过了，ninja：`out/host/linux-x86/bin/fdtput` needed by `dtb.img`，无规则。
- **根因**：Lineage `kernel.mk` + QCOM `merge_dtbs.py` 要 `fdtget`/`fdtput`/`fdtoverlay`/`fdtoverlaymerge`/`ufdt_apply_overlay`。AOSPA `external/dtc` 有 `fdtput.c` 但没编 host 二进制；没有 `fdtoverlaymerge.c`（Lineage 多出来的）。
- **解决**：`prebuilts-cerro/dtc/fdtoverlaymerge.c` + `scripts/patch-soong-dtc-fdt-tools.py` 给 AOSPA dtc 加两个 `cc_binary_host`。不要整仓覆盖 `external/dtc`。

### 2026-08-25 — ninja: libcommonchiutils DT_NEEDED libgralloc.qti

- **症状**：`check_elf_file`：`libcommonchiutils.so` DT_NEEDED `libgralloc.qti.so` is not specified in shared_libs。Android.bp **已经**写了 `libgralloc.qti`。
- **根因**：0003 把 CAF gralloc 放进 soong_namespace。Soong 分析能解析；make `check_elf_file` 的 `--shared-lib` 白名单只有 root namespace 产物，ninja 里 `libgralloc.qti` 只出现 `meta_lic`。
- **解决**：`scripts/patch-soong-nubia-elf-check.py` 给 nubia `cc_prebuilt_*` 加 `check_elf_files: false`。文档：`docs/features/0013-nubia-elf-check.md`。display 脚本关 FM 的检测窗口要盖过插在 `name:` 后面的 check_elf 注释，否则会重复 `enabled: false`。

### 2026-08-25 — ninja: scsi/ufs/ioctl.h not found (librecovery_updater)

- **症状**：`vendor/qcom/opensource/recovery-ext/.../recovery-ufs-bsg.cpp`：`scsi/ufs/ioctl.h` file not found。
- **根因**：`qti_kernel_headers` 仍是空 stub。未设 `ufsbsg.ufsframework=bsg` 时会去 include 内核 UAPI。
- **解决**：BoardConfig `$(call soong_config_set,ufsbsg,ufsframework,bsg)`。文档：`docs/features/0014-ufs-bsg-headers.md`。

### 2026-08-25 — sepolicy: unknown type hal_lineage_touch_default

- **症状**：`recovery_sepolicy.cil`：`hal_lineage_touch_default.te` 的 `rw_dir_file` 展开后 `unknown type hal_lineage_touch_default`。UFS BSG（0014）已过。
- **试过**：不要 include 整份 `device/lineage/sepolicy/common/sepolicy.mk`（会和 AOSPA 已有的 `hal_lineage_health` public 属性撞）。
- **根因**：类型/属性在 Lineage `common/{public,vendor,dynamic}`。BoardConfig 只拉了 libperfmgr + QCOM vndr。AOSPA 只定义了 health，没有 touch。overlay 原先只写了 allow，没声明 type。
- **解决**：overlay 按 AOSPA health 写法补 public attributes + vendor domain/service + private clients。文档：`docs/features/0015-lineage-touch-sepolicy.md`。

### 2026-08-25 — sepolicy: unknown type platform_app_36

- **症状**：`recovery_sepolicy.cil`：`platform_app.te` `allow platform_app_36 hal_camera_default:binder`。0015 已过。
- **根因**：Plasma 给 NubiaCamera API 36 写了 Treble 映射类型。recovery 单体策略只有 `platform_app`，没有 `platform_app_36`。
- **解决**：删掉这四行；同文件已有 `platform_app` 等价规则。不要在 overlay 里声明 `type platform_app_36`。文档：`docs/features/0016-platform-app-36-sepolicy.md`。

### 2026-08-25 — ninja: undeclared fdt_overlay_merge

- **症状**：`external/dtc/fdtoverlaymerge.c:131`：`use of undeclared identifier 'fdt_overlay_merge'`。sepolicy 0015/0016 已过。
- **根因**：CAF/Lineage 的 `fdtoverlaymerge` 要把多个 `.dtbo` 合成一个，调用 `fdt_overlay_merge()`。AOSPA / 上游 libfdt 只有 `fdt_overlay_apply()`（overlay 打到 base DT）。0012 只加了工具源码，没加 API。
- **解决**：从 Lineage 23.2 拷 `libfdt/fdt_overlay.c`，脚本补 `libfdt.h` / `version.lds`。不要整仓覆盖 dtc。文档：`docs/features/0017-fdt-overlay-merge.md`。

### 2026-08-25 — ninja: display/drm/sde_drm.h not found (UdfpsExtension)

- **症状**：`libudfps_extension.sm8650`：`#include <display/drm/sde_drm.h>` file not found。0017 的 fdtoverlaymerge 已过。
- **根因**：模块依赖空的 `generated_kernel_headers`。头在 display-drivers UAPI，且会再 include `<drm/drm.h>`。
- **解决**：overlay 内联 `FOD_PRESSED_LAYER_ZORDER`（与内核 `0x20000000u` 一致），去掉 stub header_libs。不要为此 overlay 整份 UAPI。文档：`docs/features/0018-udfps-fod-zorder.md`。

### 2026-08-25 — ninja: kernel olddefconfig, clang not found

- **症状**：`Building Kernel Config` → `HOSTCC scripts/basic/fixdep` → `clang: 未找到命令`。0018 UDFPS 已过。
- **根因**：0012 用 `clang-stable`。AOSPA 这份只有 format 工具。`KERNEL_NO_GCC` 分支没传 `HOSTCC=` 绝对路径；空 `CCACHE_BIN` 让 `CC=" clang"`。
- **解决**：`clang-stable/bin/clang` 没有就改用 `LLVM_PREBUILTS_VERSION`（`clang-r547379`），HOSTCC 走绝对路径。文档：`docs/features/0019-kernel-clang-path.md`。

### 2026-08-25 — ninja: no member named MotionFlag (libinput_shim)

- **症状**：`hardware/lineage/compat/libinput/Input.cpp`：`android::MotionFlag` 不存在。0019 的 clang 路径这轮还没编到内核。
- **根因**：0007 的 Voltage shim 转到 Lineage 24 的 `ftl::Flags<MotionFlag>`。AOSPA calcite 的 `MotionEvent::initialize` 仍是 `int32_t flags`。
- **解决**：shim 只保留 `int displayId` → `LogicalDisplayId` 旧 ABI，目标符号用 AOSPA 的 int flags 版本。文档：`docs/features/0020-libinput-shim-aospa-flags.md`。

### 2026-08-25 — ninja: perl libcrypt.so.1 (kernel Image)

- **症状**：`PERLASM sha256-core.S` / `GEN oid_registry_data.c`：`perl: libcrypt.so.1: cannot open shared object file`。clang（0019）、dtb merge（0017）、libinput_shim（0020）已过。
- **根因**：`PATH` 优先 `prebuilts/tools-lineage/.../perl`，链 glibc `libcrypt.so.1`。Fedora 44 只有 `.so.2`。
- **解决**：`PERL=/usr/bin/perl` 不够（`oid_registry` 写死 `perl`）。overlay `build/host-bin/perl` 插到 PATH 最前，并去掉 `PERL5LIB=tools-lineage/perl-base`（5.26 XS vs 本机 5.42）。文档：`docs/features/0021-kernel-system-perl.md`。

### 2026-08-25 — ninja: audio-kernel modpost snd_event_* / swr_* undefined

- **症状**：`Building Kernel Image` 已 OBJCOPY `Image`，编 `audio-kernel` 时 modpost：`snd_event_client_register`、`swr_driver_register` 等 undefined（一百多个）。Perl（0021）已过。
- **试过**：确认 `CONFIG_ARCH_PINEAPPLE=y`；`snd_event.c` 在 `audio-kernel/soc/`；`modules.load` 有 `snd_event_dlkm.ko`。
- **根因**：日志 `BOARD_PLATFORM=` 为空。`audio-kernel/Makefile` 需要 `TARGET_BOARD_PLATFORM`。`soc/Kbuild` 只在 `BOARD_PLATFORM=pineapple` 时 include `pineappleauto.conf`（`CONFIG_SND_EVENT` / `SOUNDWIRE`）；`ipc/` 用 `CONFIG_ARCH_PINEAPPLE` 仍会编 `gpr_dlkm`。
- **解决**：`BoardConfigKernel.mk`：`KERNEL_MAKE_FLAGS += TARGET_BOARD_PLATFORM=$(TARGET_BOARD_PLATFORM)`。不要改 modules 仓。文档：`docs/features/0023-kernel-board-platform.md`。

### 2026-08-25 — ninja: Failed to find aop.img (target_files radio)

- **症状**：内核 Image / vendor 分区已出。`add_img_to_target_files.py`：`AssertionError: Failed to find aop.img`。0023 audio modpost 已过。
- **试过**：`vendor/nubia/cerro/radio/aop.img` 存在且 SHA1 与 `Android.mk` 一致（0022 LFS 已拉）。`out/target/product/cerro/` 没有 `aop.img`。
- **根因**：`vendor/nubia/cerro/Android.mk` 调 Lineage 的 `add-radio-file-sha1-checked`。AOSPA 没有这个宏，`$(call)` 为空，radio 没进 `INSTALLED_RADIOIMAGE_TARGET`；`BoardConfigVendor.mk` 仍把 `aop` 列入 `AB_OTA_PARTITIONS`。
- **解决**：overlay `build/radio-sha1.mk` 从 BoardConfig include（不要放 tasks）。不要改 vendor 仓。文档：`docs/features/0024-radio-sha1-checked.md`。

### 2026-08-25 — ninja: Failed to find dtbo.img (target_files)

- **症状**：0024 之后 `RADIO/` 有 aop/modem。`CheckAbOtaImages`：`Failed to find dtbo.img`。产物目录没有 `dtbo.img`。
- **试过**：`TARGET_NEEDS_DTBOIMAGE := true`；`DTB_OBJ/out/` 已有 merge 后的 `.dtbo`。
- **根因**：`Makefile` 要在 tasks 之前看到 `BOARD_PREBUILT_DTBOIMAGE` 才会生成 `dtbo.img`。0012 的 Lineage `BoardConfigKernel.mk` 在 tasks 才 include，设得太晚。AOSPA 官方宏只在 `BOARD_KERNEL_SEPARATED_DTBO` 时设 `prebuilt_dtbo.img`。
- **解决**：`BoardConfigCommon.mk`：`BOARD_PREBUILT_DTBOIMAGE := $(PRODUCT_OUT)/prebuilt_dtbo.img`。不要开 `BOARD_KERNEL_SEPARATED_DTBO`。文档：`docs/features/0025-prebuilt-dtboimage.md`。

### 2026-08-25 — ninja: VINTF livedisplay / HighTouchPollingRate

- **症状**：target_files 已出。`ota_from_target_files`：`VINTF compatibility check failed`，device manifest 有 `vendor.lineage.livedisplay.ISunlightEnhancement/default` 和 `vendor.lineage.touch.IHighTouchPollingRate/default`。0025 dtbo 已过。
- **根因**：cerro 打了 Lineage sysfs livedisplay（SE）和 nubia 高报点 HAL。AOSPA FCM 没有 `vendor.lineage.{livedisplay,touch}`。Lineage 矩阵在 `hardware/lineage/interfaces`，没有 inherit 产品层就不会进框架矩阵。
- **解决**：overlay `device_framework_matrix.xml` 加这两项 optional AIDL。不要 inherit 整份 Lineage FCM。文档：`docs/features/0026-lineage-hal-fcm.md`。

### 2026-08-25 — 凑合项按更好做法落地（0031–0035）

- **0013 elf-check**：去掉 gralloc **嵌套** NS；Adreno 等 import 父 NS `hardware/qcom-caf/sm8650`（0031）。**不要**把整棵 CAF 放进 `PRODUCT_SOONG_NAMESPACES`（会撞 install）。Make check_elf 仍看不见 CAF-NS → nubia prebuilt **批量** `check_elf_files: false`（点关会打地鼠）。FM 仍关。`sm8650/Android.bp` 是 `os_pickup_qssi.bp` 的 symlink，空 NS ≠ root。
- **0010 NXP**：rc/**vintf xml** 改 `*-qti` 名（含 strongbox，避开 libese 同路径）并去掉 `enabled: false`（0032）。
- **0011 mkdir**：`mkdir.mk` 仅 PACKAGES 时建目录；重开三个 soong mkdir（0033）。
- **compat so**：`prebuilts-cerro/SHA256SUMS` + README 作固定 pin（上游 AOSPA 仍待）。
- **beryl zip 名**：apply 时 `AOSPA_MAJOR_VERSION := calcite`（0034）。
- **FULL_RECOVERY / imgdiff**：`local_manifests/cerro-imgdiff.xml` + `bootable/deprecated-ota`；关掉 `non_ab_unit_tests`（health V4+V5）；去掉 `BOARD_USES_FULL_RECOVERY_IMAGE`（0035）。`m imgdiff` 已产出 `out/host/linux-x86/bin/imgdiff`。

### 2026-08-25 — 对照 229 Voltage/Plasma：我们“凑合”项人家怎么做

- **环境**：只读对照已拷到本机 `ref-229/`（约 195M；**不含** `cerro-opt/overlays/camera-a16` 1.7G）。来源 `rong@192.168.0.229:/mnt/data/ArtistAOSP`。
- **内核 UAPI / `generated_kernel_headers`**：Voltage 用 `vendor/voltage/build/soong/Android.bp` 的 `voltage_generator`（`generated_kernel_includes`）真正跑 `headers_install`（或 bazel `_uapi_headers_dist`），再 `vendor/voltage/tools/clean_headers.sh`。`qti_kernel_headers` 等 defaults 挂在这份 gen 上。audio out-of-tree UAPI 另有 `scripts/stage-audio-kernel-uapi.sh` + TROUBLESHOOTING「liblx-osal missing msm_audio.h」补进 genDir。**不是**空 stub。
- **落地（0030）**：已在 `device-overlay/.../build/soong` 接 `cerro_generator` + `BoardConfigSoong.mk`（`cerroVarsPlugin`），CAF defaults 改挂 `generated_kernel_includes`；audio stage 在 `build/tools/stage-audio-kernel-uapi.sh`。`KERNEL_MAKE_FLAGS` **不要**进 soong.variables（引号会弄坏 JSON），改由 `run-headers-install.sh` 本地组 flag。`bash scripts/apply-device-overlay.sh` 重放。`m nothing` 已过 soong。
- **`check_elf_files`**：Voltage/Plasma **没有**全局关；只对出问题的 prebuilt 点关（WFD、`camera.qcom`、cerro 相机 bp、SukiSU prebuilt）。与我们因 soong_namespace 导致 make 白名单丢 `libgralloc.qti` 而批量关不同——他们主线是 Lineage/Voltage CAF 路径，namespace 坑少。
- **userdata / wrappedkey**：229 的 `fstab.qcom` **完整保留** `wrappedkey_v0` + `keydirectory=/metadata/vold/metadata_encryption`。能开机，**不靠**关掉 metadata encryption。印证我们 0029 去掉 crypto 后仍卡 logo：主因不在这里。
- **ramoops**：229 `pineapple.dtsi` 与上游一样只有 `pmsg-size = 0x200000`，**没有** `console-size`。他们靠正常进系统后的 adb/logcat，不靠我们 0027 的 console 切分做 bringup。
- **recovery / imgdiff**：`BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true`；设备树里**未见** `BOARD_USES_FULL_RECOVERY_IMAGE`。host 工具链完整时不需要我们为缺 `imgdiff` 开 full recovery。
- **产品层**：`voltage_cerro.mk` / Plasma / SukiSU —— 我们故意不搬；硬件改良在 `cerro-opt`（perf/SF/触控等），相机大包在已排除的 overlay。
- **结论**：headers 已按 Voltage 流水线接入；elf-check / crypto / ramoops / full-recovery 仍是 AOSPA/CLO 迁徙与抓日志的权宜。

### 2026-08-25 — 卡第一屏：只能从 recovery 看日志（无 adb）

- **约束（硬记）**：卡努比亚 logo **没有 adb**。不要提 `adb wait-for-device` / 开机瞬间抓 logcat。排障入口只有 **recovery**。
- **进 recovery（夹具）**：Power+Vol+ ~17s，松手后再短按 Power（解锁提示把松手当成一次按键）。`enter-recovery-hand.sh` / `servo_cli.py hold-recovery`。串口常需 `sudo`。
- **槽位坑**：曾误切到 **slot `_a`**（旧 `user/release-keys`、`ro.debuggable=0`，`adb root` 失败）。确认 `ro.boot.slot_suffix` / `fastboot --set-active=b`，刷 `_b`。
- **0027 ramoops**：DTB 在 **`vendor_boot`**（只刷 boot/dtbo 无效）。刷入后 `console_size=524288`。夹具长按是硬断电，pstore 仍空。
- **0028 bootdiag**：应写 `/metadata/cerro-boot-*.txt` 并软重启；曾失效是因为 **未 `PRODUCT_COPY_FILES` 进 vendor**（只有 rootdir 源文件）。已补进 `device.mk`，并加 kmsg 心跳 + `scripts/pull-bootdiag-from-recovery.sh`。需刷 **`vendor.img`** 后才生效。
- **vendor.img 打包**：`m vendorimage` 可能卡在 `imgdiff`（boot/recovery chunk 不一致）。staging 已有 bootdiag 时，可直接 `build_image` 打 `out/target/product/cerro/vendor.img`（2026-08-25 已打出 1.8G，`debugfs` 可见 `bin/init.cerro.bootdiag.sh`）。
- **2026-08-25 抓到首启日志**：`exec` 在 enforcing 下起不来；`vendor_boot` 加 `androidboot.selinux=permissive` + 重刷 vendor 后，~100s **软进 recovery**。`/metadata/cerro-boot-status.txt`：`zygote` 一直空、`crypto=unsupported`、`vold=running`；dmesg 里 vold 死等 `android.security.maintenance`，`vendor.qseecomd` 反复 exit 255。日志在 `cerro-bootdiag-pull4/`。
- **0029**：临时去掉 userdata wrappedkey 并 mkfs 后 **仍卡 logo** → 不全是 metadata encryption。
- **刷机**：ramoops → `vendor_boot`；fstab → `vendor_boot`+`vendor`；bootdiag → `vendor`。动态分区 vendor 须 **fastbootd**（`fastboot reboot fastboot`），bootloader 里 `flash vendor` 会 Partition not found。
- **2026-08-25 qseecomd exit 255（0036）**：strace 显示缺 **`/vendor/lib64/libdisplayconfig.qti.so`**（`libops.so` NEEDED）。CAF 该模块在空 sm8650 NS 外不可见。补 prebuilt + late-fs 启动后 qseecomd 稳定；zygote 起来，但 **surfaceflinger SIGABRT**（约 4 次后 init 杀 zygote）→ 仍无 `boot_completed`。日志 `cerro-bootdiag-pull5/`（strace）、`pull6/`（SF 循环）。下一步：编/装 HWC composer（同 NS 问题）。
- **坑**：`scripts/strip-plasma-device-overlay.sh` **会重写** `device-overlay/.../cerro/device.mk`。bootdiag / qseecomd.rc 的 `PRODUCT_COPY_FILES` 必须写进该脚本的 heredoc，否则 `apply-device-overlay.sh` 会冲掉。

### 2026-08-25 — surfaceflinger SIGABRT：缺 CAF HWC（0037）

- **症状**：0036 后 qseecomd OK、zygote 起，SF 反复 abort，无 `boot_completed`。vendor 无 `vendor.qti.hardware.display.composer-service`。
- **根因**：
  1. CAF display 在 `hardware/qcom-caf/sm8650` NS；未进 `PRODUCT_SOONG_NAMESPACES` 时 PRODUCT_PACKAGES 装不上。
  2. AOSPA 无 `vendor/qcom/opensource/display`；`os_pickup_qssi` 只能 import `commonsys-intf/display`。
  3. 编 `libsdmdal`：`utils/utils.h` not found —— AOSPA 未设 `qtidisplay.default=true`（Voltage 靠 `hardware/qcom-caf/common/BoardConfigQcom.mk`），`qtidisplay_defaults` 不带 `display_headers`。
  4. `vendor/qcom/common` wfd/perf 等 prebuilt 要 `display.config-V*-ndk`，须 import commonsys-intf NS。
- **解决**：overlay 加 soong NS + `soong_config_set_bool`（default/drmpp/gralloc4/…）+ `display-board.mk`；`patch-soong-display-namespaces.py` 维护 commonsys import。`m composer-service` 等已通过。刷 vendor（fastbootd）后用 bootdiag 验 SF。文档：`docs/features/0037-caf-display-hwc.md`。
- **勿**：整份 inherit `display-product.mk`（硬编码 `hardware/qcom/display/config`）；不要再依赖 0036 SONAME prebuilt。
- **澄清（2026-08-25）**：本树 / 已刷 `aospa_cerro` 包是 **Android 16（API 36）**。文档里曾误写「AOSPA calcite = Android 17」，是和 **VoltageOS 17**（ROM 版本号）搞混；已改正 `AGENTS.md`。机上 `ro.aospa.version=Beryl` 只是 zip 名/旧 major 字符串（`aospa-beryl-…zip`），不代表底子是别的 Android。

### 2026-08-25 — SetupWizard 黑屏无响应：mediaserver 未起（0038）

- **症状**：已进系统，Pixel 欢迎页黑屏 + ANR。
- **根因**：`WelcomeActivity` 等 `media.player`；`TARGET_DYNAMIC_64_32_MEDIASERVER` 默认走 `mediaserver32`，cerro 只有 `mediaserver64` 且未设 `ro.mediaserver.64b.enable=true`（本应由 qti-media 组件带）。
- **解决**：`vendor.prop` 加 `ro.mediaserver.64b.enable=true`。现场可 `ln -s mediaserver64 mediaserver32` + `start media` 后重启 SetupWizard。文档：`docs/features/0038-mediaserver-64b-setupwizard.md`。

### 2026-08-27 — 卡第一屏 logo：旧 vendor + IR HAL SELinux（0040）

- **症状**：全刷 fastbootd 后卡努比亚 logo；recovery 可进。
- **根因 1**：全刷用了 `target_files/IMAGES/vendor.img`（08:23），不是 `out/vendor.img`（22:51，含 display/HWC 修复）→ SF 栈不匹配。
- **根因 2**：`android.hardware.ir-service.lineage` 二进制标成 `vendor_file`，init 无法 `domain transition` → `system_server` 死等 `IConsumerIr/default`。
- **解决**：overlay 补 IR sepolicy（0040）+ **重编刷 vendor.img**。全刷只用 `out/target/product/cerro/` 里与 boot 同批次的 vendor，勿混用 target_files 旧包。
- **勿**：`setenforce 0` / 手起 IR HAL 当正式方案。

### 2026-08-27 — SetupWizard 黑屏复发：vendor.img 未含 mediaserver 属性（0038）

- **症状**：能开机但欢迎页黑屏无响应；`media.player` 不存在。
- **根因**：`vendor.prop` 已写 `ro.mediaserver.64b.enable=true`，但当时刷的 `vendor.img` 早于该改动（22:51 img vs 23:23 prop），live `/vendor/build.prop` 无此行。
- **解决**：`common.mk` 再钉 `PRODUCT_VENDOR_PROPERTIES`；重编刷 vendor 后验证 `getprop`/`init.svc.media`。

### 2026-08-27 — 凑合改 vendor / 新 vendorimage 掉 bootloader；SetupWizard+IR 正式修法

- **症状**：欢迎页又黑；或刷“修好的”vendor 后立刻回 fastboot。
- **误判/凑合（禁止再当正式方案）**：`setenforce 0` 手起 IR；手搓 `build_image` 整包；把新树的整份 `vendor_sepolicy.cil` 塞进旧 vendor；去掉 AVB footer 的注入镜像。
- **根因拆开**：
  1. **0038**：刷进去的 vendor 没有 `ro.mediaserver.64b.enable=true` → 无 `media.player` → SetupWizard ANR。
  2. **0040**：IR 二进制是 `vendor_file` → init 拒绝 domain transition → `system_server` 死等 `IConsumerIr`（可卡 logo / 拖死开机）。
  3. **刷机**：`m vendorimage`（当日）产物在本机 **秒回 bootloader**；`vendor.img.sparse`（08-25 22:51）可开机。整份替换 cil / 破坏 AVB 布局也会软砖。ABL `oem device-info` 的 `Verity mode: true` 不可信（关 AVB 后仍显示 true）。
- **已验证正式路径**：
  - overlay 保留 prop + IR `file_contexts` / te（真相源）。
  - `BOARD_USES_FULL_RECOVERY_IMAGE := true`（跳过坏掉的 `imgdiff recovery_from_boot.p`），便于以后再编 vendorimage。
  - 刷机用 `bash scripts/inject-vendor-mediaserver-ir-label.sh`：在 **22:51 sparse 底包** 上只追加 mediaserver prop + IR 二进制 `hal_ir_default_exec` xattr，**保留 AVB footer**，fastbootd 刷 `vendor_a`。
  - 验证：`Enforcing`、`init.svc.media=running`、`init.svc.vendor.ir-default=running`、`media.player` + `IConsumerIr`、`WelcomeActivity`。
- **未决**：为何当日完整 `vendor.img` 不能开机（与 0038/0040 内容无关——该包里 prop/标签都对仍掉 BL）。修好前不要用新 `m vendorimage` 产物当唯一刷机源。


- **症状**：无声卡；`sound` deferred；AW882 已 probe；HAL 报 `Failed to initStreamVolume`。
- **误判**：以为要还原 Voltage→Lineage 的 `device/*/audio` XML（已与 lineage-23.2 一致，无差）。
- **根因**：`merge_dtbs` 后 MTP `pineapple-audio` 与 zte-cerro 同 DTBO；ABL 后写保留 MTP `num-macros=4` / `wsa-max-devs=2` / WSA routing。WSA macro 已被 zte disable → lpass-cdc 不注册；即便强改 max-devs，WSA routing 仍令 `register_card` -ENODEV。
- **试过**：跳过全部 pineapple-audio techpack → 缺 symbol 软砖；`dtc` 反编译再编 DTBO → 弄坏 wcd 电压属性；只改 `wsa-max-devs` 不够。
- **解决**：`fix-cerro-audio-dtbo.py` 原地改 merged `*zte-cerro*.dtbo`；`merge_dtbs.py` 写出后调用。急救包：`out/target/product/cerro/dtbo-cerro-audio-fix.img`。文档：`docs/features/0039-cerro-audio-dtbo-merge.md`。
- **勿**：跳过 audio techpack；勿对合并 DTBO 做 dtc round-trip。


- **症状**：卡努比亚 logo；能进 recovery。点 Factory reset / 格式化 data 后日志像没真正 mkfs userdata。
- **环境**：`aospa_cerro` 刷机包；当前槽 `_b`；`adb root` 可读 `/tmp/recovery.log`。
- **日志要点**：
  - `Formatting /data...` → `wipe metadata encrypted ... userdata` → 只 **discard** userdata
  - 随后完整 `mkfs.f2fs` 的是 **`/metadata`（64MB）**，不是 userdata
  - `Data wipe complete.`（recovery 认为成功）
  - `wipe via secure discard failed, used discard instead`（UFS 常见警告）
  - `E:Unable to create /etc/fstab`（次要）
- **实测**：wipe 后 `sda12`（userdata）全 0、无 F2FS magic；`sda10`（metadata）可挂载。
- **根因**：fstab 启用了 `metadata_encryption=...wrappedkey_v0` + `keydirectory=/metadata/vold/metadata_encryption`。这类 data 在 recovery 里**故意不 mkfs**：只擦 userdata、重建 metadata，留给首启 init/vold 建加密文件系统。UI 上会像「没格式化 data」。
- **和卡 logo 的关系**：wipe 本身按设计完成了；卡 logo 是首启没能建好/挂上 `/data`（或更早挂掉），不是 recovery wipe 失败。
- **抓日志约束（记住）**：**卡第一屏没有 adb**。不要指望 `adb wait-for-device`。只能进 recovery 后看残留：`/tmp/recovery.log`（本次 recovery）、`/sys/fs/pstore/*`（若内核/DT 开了 ramoops，从卡死强制进 recovery 后可能有上次 console）、`/dev/block/by-name/logdump`（本机现有内容是旧 mainline/pmOS，不是 AOSP 首启）。当前 pstore 为空、DT 里未见 ramoops 节点时，强制重启进 recovery 也抓不到内核 console。
- **不要**在 recovery 里对 userdata 随便跑裸 `make_f2fs`（会和 metadata encryption / wrappedkey 布局冲突）。


- **症状**：`signapk` 打 `NubiaCamera.apk`：`ZipException: zip END header not found`。
- **根因**：文件是 Git LFS 指针（134 字节 ASCII），不是 599MB APK。`repo sync` 没拉 LFS。radio img 同样。
- **解决**：`scripts/pull-vendor-lfs.sh`（FlClash 代理）+ `sync-calcite.sh`。文档：`docs/features/0022-vendor-git-lfs.md`。

## 2026-09-21 — 旧 A16 树删除，改拉 aospa-shadedark calcite（A17）

- 已删除 `/mnt/data/AOSPA_Z60U/source`，保留 docs / device-overlay / scripts / clo-agent-kit / 交接文档。
- 新树：`/mnt/data/PenguinOS_cerro/source`（`--depth=1` + `phone-only.xml` + `cerro.xml`）。
- 代理：`source scripts/proxy-env.sh`；**unset REPO_URL**。

### 2026-09-21 — shadedark A17 cerro：beans 重复 / soong / phone-only 剪枝

- **症状**：`./rom-build.sh cerro` 立刻挂：`duplicate path device/nubia/cerro`、`Product name must be unique aospa_cerro`、随后 soong 大量 `already defined` / `undefined module`。
- **环境**：`/mnt/data/PenguinOS_cerro/source`，aospa-shadedark `calcite`（QSSI 17），设备底 nubia-sm8650-devs `lineage-23.2`，phone-only 浅克隆。
- **根因**：
  1. `vendor/aospa/products/cerro/beans.xml` 与 `.repo/local_manifests/cerro.xml` 重复声明同一 path；barista 再写 `baristablend.xml`。
  2. `device/nubia/cerro/aospa_cerro.mk` 与 `vendor/aospa/products/cerro/aospa_cerro.mk` 双份 `PRODUCT_NAME`。
  3. Lineage CAF `hardware/qcom-caf/common/Android.bp` 与 AOSPA `device/qcom/common` 重复 rfs/mountpoint；Soong 仍扫描整份 bp。
  4. phone-only 去掉 cuttlefish/Car 后，残留 Android.bp（automotive/hcct/igt/trusty）仍引用缺失模块；A17 SystemUI 又硬依赖 `android.car`，不能整棵去掉 `packages/services/Car`。
- **解决**：
  1. 删 local `cerro.xml`，只留 beans；产品壳只在 `vendor/aospa/products/cerro/`。
  2. CAF HAL 进 beans；`scripts/apply-keep-wiring.sh` + `scripts/apply-soong-patches.sh`（isolate-caf-common / display-namespaces / nubia-namespaces / libinput_shim）。
  3. KEEP：`TARGET_USES_KERNEL_PLATFORM=false`、qtidisplay flags、Wi‑Fi soong 全路径、`BOARD_PREBUILT_DTBOIMAGE`、ufsbsg=bsg、qseecomd late-fs、去掉 lineage touch/health/livedisplay/firmware mountpoint/telephony-ext BOOT_JARS。
  4. phone-only：恢复 `packages/services/Car` + Car apps + `frameworks/opt/car/{services,setupwizard}`；`PRODUCT_SOURCE_ROOT_DIRS` 只剪 cuttlefish/display 测试、automotive proxy、trusty、libwatchdog fuzzer。
  5. 若干 vendor/qcom/common 空 NS 补 import `hardware/qcom-caf/sm8650`（adreno/perf/qseecomd/media）与 `commonsys-intf/display`（system/perf）。
- **重放**：`bash scripts/apply-keep-wiring.sh && bash scripts/apply-soong-patches.sh`，然后 `lunch aospa_cerro-userdebug && m bacon`。

### 2026-09-21 — shadedark：`m bacon` 无目标

- **症状**：soong/kati 已过后 `ninja: unknown target "bacon"`。
- **根因**：Lineage 习惯 `bacon`；AOSPA `rom-build.sh` 默认 `m otapackage`（或 `target-files-package`）。
- **解决**：`m otapackage -j12`，或 `./rom-build.sh cerro`。

### 2026-09-21 — shadedark：缺 prebuilts-cerro/dtc（fdtput / fdtoverlaymerge）

- **症状**：`otapackage` → `dtb.img` 需要 `out/host/.../fdtput`，无规则。
- **根因**：PenguinOS `apply-soong-patches.sh` 未挂 `patch-soong-dtc-fdt-tools.py`；`prebuilts-cerro/dtc/` 也未落盘。
- **解决**：从 LineageOS `android_external_dtc` @ lineage-23.2 取 `fdtoverlaymerge.c` + `libfdt/fdt_overlay.c` 入 `prebuilts-cerro/dtc/`；脚本挂进 apply 链后重放。

### 2026-09-21 — shadedark：内核缺 gelf.h / opensslv.h

- **症状**：`Building Kernel Image` 失败：`gelf.h` / `libelf.h` / `openssl/opensslv.h` file not found（HOSTCFLAGS 走 sysroot + kernel-build-tools）。
- **根因**：缺 `prebuilts/kernel-build-tools`（beans 原先只有 `tools-lineage`）。
- **解决**：beans / `local_manifests/cerro-kernel-tools.xml` 加 `kernel/prebuilts/build-tools` @ `main-kernel-2025`，`repo sync prebuilts/kernel-build-tools`。

### 2026-09-22 — shadedark：recovery_sepolicy 缺 vendor_hal_qspmhal_client

- **症状**：`recovery_sepolicy.cil`：`gmscore_app.te` → `attribute vendor_hal_qspmhal_client is not declared`。
- **根因**：`device/qcom/sepolicy/generic/public/attributes` 相对 API34 prebuilt 丢了 `vendor_hal_qspmhal{,_client,_server}`，但 `sepolicy_vndr` 的 `gmscore_app.te` 仍 `hal_client_domain(..., vendor_hal_qspmhal)`。
- **解决**：`scripts/patch-sepolicy-qspmhal-attributes.py` 幂等补回；挂进 apply 链。

### 2026-09-22 — shadedark：file_contexts 引用已删的 hal_lineage_touch

- **症状**：`file_contexts.device.sorted.tmp`：`hal_lineage_touch_default_exec is not defined`。
- **根因**：`apply-keep-wiring.sh` 只拷 `file_contexts` 并 `rm` 掉 `hal_lineage_touch_default.te`，类型没了路径还在。
- **解决**：按 0015 整份 touch sepolicy（public attributes + vendor te + private clients）进 overlay；KEEP 改为 `rsync` 整树 sepolicy，**不要**删 touch `.te`。

### 2026-09-23 — shadedark：卡第二屏（IR 标签 + tcmd seccomp）

- **症状**：bootanim 循环；`sys.boot_completed` 空；adb 可用。
- **根因 1**：`system_server` Watchdog 死等 `android.hardware.ir.IConsumerIr/default`。`android.hardware.ir-service.lineage` 落成 `u:object_r:vendor_file:s0`，init 无法 transition（0040）。OTA 里的 `vendor_file_contexts` **缺** lineage IR 行（touch 有、IR 无）。
- **根因 2**：`tcmd` seccomp 拦 `lseek` → SIGSYS；崩 4 次后 `sys.init.updatable_crashing=1` 触发 `flags_health_check`。nubia 的 `tcmd.policy` 比 qcom common 少 `lseek: 1`。
- **验证**：`setenforce 0` 后 IR 可起、`IConsumerIr` 出现。
- **热修镜像**：`vendor-WORKING-0040-ir.img`（xattr + file_contexts）；`system_ext-WORKING-tcmd-lseek.img`。
- **持久**：overlay `file_contexts` 已有 IR；重编须确认进 `vendor_file_contexts`；`vendor/nubia/.../tcmd.policy` 已补 `lseek: 1`。

### 2026-09-23 — 幽灵 h2w/LINE：有声卡仍无声

- **症状**：`/proc/asound/cards` 有 card；Music 播放 `Standby: no`、AW882 `start_pa success`；仍听不到（或路由错）。
- **根因**：`pineapple-mtp-snd-card Headset Jack` 的 `SW_LINEOUT`/`PHYSICAL` 开机卡插入 → `AudioDeviceOut LINE name:h2w` 抢路由。cerro 无 3.5mm。
- **热修**：`sendevent` 清 event8 的 SW 2/4/6/7；确认 `Devices: speaker`。
- **持久**：`config_useDevInputEventForAudioJack=false` + `init.cerro.audio_jack.rc`（0043）。

### 2026-09-23 — 振动 FIFO：Only support custom FIFO data

- **症状**：触感全无；`cmd vibrator_manager synced oneshot` 后 dmesg 刷 FIFO 拒。
- **根因**：CLO vibrator 不吃 `soong_config`，oneshot 用 `FF_CONSTANT`；awinic 只要 FIFO。
- **解决**：`patch-soong-vibrator-effect-stream.py` + richtap `libqtivibratoreffect.nubia_sm8650-richtap`（0042）。热推后无 FIFO 拒、log 见 `perform effect`。

### 2026-09-23 — 双卡联通 LTE、移动 NR_SA

- **症状**：同卡 OP12 有 5G；cerro 联通 `RilData=LTE`，移动 `NR_SA`。`carrier_nr` 已改 SA+NSA，`5g_mode_pref=1`。
- **观察**：基站对联通有时 `isEnDcAvailable=true` 仍停 LTE；独插联通时也曾 `isNrAvailable=false`。modem 仅有 `China/CU/Commercial/VoLTE` MBN（无 OpenMkt）。
- **已做**：全量 RAT bitmask、DDS 切联通、overlay `5g_mode_pref=1`。
- **待查**：CU MBN NR 能力 / 双卡 DSDA 次卡策略 / 与 OP12 同址对照 `isEnDcAvailable`。

### 2026-09-23 — 幽灵 h2w/LINE：有声卡仍无声

- **症状**：`/proc/asound/cards` 有 card；Music 播放 `Standby: no`、AW882 `start_pa success`；仍听不到（或路由错）。
- **根因**：`pineapple-mtp-snd-card Headset Jack` 的 `SW_LINEOUT`/`PHYSICAL` 开机卡插入 → `AudioDeviceOut LINE name:h2w` 抢路由。cerro 无 3.5mm。
- **热修**：`sendevent` 清 event8 的 SW 2/4/6/7；确认 `Devices: speaker`。
- **持久**：`config_useDevInputEventForAudioJack=false` + `init.cerro.audio_jack.rc`（0043）。

### 2026-09-23 — 振动 FIFO：Only support custom FIFO data

- **症状**：触感全无；`cmd vibrator_manager synced oneshot` 后 dmesg 刷 FIFO 拒。
- **根因**：CLO vibrator 不吃 `soong_config`，oneshot 用 `FF_CONSTANT`；awinic 只要 FIFO。
- **解决**：`patch-soong-vibrator-effect-stream.py` + richtap `libqtivibratoreffect.nubia_sm8650-richtap`（0042）。热推后无 FIFO 拒、log 见 `perform effect`。

### 2026-09-23 — 双卡联通 LTE、移动 NR_SA

- **症状**：同卡 OP12 有 5G；cerro 联通 `RilData=LTE`，移动 `NR_SA`。`carrier_nr` 已改 SA+NSA，`5g_mode_pref=1`。
- **观察**：基站对联通有时 `isEnDcAvailable=true` 仍停 LTE；独插联通时也曾 `isNrAvailable=false`。modem 仅有 `China/CU/Commercial/VoLTE` MBN（无 OpenMkt）。
- **已做**：全量 RAT bitmask、DDS 切联通、overlay `5g_mode_pref=1`。
- **待查**：CU MBN NR 能力 / 双卡 DSDA 次卡策略 / 与 OP12 同址对照 `isEnDcAvailable`。

### 2026-09-23 — 振动 FIFO：Only support custom FIFO data

- **症状**：触感全无；`cmd vibrator_manager synced oneshot` 后 dmesg 刷 FIFO 拒。
- **根因（初判有误）**：以为 awinic 拒 `FF_CONSTANT`。实际 `upload_constant_effect` **接受** CONSTANT（RAM_LOOP）。FIFO 拒包来自 `FF_PERIODIC` 且 `custom_len != sizeof(custom_fifo_data)`。
- **另**：`upload_custom_effect` 少分配 `sizeof(int)`（0044）；Voltage `on()` 仍走 CONSTANT。
- **HAL**：`patch-soong-vibrator-effect-stream.py` + richtap（0042）让 oneshot/perform 能上传合法 FIFO。
- **内核**：`patch-kernel-haptic-custom-alloc.py`（需重编 haptic.ko）。热测：`EVIOCSFF` 成功但无 `RTP_GO` 日志、无触感 → 等内核补丁刷入后再验。

### 2026-09-23 — 声卡通路已通仍可能无声感

- **症状**：用户仍报无声。
- **实测**：`AudioTrack` 播放 440Hz，`AudioFlinger` `Frames written≈286080`；dmesg `aw882xx_device_start` / `start_pa: start success`。APM `Devices: speaker`。
- **残留**：`aw_check_dsp_ready: rx topo id is 0x0`（SmartPA DSP 拓扑未起来）；tinymix `Headset Jack` 仍 On（ALSA 控件，与 input SW 脱钩）；偶发幽灵 LINE 历史。
- **持久**：0043 jack RRO/init；mixer HPH 默认 Off。下一步查 `aw882xx_acf.bin`/ACDB 与 topo。

### 2026-09-23 — 联通 5G：VoLTE-only MBN + 共享基站 ENDC 闪断

- **症状**：双卡插入后移动 `NR_SA`，联通常 `LTE`；同卡 OP12 有 5G。
- **观察**：飞机模式后联通短时 `isEnDcAvailable=true` / `nrState=NOT_RESTRICTED`，随后落到 `mnc=11` CT 共享小区且 `isEndcAvailable=false`。
- **机侧**：modem 仅 `China/CU/Commercial/VoLTE`（无 OpenMkt，对比 CMCC/CT 有 OpenMkt）。
- **已做**：`5g_mode_pref=3`（NSA+SA）、联通 `hide_enabled_5g_bool=false`、46001/05/09 `carrier_nr` SA+NSA。
- **下一步**：从 OP12/厂包取 CU OpenMkt（或带 NR 的）mbn 替换 VoLTE-only；同址对照 OP12 ENDC 指示。

### 2026-09-23 — mixer 默认 RX_HPH PCM=On

- **症状**：路由已是 speaker、AW882 `start_pa success`，但 codec `RX_HPH PCM`/`HPH PCM Enable` 仍 On（MTP 初始 ctl=1）。
- **解决**：`mixer_paths_pineapple_mtp.xml` 初始改为 0，并在 `path name=speaker` 里显式关掉 HPH。

### 2026-09-23 — 振动无感：DTBO reset-gpio=120 未生效

- **症状**：HAL oneshot 跑满 timeout、`fftest2` CONST playing、richtap perform 瞬间 complete，仍无触感。
- **根因**：cerro overlay 只覆盖 `reset-gpio=<&tlmm 120>`；DTBO 片段里 `&tlmm` fixup 成 `0xffffffff`，实机仍用 common **gpio 90**。
- **证据**：`xxd .../reset-gpio` 第二 cell=`0x5a`；DTBO 内 cerro 片段为 `ffffffff 00000078`。
- **解决**：`zte-cerro-overlay.dtsi` `/delete-node/` 后整节点重建（0045）；`patch-kernel-haptic-reset-gpio.py`。需重编刷 **dtbo**。另 FIFO 堆分配见 0044（已热插 `haptic.ko`）。

### 2026-09-23 — 联通 5G：modem.img 缺 CU OpenMkt 文件

- **更新**：`mbn_sw.txt` 有 `China/CU/Commercial/OpenMkt`，但 `modem.img`/实机目录不存在该 mbn（只有 VoLTE）。
- **对照**：CMCC `Volte_OpenMkt` 存在 → 移动 NR_SA；联通飞机模式曾闪 `isEnDcAvailable=true` / 紧急 NR n78，正常仍 LTE。
- **文档**：0046。待从厂包/OP12 取 OpenMkt 注入。

### 2026-09-23 — 音频：通路通仍可能听不到

- **更新**：Tone 播放时 PAL `SPEAKER` + AGM `MI2S-LPAIF-RX-PRIMARY` + `start_pa success` + `mute=0`；`rx topo id is 0x0`、ACDB `Error[19]` 无 delta cal；`vmax=0x0`。
- **幽灵 h2w**：input SW 可清，但 tinymix `Headset Jack` 控件仍 On；boot 后需 `cerro_clear_audio_jack.sh`（0043）。
- **下一步**：核对 `aw882xx_acf.bin`/SmartPA ADSP topo 与 cerro ACDB；整节点 DT 刷入后复测振动。

### 2026-09-23 — vendor 写满导致二进制被截成 0 字节

- **症状**：热推 `haptic.ko` 时 `cp: short write`；随后振动 HAL/`impl.so`/`richtap.so`、部分 `CAMERA_ICP.b1x`/`evass.b1x` 变成 **0 字节**；boot Watchdog、`vibrator`/`AGMIPC` 起不来。
- **根因**：`/vendor` 与 `vendor_dlkm` 100% 满。
- **急救**：删大块相机资源腾空间后从 `out/vendor` 恢复 vibrator 三件套；**须重刷 vendor（+vendor_dlkm）** 才能完整恢复 CAMERA/evass 分片。
- **DT**：common `reset-gpio` 90→120 后实机 `xxd` 第二 cell=`0x78`（0045）。

### 2026-09-23 — 振动：缺 `haptic.ko`（awinic）

- **症状**：`vendor.qti.vibrator` 有 oneshot 日志，无触感；`/sys/class/leds/vibrator` 不存在。
- **根因**：`haptic_hv@5A` 无 `haptic.ko`（`CONFIG_AWINIC_HAPTIC_HV`）；只有 qcom-hv / swr_haptics。
- **热修**：`insmod` Voltage `haptic.ko` → `input: awinic_haptic`；`vendor_dlkm` 满时勿 cp（0 字节）。
- **持久**：0047 + `patch-kernel-awinic-haptic.py`；重编刷 vendor_dlkm。

### 2026-09-23 — 音频：fix 脚本只改了 u32，routing 仍是 WSA

- **症状**：`wsa-max-devs=0` / `num-macros=3` 但 `qcom,audio-routing` 仍有 `HAP_IN`/`WSA_*`，`snd_soc_register_card -ENODEV`。
- **根因**：旧 `fix-cerro-audio-dtbo.py` 只在**同一 FDT** 内配对「空填充 routing」；MTP 片段只有 WSA、没有 clean 模板 → 不改 routing / codec-names。
- **解决**：跨 FDT 取 zte 干净 routing 覆盖含 WSA/HAP 的条目，并剥离 `asoc-codec-names`（0049/0039）。

### 2026-09-23 — `dtbo-WORKING-asoc2` 软砖

- **症状**：刷 asoc2 后 USB 短暂 `4ee0`/`4e11` 即断，长时间无 adb/fastboot；舵机串口也不在。
- **根因**：把 `asoc-codec` phandle 置 `0`（历史 hang 试验路径）。
- **急救**：进 fastboot/9008 后刷回 **`dtbo-WORKING-fill-v3.img`**（勿再用 asoc2）。后台 watcher：`/tmp/cerro-dtbo-recover.log`。

### 2026-09-23 — 联通 5G：Voltage modem 也无 CU OpenMkt

- **更新**：229 ArtistAOSP `modem.img` 挂载后 CU/Commercial **仅 VoLTE**。OpenMkt 仍须厂包/OP12。

### 2026-09-23 — 开机故障分类（用户硬规则）

卡 logo / 无 USB 时**不要先怪线**。两种模式：

1. **卡第一屏**（努比亚 logo）：一直挂着。**≥5 分钟仍不动 = 卡第一屏**。USB 长期无设备（无 adb / fastboot / 9008）。排障只能 **手动进 recovery**（夹具 Power+Vol+），不要 `adb wait-for-device`。
2. **无限重启**：通常 **5 分钟内** ABL 会标当前槽 unbootable → 切另一槽。另一槽若正常则进那套系统；若也无限重启 → **fastboot**；若另一槽是卡第一屏 → USB 仍会一直空（看起来像「线坏了」）。

### 2026-09-23 — asoc2 急救后仍卡第一屏（时间线）

- **环境**：真机树在 `/mnt/data/PenguinOS_cerro/source`（aospa-shadedark A17）；可重放真相源仍在 `AOSPA_Z60U/{device-overlay,docs,scripts,prebuilts-cerro,clo-agent-kit}`。
- **经过**：
  1. `dtbo-WORKING-asoc2` 软砖（asoc-codec phandle=0）。
  2. ~18:05 recovery 刷 fill-v3 → `dtbo_a/_b` → reboot（`/tmp/cerro-dtbo-recover.log` RECOVERED）。
  3. 随后进 **9008**；EDL 再写 fill-v3 到 a/b（`/tmp/cerro-dtbo-9008-dump/write_{a,b}.log`）；firehose reset 报 USBError。
  4. 之后长时间 USB 空、无 adb/fastboot → 按上条规则判为 **卡第一屏**（非线、非无限重启）。
- **已知可开机对照**：Sep22 stock `target_files/.../IMAGES/dtbo.img`、以及 `dtbo-WORKING-fill-v2` 曾 ~33s `BOOT_OK`（终端 4645/4648）。fill-v3 写完后仍卡 logo → 嫌疑不只 DTBO（vendor 写满 0 字节 / 槽位 / boot 链也可能）。
- **下一步**：夹具进 recovery → 看 `ro.boot.slot_suffix`；必要时刷 Sep22 stock dtbo + 已知 WORKING vendor（`vendor-WORKING-0040-ir` / `atfwd-lseek`），勿再刷 asoc2。

### 2026-09-23 — 实机确认 BOOT_OK 镜像（急救优先用这套）

日志证据（终端号）：

| 组件 | 路径 | sha1 前 12 | 证据 |
|------|------|------------|------|
| **DTBO（首选）** | `.../target_files/.../IMAGES/dtbo.img`（Sep22 02:39）钉为 `prebuilts-cerro/dtbo/dtbo-STOCK-sep22-BOOT_OK.img` | `c6a2b09243af` | **4645/4647** ~33s `BOOT_OK` / `STOCK_BOOT_OK` |
| DTBO（次选） | `dtbo-WORKING-fill-v2.img` → `prebuilts-cerro/dtbo/dtbo-WORKING-fill-v2-BOOT_OK.img` | `e9e7c4989b93` | **4648** `BOOT_OK`（无声卡，仅证明能进系统） |
| vendor | `vendor-WORKING-0040-ir.img` | （1.8G raw） | **4638** 刷 `_b` 后 IR/ConsumerIr 起来；后续 stock DTBO 会话在此基础上 |
| system_ext | `system_ext-WORKING-tcmd-lseek.img` | | **4638** 同刷，`tcmd` 含 `lseek` |
| vendor（后补） | `vendor-WORKING-atfwd-lseek.img` | | atfwd seccomp；**未单独**再验 BOOT_OK |

**不要用**：`dtbo-WORKING-asoc2`（软砖）；`fill-v3` 仅 asoc2 急救，**未**留下 `BOOT_OK` 日志（EDL 写后仍卡第一屏）。

急救（9008 / fastboot）：

```bash
# 优先 STOCK dtbo 双槽
edl w dtbo_a prebuilts-cerro/dtbo/dtbo-STOCK-sep22-BOOT_OK.img
edl w dtbo_b prebuilts-cerro/dtbo/dtbo-STOCK-sep22-BOOT_OK.img
# 若仍卡 logo，再刷 vendor+system_ext（fastbootd 或 EDL）
# vendor-WORKING-0040-ir.img + system_ext-WORKING-tcmd-lseek.img → 活跃槽
```

### 2026-09-23 — 上下文丢失 / 无法判断哪版改坏开机

- **症状**：卡第一屏；agent 上下文丢了，不知道最近改坏了什么；只备份“能开机点”无法继续推进。
- **错误做法**：只留单个 WORKING img / 口头说“这版能开”。
- **正确做法**：元仓 https://github.com/ycrrongos/AOSPA_Z60U （私有）。每版跑 `bash scripts/github-snapshot.sh "标题"`（同步 Cursor 聊天到 `docs/agent-transcripts/` + 详细 commit + `snapshot-*` tag）。回滚：`git fetch && git tag -l 'snapshot-*'` / `git checkout <tag> -- device-overlay scripts docs`。
- **文档**：`docs/features/0048-github-version-snapshots.md`；`AGENTS.md` 规则 6。

### 2026-09-23 — 声音修补全部撤回，先编无音频修整包

- **原因**：音频 DTBO/jack 试验与卡第一屏纠缠；上下文丢失后无法定位。用户要求声音从头重做。
- **已删**：`fix-cerro-audio-dtbo.py`、jack rc/sh；mixer/HPH 与 `config_useDevInputEventForAudioJack` 回 Lineage；0039/0043 标撤回。
- **未动**：触感等非声音功能。
- **树**：`AOSPA_Z60U/source` → `PenguinOS_cerro/source`（shadedark calcite）。参考 OTA `~/Downloads/aospa_cerro-ota.zip` 只查阅不刷。
- **文档**：`docs/features/0049-audio-reset-full-build-baseline.md`
