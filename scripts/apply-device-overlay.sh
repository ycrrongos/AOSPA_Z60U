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

# AOSPA product shell lives under vendor/aospa/products/cerro (not dual-registered
# with device/nubia/cerro/aospa_cerro.mk — PRODUCT_NAME must be unique).
VENDOR_PROD_SRC="$ROOT/device-overlay/vendor-aospa/products/cerro"
VENDOR_PROD_DST="$SOURCE/vendor/aospa/products/cerro"
if [[ -d "$VENDOR_PROD_SRC" && -d "$SOURCE/vendor/aospa/products" ]]; then
  mkdir -p "$VENDOR_PROD_DST"
  rsync -a --delete "$VENDOR_PROD_SRC/" "$VENDOR_PROD_DST/"
  echo "[apply-device-overlay] installed vendor/aospa/products/cerro"
fi

PRODUCTS_MK="$SOURCE/vendor/aospa/products/AndroidProducts.mk"
if [[ -f "$PRODUCTS_MK" ]]; then
  python3 - "$PRODUCTS_MK" <<'PY'
from pathlib import Path
import re
import sys
p = Path(sys.argv[1])
text = p.read_text()
removed = False
text2, n = re.subn(
    r"(?m)^# cerro \(unofficial, local overlay\)\n"
    r"PRODUCT_MAKEFILES \+= device/nubia/cerro/aospa_cerro\.mk\n"
    r"COMMON_LUNCH_CHOICES \+= aospa_cerro-userdebug\n?",
    "",
    text,
)
if n:
    text = text2
    removed = True
    print("[apply-device-overlay] removed legacy device/nubia cerro PRODUCT_MAKEFILES append")
# Ensure vendor product is listed once
line_mk = "    $(LOCAL_DIR)/cerro/aospa_cerro.mk \\"
line_lunch = "    aospa_cerro-userdebug \\"
changed = False
if "$(LOCAL_DIR)/cerro/aospa_cerro.mk" not in text:
    anchor = "PRODUCT_MAKEFILES += \\\n"
    if anchor not in text:
        raise SystemExit("AndroidProducts.mk missing PRODUCT_MAKEFILES block")
    text = text.replace(anchor, anchor + line_mk + "\n", 1)
    changed = True
    print("[apply-device-overlay] registered $(LOCAL_DIR)/cerro/aospa_cerro.mk")
if "aospa_cerro-userdebug" not in text:
    anchor = "COMMON_LUNCH_CHOICES += \\\n"
    if anchor not in text:
        raise SystemExit("AndroidProducts.mk missing COMMON_LUNCH_CHOICES block")
    text = text.replace(anchor, anchor + line_lunch + "\n", 1)
    changed = True
    print("[apply-device-overlay] registered aospa_cerro-userdebug lunch")
if changed or removed:
    p.write_text(text)
else:
    print("[apply-device-overlay] AndroidProducts already lists vendor cerro only")
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
