# AOSPA_Z60U（cerro meta）

Nubia Z60 Ultra（`cerro`）非官方 **AOSPA calcite** 移植的**可回滚元仓**。

- 真相源：`device-overlay/`、`scripts/`、`docs/`、`local_manifests/`
- 不包含：整棵 `source/` ROM 树、`prebuilts-cerro/`、对照树 `ref-229/`
- 平台：Android 16 / API 36（`calcite` 是 ROM 代号，不是 `ro.build.version.release=17`）

## 每版必推

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

聊天记录镜像：`docs/agent-transcripts/`（由 `scripts/sync-agent-transcripts.sh` 从 Cursor 同步）。

约定见 [`AGENTS.md`](AGENTS.md)、[`docs/features/0048-github-version-snapshots.md`](docs/features/0048-github-version-snapshots.md)。

Owner: [ycrrongos](https://github.com/ycrrongos)
