#!/vendor/bin/sh
# AOSPA cerro: dump boot logs to /metadata (survives hard power-off) and
# soft-reboot into recovery if boot_completed never arrives (preserves ramoops).
# Marker: AOSPA cerro bootdiag

META=/metadata
DMESG_OUT="$META/cerro-boot-dmesg.txt"
LOGCAT_OUT="$META/cerro-boot-logcat.txt"
STATUS_OUT="$META/cerro-boot-status.txt"
WAIT_S="${CERRO_BOOTDIAG_WAIT_S:-60}"
INTERVAL_S=2

kmsg() {
    echo "cerro_bootdiag: $*" > /dev/kmsg 2>/dev/null || true
}

kmsg "start wait=${WAIT_S}s"

# metadata is mounted at post-fs; mkdir is usually a no-op
mkdir -p "$META" 2>/dev/null || true

if ! echo "bootdiag start wait=${WAIT_S}s" >"$STATUS_OUT" 2>/dev/null; then
    kmsg "WARN cannot write $STATUS_OUT (metadata missing/ro?)"
fi
sync

elapsed=0
while [ "$elapsed" -lt "$WAIT_S" ]; do
    dmesg >"$DMESG_OUT" 2>/dev/null || true
    # logcat may be unavailable early; ignore failures
    logcat -d -b all -v threadtime >"$LOGCAT_OUT" 2>/dev/null || true

    boot_completed="$(getprop sys.boot_completed)"
    if [ "$boot_completed" = "1" ]; then
        echo "boot_completed=1 after ${elapsed}s — exit" >>"$STATUS_OUT" 2>/dev/null || true
        dmesg >"$DMESG_OUT" 2>/dev/null || true
        sync
        kmsg "boot_completed=1 after ${elapsed}s — exit"
        exit 0
    fi

    echo "t=${elapsed}s boot_completed=${boot_completed} init.svc.zygote=$(getprop init.svc.zygote) crypto=$(getprop ro.crypto.state) vold=$(getprop init.svc.vold)" \
        >>"$STATUS_OUT" 2>/dev/null || true

    # heartbeat every 10s so ramoops still shows progress if metadata write fails
    rem=$((elapsed % 10))
    if [ "$rem" -eq 0 ]; then
        kmsg "t=${elapsed}s boot_completed=${boot_completed} zygote=$(getprop init.svc.zygote)"
        sync
    fi

    sleep "$INTERVAL_S"
    elapsed=$((elapsed + INTERVAL_S))
done

echo "TIMEOUT ${WAIT_S}s without boot_completed — soft reboot recovery" >>"$STATUS_OUT" 2>/dev/null || true
dmesg >"$DMESG_OUT" 2>/dev/null || true
logcat -d -b all -v threadtime >"$LOGCAT_OUT" 2>/dev/null || true
sync
kmsg "TIMEOUT ${WAIT_S}s — soft reboot recovery"

# Soft reboot preserves ramoops console; clamp long-press does not.
setprop sys.powerctl "reboot,recovery"
sleep 5
# Fallback if powerctl ignored
reboot recovery 2>/dev/null || /system/bin/reboot recovery 2>/dev/null || true
