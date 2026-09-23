#!/usr/bin/env bash
# Strip kernel-only attrs from staged audio UAPI (userspace compile).
set -euo pipefail
GEN="${1:?gen dir}"
for d in \
  "$GEN/usr/include/audio" \
  "$GEN/usr/audio/include/uapi" \
  "$GEN/usr/include/audio/include/uapi"
do
  [[ -d "$d" ]] || continue
  find "$d" -type f -name '*.h' -exec sed -i \
    -e 's/__user//g' \
    -e 's/__force//g' \
    -e 's/__iomem//g' {} +
done
