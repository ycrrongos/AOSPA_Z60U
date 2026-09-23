#
# SPDX-FileCopyrightText: Paranoid Android / cerro port
# SPDX-License-Identifier: Apache-2.0
#

ifeq (aospa_cerro,$(TARGET_PRODUCT))

# QCOM common (aospa-target.mk) reads this before BoardConfig.
TARGET_BOARD_PLATFORM := pineapple
# Must precede inherit aospa-target.mk — in-tree Lineage kernel, not qti-dlkm Image.
TARGET_USES_KERNEL_PLATFORM := false

# phone-only.xml removed packages/services/Car + cuttlefish; prune leftover
# Android.bp that still reference those modules (soong bootstrap otherwise fails).
PRODUCT_SOURCE_ROOT_DIRS += \
    -platform_testing/tools/automotive \
    -tools/security/fuzzing/system_fuzzers/libwatchdog_perf_service

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/aosp_base_telephony.mk)

$(call inherit-product, device/nubia/cerro/device.mk)

$(call inherit-product, vendor/aospa/target/product/aospa-target.mk)

TARGET_BOOT_ANIMATION_RES := 1080
TARGET_SCREEN_HEIGHT := 2480
TARGET_SCREEN_WIDTH := 1116

PRODUCT_BRAND := nubia
PRODUCT_DEVICE := cerro
PRODUCT_MANUFACTURER := nubia
PRODUCT_MODEL := NX721J
PRODUCT_NAME := aospa_cerro
PRODUCT_SYSTEM_DEVICE := PQ83A01
PRODUCT_SYSTEM_NAME := PQ83A01-UN

PRODUCT_GMS_CLIENTID_BASE := android-zte

PRODUCT_BUILD_PROP_OVERRIDES += \
    BuildDesc="PQ83A01-UN PQ83A01 15 AQ3A.240812.002 20250916.013811 release-keys" \
    BuildFingerprint=nubia/PQ83A01-UN/PQ83A01:15/AQ3A.240812.002/20250916.013811:user/release-keys \
    DeviceName=$(PRODUCT_SYSTEM_DEVICE) \
    DeviceProduct=$(PRODUCT_SYSTEM_NAME)

endif
