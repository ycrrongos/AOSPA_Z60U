#!/usr/bin/env bash
# Snapshot the cerro meta-tree to GitHub: sync chats, commit with a detailed
# message, and push. Use after every meaningful version / feature change.
#
# Usage:
#   bash scripts/github-snapshot.sh "short title" <<'EOF'
#   ## What changed
#   - ...
#   ## Why
#   - ...
#   ## Boot / test status
#   - unknown | boots | stuck on splash | recovery-only
#   ## Rollback
#   - git revert <this> or checkout previous tag
#   EOF
#
# Env:
#   AOSPA_CERRO_GIT_REMOTE   default: origin
#   AOSPA_CERRO_GIT_BRANCH   default: current branch or main
#   AOSPA_CERRO_NO_PUSH=1    commit only
#   AOSPA_CERRO_SKIP_TRANSCRIPTS=1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ ! -d .git ]]; then
  echo "github-snapshot: ${ROOT} is not a git repo. Init + add remote first." >&2
  exit 1
fi

TITLE="${1:-}"
if [[ -z "${TITLE}" ]]; then
  echo "usage: bash scripts/github-snapshot.sh \"short title\" < body.md" >&2
  exit 1
fi

if [[ ! -t 0 ]]; then
  BODY="$(cat)"
else
  BODY="(no detailed body provided on stdin)"
fi

# Prefer proxy for GitHub (FlClash). Non-fatal if missing.
if [[ -f "${ROOT}/scripts/proxy-env.sh" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT}/scripts/proxy-env.sh" || true
fi

if [[ "${AOSPA_CERRO_SKIP_TRANSCRIPTS:-0}" != "1" ]]; then
  bash "${ROOT}/scripts/sync-agent-transcripts.sh" || {
    echo "github-snapshot: transcript sync failed (continuing with code snapshot)" >&2
  }
fi

# Local identity for this invocation only (do not write global git config).
GIT_NAME="${GIT_AUTHOR_NAME:-ycrrongos}"
GIT_EMAIL="${GIT_AUTHOR_EMAIL:-124893015+ycrrongos@users.noreply.github.com}"
git_cmd() {
  git -c "user.name=${GIT_NAME}" -c "user.email=${GIT_EMAIL}" "$@"
}

REMOTE="${AOSPA_CERRO_GIT_REMOTE:-origin}"
# Unborn branch: `rev-parse --abbrev-ref HEAD` fails; prefer symbolic-ref.
if [[ -n "${AOSPA_CERRO_GIT_BRANCH:-}" ]]; then
  BRANCH="${AOSPA_CERRO_GIT_BRANCH}"
elif BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null)"; then
  :
elif BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"; then
  :
else
  BRANCH="main"
fi
if [[ "${BRANCH}" == "HEAD" || -z "${BRANCH}" ]]; then
  BRANCH="main"
fi

# Stage everything tracked by .gitignore rules
git add -A

if git diff --cached --quiet; then
  echo "github-snapshot: nothing to commit (working tree clean after sync)."
  if [[ "${AOSPA_CERRO_NO_PUSH:-0}" != "1" ]]; then
    git push -u "${REMOTE}" "${BRANCH}" || true
  fi
  exit 0
fi

TS_UTC="$(date -u '+%Y-%m-%d %H:%M:%SZ')"
STAT="$(git diff --cached --stat)"
NAMESTAT="$(git diff --cached --name-status)"

MSG="$(cat <<EOF
cerro: ${TITLE}

Time (UTC): ${TS_UTC}
Branch: ${BRANCH}

${BODY}

## Files (name-status)
${NAMESTAT}

## Diffstat
${STAT}
EOF
)"

git_cmd commit -m "${MSG}"

# Lightweight moving tag for "latest snapshot" + dated tag for rollback lists
TAG_DATE="snapshot-$(date -u '+%Y%m%d-%H%M%S')"
git_cmd tag -f "cerro-latest" HEAD
git_cmd tag "${TAG_DATE}" HEAD

echo "github-snapshot: committed as $(git rev-parse --short HEAD) tag ${TAG_DATE}"

if [[ "${AOSPA_CERRO_NO_PUSH:-0}" == "1" ]]; then
  echo "github-snapshot: AOSPA_CERRO_NO_PUSH=1 — skip push"
  exit 0
fi

git push -u "${REMOTE}" "${BRANCH}"
git push -f "${REMOTE}" "cerro-latest" || true
git push "${REMOTE}" "${TAG_DATE}"

echo "github-snapshot: pushed ${BRANCH} + ${TAG_DATE} to ${REMOTE}"
