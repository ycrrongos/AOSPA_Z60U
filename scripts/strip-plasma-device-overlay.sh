#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERRO="$ROOT/device-overlay/nubia/cerro"
COMMON="$ROOT/device-overlay/nubia/sm8650-common"
die() { echo "strip-plasma: $*" >&2; exit 1; }
[[ -d "$CERRO" ]] || die "missing $CERRO"
[[ -d "$COMMON" ]] || die "missing $COMMON"
echo "[strip-plasma] cerro=$CERRO"
rm -rf \
  "$CERRO/plasma_sukisu" \
  "$CERRO/overlay/PowerLayers" \
  "$CERRO/voltage_cerro.mk" \
  "$CERRO/lineage_cerro.mk" \
  "$CERRO/artist_cerro.mk" \
  "$CERRO/plasma_branding.mk" \
  "$CERRO/lineage.dependencies"
cat > "$CERRO/device.mk" <<'EOF'
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

$(call inherit-product, device/nubia/sm8650-common/common.mk)

DEVICE_PATH := device/nubia/cerro

PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/audio/mixer_paths_pineapple_mtp.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_pineapple/mixer_paths_pineapple_mtp.xml

PRODUCT_SOONG_NAMESPACES += \
    $(DEVICE_PATH)

PRODUCT_PACKAGES += \
    SettingsProviderResCerro

$(call inherit-product, vendor/nubia/cerro/cerro-vendor.mk)

PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/rootdir/bin/init.cerro.camera.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.cerro.camera.sh \
    $(DEVICE_PATH)/rootdir/etc/init.cerro.camera.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.cerro.camera.rc \
    $(DEVICE_PATH)/rootdir/bin/init.cerro.bootdiag.sh:$(TARGET_COPY_OUT_VENDOR)/bin/init.cerro.bootdiag.sh \
    $(DEVICE_PATH)/rootdir/etc/init.cerro.bootdiag.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.cerro.bootdiag.rc \
    $(DEVICE_PATH)/rootdir/etc/init/qseecomd.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/qseecomd.rc \
    $(DEVICE_PATH)/rootdir/etc/init.cerro.adb_root.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.cerro.adb_root.rc

# 0050 bringup debug: default ADB + adbd as root on userdebug (no Settings toggle).
ifeq ($(TARGET_BUILD_VARIANT),userdebug)
PRODUCT_PRODUCT_PROPERTIES += \
    persist.sys.usb.config=adb \
    ro.adb.secure=0
endif
EOF
cat > "$CERRO/AndroidProducts.mk" <<'EOF'
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#
# Lunch is registered in vendor/aospa/products/AndroidProducts.mk only.
# Do not dual-register aospa_cerro here (PRODUCT_NAME must be unique).
#

PRODUCT_MAKEFILES :=

COMMON_LUNCH_CHOICES :=
EOF
if grep -q 'plasmaos_sukisu.config' "$COMMON/BoardConfigCommon.mk"; then
  sed -i '/vendor\/plasmaos_sukisu.config/d' "$COMMON/BoardConfigCommon.mk"
fi
# AOSPA: do not inherit Lineage qcom-caf common.mk (duplicates device/qcom/common)
if grep -q 'hardware/qcom-caf/common/common.mk' "$COMMON/common.mk"; then
  sed -i 's#$(call inherit-product, hardware/qcom-caf/common/common.mk)#\# AOSPA: skip qcom-caf common.mk (duplicates device/qcom/common)#' "$COMMON/common.mk"
fi
echo "[strip-plasma] done"
