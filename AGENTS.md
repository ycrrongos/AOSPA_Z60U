# AOSPA cerro Agent Guide

给后续 agent 的工作约定。改代码前先读本文件、对应功能文档、以及 [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)。

本仓库是 **Nubia Z60 Ultra (`cerro`)** 的 **非官方 AOSPA calcite** 移植工程。  
**平台版本是 Android 16（API 36）**，不是 Android 17。`calcite` / 对照机上的 VoltageOS **17** 都是 **ROM 代号/大版本号**，不要当成 `ro.build.version.release=17`。  
当前主线编译树是 **AOSPA calcite (`source/`)**。设备树真相源在 **`device-overlay/`**（改良自 229 PlasmaAOSP / VoltageOS 17，已剥品牌与 SukiSU）。刷机/硬件见 **`clo-agent-kit/`**。

cerro 定制必须能在上游 `repo sync` 之后用 apply 脚本重新打进去。

内部补丁/开关前缀建议用 **`AOSPA_CERRO_*`**（若引入功能开关文档，放 `docs/aospa-cerro-patch-toggles.md`）。

与 229 PlasmaAOSP 规则对齐：本文件的 **硬性规则、补丁形式、新功能流程、上游重放、完成前自检** 结构同 229 `ArtistAOSP/AGENTS.md`（只读对照），下面映射到本仓库路径。

---

## 硬性规则

1. **不要把 `source/` 当成真相源。** 那里只是 AOSPA calcite 编译检出树，随时会被 `repo sync` 覆盖或删掉重下。
2. **修改和新增功能必须以可重放形式落地。** 可编译验证时可以改 `source/`，但结束前必须回写到 `device-overlay/`、`patches/`、`scripts/` 或 apply 脚本，并保证 `bash scripts/apply-device-overlay.sh`（及后续 `apply-all.sh` 若存在）能从干净树重放。
3. **每做一个功能，必须写一篇功能开发文档**（`docs/features/<id>-<slug>.md`）。文档要让没读过本次对话的 agent 能独立接入。
4. **每次卡住、踩坑、误判，必须记入 `docs/TROUBLESHOOTING.md`。** 记症状、试过的方法、最终原因、解决办法。不要只记在聊天里。
5. **不要直接大段覆盖上游 SystemUI / Settings 来“顺便”带功能。**
6. **每个可回滚的版本必须推到 GitHub（强制）。** 改完 `device-overlay/` / `patches/` / `scripts/` / 功能文档后，立刻：
   `bash scripts/github-snapshot.sh "短标题" <<'EOF' …详细说明… EOF`
   该脚本会同步 Cursor 聊天记录到 `docs/agent-transcripts/`、写带文件列表的 commit、打 `snapshot-YYYYMMDD-HHMMSS` 标签并 push。丢上下文后靠 GitHub 历史回滚，不要只靠本机或“能开机快照”。无关的琐碎本地试验可以暂不推；**凡是刷机/验证过的版本必须推。**
7. **不要把 cerro 补丁打进无关对照树。** 本机只看 `AOSPA_Z60U`；229 上 ArtistAOSP / OnlyAOSP **只读对照**，不在 229 上 sync。
8. **`repo sync` 及一切 GitHub 访问必须先开 FlClash 代理**（`scripts/proxy-env.sh`）。未开代理不要 sync / fetch。
9. **第一版不带 SukiSU / Plasma / Voltage 产品层。** 硬件改良（SF/perf、相机 bootstrap、触控旋转）保留在 `device-overlay/`；产品层用 `aospa_cerro.mk` + `aospa-target.mk`。
10. **禁止把根目录 `github` 凭据文件、token、`.git-credentials` 提交进仓。** 已在 `.gitignore`。

---

## 目录与真相源

| 路径 | 角色 |
|------|------|
| `device-overlay/nubia/cerro/` | cerro 设备树 + **`aospa_cerro.mk`** 真相源（≈ Plasma 的 `devices/nubia/cerro/` + 部分 `source/device`） |
| `device-overlay/nubia/sm8650-common/` | SM8650 平台公共树真相源（Plasma 改良：perf/SF/触控/sepolicy） |
| `patches/` | 根级 unified diff（框架/vendor 改动放这里） |
| `scripts/` | sync / strip / apply / build；**新功能必须挂进 apply 链** |
| `docs/agent-transcripts/` | Cursor 聊天记录镜像（`scripts/sync-agent-transcripts.sh`） |
| `scripts/github-snapshot.sh` | **每版必跑**：同步聊天 + 详细 commit + tag + push |
| `source/` | **AOSPA calcite** 主线编译树，**可删可重下**（不进本 git） |
| `source/.repo/local_manifests/cerro.xml` | nubia-sm8650-devs device/kernel/vendor（lineage-23.2） |
| `clo-agent-kit/` | EDL / fastboot / 硬件笔记（不进 `.repo`；`tools/` 不进 git） |
| `neoteric_caza-*.zip` | 能开机的 neo A16 fastboot 对照包 |
| GitHub | **https://github.com/ycrrongos/AOSPA_Z60U**（元仓真相备份；私有） |

229 只读参考（**不在本仓库内**）：

| 229 路径 | 用途 |
|----------|------|
| `ArtistAOSP/source/` | VoltageOS 17 cerro，A17 已出包 |
| `ArtistAOSP/vendor/plasmaos/device/cerro-opt/` | 硬件改良配方 |
| `OnlyAOSP/manifest/cerro-hals.xml` | Lineage CAF 对照清单（勿整份搬进 CLO） |

`source/` 里出现的 cerro 改动若还没回写 overlay：

```bash
# 手动 diff 后同步；后续可加 extract 脚本
diff -ru device-overlay/nubia/cerro source/device/nubia/cerro
```

---

## 访问边界

| 范围 | 规则 |
|------|------|
| **本机** | 只看 **`/mnt/data/AOSPA_Z60U`**。不要浏览本机 `/mnt/data/` 下其它目录 |
| **229** | `/mnt/data/` 整棵可读；**不要在 229 上 sync**（盘已满） |
| **凭据** | 不要写入仓库、计划或脚本 |

---

## 补丁形式（必须）

按可维护性从高到低选一种。**禁止**只改 `source/` 而不留下可重放产物。

### A. Unified diff（小改动首选）

放 `patches/`，apply 脚本里 `patch -p1` 或 `git apply`。

### B. Python 上下文补丁（易漂移的 Java/Kotlin 首选）

MARKER 用 `// AOSPA cerro: ...`，幂等、可检测、锚点稳定，参数收 `SOURCE_DIR`。

### C. 文件副本 + apply 脚本

设备树整树放 `device-overlay/`，由 `apply-device-overlay.sh` rsync 进 `source/`（当前 cerro 主线做法）。

### D. 明确禁止

- 只改 `source/` 就结束  
- 把补丁打进 229 上的树  
- 整份 OnlyAOSP `cerro-hals.xml` 盖掉 AOSPA CLO 路径  

细节约定：幂等、可检测、锚点稳定、参数收 `SOURCE_DIR`（与 Plasma 相同）。

---

## 新功能标准流程

1. 查重：`docs/features/README.md`、已有 `device-overlay/` / `patches/`
2. 写 `docs/features/<id>-<slug>.md` 草稿
3. 实现到 `device-overlay/` / `patches/` / `scripts/`
4. 挂 apply 链（至少 `apply-device-overlay.sh`；全局改动加进未来的 `apply-all.sh`）
5. 补全文档与 `docs/features/README.md` 索引
6. 验证：`bash scripts/apply-device-overlay.sh`（sync 后）
7. 踩坑写入 `docs/TROUBLESHOOTING.md`

产品层：lunch **`aospa_cerro-userdebug`**，inherit **`vendor/aospa/target/product/aospa-target.mk`**，不要 inherit `vendor/voltage` / `vendor/lineage`。

---

## 上游更新后如何重放

```bash
# 1. 开 FlClash
source scripts/proxy-env.sh

# 2. sync AOSPA calcite
bash scripts/sync-calcite.sh [jobs]
# 内部：repo sync --current-branch --no-tags → apply-device-overlay.sh

# 3. 若还有框架补丁（未来）
# bash scripts/apply-all.sh
```

只改过 `device-overlay/`、未 sync 时：

```bash
bash scripts/apply-device-overlay.sh
```

从 229 刷新 Plasma 改良设备树（只读 rsync 后必跑 strip）：

```bash
rsync -a --exclude='.git' rong@192.168.0.229:/mnt/data/ArtistAOSP/source/device/nubia/cerro/ \
  device-overlay/nubia/cerro/
rsync -a --exclude='.git' rong@192.168.0.229:/mnt/data/ArtistAOSP/source/device/nubia/sm8650-common/ \
  device-overlay/nubia/sm8650-common/
bash scripts/strip-plasma-device-overlay.sh
bash scripts/apply-device-overlay.sh   # 需已 sync
```

---

## 日常命令

```bash
source scripts/proxy-env.sh
bash scripts/sync-calcite.sh              # sync + overlay
bash scripts/apply-device-overlay.sh      # 仅重放 overlay
bash scripts/strip-plasma-device-overlay.sh

cd source
source build/envsetup.sh
lunch aospa_cerro-userdebug
./rom-build.sh cerro
```

下载 / GitHub **默认走** `scripts/proxy-env.sh`（FlClash `127.0.0.1:7890`）。

Kernel：**`TARGET_KERNEL_SOURCE := kernel/nubia/sm8650`**。不要 `plasmaos_sukisu.config`。

---

## AOSPA / cerro 专有条目（Plasma 规则之外的补充）

| 项 | 约定 |
|----|------|
| 分支 | **`calcite`**（AOSPA 代号；底子 **Android 16 / API 36**），不是 `beryl` 代号树 |
| 官方产品 | AOSPA 无 cerro；`local_manifests/cerro.xml` + overlay |
| 音频/触控 | AW88261 + Goodix brl-d；不抄 oplus 驱动 |
| 刷机 | `clo-agent-kit/`：工程 ABL、AVB off、Firehose **v1**、双槽 |
| HAL | sync 后 diff 缺项再补 manifest，禁止整份 Lineage HAL 顶 CLO |

硬件清单：[`clo-agent-kit/docs/cerro-hardware.md`](clo-agent-kit/docs/cerro-hardware.md)。

---

## 完成前自检

- [ ] `source/` 改动已回写 `device-overlay/` / `patches/` / apply 脚本
- [ ] 干净树上 `apply-device-overlay.sh` 可重放（sync 后）
- [ ] `docs/features/` 与索引已更新（若有新功能）
- [ ] 坑已写入 `docs/TROUBLESHOOTING.md`
- [ ] **已 `bash scripts/github-snapshot.sh "..."` 推到 GitHub**（含聊天记录镜像）
- [ ] GitHub / sync 前已 `source scripts/proxy-env.sh`
- [ ] overlay 无 Voltage / Plasma / SukiSU 产品层
- [ ] 未浏览本机 `/mnt/data` 其它目录；未在 229 上 sync
- [ ] lunch 为 **`aospa_cerro-*`**，不是 `voltage_cerro` / `lineage_cerro`
- [ ] 未把 `github` / token / 凭据文件加入提交
