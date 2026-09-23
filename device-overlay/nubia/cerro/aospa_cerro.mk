#
# AOSPA calcite — Nubia Z60 Ultra (cerro)
# Lunch: aospa_cerro-userdebug
#
# NOTE: lunch uses vendor/aospa/products/cerro/aospa_cerro.mk (same toggles).
# Keep this file in sync for anyone who still points PRODUCT_MAKEFILES here.
#

ifeq (aospa_cerro,$(TARGET_PRODUCT))

# QCOM common (aospa-target.mk) reads this before BoardConfig.
TARGET_BOARD_PLATFORM := pineapple
# Must precede inherit aospa-target.mk (see sm8650-common/common.mk).
TARGET_USES_KERNEL_PLATFORM := false

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/aosp_base_telephony.mk)

$(call inherit-product, device/nubia/cerro/device.mk)

$(call inherit-product, vendor/aospa/target/product/aospa-target.mk)

TARGET_SCREEN_HEIGHT := 2480
TARGET_SCREEN_WIDTH := 1116

PRODUCT_BRAND := nubia
PRODUCT_DEVICE := cerro
PRODUCT_MANUFACTURER := nubia
PRODUCT_MODEL := NX721J
PRODUCT_NAME := aospa_cerro

PRODUCT_GMS_CLIENTID_BASE := android-zte

# See vendor/aospa/products/cerro/aospa_cerro.mk — same toggle.
AOSPA_CERRO_SPOOF_STOCK_FINGERPRINT ?= false
ifeq ($(AOSPA_CERRO_SPOOF_STOCK_FINGERPRINT),true)
PRODUCT_SYSTEM_DEVICE := PQ83A01
PRODUCT_SYSTEM_NAME := PQ83A01-UN
PRODUCT_BUILD_PROP_OVERRIDES += \
    BuildDesc="PQ83A01-UN PQ83A01 15 AQ3A.240812.002 20250916.013811 release-keys" \
    BuildFingerprint=nubia/PQ83A01-UN/PQ83A01:15/AQ3A.240812.002/20250916.013811:user/release-keys \
    DeviceName=$(PRODUCT_SYSTEM_DEVICE) \
    DeviceProduct=$(PRODUCT_SYSTEM_NAME)
endif

endif
