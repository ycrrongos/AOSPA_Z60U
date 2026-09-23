#!/usr/bin/env bash
# Mirror Cursor agent transcripts into docs/agent-transcripts/ (tracked by git).
# Idempotent. Does not commit or push by itself.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${ROOT}/docs/agent-transcripts"
SRC_DEFAULT="${HOME}/.cursor/projects/mnt-data-AOSPA-Z60U/agent-transcripts"
SRC="${AOSPA_CERRO_TRANSCRIPTS_SRC:-$SRC_DEFAULT}"

mkdir -p "${DEST}"

if [[ ! -d "${SRC}" ]]; then
  echo "sync-agent-transcripts: source missing: ${SRC}" >&2
  echo "Set AOSPA_CERRO_TRANSCRIPTS_SRC if Cursor stores chats elsewhere." >&2
  exit 1
fi

# Copy jsonl trees; keep uuid folder layout for stable paths across sessions.
rsync -a --delete \
  --exclude='*.tmp' \
  --exclude='.DS_Store' \
  "${SRC}/" "${DEST}/"

# Index for humans / agents without opening every jsonl
INDEX="${DEST}/README.md"
{
  echo "# Agent transcripts (Cursor)"
  echo
  echo "Mirrored from \`${SRC}\` by \`scripts/sync-agent-transcripts.sh\`."
  echo "Do not edit by hand; re-run the sync script."
  echo
  echo "| UUID | Size | Lines | mtime |"
  echo "|------|------|-------|-------|"
  find "${DEST}" -type f -name '*.jsonl' ! -path '*/subagents/*' | sort | while read -r f; do
    rel="${f#"${DEST}/"}"
    uuid="$(basename "$(dirname "${f}")")"
    lines="$(wc -l < "${f}" | tr -d ' ')"
    size="$(du -h "${f}" | awk '{print $1}')"
    mtime="$(date -u -d "@$(stat -c %Y "${f}")" '+%Y-%m-%dT%H:%MZ')"
    echo "| [\`${uuid}\`](${rel}) | ${size} | ${lines} | ${mtime} |"
  done
  echo
  echo "Subagent transcripts live under \`<uuid>/subagents/\`."
} > "${INDEX}"

count="$(find "${DEST}" -type f -name '*.jsonl' | wc -l | tr -d ' ')"
echo "sync-agent-transcripts: mirrored ${count} jsonl file(s) -> ${DEST}"
