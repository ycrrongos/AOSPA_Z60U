# Nubia Z60 Ultra (cerro / NX721J) — 下游硬件配置清单

> 来源:对本机 EDL 全量备份 `backups/device-dump-20260717-222750/by-name/` 中
> `vendor_boot_a.img`(基础 SoC DTB ×7)与 `dtbo_a.img`(DT overlay ×4)反编译得到。
> cerro 专属配置全部集中在 **dtbo overlay #1**(`downstream-dt/dts/dtbo_1.dts`)。
> 反编译产物见 `downstream-dt/dts/`。

## SoC / 平台

| 项 | 值 |
|----|----|
| SoC | Qualcomm Snapdragon 8 Gen 3 = **SM8650**,代号 pineapple/lanai |
| 主线内核 | 已支持(v6.6 引入,v6.8+ 较完整) |
| 架构 | aarch64 |
| 存储 | UFS（sector size 4096）；Linux 根为 `/dev/sda12` ext4，2026-08-17 在线扩至 453.1GiB（未改 GPT/未格式化） |
| boot.img | header v4,GKI 内核 ~34MB(gzip),ramdisk 在 init_boot/vendor_boot |
| vendor cmdline | `ignore_loglevel sysctl.kernel.firmware_config.force_sysfs_fallback=1 bootconfig` |

## 显示(重点)

- **主线 Linux 实机（2026-08-17）**：Adreno 750 使用 Mesa msm/freedreno，EGL/OpenGL renderer=`FD750`；Plasma `kwin_wayland` 的 OpenGL compositing 初始化成功，无软件渲染回退变量。
- **实机主屏（AOSP 实测 2026-08-11）**：**BF068 / Raydium RM692H0**，**1116×2480**，**CMD + DSC**，**OLED（无独立背光；亮度走 DCS `0x51`，vendor 带 inverted-dbv）**。
  - overlay 默认：`panel = <&dsi_bf068_rm692h0_6p8_plus_dsc_cmd>`
  - SurfaceFlinger / `dsi_display_set_mode`：`hactive=1116, vactive=2480`
- DTBO 另有 Visionox **VTDR6130**（1080×2400）备选节点；主线 `panel-visionox-vtdr6130` **不能当 cerro 主屏**（会黑屏）。
- 电源轨映射(PM8550B,"B" 后缀) + cerro GPIO 供电路：
  - `vdd`  = **L11B**；`vddio` = **L12B**；`vci` = **L13B**
  - 另见 `zte-lcd-supply-cerro`：`display_panel_vddio` / `display_panel_vddd` GPIO 开关
- 显示控制器:`mdss_mdp@ae00000`、`dsi_ctrl0@ae94000`、`dsi_ctrl1@ae96000`、`dp_display@ae154000`、`sde_rscc@af20000`(标准 sm8650 地址)。

## 触摸屏

| 项 | 值 |
|----|----|
| **本机实机（RM692H0 / AOSP 2026-08-15）** | **`goodix,brl-d`，PID `9916R`**（`goodix-berlin-d@0`） |
| 同总线备用节点 | `goodix,gt9916S`（`goodix-berlin@0`）在本 SKU **status=disabled**；stock DTBO 里 `qcom,touch-active` 仍可能写 gt9916S |
| 总线 | SPI `@a90000`（spi0.0），**20MHz** MODE0（gt9916S 路径曾写 1MHz） |
| 主线驱动 | `goodix-berlin-core` + `goodix-berlin-spi` |
| reset-gpio | TLMM **161** |
| irq-gpio | TLMM **162**，flags EDGE_FALLING |
| **AVDD** | **TLMM gpio28 负载开关**（非 L14B；AOSP 上 L14B disabled） |
| IOVDD | L12B / `vdd`（1.8V） |
| 固件 | `goodix_firmware_9916r.bin` + `goodix_cfg_group_9916r.bin`（`*_spi.bin` 不存在） |
| 分辨率 | brl-d panel-max 17856×39680（=16×1116×2480） |

旧笔记曾把 gt9916S+L14B 当主触；对 BF068/RM692H0 机以 brl-d 为准。

**主线 Linux 用户态（2026-08-17）**：内核设备名 `Goodix Berlin Capacitive TouchScreen`、`/dev/input/event2`；libinput capability=`touch`。Plasma 会话使用 Wayland，以支持 KDE 多指手势路径。

## 无线 / 连接

| 功能 | 器件 | 主线方向 |
|------|------|---------|
| WiFi/BT | `qcom,cnss-kiwi@b0000000`；PCI **`17cb:1107`**；驱动 `qca_cld3_kiwi_v2`+`cnss2`；BT `bt_kiwi`/`qcom,kiwi`/`bt_power`，UART **0x898000**，soc 名 **hamilton** | **实机 PASS**：`ath12k_wifi7`/WCN7850 hw2.0（board_id `0xff`）可扫描、关联、DHCP/HTTPS；BT `hci0` UART UP/RUNNING，Bluetooth 5.4、powered/pairable。固件见 `notes/firmware-kiwi/` |
| NFC | `st21nfc@08`(ST,I²C) + `st54spi@0`(ST 安全元件,SPI) | 社区 st-nfc 驱动 |
| GPS | 走 modem/qcom pd | 未验证 |
| Modem | AOSP: `remoteproc-mss@4080000` ONLINE, FW `modem.b*` on `firmware_mnt`. Native Debian has MPSS/ADSP/PAS, IPA, RMTFS, TQFTP, service52 DHMS and service64 root-PD working. `cellular-modempr-c1` mounts stock modem_a read-only, verifies all196 modem_pr files (`c22817b4...`) and successfully serves RF HWID1006 plus MCFG SW digest. `cellular-modempr-nometa-c1` disables the early Meta_Build_ID0x69 sender with an exact `/bin/true` no-op. Under this combination ModemManager exposes Qualcomm modem0 as power-on/registered on China Mobile46000 home network, packet attached over5GNR with recent50% signal; CMCC carrier config and CMNET/IPv4v6 load with no network rejection. This resolves the prior RF initialization and cellular-registration failure. Whole-device hard resets were root-caused on 2026-08-19 to the missing stock IPA IMEM identity mapping (see below); after flashing stability-ipa-imem-c1 (boot SHA `9d3bcae4...`) the reset loop stopped and one boot stayed stable for 31+ minutes with cellular registered/attached. No data bearer has been created because it requires separate setter authorization. | cellular registration PASS; stability PASS (IPA IMEM fix). Data-bearer testing still needs separate authorization; no unapproved setter/reboot/EFS rollback/remoteproc-only restart |

**AOSP 实机（2026-08-15）**：`wlan0` 可扫 AP；BT State=ON；regulator 绑定 L15B/L3C/L6K/S1C–S3C/S6C/S4I（与下游 cnss-kiwi 一致）。

**Modem EFS 实机补证（2026-08-18）**：cellular-pdmap-c1 冷启动后的 Debian `rmtfs -P -s` 已累计从块设备实际读取 160,616,448 bytes、写入 4,194,304 bytes，并同时持有 `qcom_rmtfs_mem1`、modemst1/2；stock 与 Debian 的 modemst1/2/fsc/fsg 分区映射一致。故已排除“MPSS 根本未访问 EFS”和“分区映射错误”，下一层应比较原厂 `rmt_storage` 与主线 `rmtfs` 的共享内存 coherency/记录语义。

**MODEMPR-C1 EFS 终值（2026-08-18）**：modemst1 `1219b477...`、fsc `fa43239b...`、fsg `6d93f71f...` 与本候选启动前一致；modemst2 从 `e5784ebc...` 变为 `943a3e4a...`，符合已授权的基带运行时 RMTFS 写入范围。未回滚 EFS，未直接写其他分区。

**MODEMPR-NOMETA-C1 EFS 终值（2026-08-18）**：modemst1 `1219b477...`、modemst2 `943a3e4a...`、fsc `fa43239b...`、fsg `6d93f71f...` 均与本次安装前一致；未回滚 EFS，未观察到新的授权范围内 EFS 内容变化。

**IPA IMEM/SMMU 精确差异（2026-08-18，2026-08-19 已验证为根因）**：实机 Debian 多次在 SID `0x4a0` 报完全相同的 IOMMU translation fault，IOVA=`0x14684080`。SID `0x4a0` 是 IPA AP context。原厂编译产物 `pineapple-ipa.dtbo`（SHA-256 `3d7bdda8...`）明确给该 context 增加 identity mapping `0x14683000..0x14684fff`，恰好覆盖故障地址；原主线 Cerro DTB 只通过 `sram` 映射 `0x14688000..0x14689fff`。2026-08-19 刷入仅改 DT `sram` reg `<0x8000 0x2000>`→`<0x3000 0x2000>` 的候选 boot（`stability-ipa-imem-c1`，SHA `9d3bcae4...`）后：translation fault 归零、IPA setup 成功、同一 boot ID 稳定存活 31+ 分钟，**确认该映射缺失就是整机硬重启根因**；此修正必须保留进 `linux/sm8650-nubia-cerro.dts`。

**主线 Linux 实机（2026-08-17）**：`wlan0` 已连接 5GHz AP 并通过 HTTPS；USB ECM 仅作 metric 2000 的备用默认路由。BT controller 名 `Nubia Z60 Ultra`，manufacturer Qualcomm (`0x001d`)。

## 音频（实机 / AOSP 2026-08-17）

| 路径 | 器件 | 证据 |
|------|------|------|
| **扬声器（本 SKU）** | **2× Awinic AW88261（chipid `0x2113`）** | AOSP `aw882xx 2113 detected`；I²C **`i2c_hub_3` @98c000** `0x34`/`0x35`；gpio**70/71**=SDA/SCL (`i2chub0_se3`)；stock `dtbo_1` fragment@159 |
| WSA884x SoundWire | **本 SKU 禁用** | 运行时 `wsa-macro`/`wsa2-macro` **`status=disabled`**；`msm_int_wsa881x_init: WSA is not enabled`；LPASS gpio10/11/15/16/21 UNCLAIMED |
| 耳机 / WCD | WCD939x on swr1/swr2 | AOSP `swrm_get_logical_dev_num` 有 `e01170224/223` |
| 扬声器 PCM（AOSP） | SPF + **pri_mi2s / i2s0** | gpio**126** sck / **129** ws / **127** data0 / **128** data1；port `0x1006`/`0x1007` |
| 扬声器 PCM（主线 s5fy / SD0） | `PRIMARY_MI2S_RX` + 2× AW88261 | IBIT 投票 + tplg `HW_IF_TYPE=0`；PCM、两颗 AW PLL/SYSST/start/unmute 均 PASS，但重复 1kHz 采样两颗 `VSNDAT=0`、`ISNDAT` 仅噪声；用户确认 -22.5/-7.5 dB 均物理无声，端到端 FAIL |
| **扬声器 PCM（主线 s5fz / SD1）** | topology `SD_LINE_IDX=2`（gpio128/data1） | **端到端及双功放可闻 PASS**：用户确认 1kHz、700Hz 左、1200Hz 右均可闻；再把另一颗音量降到 0，隔离 0x34 播 800Hz、隔离 0x35 播 1400Hz，用户确认两段都响。0x35 `VSNDAT=0` 与实听冲突，不能用作该颗无输出的结论 |
| 固件 | `aw882xx_acf.bin` (+ `aw_cali.bin`) | `notes/firmware-aw882xx/`；主线 `firmware-name` |

## 传感器 / 输入 / 其它

- 指纹:`goodix,fingerprint`(屏下,SPI),pwr-gpio = TLMM **93** (0x5d)。**主线无驱动**,需用户态方案。
- 马达:`haptic_hv@5A`(I²C 0x5A,awinic haptic 系列)。
- ToF:`tof@29`(激光对焦)。
- 霍尔:`hall_sensor`。
- **游戏肩键**:`gpio_keys_nubia`(`game_sw_on` / `game_sw_off`)—— Z60U 特色的实体肩键滑块。
- USB:`usb-role-switch`(Type-C 角色切换);`nubia,usb_switch_dp`(DP alt-mode 切换)。

## PMIC 推断

SM8650 标准配套:pmk8550 / pm8550 / **pm8550b**(L11B/L12B/L13B/L14B 来自此)/ pm8550ve / pm8550vs / pmr735d。
主线 dts 引用方式:`&pm8550b_l11` 等(具体电压约束以主线 `pm8550.dtsi` 为准)。

## 移植可行性速评

| 子系统 | 主线现状 | cerro 难度 |
|--------|---------|-----------|
| CPU/UFS/USB/串口 | Works | 低 |
| 显示(VTDR6130) | 驱动已在主线 | **低**(最大惊喜) |
| GPU(Adreno 750 / freedreno) | Works | 低 |
| 触摸(goodix-berlin SPI) | 驱动在主线 | 低-中(需正确 SPI+电源+GPIO) |
| WiFi/BT(kiwi) | ath1xk | 中(需固件+节点) |
| 音频 | WCD 主线有；**扬声器是 AW882xx 非 WSA** | 中-高（需 Awinic + 路由） |
| Modem 蜂窝 | Works(参考机) | 中-高(rmtfs/固件) |
| 指纹/相机 | 无/弱 | 高(基本放弃) |
