# Copyright (C) 2018-2024 The LineageOS Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# AOSPA cerro: Lineage BoardConfigKernel, retargeted off vendor/voltage.
# Included early from BoardConfigCommon.mk (for soong headers) and again from
# build/tasks/kernel.mk (guarded). BOARD_PREBUILT_DTBOIMAGE is set with := in
# BoardConfigCommon before this file's ?= can override with a bad empty path.

ifndef AOSPA_CERRO_BOARDCONFIG_KERNEL
AOSPA_CERRO_BOARDCONFIG_KERNEL := true

# $(call is-version-greater-or-equal,version_a,version_b)  version_a >= version_b
define is-version-greater-or-equal
$(strip \
  $(eval a_major := $(word 1,$(subst ., ,$(1)))) \
  $(eval a_minor := $(word 2,$(subst ., ,$(1)))) \
  $(eval b_major := $(word 1,$(subst ., ,$(2)))) \
  $(eval b_minor := $(word 2,$(subst ., ,$(2)))) \
  $(if $(call math_gt,$(a_major),$(b_major)),true, \
    $(if $(call math_gt_or_eq,$(a_major),$(b_major)), \
      $(if $(call math_gt_or_eq,$(a_minor),$(b_minor)),true,false), \
    false)) \
)
endef

# $(call is-version-lower-or-equal,version_a,version_b)  version_a <= version_b
define is-version-lower-or-equal
$(strip \
  $(eval a_major := $(word 1,$(subst ., ,$(1)))) \
  $(eval a_minor := $(word 2,$(subst ., ,$(1)))) \
  $(eval b_major := $(word 1,$(subst ., ,$(2)))) \
  $(eval b_minor := $(word 2,$(subst ., ,$(2)))) \
  $(if $(call math_lt,$(a_major),$(b_major)),true, \
    $(if $(call math_lt_or_eq,$(a_major),$(b_major)), \
      $(if $(call math_lt_or_eq,$(a_minor),$(b_minor)),true,false), \
    false)) \
)
endef

BUILD_TOP := $(abspath .)

TARGET_AUTO_KDIR := $(shell echo $(TARGET_DEVICE_DIR) | sed -e 's/^device/kernel/g')
TARGET_KERNEL_SOURCE ?= $(TARGET_AUTO_KDIR)

TARGET_KERNEL_ARCH := $(strip $(TARGET_KERNEL_ARCH))
ifeq ($(TARGET_KERNEL_ARCH),)
    KERNEL_ARCH := $(TARGET_ARCH)
else
    KERNEL_ARCH := $(TARGET_KERNEL_ARCH)
endif

KERNEL_VERSION := $(shell grep -s "^VERSION = " $(TARGET_KERNEL_SOURCE)/Makefile | awk '{ print $$3 }')
KERNEL_PATCHLEVEL := $(shell grep -s "^PATCHLEVEL = " $(TARGET_KERNEL_SOURCE)/Makefile | awk '{ print $$3 }')
TARGET_KERNEL_VERSION ?= $(shell echo $(KERNEL_VERSION)"."$(KERNEL_PATCHLEVEL))

TARGET_KERNEL_NO_GCC ?= true

ifneq ($(KERNEL_VERSION),)
    ifeq ($(call is-version-greater-or-equal,$(TARGET_KERNEL_VERSION),6.11),true)
        TARGET_KERNEL_LIBC_SYSROOT_USE ?= host
    endif
endif

ifeq ($(TARGET_KERNEL_NO_GCC), true)
    KERNEL_NO_GCC := true
endif

ifneq ($(TARGET_KERNEL_CLANG_VERSION),)
    KERNEL_CLANG_VERSION := clang-$(TARGET_KERNEL_CLANG_VERSION)
else ifneq ($(wildcard $(BUILD_TOP)/prebuilts/clang/host/$(HOST_PREBUILT_TAG)/clang-stable/bin/clang),)
    KERNEL_CLANG_VERSION := clang-stable
else ifneq ($(LLVM_PREBUILTS_VERSION),)
    # AOSPA calcite: clang-stable is clang-format only; Soong default has the compiler
    KERNEL_CLANG_VERSION := $(LLVM_PREBUILTS_VERSION)
else
    KERNEL_CLANG_VERSION := clang-r547379
endif
TARGET_KERNEL_CLANG_PATH ?= $(BUILD_TOP)/prebuilts/clang/host/$(HOST_PREBUILT_TAG)/$(KERNEL_CLANG_VERSION)

TARGET_KERNEL_RUST_VERSION ?= stable

ifneq ($(USE_CCACHE),)
    ifneq ($(CCACHE_EXEC),)
        CCACHE_BIN := $(CCACHE_EXEC)
    endif
endif

KERNEL_MAKE_FLAGS :=

KERNEL_MAKE_FLAGS += \
    KBUILD_BUILD_USER="build-user" \
    KBUILD_BUILD_HOST="build-host"

KERNEL_MAKE_FLAGS += -j$(shell getconf _NPROCESSORS_ONLN)

TOOLS_PATH_OVERRIDE := \
    HIP_PATH=none

ifneq ($(KERNEL_NO_GCC), true)
    GCC_PREBUILTS := $(BUILD_TOP)/prebuilts/gcc/$(HOST_PREBUILT_TAG)
    KERNEL_TOOLCHAIN_arm64 := $(GCC_PREBUILTS)/aarch64/aarch64-linux-android-4.9/bin
    KERNEL_TOOLCHAIN_PREFIX_arm64 := aarch64-linux-android-
    KERNEL_TOOLCHAIN_arm := $(GCC_PREBUILTS)/arm/arm-linux-androideabi-4.9/bin
    KERNEL_TOOLCHAIN_PREFIX_arm := arm-linux-androidkernel-
    KERNEL_TOOLCHAIN_x86 := $(GCC_PREBUILTS)/x86/x86_64-linux-android-4.9/bin
    KERNEL_TOOLCHAIN_PREFIX_x86 := x86_64-linux-androidkernel-

    TARGET_KERNEL_CROSS_COMPILE_PREFIX := $(strip $(TARGET_KERNEL_CROSS_COMPILE_PREFIX))
    ifneq ($(TARGET_KERNEL_CROSS_COMPILE_PREFIX),)
        KERNEL_TOOLCHAIN_PREFIX ?= $(TARGET_KERNEL_CROSS_COMPILE_PREFIX)
    else
        KERNEL_TOOLCHAIN ?= $(KERNEL_TOOLCHAIN_$(KERNEL_ARCH))
        KERNEL_TOOLCHAIN_PREFIX ?= $(KERNEL_TOOLCHAIN_PREFIX_$(KERNEL_ARCH))
    endif

    TARGET_KERNEL_CROSS_COMPILE_PREFIX_ARM32 := $(strip $(TARGET_KERNEL_CROSS_COMPILE_PREFIX_ARM32))
    ifneq ($(TARGET_KERNEL_CROSS_COMPILE_PREFIX_ARM32),)
        KERNEL_TOOLCHAIN_PREFIX_ARM32 ?= $(TARGET_KERNEL_CROSS_COMPILE_PREFIX_ARM32)
    else
        KERNEL_TOOLCHAIN_ARM32 ?= $(KERNEL_TOOLCHAIN_arm)
        KERNEL_TOOLCHAIN_PREFIX_ARM32 ?= $(KERNEL_TOOLCHAIN_PREFIX_arm)
    endif

    ifeq ($(KERNEL_TOOLCHAIN),)
        KERNEL_TOOLCHAIN_PATH := $(KERNEL_TOOLCHAIN_PREFIX)
    else
        KERNEL_TOOLCHAIN_PATH := $(KERNEL_TOOLCHAIN)/$(KERNEL_TOOLCHAIN_PREFIX)
    endif

    ifeq ($(KERNEL_TOOLCHAIN_ARM32),)
        KERNEL_TOOLCHAIN_PATH_ARM32 := $(KERNEL_TOOLCHAIN_PREFIX_ARM32)
    else
        KERNEL_TOOLCHAIN_PATH_ARM32 := $(KERNEL_TOOLCHAIN_ARM32)/$(KERNEL_TOOLCHAIN_PREFIX_ARM32)
    endif

    KERNEL_TOOLCHAIN_PATH_gcc := $(KERNEL_TOOLCHAIN_$(KERNEL_ARCH))

    ifeq ($(KERNEL_ARCH),x86)
        KERNEL_MAKE_FLAGS += $(strip \
                                AR=$(KERNEL_TOOLCHAIN_PREFIX)ar \
                                NM=$(KERNEL_TOOLCHAIN_PREFIX)nm \
                                OBJCOPY=$(KERNEL_TOOLCHAIN_PREFIX)objcopy \
                                OBJDUMP=$(KERNEL_TOOLCHAIN_PREFIX)objdump \
                                READELF=$(KERNEL_TOOLCHAIN_PREFIX)readelf \
                                OBJSIZE=$(KERNEL_TOOLCHAIN_PREFIX)size \
                                STRIP=$(KERNEL_TOOLCHAIN_PREFIX)strip \
                                )
        ifeq ($(TARGET_KERNEL_CLANG_COMPILE),false)
            KERNEL_MAKE_FLAGS += $(strip \
                                    CC=$(KERNEL_TOOLCHAIN_PREFIX)gcc \
                                    LD=$(KERNEL_TOOLCHAIN_PREFIX)ld \
                                    )
        endif
    endif

    ifneq ($(TARGET_KERNEL_CLANG_COMPILE),false)
        KERNEL_CROSS_COMPILE := CROSS_COMPILE="$(KERNEL_TOOLCHAIN_PATH)"
    else
        KERNEL_CROSS_COMPILE := CROSS_COMPILE="$(CCACHE_BIN) $(KERNEL_TOOLCHAIN_PATH)"
    endif

    ifeq ($(KERNEL_ARCH),arm64)
        KERNEL_CROSS_COMPILE += CROSS_COMPILE_ARM32="$(KERNEL_TOOLCHAIN_PATH_ARM32)"
        KERNEL_CROSS_COMPILE += CROSS_COMPILE_COMPAT="$(KERNEL_TOOLCHAIN_PATH_ARM32)"
    endif

    ifeq ($(TARGET_KERNEL_CLANG_COMPILE),false)
        ifeq ($(KERNEL_ARCH),arm)
            KERNEL_MAKE_FLAGS += CFLAGS_MODULE="-fno-pic"
        endif
        ifeq ($(KERNEL_ARCH),arm64)
            KERNEL_MAKE_FLAGS += CFLAGS_MODULE="-fno-pic"
        endif
    endif

    KERNEL_MAKE_FLAGS += HOSTCFLAGS="-I/usr/include -I/usr/include/x86_64-linux-gnu" HOSTLDFLAGS="-L/usr/lib/x86_64-linux-gnu -L/usr/lib64 -fuse-ld=lld"

    ifeq ($(KERNEL_ARCH),arm64)
        TOOLS_PATH_OVERRIDE += PATH=$(BUILD_TOP)/prebuilts/tools-lineage/$(HOST_PREBUILT_TAG)/bin:$(KERNEL_TOOLCHAIN_arm):$$PATH
    else
        TOOLS_PATH_OVERRIDE += PATH=$(BUILD_TOP)/prebuilts/tools-lineage/$(HOST_PREBUILT_TAG)/bin:$$PATH
    endif

    KERNEL_MAKE_FLAGS += HOSTAR=$(TARGET_KERNEL_CLANG_PATH)/bin/llvm-ar
    KERNEL_MAKE_FLAGS += HOSTCC=$(TARGET_KERNEL_CLANG_PATH)/bin/clang
    KERNEL_MAKE_FLAGS += HOSTLD=$(TARGET_KERNEL_CLANG_PATH)/bin/ld.lld
    KERNEL_MAKE_FLAGS += HOSTCXX=$(TARGET_KERNEL_CLANG_PATH)/bin/clang++
    ifneq ($(TARGET_KERNEL_CLANG_COMPILE), false)
        ifneq ($(TARGET_KERNEL_LLVM_BINUTILS), false)
            KERNEL_MAKE_FLAGS += LD=$(TARGET_KERNEL_CLANG_PATH)/bin/ld.lld
            KERNEL_MAKE_FLAGS += AR=$(TARGET_KERNEL_CLANG_PATH)/bin/llvm-ar
        endif
    endif
else
    ifeq ($(TARGET_KERNEL_LIBC_SYSROOT_USE), host)
        KERNEL_HOST_C_LD_FLAGS_SYSROOT :=
    else
        KERNEL_HOST_C_LD_FLAGS_SYSROOT := --sysroot=$(BUILD_TOP)/prebuilts/gcc/linux-x86/host/x86_64-linux-glibc2.17-4.8/sysroot
    endif

    KERNEL_MAKE_FLAGS += HOSTCFLAGS="$(KERNEL_HOST_C_LD_FLAGS_SYSROOT) -I$(BUILD_TOP)/prebuilts/kernel-build-tools/linux-x86/include"
    KERNEL_MAKE_FLAGS += HOSTLDFLAGS="$(KERNEL_HOST_C_LD_FLAGS_SYSROOT) -Wl,-rpath,$(BUILD_TOP)/prebuilts/kernel-build-tools/linux-x86/lib64 -L $(BUILD_TOP)/prebuilts/kernel-build-tools/linux-x86/lib64 -fuse-ld=lld --rtlib=compiler-rt"

    KERNEL_MAKE_FLAGS += HOSTAR=$(TARGET_KERNEL_CLANG_PATH)/bin/llvm-ar
    KERNEL_MAKE_FLAGS += HOSTCC=$(TARGET_KERNEL_CLANG_PATH)/bin/clang
    KERNEL_MAKE_FLAGS += HOSTLD=$(TARGET_KERNEL_CLANG_PATH)/bin/ld.lld
    KERNEL_MAKE_FLAGS += HOSTCXX=$(TARGET_KERNEL_CLANG_PATH)/bin/clang++
    ifneq ($(TARGET_KERNEL_CLANG_COMPILE), false)
        ifneq ($(TARGET_KERNEL_LLVM_BINUTILS), false)
            KERNEL_MAKE_FLAGS += LD=$(TARGET_KERNEL_CLANG_PATH)/bin/ld.lld
            KERNEL_MAKE_FLAGS += AR=$(TARGET_KERNEL_CLANG_PATH)/bin/llvm-ar
        endif
    endif

    TOOLS_PATH_OVERRIDE += PATH=$(BUILD_TOP)/device/nubia/sm8650-common/build/host-bin:$(BUILD_TOP)/prebuilts/tools-lineage/$(HOST_PREBUILT_TAG)/bin:$(TARGET_KERNEL_CLANG_PATH)/bin:$(BUILD_TOP)/prebuilts/rust/$(HOST_PREBUILT_TAG)/$(TARGET_KERNEL_RUST_VERSION)/bin:$(BUILD_TOP)/prebuilts/clang-tools/$(HOST_PREBUILT_TAG)/bin:$$PATH
endif

# AOSPA cerro: tools-lineage perl needs libcrypt.so.1; Fedora 44 only has .so.2.
# lib/Makefile hardcodes "perl" (not $(PERL)); host-bin/perl must be first on PATH.
KERNEL_MAKE_FLAGS += PERL=/usr/bin/perl

# QCOM audio/display/camera Makefiles: BOARD_PLATFORM=$(TARGET_BOARD_PLATFORM).
# soc/Kbuild only includes pineappleauto.conf (CONFIG_SND_EVENT / SOUNDWIRE) when
# BOARD_PLATFORM=pineapple; ipc/codecs can still build via CONFIG_ARCH_PINEAPPLE.
KERNEL_MAKE_FLAGS += TARGET_BOARD_PLATFORM=$(TARGET_BOARD_PLATFORM)

ifneq (,$(filter true, $(TARGET_NEEDS_DTBOIMAGE) $(BOARD_KERNEL_SEPARATED_DTBO)))
    TARGET_KERNEL_DTBO_PREFIX ?=
    TARGET_KERNEL_DTBO ?= dtbo.img
    BOARD_PREBUILT_DTBOIMAGE ?= $(TARGET_OUT_INTERMEDIATES)/DTBO_OBJ/arch/$(KERNEL_ARCH)/boot/$(TARGET_KERNEL_DTBO_PREFIX)$(TARGET_KERNEL_DTBO)
endif

TARGET_KERNEL_DTB ?= dtbs

TARGET_KERNEL_EXT_MODULE_ROOT ?=
TARGET_KERNEL_EXT_MODULES ?=

KERNEL_MAKE_CMD := $(BUILD_TOP)/prebuilts/build-tools/$(HOST_PREBUILT_TAG)/bin/make

ifneq ($(TARGET_KERNEL_CLANG_COMPILE), false)
    ifneq ($(TARGET_KERNEL_LLVM_BINUTILS), false)
        KERNEL_MAKE_FLAGS += LLVM=1 LLVM_IAS=1
    endif
endif

KERNEL_MAKE_FLAGS += LZ4=$(BUILD_TOP)/prebuilts/kernel-build-tools/linux-x86/bin/lz4

KERNEL_MAKE_FLAGS += LEX=$(BUILD_TOP)/prebuilts/build-tools/$(HOST_PREBUILT_TAG)/bin/flex
KERNEL_MAKE_FLAGS += YACC=$(BUILD_TOP)/prebuilts/build-tools/$(HOST_PREBUILT_TAG)/bin/bison
KERNEL_MAKE_FLAGS += M4=$(BUILD_TOP)/prebuilts/build-tools/$(HOST_PREBUILT_TAG)/bin/m4
TOOLS_PATH_OVERRIDE += BISON_PKGDATADIR=$(BUILD_TOP)/prebuilts/build-tools/common/bison

KERNEL_MAKE_FLAGS += PAHOLE=$(BUILD_TOP)/prebuilts/kernel-build-tools/linux-x86/bin/pahole

KERNEL_MAKE_FLAGS += LIBCLANG_PATH=$(TARGET_KERNEL_CLANG_PATH)/lib

OUT_DIR_PREFIX := $(shell echo $(OUT_DIR) | sed -e 's|/target/.*$$||g')
KERNEL_BUILD_OUT_PREFIX :=
ifeq ($(OUT_DIR_PREFIX),out)
    KERNEL_BUILD_OUT_PREFIX := $(BUILD_TOP)/
endif

# Soong cerroVarsPlugin exports (may be empty under TARGET_KERNEL_NO_GCC).
KERNEL_CROSS_COMPILE ?=
KERNEL_PATH ?=
TARGET_KERNEL_PLATFORM_TARGET ?=
TARGET_PREBUILT_KERNEL_HEADERS ?=

endif # AOSPA_CERRO_BOARDCONFIG_KERNEL
