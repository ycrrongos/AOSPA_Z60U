# AOSPA cerro: export safe kernel vars into soong (cerroVarsPlugin).
# Do NOT export KERNEL_MAKE_FLAGS / PATH_OVERRIDE_SOONG — embedded quotes break
# soong.variables JSON. headers_install flags live in build/tools/run-headers-install.sh.
# Include after build/BoardConfigKernel.mk.

EXPORT_TO_SOONG := \
    KERNEL_ARCH \
    KERNEL_BUILD_OUT_PREFIX \
    TARGET_KERNEL_SOURCE \
    TARGET_KERNEL_PLATFORM_TARGET

$(call add_soong_config_namespace,cerroVarsPlugin)
$(foreach v,$(EXPORT_TO_SOONG),$(eval $(call add_soong_config_var,cerroVarsPlugin,$(v))))
