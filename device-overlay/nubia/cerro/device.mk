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
