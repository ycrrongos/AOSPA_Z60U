#!/usr/bin/env bash
# Stage out-of-tree audio-kernel UAPI into generated_kernel_includes layout.
# Intended to run from Android build top (soong generator cmd cds there).
set -euo pipefail

GEN_DIR="${1:?usage: stage-audio-kernel-uapi.sh <genDir> [audio-uapi-src]}"
SRC="${2:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "$SRC" ]]; then
  SRC="kernel/nubia/sm8650-modules/qcom/opensource/audio-kernel/include/uapi/audio"
fi

if [[ ! -d "$SRC" ]]; then
  echo "[audio-uapi] WARN: missing $SRC — skip" >&2
  exit 0
fi

for dest in \
  "$GEN_DIR/usr/include/audio" \
  "$GEN_DIR/usr/audio/include/uapi" \
  "$GEN_DIR/usr/include/audio/include/uapi"
do
  mkdir -p "$dest"
  cp -a "$SRC"/. "$dest/"
done

bash "$HERE/strip-staged-audio-uapi.sh" "$GEN_DIR"

if [[ -f "$GEN_DIR/usr/include/audio/linux/msm_audio.h" ]]; then
  echo "[audio-uapi] OK $GEN_DIR/usr/include/audio/linux/msm_audio.h"
else
  echo "[audio-uapi] ERROR: msm_audio.h not staged" >&2
  exit 1
fi
