#!/usr/bin/env python3
"""Install Lineage libinput_shim into AOSPA hardware/lineage/compat.

libwfdnative (nubia system_ext blob) DT_NEEDED this shim. AOSPA compat
never shipped libinput/. Do not overlay the whole Lineage compat tree.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
PREBUILT = ROOT / "prebuilts-cerro/libinput_shim"
COMPAT = SOURCE / "hardware/lineage/compat"
BP = COMPAT / "Android.bp"
MARKER = "// AOSPA cerro: libinput_shim for nubia libwfdnative"

MODULE = f"""
{MARKER}
cc_library {{
    name: "libinput_shim",
    srcs: [
        "libinput/android_view_KeyEvent.cpp",
        "libinput/Input.cpp",
    ],
    include_dirs: [
        "frameworks/native/include",
        "frameworks/native/libs/ui/include",
    ],
    shared_libs: [
        "libandroid_runtime",
        "libinput",
    ],
    compile_multilib: "64",
    system_ext_specific: true,
}}
"""

SOURCES = ("Input.cpp", "android_view_KeyEvent.cpp")


def copy_srcs() -> None:
    dst_dir = COMPAT / "libinput"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in SOURCES:
        src = PREBUILT / name
        if not src.is_file():
            print(f"[libinput-shim] skip missing {src}")
            continue
        dst = dst_dir / name
        shutil.copy2(src, dst)
        print(f"[libinput-shim] installed {dst.relative_to(SOURCE)}")


def append_bp() -> None:
    if not BP.is_file():
        print(f"[libinput-shim] skip missing {BP}")
        return
    text = BP.read_text()
    if MARKER in text or 'name: "libinput_shim"' in text:
        print("[libinput-shim] Android.bp already has libinput_shim")
        return
    BP.write_text(text.rstrip() + "\n" + MODULE)
    print("[libinput-shim] appended module to hardware/lineage/compat/Android.bp")


def main() -> None:
    if not COMPAT.is_dir():
        print(f"[libinput-shim] skip missing {COMPAT}")
        return
    copy_srcs()
    append_bp()


if __name__ == "__main__":
    main()
