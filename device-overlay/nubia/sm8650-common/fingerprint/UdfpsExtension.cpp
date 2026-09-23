/*
 * SPDX-FileCopyrightText: 2025 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

#include <compositionengine/UdfpsExtension.h>

/* AOSPA cerro: generated_kernel_headers is a stub. Only FOD_PRESSED_LAYER_ZORDER
 * is used; keep in sync with
 * kernel/nubia/sm8650-modules/qcom/opensource/display-drivers/include/uapi/display/drm/sde_drm.h
 */
#ifndef FOD_PRESSED_LAYER_ZORDER
#define FOD_PRESSED_LAYER_ZORDER 0x20000000u
#endif

uint32_t getUdfpsDimZOrder(uint32_t z) {
    return z;
}

uint32_t getUdfpsZOrder(uint32_t z, bool touched) {
    if (touched) {
        z |= FOD_PRESSED_LAYER_ZORDER;
    }
    return z;
}

uint64_t getUdfpsUsageBits(uint64_t usageBits, bool) {
    return usageBits;
}
