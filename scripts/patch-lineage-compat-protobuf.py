#!/usr/bin/env python3
"""Install Lineage libprotobuf-cpp-{full,lite}-21.7 into AOSPA hardware/lineage/compat.

nubia extract-utils blobs DT_NEEDED these SONAMEs. AOSPA compat only ships
3.9.1 / v29 vendorcompat. Do not overlay the whole Lineage compat tree.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
COMPAT = SOURCE / "hardware/lineage/compat"
BP = COMPAT / "Android.bp"

LIBS = (
    {
        "name": "libprotobuf-cpp-full-21.7",
        "prebuilt": ROOT / "prebuilts-cerro/libprotobuf-cpp-full-21.7",
        "so": "libprotobuf-cpp-full-21.7.so",
        "marker": "// AOSPA cerro: libprotobuf-cpp-full-21.7 for nubia vendor blobs",
        "shared_libs": ('"libc++"', '"liblog"', '"libz"'),
    },
    {
        "name": "libprotobuf-cpp-lite-21.7",
        "prebuilt": ROOT / "prebuilts-cerro/libprotobuf-cpp-lite-21.7",
        "so": "libprotobuf-cpp-lite-21.7.so",
        "marker": "// AOSPA cerro: libprotobuf-cpp-lite-21.7 for nubia vendor blobs",
        "shared_libs": ('"libc++"', '"liblog"'),
    },
)


def module_text(lib: dict) -> str:
    shared = ",\n        ".join(lib["shared_libs"])
    so = lib["so"]
    return f"""
{lib["marker"]}
cc_prebuilt_library_shared {{
    name: "{lib["name"]}",
    system_ext_specific: true,
    vendor_available: true,
    strip: {{
        none: true,
    }},
    shared_libs: [
        {shared},
    ],
    target: {{
        android_arm: {{
            srcs: ["libprotobuf/arm/{so}"],
        }},
        android_arm64: {{
            srcs: ["libprotobuf/arm64/{so}"],
        }},
    }},
    compile_multilib: "both",
}}
"""


def copy_sos(lib: dict) -> None:
    for abi in ("arm", "arm64"):
        src = lib["prebuilt"] / abi / lib["so"]
        dst_dir = COMPAT / "libprotobuf" / abi
        if not src.is_file():
            print(f"[protobuf-21.7] skip missing {src}")
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        print(f"[protobuf-21.7] installed {dst.relative_to(SOURCE)}")


def append_bp(lib: dict) -> None:
    if not BP.is_file():
        print(f"[protobuf-21.7] skip missing {BP}")
        return
    text = BP.read_text()
    name = lib["name"]
    if lib["marker"] in text or f'name: "{name}"' in text:
        print(f"[protobuf-21.7] Android.bp already has {name}")
        return
    BP.write_text(text.rstrip() + "\n" + module_text(lib))
    print(f"[protobuf-21.7] appended {name} to hardware/lineage/compat/Android.bp")


def main() -> None:
    if not COMPAT.is_dir():
        print(f"[protobuf-21.7] skip missing {COMPAT}")
        return
    for lib in LIBS:
        copy_sos(lib)
        append_bp(lib)


if __name__ == "__main__":
    main()
