# 工程版 bootloader 直刷分区可行性评估(t6)

> 依据:`tools/edl-tools/` 中已复制的实机脚本与镜像
> (`restore-bootchain.sh`、`nubia_sm8650_eng/README.md`、`flash-failsafe.sh`)。

## 现状事实(已核实)

- 手机代号 **cerro / NX721J / caza**,属 `sm8650_v1`;README 明确列入。
- 已有 **签名 firehose 加载器** `nubia_sm8650_eng/prog_ufs_firehose_sm8650_v1_ddr.elf`,
  可在 9008(EDL)下对**任意分区** `w <part> <img>`(实测脚本刷 boot/vendor_boot/
  init_boot/dtbo/recovery/vbmeta/vbmeta_system 双槽)。
- 已有 **工程版引导** `nubia_sm8650_eng/eng_v1/{abl.img, xbl.img, xbl_config.img}`。
- 解锁流程(README):刷 eng `abl.img` → 重启 fastboot → `fastboot flashing unlock`。
  即 **工程 ABL 的作用是放行 `flashing unlock`**,retail ABL 会拒绝。
- 当前机器上是 **发行版(retail)xbl/abl**(解锁后已刷回),BL 处于已解锁状态。
- 脚本已备好 **关闭 AVB 的 vbmeta**(`vbmeta_system_flags3.img`,`flash-failsafe.sh`),
  用于让改过/未签名的镜像通过校验。

## 已核实:中兴家族工具箱 vs edl-tools 工程版(SHA256 对比)

工具箱路径 `中兴家族工具箱1.2.8-beta4/bin/res/PQ83A01/`(PQ83A01 = NX721J = cerro),
**该目录只有两个文件**:`abl_unlock.elf` 和 `devprg`。逐字节比对:

| 文件 | 工具箱(PQ83A01) | edl-tools(nubia_sm8650_eng) | 结果 |
|------|------------------|------------------------------|------|
| 特殊 ABL | `abl_unlock.elf` `196876875f…` | `eng_v1/abl.img` `196876875f…` | **完全相同** |
| firehose 加载器 | `devprg` `01e4f38fd9…` | `prog_ufs_firehose_sm8650_v1_ddr.elf` `01e4f38fd9…` | **完全相同** |
| 特殊 XBL | *(工具箱未提供)* | `eng_v1/xbl.img` `a56f1d9a…` | 工具箱无此项 |

**结论修正**:对 cerro,中兴工具箱的解锁流程**只替换 ABL**,并不刷 XBL。
你记忆中的"特殊 ABL"就是 `abl_unlock.elf`(与 edl-tools 里的工程 ABL 同一文件);
"特殊 XBL"在本机型的工具箱里并不存在。edl-tools 里的 `eng_v1/xbl.img`/`xbl_config.img`
是另行(从库存固件)提取的,与工具箱解锁流程无关,**引导 pmOS 也用不到**。
这与下方 t6 结论一致:只需 ABL 层面处理,XBL 不用碰。

## 关键判断

**"能不能刷分区" 从来不是瓶颈 —— EDL firehose 已经能刷任何分区,
与装的是发行版还是工程版 ABL 无关**(firehose 运行在比 ABL 更早的阶段)。

真正决定"刷进去的 pmOS 内核能不能被引导"的是 **ABL 里的 AVB 校验**:
- retail ABL + AVB 开启 → 未签名 boot 会被拒/红屏;
- 解决办法是刷 **AVB 关闭的 vbmeta**(已具备),retail ABL 也就不再校验 boot 签名。

因此用户设想的"工程版 bootloader 或许可以直接刷写分区"——
结论是:**工程版 ABL 不是刷分区的前提,也不是引导 pmOS 的必需品**;
它的价值只是 ① 放行 `fastboot flashing unlock`(已用过),
② 作为"连 AVB 都懒得管、直接引导未签名镜像"的宽松兜底。

## 推荐路线(按风险从低到高)

1. **主路线(推荐):不动 xbl/abl。**
   - 保持发行版 xbl/abl(已解锁)。
   - 用 EDL firehose 把 pmOS 生成的 `boot.img` 刷入 `boot_a`;
   - 同时刷 AVB-off 的 `vbmeta` / `vbmeta_system`(现成),让 ABL 不校验;
   - 风险最低:完全不碰 xbl/abl,救砖只需再用 firehose 刷回备份。

2. **可选增强:刷工程版 ABL(`eng_v1/abl.img` → `abl_a/abl_b`)。**
   - 好处:即使 AVB 复位/仍有残留校验,工程 ABL 也能直接引导未签名镜像,
     且允许 `fastboot flash` 任意分区(retail fastboot 会拦 boot/xbl 等)。
   - 代价:可能有工程告警画面/行为差异;属"解锁助手"定位。
   - **可逆**:stock abl 已可从备份/`stock/` 刷回。

3. **不建议:刷工程版 XBL。**
   - XBL 是最早阶段,引导别的 OS **用不到**改 XBL(把关 boot.img 的是 ABL)。
   - 刷坏 XBL 只能靠纯 9008 救(本机可救,但代价最高),收益为零。

## 落地到本项目的动作

- pmbootstrap 生成 `boot.img` 后,用 `tools/edl-tools/` 的 firehose 刷 `boot_a`
  (可仿照 `restore-bootchain.sh` 写一个 `flash-pmos-boot.sh`,镜像指向
  pmbootstrap 的 `boot.img`,并带上 AVB-off vbmeta)。
- 一切新脚本/镜像都放在 `/mnt/data/LOA_Nubia_Z60U/tools/`,不改 ArtistAOSP。
