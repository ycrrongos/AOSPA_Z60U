#!/usr/bin/env python3
"""Install Lineage libtinyxml2-v34 into AOSPA hardware/lineage/compat.

nubia vendor blobs (libsnapdragoncolor-manager) DT_NEEDED this SONAME.
AOSPA compat vndk/v34 only ships libaudioroute-v34 / libui-v34.
Do not overlay the whole Lineage compat tree.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
PREBUILT = ROOT / "prebuilts-cerro/libtinyxml2-v34"
COMPAT = SOURCE / "hardware/lineage/compat"
BP = COMPAT / "Android.bp"
MARKER = "// AOSPA cerro: libtinyxml2-v34 for nubia vendor blobs"

MODULE = f"""
{MARKER}
cc_prebuilt_library_shared {{
    name: "libtinyxml2-v34",
    vendor: true,
    strip: {{
        none: true,
    }},
    shared_libs: [
        "liblog",
        "libc++",
        "libc",
        "libm",
        "libdl",
    ],
    target: {{
        android_arm: {{
            srcs: ["vndk/v34/arm/libtinyxml2-v34.so"],
        }},
        android_arm64: {{
            srcs: ["vndk/v34/arm64/libtinyxml2-v34.so"],
        }},
    }},
    compile_multilib: "both",
}}
"""


def copy_sos() -> None:
    for abi in ("arm", "arm64"):
        src = PREBUILT / abi / "libtinyxml2-v34.so"
        dst_dir = COMPAT / "vndk/v34" / abi
        if not src.is_file():
            print(f"[tinyxml2-v34] skip missing {src}")
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        print(f"[tinyxml2-v34] installed {dst.relative_to(SOURCE)}")


def append_bp() -> None:
    if not BP.is_file():
        print(f"[tinyxml2-v34] skip missing {BP}")
        return
    text = BP.read_text()
    if MARKER in text or 'name: "libtinyxml2-v34"' in text:
        print("[tinyxml2-v34] Android.bp already has libtinyxml2-v34")
        return
    BP.write_text(text.rstrip() + "\n" + MODULE)
    print("[tinyxml2-v34] appended module to hardware/lineage/compat/Android.bp")


def main() -> None:
    if not COMPAT.is_dir():
        print(f"[tinyxml2-v34] skip missing {COMPAT}")
        return
    copy_sos()
    append_bp()


if __name__ == "__main__":
    main()
