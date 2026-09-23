# 0048 — GitHub 版本快照 + Cursor 聊天备份

## 问题

上下文丢失后无法判断「哪一版改坏了开机」。只备份单个「能开机」点不够：系统移植要连续推进，需要**每个版本**可回滚，并保留对应聊天记录。

## 方案

元仓真相源推到 GitHub：**https://github.com/ycrrongos/AOSPA_Z60U**（私有）。

| 产物 | 作用 |
|------|------|
| `scripts/sync-agent-transcripts.sh` | 把 `~/.cursor/projects/.../agent-transcripts/` 镜像到 `docs/agent-transcripts/` |
| `scripts/github-snapshot.sh` | 同步聊天 → 详细 commit（含 name-status / diffstat）→ tag → push |
| `.cursor/hooks.json` | `sessionEnd` / `stop` 时自动镜像聊天（不自动 push，避免半成品） |
| `.gitignore` | 排除 `source/`、`prebuilts-cerro/`、`ref-229/`、`clo-agent-kit/tools/`、根目录 `github` 凭据 |

## Agent 强制流程

每完成一个可验证版本（功能落地 / 刷机试过 / 文档写完）：

```bash
source scripts/proxy-env.sh   # FlClash
bash scripts/github-snapshot.sh "0047 awinic haptic module" <<'EOF'
## What changed
- …

## Why
- …

## Boot / test status
- stuck on splash | boots | recovery-only | untested

## Rollback
- git checkout snapshot-YYYYMMDD-HHMMSS -- .
# 或 git revert <sha>
EOF
```

## 回滚

```bash
git fetch origin
git tag -l 'snapshot-*' | tail
git log --oneline origin/main | head
# 整树回到某快照（谨慎）：
git checkout snapshot-YYYYMMDD-HHMMSS -- device-overlay scripts docs patches local_manifests
# 然后 apply-device-overlay.sh
```

聊天：打开对应 `docs/agent-transcripts/<uuid>/…jsonl`。

## 不进仓

- 整棵 `source/`（可 `repo sync` 重下）
- `prebuilts-cerro/`、`ref-229/`、`clo-agent-kit/tools/`
- 根目录 `github` token 文件（必须 rotate 若曾泄露）

## 状态

已落地脚本与 AGENTS 规则；首次 snapshot 在建立本功能时推送。
