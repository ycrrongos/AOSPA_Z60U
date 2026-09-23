#!/usr/bin/env python3
"""Rename vendor/nxp QTI eSE init_rc / vintf so they no longer collide with AOSP.

Binary module names were already *-qti / *-nxp; rc/xml still used AOSP filenames.
Rename to *-qti.* and drop enabled:false so the modules are buildable; cerro does
not package them (TARGET_USES_ESE_KEYMINT=false) but enabling later is safe.

Do not overlay the whole vendor/nxp tree.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))

# (Android.bp, module name line, old rc/xml refs → new)
RENAMES = (
    {
        "bp": SOURCE
        / "vendor/nxp/opensource/keymaster/keymint/KM300/authsecret/Android.bp",
        "name": 'name: "android.hardware.authsecret-service.nxp-qti"',
        "files": (
            (
                "android.hardware.authsecret-service.nxp.rc",
                "android.hardware.authsecret-service.nxp-qti.rc",
            ),
            (
                "android.hardware.authsecret-service.nxp.xml",
                "android.hardware.authsecret-service.nxp-qti.xml",
            ),
        ),
        "init_rc": 'init_rc: ["android.hardware.authsecret-service.nxp-qti.rc"],',
        "vintf": 'vintf_fragments: ["android.hardware.authsecret-service.nxp-qti.xml"],',
        "old_init": 'init_rc: ["android.hardware.authsecret-service.nxp.rc"],',
        "old_vintf": 'vintf_fragments: ["android.hardware.authsecret-service.nxp.xml"],',
    },
    {
        "bp": SOURCE / "vendor/nxp/opensource/keymaster/keymint/KM300/Android.bp",
        "name": 'name: "android.hardware.security.keymint-service.strongbox-nxp"',
        "files": (
            (
                "android.hardware.security.keymint-service.strongbox.nxp.rc",
                "android.hardware.security.keymint-service.strongbox.nxp-qti.rc",
            ),
            (
                "android.hardware.security.keymint-service.strongbox.xml",
                "android.hardware.security.keymint-service.strongbox.nxp-qti.xml",
            ),
            (
                "android.hardware.security.sharedsecret-service.strongbox.xml",
                "android.hardware.security.sharedsecret-service.strongbox.nxp-qti.xml",
            ),
        ),
        "init_rc": 'init_rc: ["android.hardware.security.keymint-service.strongbox.nxp-qti.rc"],',
        "old_init": 'init_rc: ["android.hardware.security.keymint-service.strongbox.nxp.rc"],',
        "vintf": (
            'vintf_fragments: [\n'
            '        "android.hardware.security.keymint-service.strongbox.nxp-qti.xml",\n'
            '        "android.hardware.security.sharedsecret-service.strongbox.nxp-qti.xml",\n'
            '    ],'
        ),
        "old_vintf": (
            'vintf_fragments: [\n'
            '        "android.hardware.security.keymint-service.strongbox.xml",\n'
            '        "android.hardware.security.sharedsecret-service.strongbox.xml",\n'
            '    ],'
        ),
    },
    {
        "bp": SOURCE / "vendor/nxp/opensource/keymaster/weaver/Android.bp",
        "name": 'name: "android.hardware.weaver-service.nxp-qti"',
        "files": (
            (
                "aidl_impl/android.hardware.weaver-service.nxp.rc",
                "aidl_impl/android.hardware.weaver-service.nxp-qti.rc",
            ),
        ),
        "init_rc": 'init_rc: ["aidl_impl/android.hardware.weaver-service.nxp-qti.rc"],',
        "old_init": 'init_rc: ["aidl_impl/android.hardware.weaver-service.nxp.rc"],',
        "vintf": None,
        "old_vintf": None,
    },
    {
        "bp": SOURCE / "vendor/nxp/opensource/keymaster/weaver/Android.bp",
        "name": 'name: "android.hardware.weaver-service.nxp.xml"',
        "files": (
            (
                "aidl_impl/android.hardware.weaver-service.nxp.xml",
                "aidl_impl/android.hardware.weaver-service.nxp-qti.xml",
            ),
        ),
        "rename_module": 'name: "android.hardware.weaver-service.nxp-qti.xml"',
        "src_line": 'src: "aidl_impl/android.hardware.weaver-service.nxp-qti.xml",',
        "old_src": 'src: "aidl_impl/android.hardware.weaver-service.nxp.xml",',
    },
)

DISABLE_MARKERS = (
    "// AOSPA cerro: disabled; init_rc/vintf collide with hardware/nxp",
    "// AOSPA cerro: disabled; init_rc collides with hardware/nxp KM200",
    "// AOSPA cerro: disabled; init_rc collides with hardware/nxp weaver",
    "// AOSPA cerro: disabled; vintf collides with hardware/nxp weaver",
)


def rename_file(bp_dir: Path, old: str, new: str) -> None:
    src = bp_dir / old
    dst = bp_dir / new
    if dst.is_file():
        return
    if not src.is_file():
        print(f"[nxp-ese] missing {src}")
        return
    shutil.copy2(src, dst)
    print(f"[nxp-ese] copied {old} → {new}")


def strip_enabled_false(text: str, name_line: str) -> str:
    if name_line not in text:
        return text
    # remove marker + enabled:false immediately after name
    for marker in DISABLE_MARKERS:
        old = f"    {name_line},\n    {marker}\n    enabled: false,"
        new = f"    {name_line},"
        if old in text:
            text = text.replace(old, new, 1)
    # also plain enabled:false after name
    old2 = f"    {name_line},\n    enabled: false,"
    if old2 in text:
        text = text.replace(old2, f"    {name_line},", 1)
    return text


def patch_one(spec: dict) -> None:
    bp: Path = spec["bp"]
    if not bp.is_file():
        print(f"[nxp-ese] skip missing {bp}")
        return
    bp_dir = bp.parent
    for old, new in spec["files"]:
        rename_file(bp_dir, old, new)

    text = bp.read_text()
    name = spec["name"]
    text = strip_enabled_false(text, name)

    if "rename_module" in spec:
        if spec["rename_module"] not in text:
            text = text.replace(name, spec["rename_module"], 1)
        if spec.get("old_src") and spec["old_src"] in text:
            text = text.replace(spec["old_src"], spec["src_line"], 1)
        marker = "// AOSPA cerro: weaver xml renamed *-qti to avoid AOSP collide"
        if marker not in text and spec["rename_module"] in text:
            text = text.replace(
                spec["rename_module"] + ",",
                spec["rename_module"] + f",\n    {marker}",
                1,
            )
    else:
        if spec.get("old_init") and spec["old_init"] in text:
            text = text.replace(spec["old_init"], spec["init_rc"], 1)
        if spec.get("old_vintf") and spec.get("vintf") and spec["old_vintf"] in text:
            text = text.replace(spec["old_vintf"], spec["vintf"], 1)
        marker = "// AOSPA cerro: init_rc/vintf use *-qti names (no collide with hardware/nxp)"
        if marker not in text and name in text:
            text = text.replace(name + ",", name + f",\n    {marker}", 1)

    bp.write_text(text)
    print(f"[nxp-ese] patched {bp.relative_to(SOURCE)} ({name})")


def main() -> None:
    for spec in RENAMES:
        patch_one(spec)


if __name__ == "__main__":
    main()
