# 给之前做 cerro AOSPA 错位树的 agent

用户（ycrrongos）要你**重做** Nubia Z60 Ultra（`cerro` / NX721J）的 AOSPA 移植。  
**不要**在你上次那棵公开设备树上继续打补丁。  
**也不要**在用户这台电脑上继续 `repo sync` / 编译：硬盘不够，用户已经叫停。

本文自洽。工程目录在 `/mnt/data/PenguinOS_cerro`（若你能读到那台机器），但**完整 ROM 树不要在那台机器上接着拉**。

---

## 1. 上次错在哪

你当时和用户都以为 **AOSPA = Android 17**，没有核对 manifest / QSSI 标签，也没有搞清怎样才是真 A17。

实际做的是：

1. 拿 `/mnt/data/ArtistAOSP` 里 **VoltageOS 17（真 A17）** 改过的 cerro 设备树当底座。
2. 硬接到当时其实还是 **Android 16 早期** 的 AOSPA（`beryl` / 早期 `calcite`，`LA.QSSI.16.0`）。
3. 改到能开机（`sys.boot_completed=1`），然后才发现系统是 **A16 早期**。
4. 真机：**没有声音**，**打电话崩**。

所以 GitHub 上这两仓是「版本错位 + 不正常接线」的产物，**不当 base**：

- https://github.com/ycrrongos/android_device_nubia_cerro （`main`，README 自己写着 “AOSPA calcite（Android 16 / API 36）”）
- https://github.com/ycrrongos/android_device_nubia_sm8650-common

vendor 上有 `aospa-cerro` 分支（相对 lineage 的增量，只能当 diff 参考，不能整枝当底）：

- https://github.com/ycrrongos/proprietary_vendor_nubia_cerro/tree/aospa-cerro
- https://github.com/ycrrongos/proprietary_vendor_nubia_sm8650-common （同样有 `aospa-cerro`）

那棵树几乎是一锅端提交（`Initial public tree for PenguinOS / AOSPA cerro review`），注释里全是「Voltage 有、AOSPA 没有」的桥。能开机的价值只在**记下了哪些 AOSPA 坑**，不在文件本身。

---

## 2. 官方 AOSPA 和社区版不是一回事，但版本坑已经变了

| 组织 | 是什么 |
|------|--------|
| [AOSPA](https://github.com/AOSPA) | 官方 Paranoid Android |
| [aospa-shadedark](https://github.com/aospa-shadedark) | 从 AOSPA fork 的社区树，多 PI/keybox 伪装、vanilla/microG 等 |

**现在**两边默认分支都叫 `calcite`，而且**都已经是 Android 17**：

- 官方 manifest 已合 `LA.QSSI.17.0`（例如 `LA.QSSI.17.0.r1-10900-qssi.0`）。
- `beryl` 才是停住的 A16（`LA.QSSI.16.0`，大约到 2026-05）。
- 官网 [paranoidandroid.co](https://paranoidandroid.co/) 仍主推旧稳定版，**不要看官网判断源码代际**。

shadedark 的 `calcite` 跟官方同源，manifest 只多「跟踪自己的 fork」。它**没有**比官方更早做出 A17；多出来的是 spoof / vanilla 一类提交（`frameworks/base` 大约领先官方上百个 commit）。

**用户拍板：平台用 aospa-shadedark `calcite`，不要用官方最小树。** 这样 PI spoof / vanilla 直接在平台里，不用以后再搬。

上次失败的那版是 **A16 平台 × A17 设备树写法**。换 shadedark **不会自动修好没声音和通话**；那两件事是设备/音频/IMS 没接完。

---

## 3. 这次要做成什么样

- 机型：努比亚 Z60 Ultra，codename `cerro`，型号 NX721J，平台 `pineapple` / SM8650。
- ROM 平台：**aospa-shadedark `calcite`**，init 必须带 **`--git-lfs`**。
- 必须先核对是真 A17。本机已经对过一次：`source/.repo/manifests/system.xml` 里 QCOM QSSI upstream 是 `refs/heads/qcom-sysintf.lnx.17.0.r2-rel`。换机器后**再核一次**，不要凭分支名 `calcite` 假设。
- 设备树：**从 [nubia-sm8650-devs](https://github.com/nubia-sm8650-devs) `lineage-23.2` fork 新分支**（建议名 `penguinos-calcite`），再打 AOSPA/shadedark 接线。
- **禁止**把旧 ycrrongos AOSPA `main` 当上游继续 rebase。
- **禁止**把 ArtistAOSP / Plasma / Voltage 功能整包搬进 AOSPA。`/mnt/data/ArtistAOSP` 只读对照。
- PenguinOS 品牌组件**以后再说**，进 `vendor/penguinos/`，不要塞进 `device/nubia/*` 基线。
- 先做：开机 → 显示 → 无线 → **媒体有声** → 数据 → **通话不崩**。SELinux 目标是 enforcing，不要长期 `permissive`。

官方/shadedark 的 `vendor/aospa/products/` **都没有 cerro**。产品壳要自己写（`aospa_cerro.mk` + `beans.xml`）。

---

## 4. 三棵树怎么用

| 代号 | 来源 | 怎么用 |
|------|------|--------|
| **U** | nubia-sm8650-devs `@ lineage-23.2` | **新树的文件底** |
| **V** | `/mnt/data/ArtistAOSP/source/device/nubia/{cerro,sm8650-common}` | 真 A17 上能编的对照。只看差异，**整树不要搬**。里面有 `plasma_*`、`voltage_cerro.mk` |
| **A** | ycrrongos 那两仓 `main` | **只摘接线知识**，不当 base |

一句话：A = 把 V（A17 Lineage/Voltage 写法）拧到当时的 A16 AOSPA，再加 permissive / bootdiag。

本机对照拷贝（若还在）：

- Lineage 参考：`/mnt/data/ArtistAOSP/reference/device-trees/lineage-cerro`、`lineage-sm8650-common`
- Voltage 工作树：`/mnt/data/ArtistAOSP/source/device/nubia/`
- Voltage 的 local manifest 也是拉 nubia-sm8650-devs `lineage-23.2`

---

## 5. 从旧树 A 里只带走这些（KEEP）

实现时以 **U 为底重写**，不要整文件粘贴 A。

### 必须重做进新树

1. **`TARGET_USES_KERNEL_PLATFORM := false`**，而且必须写在 `inherit aospa-target.mk` **之前**。否则 AOSPA qti-dlkm 会去拷 `device/qcom/pineapple-kernel/Image`。cerro 内核在 `kernel/nubia/sm8650`，走 Lineage 式 `kernel.mk`。
2. **躲开 CLO `kernel_definitions.mk`**：A 用  
   `TARGET_PREBUILT_KERNEL := $(PRODUCT_OUT)/obj/KERNEL_OBJ/arch/arm64/boot/Image`  
   骗过 QGKI 菜谱（它一看到非空 prebuilt 就跳过），Lineage `kernel.mk` 仍真编。上真 calcite 后先确认是否还撞，能少 hack 就少。
3. **`BOARD_PREBUILT_DTBOIMAGE := $(PRODUCT_OUT)/prebuilt_dtbo.img`** 要早点设。AOSPA Makefile 拷 dtbo 的时机早于 Lineage `BoardConfigKernel`（那时还没有 `TARGET_OUT_INTERMEDIATES`）。
4. **`ufsbsg` soong_config = `bsg`**（官方 pineapple 也用 bsg）。
5. **整组 `qtidisplay` soong flags**。AOSPA 的 `device/qcom` BoardConfigQcom **没有** Voltage/Lineage CAF 那套变量。缺了 `qtidisplay_defaults` 不带 `display_headers`，`libsdmdal` 编译失败（A 里记过 0037）：
   - `default`、`drmpp`、`gralloc4`、`displayconfig_enabled`、`ubwcp_headers`、`udfps`、`legacy_pphwresourceinfo` = true
   - `composer_version` = `v3`
6. **`PRODUCT_SOONG_NAMESPACES` 含 `hardware/qcom-caf/sm8650`**，否则 display composer/allocator/`libdisplayconfig.qti` 装不进。不要把更宽的 CAF 树一股脑加进去。
7. **不要**再 inherit `hardware/qcom-caf/common/common.mk` 去建 rfs/mountpoint。AOSPA 已经通过 `device/qcom/common` 做过，重复会 ckati override。
8. **不要**用 Lineage 式 `PRODUCT_PACKAGES` 再建 `vendor/firmware_mnt`、`bt_firmware`、`dsp`。AOSPA 在 `TARGET_FWK_SUPPORTS_FULL_VALUEADDS=true` 时已经建了。
9. **Wi‑Fi 库用 soong 全路径**，不要 Lineage 短模块名。AOSPA CLO 的 qcwcn 在 namespace 里，短名 hostapd 看不见：
   - `BOARD_HOSTAPD_PRIVATE_LIB := //hardware/qcom/wlan/qcwcn/wpa_supplicant_8_lib:lib_driver_cmd_qcwcn`
   - `BOARD_WPA_SUPPLICANT_PRIVATE_LIB` 同样
10. **`qseecomd` 改到 `on late-fs` 再 start**。persist 没挂就按 proprietary 的 on-init 起会挂。用 `PRODUCT_COPY_FILES` 盖掉 vendor 里的 rc。
11. **产品壳结构保留**：`TARGET_BOARD_PLATFORM := pineapple`，`core_64_bit_only`，`aosp_base_telephony`，然后 inherit `device/nubia/cerro/device.mk`，再 inherit `vendor/aospa/target/product/aospa-target.mk`。屏幕 1116×2480。指纹继续用库存  
    `nubia/PQ83A01-UN/PQ83A01:15/AQ3A.240812.002/20250916.013811`。  
    Lunch：`aospa_cerro-userdebug`。
12. **`beans.xml` 要新写**（shadedark 没有 cerro）。设备/内核/vendor 路径按 U，revision 用你的新分支，不要写死旧 `main`。
13. **`telephony-ext` 不要再加进 `PRODUCT_BOOT_JARS`**。`aospa-target.mk` 已经加了。

### 条件保留（先别当正确实现）

- A 自带的 `build/tasks/kernel.mk`、`BoardConfigKernel.mk`、`stage-audio-kernel-uapi.sh`：只有 U 的内核构建在 calcite 上还和 CLO 撞，才精简搬过去。
- `init.cerro.camera.sh`：相机后置，先别挡音频和电话。
- `SettingsProviderResCerro`：还需要默认设置再留。
- DT ramoops carve（`android_kernel_nubia_sm8650-devicetrees`）：调试需要再留。
- vendor `aospa-cerro`：**先 diff 相对 `lineage-23.2`**，只拣 Android.bp / 拷贝规则。blob 底仍是 nubia-sm8650-devs `lineage-23.2`，不要拿 A16 时期 blob 直接配 A17 framework。

### 丢掉（DISCARD）

- 整仓 A 当 base。
- 长期 `androidboot.selinux=permissive`（A 的 `BoardConfigCommon.mk` 里有）。只允许极早期调试。
- `init.cerro.bootdiag.*`（纯调试）。
- README 里「calcite = Android 16」的说法。
- 为了编过随便加、没验证的 prop。
- 全部 Plasma/Voltage：`plasma_*`、`plasma_privexec`、`plasma_sukisu`、`artist_cerro.mk`、`voltage_cerro.mk`、Gboard 预装、`vendor/plasmaos` apply 链。
- Lineage 专用、AOSPA 没有对等物的包，除非你确认 shadedark 仍提供：
  - `vendor.lineage.health-service.default`
  - `vendor.lineage.livedisplay-service.sysfs`
  - `vendor.lineage.touch-service.nubia_sm8650` + `TouchscreenRotation`（滑键会缺，需另做或暂缺）
  - `inherit vendor/lineage/config/common_full_phone.mk` → 改成 `aospa-target.mk`
  - 完整 `device/lineage/sepolicy` common。A 只 include 了 `device/lineage/sepolicy/libperfmgr/sepolicy.mk`，再加自己的 `sepolicy/{public,private,vendor}`。新树同样不要全量 inherit，te 只留确有的，再收紧。

### 必须重做，不能照抄 A 的现状（REWORK）

| 主题 | 原因 |
|------|------|
| **音频** | XML 骨架（`sku_pineapple` + mixer / resourcemanager / policy）U/V/A 很像，但 CLO/ADSP/HAL 代际不同。A 上**完全没声音**，说明那套拷贝在旧平台上是失败的。以 U + **这次 calcite 的 CAF audio** 重接。先媒体声，再通话。 |
| **电话 / IMS** | overlay 里写 `org.codeaurora.ims` 只是声明。崩溃要看 radio/ims/audioserver/tombstone。常见是一开 voice path，坏音频栈把 Dialer 或 audioserver 打挂。 |
| **blob / 固件** | 按 A17 CLO 核对。A16 早期 blob 和 A17 binder/framework 混用会炸。 |
| **SELinux** | A 的 sepolicy 只当线索，目标 enforcing。 |

---

## 6. 旧树里已经写死、你重做时会再碰到的细节

这些是 A 的 `common.mk` / `BoardConfigCommon.mk` / cerro `device.mk` 里的原话，方便你搜索，不是让你复制文件：

- 音频包：`audio.primary.pineapple`、`sound_trigger.primary.pineapple`、HIDL audio 7.1 / effect 7.0、PAL/AGM。  
  配置拷到 `$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_pineapple/`。  
  HAL 路径写成 `hardware/qcom-caf/sm8650/audio/primary-hal` 和 `.../audio/pal`。**在新 calcite 上先确认这个路径还在**，AOSPA 可能改成 `device/qcom` 或 `vendor/qcom/opensource`。
- `BOARD_SHIPPING_API_LEVEL` / `PRODUCT_SHIPPING_API_LEVEL := 34`（出厂是 Android 14）。这是设备 shipping level，不是「系统是不是 17」。
- `androidboot.selinux=permissive` 在 `BOARD_BOOTCONFIG` 里。新树拿掉。
- cerro `device.mk` 额外拷了 camera init、bootdiag、以及覆盖用的 `qseecomd.rc`。
- sepolicy 里还有 `hal_lineage_touch`。去掉 lineage touch HAL 时一起删，否则 neverallow/编译会炸。

---

## 7. 建议的仓库拼法

```
device/nubia/cerro           ← fork U，产品改成 aospa_cerro.mk
device/nubia/sm8650-common   ← fork U，按上面 KEEP 逐条加接线
kernel/nubia/sm8650
kernel/nubia/sm8650-devicetrees
kernel/nubia/sm8650-modules
vendor/nubia/cerro
vendor/nubia/sm8650-common   ← U 的 lineage-23.2，再拣 aospa-cerro 的必要 delta
vendor/aospa/products/cerro/ ← 新写 aospa_cerro.mk 入口 + beans.xml
                               （或 fork shadedark 的 android_vendor_aospa）
```

拉源码（**在磁盘够的机器上**，大约要留 **250GB+ 空闲**，浅克隆、只要手机源码；全历史 + 模拟器/电视/车机会到 400GB+ 并容易写满）：

```bash
source scripts/proxy-env.sh   # 若在用户机器上：flclash http://127.0.0.1:7890
# 用户这台机器上 REPO_URL 清华源会把 git-repo 自身排队到 Position 600+。
# 已验证做法：unset REPO_URL，走代理直连 googlesource。

repo init -u https://github.com/aospa-shadedark/manifest -b calcite --git-lfs
# 放入 local manifest（设备指向你的 penguinos-calcite，或先指 nubia-sm8650-devs lineage-23.2）
repo sync --current-branch --no-tags -j4
```

编译（源码根目录自带）：

```bash
./rom-build.sh cerro
```

核对 A17（sync 之后）：

- `system.xml` / QSSI 项目 revision 含 `17.0`，不要是 `LA.QSSI.16.0`。
- 刷机后 `getprop ro.build.version.release` 为 17。

---

## 8. 用户这台电脑：停，不要接着干

用户原话：硬盘空间不够，不想在这台电脑上做这件事。

已经发生过的事（2026-09-17～09-19，`/mnt/data/PenguinOS_cerro/source`）：

1. `repo init` **aospa-shadedark `calcite` `--git-lfs` 成功**。QSSI 已确认是 17（`qcom-sysintf.lnx.17.0.r2-rel`）。
2. local manifest 指的是 **nubia-sm8650-devs `lineage-23.2`**，还不是 `penguinos-calcite`（那个分支还没建）。
3. `repo sync` 多次把盘写满。`/mnt/data` 约 1.5T，旁边还有 ArtistAOSP（约 371G）、Avium 等树。
4. 曾误拉成 **全部分支全历史**（清单里的 `clone-depth=1` 对已有非 shallow 仓库无效；钉 SHA 失败时会关掉 `current_branch_only`，变成 `refs/heads/*`）。`source/` 一度到约 443G。预编译对象库：rust ~51G、clang ~39G、tradefederation ~34G。
5. 已加 `local_manifests/phone-only.xml` 去掉模拟器、电视、车机、手表、其它 QCOM 芯片、32 位 QSSI 等。并删过废 `tmp_pack_*`。
6. 后来改成 `repo.depth=1`，删掉 prebuilts 对象库准备浅克隆重下。**这次浅克隆没有在这台机器上跑完。**
7. 2026-09-20 左右这棵 `source/` 大约 **162G**，是**未完成树**。不要把它当成能编的 A17 树，也不要在这台机器上 `--force-sync` 续拉。

若你在别的机器做：重新 `repo init` + 浅克隆 + 只要 arm64 手机相关项目。不要把这台机器上半截 `source/` 拷走当完整树。

用户机器上的代理（仅当你不得不在这台机器上下载时）：flclash `127.0.0.1:7890`，先 `source /mnt/data/PenguinOS_cerro/scripts/proxy-env.sh`。代理不通就停，不要改成直连再怪镜像。

---

## 9. 你接下来按这个顺序做

1. 换到**磁盘够**的环境。不要续用户这台机器的 sync。
2. `repo init` aospa-shadedark `calcite --git-lfs`，确认 QSSI 17。
3. Fork nubia-sm8650-devs 的 device/common（以及按需 kernel/vendor）到 ycrrongos **新分支** `penguinos-calcite`。不要推回旧 `main`。
4. 以 U 为底，只打第 5 节的 KEEP。产品壳和第 6 节路径在新树上重对一次。
5. `lunch aospa_cerro-userdebug` 能过 soong。
6. 亮机 → 媒体有声 → 再通话。没声/通话崩时抓 log，不要先堆 Plasma 功能。
7. 不要 git commit，除非用户明确说提交。

开机后若还是没声或打电话崩，先抓：

```bash
adb logcat -b all | tee audio.log
# 搜 audioserver | audio_hw | qti_audio | ADSP | Fatal

adb logcat -b crash -b main -b radio | tee call.log
# 搜 Dialer | Telecom | ImsService | qcril | audioserver | tombstone
```

---

## 10. 用户身份（避免再误判）

- 用户就是 GitHub 上的 **ycrrongos**。
- 旧公开树是同一个人、上一轮 agent 做的，不是第三方上游。
- PenguinOS 是以后要叠的组件名；**这一轮只重开干净的 shadedark A17 + cerro 基线**。
- ArtistAOSP（PlasmaAOSP）是另一套 Voltage 17 工程，继续由那边维护。不要把 Penguin 补丁打进 ArtistAOSP，也不要把 Plasma 补丁打进这次的 AOSPA。
