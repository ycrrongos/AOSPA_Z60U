#!/usr/bin/env bash
# Pull Git LFS blobs in nubia vendor trees (NubiaCamera, radio images).
# GitHub access requires FlClash via proxy-env.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${SOURCE_DIR:-$ROOT/source}"
# shellcheck disable=SC1091
source "$ROOT/scripts/proxy-env.sh"
pulled=0
for tree in vendor/nubia/cerro vendor/nubia/sm8650-common; do
  dir="$SOURCE/$tree"
  if [[ ! -d "$dir/.git" ]]; then
    echo "[vendor-lfs] skip missing $tree"
    continue
  fi
  echo "[vendor-lfs] git lfs pull in $tree"
  git -C "$dir" lfs pull
  pulled=1
done
if [[ "$pulled" -eq 0 ]]; then
  echo "[vendor-lfs] no vendor git trees found" >&2
  exit 1
fi
echo "[vendor-lfs] done"
