#!/usr/bin/env bash
# Cursor sessionEnd / stop hook: mirror agent transcripts into the repo.
# Fail-open: never block the agent if sync fails.
set -euo pipefail

# Read and discard hook JSON (we do not gate on it).
cat >/dev/null || true

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${ROOT}/.cursor/cache"
mkdir -p "${LOG_DIR}"
LOG="${LOG_DIR}/sync-transcripts-hook.log"

{
  echo "---- $(date -u '+%Y-%m-%dT%H:%MZ') ----"
  bash "${ROOT}/scripts/sync-agent-transcripts.sh" || echo "sync failed: $?"
} >>"${LOG}" 2>&1 || true

# sessionEnd/stop hooks: empty JSON is fine
echo '{}'
exit 0
