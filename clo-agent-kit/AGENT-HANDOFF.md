# CLO / 类原生 ROM Agent 交接文档（Nubia Z60 Ultra / cerro）

> **设备**：NX721J，代号 **cerro**（部分脚本写 caza，同一机）。SoC **SM8650**，Firehose 用 **v1**（`prog_ufs_firehose_sm8650_v1_ddr.elf`）。  
> **本包用途**：刷机、关 AVB、9008/fastboot 判定、AOSP 往返；**不含**完整 ROM 镜像与编译树。  
> **母仓库**：`LOA_Nubia_Z60U`（Linux 主线 + Cerro 工具）；CLO ROM 工程可能在 `ArtistAOSP` / 独立树。

---

## 1. 先读什么

| 优先级 | 文件 |
|--------|------|
| 1 | 本文件 `AGENT-HANDOFF.md` |
| 2 | `agent.md`（硬约定：双槽、先观察 USB、别当 Dump=9008） |
| 3 | `docs/usb-and-modes-quickref.md` |
| 4 | `docs/bootloader-flash-assessment.md`（AVB / 工程 ABL 结论） |
| 5 | `docs/cerro-hardware.md`（屏/触/WiFi，改内核或 vendor 时查） |
| 6 | **`docs/servo-flash-clamp.md`**（舵机刷机夹：BOM、接线、校准、进 9008） |

母仓库若还在维护：`notes/cerro-linux-bringup.md` 有完整时间线与 Debian/AOSP 往返记录。

---

## 2. 主机环境（一次性）

```bash
cd tools/edl-tools
./install-udev.sh          # 需 sudo；9008 / fastboot 权限
./setup-edl-venv.sh          # python3 venv + bkerler/edl 依赖
source ./edl-env.sh          # 之后 edl / edl-printgpt / edl-reset 可用
```

系统包（Arch/Debian 名可能不同）：`python3`、`adb`、`fastboot`、`android-tools`、`lsusb`、`timeout`。

**代理**：拉 GitHub 走 FlClash `127.0.0.1:7890`（母仓库 `scripts/proxy-env.sh` 同款）。

---

## 3. USB 模式（观察优先于结论）

| `lsusb` / 现象 | 含义 | 能做什么 |
|----------------|------|----------|
| `05c6:9008` | 真 EDL | `edl.py` 写分区 |
| `18d1:d00d` + `fastboot devices` 有应答 | fastboot | `fastboot flash` |
| `19d2:0112` | ZTE **MemoryDump**（硬崩） | **不能**当 9008 刷 |
| `1d6b:0104` | USB gadget / ACM | Linux 启动后串口；常需 `modprobe cdc_acm` |
| 黑屏无 USB | 早期 hang | cerro **很少自动进 9008**，需手动或舵机 |

### 进 9008（手动）

1. 长按电源 20–30s 关机（屏全黑）
2. **同时按住音量+和音量−**，插 USB
3. `lsusb` 应见 `05c6:9008`

### 舵机自动进 9008（刷机夹 + agent-phone）

**硬件**：3D 件 `hardware/servo-flash-clamp/nubia-z60u-clamp-v1.stl` + FireBeetle2 + 3×舵机 + **5V 外电**。详见 `docs/servo-flash-clamp.md`。

```bash
# 校准（首次 / 换件后）
tools/agent-phone/start-calibration-server.sh   # http://127.0.0.1:8787

# 进 9008（在 kit 根目录执行）
HOLD_S=90 MIN_HOLD_S=8 tools/edl-tools/enter-9008-hand.sh
```

按住到出现 `05c6:9008` 再松；串口用 Espressif **by-id**，勿占裸 `/dev/ttyACM0`（会和手机 ACM 撞车）。角度文件：`tools/agent-phone/press-angles.env`。

### 判定脚本

```bash
source tools/lib/cerro-usb-detect.sh
cerro_detect_raw              # edl|fastboot|dump|adb|none
cerro_wait_mode edl,fastboot 300
```

---

## 4. 关闭 AVB / 校验（类原生必知）

**原则**：自编或未签名 `boot` / 动态分区镜像时，必须让 ABL **不校验** AVB，否则红屏/拒绝启动。

### 方法 A：刷预制 vbmeta（推荐，本包已带）

镜像在 `tools/edl-tools/pmos-flash/`：

- `vbmeta.img` — 顶层 vbmeta（flags 已关校验）
- `vbmeta_system.img` — system 分区链 vbmeta（flags=3 风格）

**9008 双槽**（进 EDL 后）：

```bash
source tools/edl-tools/edl-env.sh
LOADER="$EDL_LOADER"
edl w vbmeta_a        tools/edl-tools/pmos-flash/vbmeta.img
edl w vbmeta_b        tools/edl-tools/pmos-flash/vbmeta.img
edl w vbmeta_system_a tools/edl-tools/pmos-flash/vbmeta_system.img
edl w vbmeta_system_b tools/edl-tools/pmos-flash/vbmeta_system.img
edl reset
```

或合并进启动链脚本（见下）。

### 方法 B：fastboot 关 verity（设备已在 fastboot 且支持时）

```bash
fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img
fastboot --disable-verity --disable-verification flash vbmeta_system vbmeta_system.img
```

（双槽机建议 **a/b 都写**，与 EDL 脚本一致。）

### 方法 C：`flash-failsafe.sh`（Artist 侧 failsafe 包）

需额外镜像目录 `FAILSAFE_IMG`（非本包默认内容）；逻辑见脚本注释。

**不要**在未关 AVB 的情况下只刷自编 `boot` 就宣称 PASS。

---

## 5. 常用刷机脚本（本包 `tools/edl-tools/`）

| 脚本 | 场景 |
|------|------|
| `wait-9008.sh <cmd>` | 等到 9008 再执行 |
| `flash-boot-any.sh <boot.img>` | **双槽** boot + stock vendor_boot + 擦 dtbo；优先 9008 |
| `flash-artistaosp-bootchain-edl.sh` | EDL 刷 AOSP boot 链（boot/init_boot/vendor_boot/dtbo/vbmeta/recovery…） |
| `flash-aosp-fastbootd.sh [--wipe] <out/product/cerro>` | fastbootd 刷动态分区 + 可选 wipe |
| `flash-infinityx-fastbootd.sh` | 同上（InfinityX 产物路径） |
| `restore-aosp-roundtrip-partitions.sh` | 从 `backups/.../pre-aosp-partitions` 还原小分区 |
| `restore-debian-userdata-fastbootd.sh` | 还原 Debian userdata sparse（母仓库备份） |
| `backup-aosp-roundtrip-partitions.sh` | 出远门刷 AOSP 前备份 |
| `auto-flash-watch.sh --daemon <boot.img>` | 后台监听 9008/fastboot 自动刷 |
| `auto-observe-boot.sh --daemon <label>` | 刷后观察 PASS/FAIL/hang |
| `restore-bootchain.sh` | Artist 树配套：built/backup 启动链 |
| `flash-pmos-boot.sh` | 第三方 boot + 本包 vbmeta（Linux 线，CLO 可忽略） |

**硬规则**：`boot_a` **和** `boot_b` 都要刷；`vendor_boot_{a,b}` 保持原厂；擦 `dtbo_{a,b}`。半刷会导致切槽后「过一会又能进」的假象。

---

## 6. CLO / 类原生 ROM 典型流程

### 6.1 首次刷入或换 ROM

1. 备份：若有母仓库 `backups/debian-native-20260817/pre-aosp-partitions/`，先校验 SHA256。
2. 编译产物：`out/target/product/cerro/`（或你的 product 名）。
3. **EDL**：`flash-artistaosp-bootchain-edl.sh`（或等价）刷 boot 链 + misc→recovery。
4. `adb reboot fastboot` → **fastbootd**。
5. `flash-aosp-fastbootd.sh [--wipe] /path/to/out/product/cerro`。
6. 若自编 boot/vendor_boot：确保 **vbmeta 已关 AVB**（§4）。
7. 重启后 `adb devices`；相机/音频等另排。

### 6.2 只改 boot（内核/GKI 实验）

```bash
./tools/edl-tools/flash-boot-any.sh /path/to/boot.img
# 同时确认 vbmeta 仍为 AVB-off
```

### 6.3 从 AOSP 还原 Debian（母仓库已有材料）

见 `notes/cerro-linux-bringup.md`「测 AOSP 前还原就绪」：V2 userdata sparse + ipa-imem-c1 boot + stock vendor_boot。

---

## 7. 工程 ABL / XBL（一般 CLO 不用动）

- 解锁已完成后：**保持 retail xbl/abl** 即可刷分区。
- 工程 `eng_v1/abl.img` 仅用于 `fastboot flashing unlock` 或更宽松 fastboot；**不是**刷分区前提。
- **不要**刷工程 XBL（救砖成本最高，收益为零）。详见 `docs/bootloader-flash-assessment.md`。

Firehose 与中兴工具箱 `abl_unlock.elf` / `devprg` 与 `nubia_sm8650_eng` **字节一致**（已核对）。

---

## 8. 本包目录结构

```
clo-agent-kit/
  AGENT-HANDOFF.md          ← 本文件
  README.md
  agent.md
  MANIFEST.txt
  docs/
    servo-flash-clamp.md    ← 舵机刷机夹（BOM/校准/进9008）
  hardware/
    servo-flash-clamp/      ← STL 打印件
  tools/
    edl-tools/              # 脚本 + edl + firehose + vbmeta
    lib/cerro-usb-detect.sh
    agent-phone/            # 舵机固件 + CLI + 网页校准
```

**未包含**（太大或机位相关，仍在母机/母仓库）：

- `venv/`（用 `setup-edl-venv.sh` 生成）
- 完整 `pmos-flash/backup-*` 分区备份（数百 MB～GB）
- AOSP/Debian 编译树、`build/linux/`
- ArtistAOSP `device-dump` 全量

若母机已有：`/mnt/data/ArtistAOSP/edl-tools/venv` 可 symlink 到本包 `tools/edl-tools/venv`。

---

## 9. Agent 行为约定（简）

1. 进 9008/fastboot 后 **先看 USB**，再下结论。
2. 刷完 **继续盯** 到 PASS/FAIL/hang，不要停。
3. MemoryDump ≠ 9008；线没插好 ≠ 脚本坏了。
4. 用户说「先 AOSP / 暂不 Linux」时：**不要擅自刷 Linux boot**。
5. 踩坑结论写回母仓库 `notes/cerro-linux-bringup.md`。

---

## 10. 快速命令备忘

```bash
# 环境
source tools/edl-tools/edl-env.sh

# GPT
edl printgpt

# 写分区（示例）
edl w boot_a my-boot.img
edl reset

# fastbootd
adb reboot fastboot
fastboot devices

# 关 AVB（fastboot 路径，镜像用本包 pmos-flash）
fastboot --disable-verity --disable-verification flash vbmeta_a tools/edl-tools/pmos-flash/vbmeta.img
```

---

*打包日期见 `MANIFEST.txt`。问题先查本文件与 `docs/`，再查母仓库 bringup 时间线。*
