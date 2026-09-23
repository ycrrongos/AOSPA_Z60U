#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${SOURCE_DIR:-$ROOT/source}"
OVERLAY="$ROOT/device-overlay/nubia"
die() { echo "apply-device-overlay: $*" >&2; exit 1; }
[[ -d "$SOURCE/.repo" ]] || die "no repo tree at $SOURCE — run repo sync first"
[[ -d "$OVERLAY/cerro" ]] || die "missing $OVERLAY/cerro"
echo "[apply-device-overlay] SOURCE=$SOURCE"
MANIFESTS="$ROOT/local_manifests"
if [[ -d "$MANIFESTS" ]]; then
  mkdir -p "$SOURCE/.repo/local_manifests"
  for xml in "$MANIFESTS"/*.xml; do
    [[ -f "$xml" ]] || continue
    cp -a "$xml" "$SOURCE/.repo/local_manifests/"
    echo "[apply-device-overlay] restored $(basename "$xml")"
  done
fi
bash "$ROOT/scripts/strip-plasma-device-overlay.sh"
for tree in cerro sm8650-common; do
  dst="$SOURCE/device/nubia/$tree"
  [[ -d "$dst" ]] || die "missing synced $dst"
  echo "[apply-device-overlay] rsync $tree"
  rsync -a --delete --exclude='.git' "$OVERLAY/$tree/" "$dst/"
done
PRODUCTS_MK="$SOURCE/vendor/aospa/products/AndroidProducts.mk"
if [[ -f "$PRODUCTS_MK" ]]; then
  python3 - "$PRODUCTS_MK" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text()
old = "# cerro (unofficial, local overlay)\n$(call inherit-product-if-exists, device/nubia/cerro/aospa_cerro.mk)"
new = (
    "# cerro (unofficial, local overlay)\n"
    "PRODUCT_MAKEFILES += device/nubia/cerro/aospa_cerro.mk\n"
    "COMMON_LUNCH_CHOICES += aospa_cerro-userdebug"
)
if old in text:
    p.write_text(text.replace(old, new))
    print("[apply-device-overlay] replaced inherit-product-if-exists with PRODUCT_MAKEFILES")
elif "device/nubia/cerro/aospa_cerro.mk" not in text:
    p.write_text(text.rstrip() + "\n\n" + new + "\n")
    print("[apply-device-overlay] appended PRODUCT_MAKEFILES for aospa_cerro")
else:
    print("[apply-device-overlay] AndroidProducts already lists aospa_cerro")
PY
fi
python3 "$ROOT/scripts/patch-soong-isolate-caf-common.py"
python3 "$ROOT/scripts/patch-soong-display-namespaces.py"
python3 "$ROOT/scripts/patch-lineage-compat-protobuf.py"
python3 "$ROOT/scripts/patch-lineage-compat-tinyxml2-v34.py"
python3 "$ROOT/scripts/patch-lineage-compat-libinput-shim.py"
python3 "$ROOT/scripts/patch-soong-vibrator-headers.py"
python3 "$ROOT/scripts/patch-soong-vibrator-effect-stream.py"
python3 "$ROOT/scripts/patch-soong-nxp-authsecret.py"
python3 "$ROOT/scripts/patch-soong-qcom-mkdir-mountpoints.py"
python3 "$ROOT/scripts/patch-soong-dtc-fdt-tools.py"
python3 "$ROOT/scripts/patch-sepolicy-qspmhal-attributes.py"
python3 "$ROOT/scripts/patch-soong-nubia-elf-check.py"
python3 "$ROOT/scripts/patch-soong-display-namespaces.py" --fm-only
python3 "$ROOT/scripts/patch-aospa-version-calcite.py"
python3 "$ROOT/scripts/patch-soong-deprecated-ota-imgdiff.py"
python3 "$ROOT/scripts/patch-kernel-ramoops-console.py"
python3 "$ROOT/scripts/patch-kernel-haptic-custom-alloc.py"
python3 "$ROOT/scripts/patch-kernel-haptic-reset-gpio.py" "$SOURCE"
python3 "$ROOT/scripts/patch-kernel-awinic-haptic.py" "$SOURCE"
echo "[apply-device-overlay] done — lunch aospa_cerro-userdebug"
