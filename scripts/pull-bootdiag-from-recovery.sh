#!/usr/bin/env bash
# Pull cerro bootdiag + ramoops leftovers from recovery.
# Device must already be in recovery with adb.
set -euo pipefail
OUT="${1:-./cerro-bootdiag-pull}"
mkdir -p "$OUT"

adb wait-for-device
adb root >/dev/null 2>&1 || true
sleep 1

echo "[pull-bootdiag] ramoops params / pstore"
adb shell 'cat /sys/module/ramoops/parameters/console_size 2>/dev/null; ls -la /sys/fs/pstore 2>/dev/null' \
  | tee "$OUT/pstore-ls.txt" || true
adb shell 'cat /sys/fs/pstore/console-ramoops-0 2>/dev/null' >"$OUT/console-ramoops-0.txt" || true
adb shell 'cat /sys/fs/pstore/dmesg-ramoops-0 2>/dev/null' >"$OUT/dmesg-ramoops-0.txt" || true

MNT=/tmp/cerro_metadata_mnt
adb shell "mkdir -p $MNT; umount $MNT 2>/dev/null; mount -t f2fs -o ro /dev/block/by-name/metadata $MNT" \
  || adb shell "mount -t ext4 -o ro /dev/block/by-name/metadata $MNT" \
  || true

echo "[pull-bootdiag] metadata listing"
adb shell "ls -la $MNT" | tee "$OUT/metadata-ls.txt" || true
for f in cerro-boot-status.txt cerro-boot-dmesg.txt cerro-boot-logcat.txt; do
  adb pull "$MNT/$f" "$OUT/$f" 2>/dev/null || echo "(missing) $f"
done

adb shell "umount $MNT" 2>/dev/null || true
echo "[pull-bootdiag] done → $OUT"
ls -la "$OUT"
