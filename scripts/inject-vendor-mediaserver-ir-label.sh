#!/usr/bin/env bash
# Inject SetupWizard/mediaserver prop + IR HAL SELinux xattr into a *known-bootable*
# vendor.img, preserving AVB footer/hashtree layout.
#
# Why this exists: a freshly built `m vendorimage` (2026-08-27) currently drops
# straight back to bootloader on cerro. The last known-good flashable vendor is
# out/target/product/cerro/vendor.img.sparse (2026-08-25 22:51, HWC-era).
# Overlay still carries the durable sources (vendor.prop / sepolicy); this script
# is the verified path to land 0038+0040 *labels* onto that base until the fresh
# vendorimage boot regression is fixed.
#
# Usage:
#   bash scripts/inject-vendor-mediaserver-ir-label.sh \
#     [src-vendor.img|sparse] [out.img]
#
# Default src: source/out/target/product/cerro/vendor.img.sparse
# Default out: source/out/target/product/cerro/vendor-WORKING-0038-0040.img
#
# Flash (fastbootd):
#   fastboot flash vendor_a <out.img> && fastboot --set-active=a && fastboot reboot
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROD="${PROD:-$ROOT/source/out/target/product/cerro}"
SRC="${1:-$PROD/vendor.img.sparse}"
OUT="${2:-$PROD/vendor-WORKING-0038-0040.img}"
WORKDIR="${WORKDIR:-$ROOT/tmp/vendor-inject-0038-0040}"
IR_BIN_REL="bin/hw/android.hardware.ir-service.lineage"
IR_CTX="u:object_r:hal_ir_default_exec:s0"

need() { command -v "$1" >/dev/null || { echo "missing $1" >&2; exit 1; }; }
need python3
need simg2img
need sudo

[[ -f "$SRC" ]] || { echo "src not found: $SRC" >&2; exit 1; }

rm -rf "$WORKDIR"
mkdir -p "$WORKDIR/mnt"

echo "[inject] src=$SRC"
if python3 -c "import sys; sys.exit(0 if open('$SRC','rb').read(4)==bytes.fromhex('3aff26ed') else 1)"; then
  simg2img "$SRC" "$WORKDIR/full.img"
else
  cp -a "$SRC" "$WORKDIR/full.img"
fi

python3 - <<PY
from pathlib import Path
import struct
full = Path("$WORKDIR/full.img").read_bytes()
idx = full.rfind(b"AVBf")
if idx < 0:
    raise SystemExit("no AVB footer — refuse to inject (keep a known-good image with footer)")
osize = struct.unpack_from(">Q", full, idx + 12)[0]
Path("$WORKDIR/vendor.fs").write_bytes(full[:osize])
Path("$WORKDIR/suffix.bin").write_bytes(full[osize:])
Path("$WORKDIR/osize").write_text(str(osize))
print(f"[inject] osize={osize} suffix={len(full)-osize}")
PY
OSIZE="$(cat "$WORKDIR/osize")"

# Free a little space without large grow when possible
sudo tune2fs -m 0 "$WORKDIR/vendor.fs" >/dev/null
sudo e2fsck -fy "$WORKDIR/vendor.fs" >/dev/null
sudo mount -o loop,rw "$WORKDIR/vendor.fs" "$WORKDIR/mnt"
AVAIL="$(df -B1 --output=avail "$WORKDIR/mnt" | tail -1 | tr -d ' ')"
if [[ "$AVAIL" -lt 4096 ]]; then
  sudo umount "$WORKDIR/mnt"
  dd if=/dev/zero bs=1M count=1 status=none >>"$WORKDIR/vendor.fs"
  sudo e2fsck -fy "$WORKDIR/vendor.fs" >/dev/null
  sudo resize2fs "$WORKDIR/vendor.fs" >/dev/null
  sudo mount -o loop,rw "$WORKDIR/vendor.fs" "$WORKDIR/mnt"
fi

if ! sudo grep -q 'ro.mediaserver.64b.enable=true' "$WORKDIR/mnt/build.prop"; then
  printf '\n# AOSPA cerro 0038\nro.mediaserver.64b.enable=true\n' \
    | sudo tee -a "$WORKDIR/mnt/build.prop" >/dev/null
  echo "[inject] appended ro.mediaserver.64b.enable=true"
else
  echo "[inject] mediaserver prop already present"
fi

[[ -f "$WORKDIR/mnt/$IR_BIN_REL" ]] || {
  echo "missing $IR_BIN_REL in vendor" >&2
  sudo umount "$WORKDIR/mnt"
  exit 1
}
sudo setfattr -n security.selinux -v "$IR_CTX" "$WORKDIR/mnt/$IR_BIN_REL"
sudo getfattr -n security.selinux "$WORKDIR/mnt/$IR_BIN_REL" | grep -q 'hal_ir_default_exec'
echo "[inject] labeled $IR_BIN_REL -> $IR_CTX"

# Do NOT replace vendor_sepolicy.cil here. Full cil swaps from a newer tree have
# soft-bricked boots on this device; platform policy already transitions
# hal_ir_default_exec. lirc allow rules remain in overlay for a future clean build.

sudo umount "$WORKDIR/mnt"

FS="$(stat -c%s "$WORKDIR/vendor.fs")"
if [[ "$FS" -gt "$OSIZE" ]]; then
  BLOCKS=$((OSIZE / 4096))
  sudo e2fsck -fy "$WORKDIR/vendor.fs" >/dev/null
  sudo resize2fs "$WORKDIR/vendor.fs" "$BLOCKS" >/dev/null
  truncate -s "$OSIZE" "$WORKDIR/vendor.fs"
elif [[ "$FS" -lt "$OSIZE" ]]; then
  python3 - <<PY
from pathlib import Path
osize = int(Path("$WORKDIR/osize").read_text())
fs = Path("$WORKDIR/vendor.fs")
fs.write_bytes(fs.read_bytes() + b"\0" * (osize - fs.stat().st_size))
PY
fi

cat "$WORKDIR/vendor.fs" "$WORKDIR/suffix.bin" >"$OUT"
cmp -n 64 <(tail -c 64 "$OUT") <(tail -c 64 "$WORKDIR/full.img") \
  || { echo "AVB footer mismatch" >&2; exit 1; }

# Verify
LOOP="$(sudo losetup -f --show --sizelimit "$OSIZE" "$OUT")"
sudo mount -o ro "$LOOP" "$WORKDIR/mnt"
sudo grep -q 'ro.mediaserver.64b.enable=true' "$WORKDIR/mnt/build.prop"
sudo getfattr -n security.selinux "$WORKDIR/mnt/$IR_BIN_REL" | grep -q 'hal_ir_default_exec'
sudo umount "$WORKDIR/mnt"
sudo losetup -d "$LOOP"

cp -a "$OUT" "$PROD/vendor.img"
echo "[inject] OK -> $OUT (also copied to $PROD/vendor.img)"
echo "[inject] flash: fastboot flash vendor_a $OUT && fastboot --set-active=a && fastboot reboot"
