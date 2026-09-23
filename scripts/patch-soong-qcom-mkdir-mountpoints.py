#!/usr/bin/env python3
"""Fix AOSPA mkdir.mk so un-packaged soong mkdir modules do not emit recipes.

AndroidBoardCommon.mk also creates vendor/{firmware_mnt,bt_firmware,dsp}.
mkdir.mk always defined $(LOCAL_SOONG_INSTALL_DIR): even when the module was
not in PRODUCT_PACKAGES → kati "overriding commands".

Better: only emit the mkdir recipe when the module is packaged. Then re-enable
the CLO soong mkdir modules (no enabled:false).

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
MK = SOURCE / "vendor/aospa/build/core/mkdir.mk"
BP = SOURCE / "device/qcom/common/Android.bp"
MARKER = "# AOSPA cerro: only mkdir when packaged (avoid AndroidBoardCommon collide)"
BP_MARKER = "// AOSPA cerro: disabled; AndroidBoardCommon.mk owns this mountpoint"

NAMES = (
    "vendor_bt_firmware_mountpoint",
    "vendor_dsp_mountpoint",
    "vendor_firmware_mnt_mountpoint",
)

DESIRED_MK = """# Copyright (C) 2025 The LineageOS Project
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

ifneq ($(LOCAL_MODULE_MAKEFILE),$(SOONG_ANDROID_MK))
$(call pretty-error,mkdir.mk may only be used from Soong)
endif

include $(BUILD_SYSTEM)/base_rules.mk

""" + MARKER + """
# Do not define $(LOCAL_SOONG_INSTALL_DIR) recipes for modules that are not in
# PRODUCT_PACKAGES — QCOM AndroidBoardCommon.mk owns the same paths on cerro.
ifneq ($(filter $(LOCAL_MODULE),$(PRODUCT_PACKAGES)),)
$(LOCAL_SOONG_INSTALL_DIR):
	@mkdir -p $@

$(LOCAL_BUILT_MODULE): $(LOCAL_SOONG_INSTALL_DIR) $(LOCAL_ADDITIONAL_DEPENDENCIES)
	@mkdir -p $(dir $@)
	@touch $@

ALL_DEFAULT_INSTALLED_MODULES += $(LOCAL_SOONG_INSTALL_DIR)
else
$(LOCAL_BUILT_MODULE): $(LOCAL_ADDITIONAL_DEPENDENCIES)
	@mkdir -p $(dir $@)
	@touch $@
endif
"""


def patch_mkdir_mk() -> None:
    if not MK.is_file():
        print(f"[qcom-mkdir] skip missing {MK}")
        return
    if MARKER in MK.read_text():
        print("[qcom-mkdir] mkdir.mk already gated on PRODUCT_PACKAGES")
        return
    MK.write_text(DESIRED_MK if DESIRED_MK.endswith("\n") else DESIRED_MK + "\n")
    print("[qcom-mkdir] patched vendor/aospa/build/core/mkdir.mk")


def reenable_soong_mkdir() -> None:
    if not BP.is_file():
        print(f"[qcom-mkdir] skip missing {BP}")
        return
    text = BP.read_text()
    if BP_MARKER not in text:
        print("[qcom-mkdir] soong mkdir modules already enabled")
        return
    for name in NAMES:
        old = (
            f'mkdir {{\n    name: "{name}",\n    {BP_MARKER}\n    enabled: false,'
        )
        new = f'mkdir {{\n    name: "{name}",'
        if old in text:
            text = text.replace(old, new, 1)
            print(f"[qcom-mkdir] re-enabled {name}")
    BP.write_text(text)


def main() -> None:
    patch_mkdir_mk()
    reenable_soong_mkdir()


if __name__ == "__main__":
    main()
