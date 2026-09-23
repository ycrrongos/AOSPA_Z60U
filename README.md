# AOSPA_Z60U（cerro meta）

Nubia Z60 Ultra（`cerro`）非官方 **AOSPA calcite** 移植的**可回滚元仓**。  
别人要做 cerro 的 PA：克隆本仓 → sync 上游 → `apply-device-overlay` → lunch 出包。

| | |
|--|--|
| 设备 | Nubia Z60 Ultra / `cerro` / NX721J |
| 上游 | AOSPA **calcite**（底子 **Android 16 / API 36**） |
| 真相源 | `device-overlay/` · `scripts/` · `docs/` · `local_manifests/` |
| 不含 | 整棵 `source/`、`prebuilts-cerro/`、对照树 |
| 标签 | `snapshot-*` / `cerro-latest` |

GitHub：https://github.com/ycrrongos/AOSPA_Z60U

---

## 给其他维护者：用本仓补丁出 cerro PA

前置：已能编 AOSPA calcite；本机有 `repo`、Python3、rsync；拉 GitHub / AOSPA 建议走代理。

```bash
git clone https://github.com/ycrrongos/AOSPA_Z60U.git
cd AOSPA_Z60U

# 1) 按你的习惯初始化 AOSPA calcite 到 ./source
#    （manifest 与官方 calcite 一致后，把本仓 local_manifests 拷进去）
mkdir -p source/.repo/local_manifests
cp local_manifests/*.xml source/.repo/local_manifests/

# 2) 代理（可选，本仓默认假设 FlClash 127.0.0.1:7890）
source scripts/proxy-env.sh

# 3) sync + 重放全部 cerro overlay / 补丁钩子
bash scripts/sync-calcite.sh          # 或：repo sync 后 bash scripts/apply-device-overlay.sh
bash scripts/pull-vendor-lfs.sh       # NubiaCamera / radio 等 LFS

# 4) 出包
cd source
source build/envsetup.sh
lunch aospa_cerro-userdebug
./rom-build.sh cerro                  # 或 m otapackage / 你们惯用目标
```

要点：

- **不要把 `source/` 当真相源**；改功能请回写 `device-overlay/` / `scripts/`，保证 `bash scripts/apply-device-overlay.sh` 可从干净树重放。
- 功能说明按 ID 看 [`docs/features/README.md`](docs/features/README.md)；开关见 [`docs/aospa-cerro-patch-toggles.md`](docs/aospa-cerro-patch-toggles.md)。
- 踩坑汇总：[`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)。
- `scripts/strip-plasma-device-overlay.sh` 会重写 `device.mk` / `AndroidProducts.mk`；设备树拷贝与属性必须写进该脚本 heredoc。
- 刷机 / 硬件笔记：`clo-agent-kit/`（工程 ABL、AVB off、Firehose v1、双槽）。

当前 bringup 默认（可关）：库存指纹伪装关、userdebug 默认 adb root —— 见功能 **0050**。

---

## 本仓维护者：每版必推

```bash
source scripts/proxy-env.sh
bash scripts/github-snapshot.sh "短标题" <<'EOF'
## What changed
- …

## Why
- …

## Boot / test status
- …

## Rollback
- …
EOF
```

聊天镜像：`docs/agent-transcripts/`。约定见 [`AGENTS.md`](AGENTS.md)、[`docs/features/0048-github-version-snapshots.md`](docs/features/0048-github-version-snapshots.md)。

Owner: [ycrrongos](https://github.com/ycrrongos)
