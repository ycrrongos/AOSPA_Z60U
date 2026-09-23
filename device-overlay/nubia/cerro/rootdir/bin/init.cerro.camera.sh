#!/vendor/bin/sh
# Cerro: seed /data/vendor/camera for Nubia HAL (watermarks + dualcam cali).
set -eu

CAMERA_DATA=/data/vendor/camera
PERSIST_CAMERA=/mnt/vendor/persist/camera
VENDOR_ICON=/vendor/etc/camera/icon

mkdir -p "$CAMERA_DATA"
chown cameraserver:camera "$CAMERA_DATA"
chmod 0770 "$CAMERA_DATA"

for asset in \
    water_mark_drawable_white.argb \
    water_mark_drawable_black.argb \
    water_mark_drawable_white_eng.argb \
    water_mark_drawable_black_eng.argb
do
    src="$VENDOR_ICON/$asset"
    dst="$CAMERA_DATA/$asset"
    if [ -f "$src" ] && [ ! -f "$dst" ]; then
        cp "$src" "$dst"
        chown cameraserver:camera "$dst"
        chmod 0644 "$dst"
    fi
done

if [ -f "$PERSIST_CAMERA/dualcam_cali.bin" ] && [ ! -f "$CAMERA_DATA/dualcam_cali.bin" ]; then
    cp "$PERSIST_CAMERA/dualcam_cali.bin" "$CAMERA_DATA/dualcam_cali.bin"
    chown cameraserver:camera "$CAMERA_DATA/dualcam_cali.bin"
    chmod 0644 "$CAMERA_DATA/dualcam_cali.bin"
fi
