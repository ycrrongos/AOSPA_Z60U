#!/usr/bin/env python3
"""Add fdtput / fdtoverlaymerge host tools used by QCOM merge_dtbs.py.

AOSPA external/dtc has fdtput.c but no cc_binary_host. fdtoverlaymerge.c is a
Lineage extra; copy from prebuilts-cerro/dtc/. AOSPA libfdt has no
fdt_overlay_merge(); copy Lineage fdt_overlay.c and declare the API.
Do not overlay whole dtc.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
DTC = SOURCE / "external/dtc"
BP = DTC / "Android.bp"
PRE = ROOT / "prebuilts-cerro/dtc"
MARKER = "// AOSPA cerro: host fdtput/fdtoverlaymerge for merge_dtbs.py"
BLOCK = """
""" + MARKER + """
cc_binary_host {
    name: "fdtput",
    defaults: ["dt_defaults"],
    srcs: [
        "fdtput.c",
        "util.c",
    ],
}

cc_binary_host {
    name: "fdtoverlaymerge",
    defaults: ["dt_defaults"],
    srcs: [
        "fdtoverlaymerge.c",
        "util.c",
    ],
}
"""
MERGE_DECL = """
/**
 * fdt_overlay_merge - Merge two overlays into one
 * @fdt: pointer to the first device tree overlay blob
 * @fdto: pointer to the second device tree overlay blob
 * @fdto_nospace: indicates if FDT_ERR_NOSPACE error code applies to @fdto
 *
 * fdt_overlay_merge() will merge second overlay blob into first overlay blob.
 *
 * Expect the first device tree to be modified, even if the function
 * returns an error.
 *
 * returns:
 *	0, on success
 *	-FDT_ERR_NOSPACE, there's not enough space in first device tree blob
 *	-FDT_ERR_BADVALUE
 */
int fdt_overlay_merge(void *fdt, void *fdto, int *fdto_nospace);

"""


def install_copy(src: Path, dst: Path, label: str) -> None:
    if not src.is_file():
        print(f"[dtc-fdt] skip missing {src}")
        return
    if not dst.is_file() or dst.read_bytes() != src.read_bytes():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[dtc-fdt] installed {label}")
    else:
        print(f"[dtc-fdt] {label} already installed")


def patch_header() -> None:
    hdr = DTC / "libfdt/libfdt.h"
    if not hdr.is_file():
        print(f"[dtc-fdt] skip missing {hdr}")
        return
    text = hdr.read_text()
    if "int fdt_overlay_merge(" in text:
        print("[dtc-fdt] libfdt.h already has fdt_overlay_merge")
        return
    needle = (
        "int fdt_overlay_target_offset(const void *fdt, const void *fdto,\n"
        "\t\t\t      int fragment_offset, char const **pathp);\n"
    )
    if needle not in text:
        print("[dtc-fdt] unexpected libfdt.h: missing fdt_overlay_target_offset")
        return
    hdr.write_text(text.replace(needle, needle + "\n" + MERGE_DECL, 1))
    print("[dtc-fdt] declared fdt_overlay_merge in libfdt.h")


def patch_version_lds() -> None:
    lds = DTC / "libfdt/version.lds"
    if not lds.is_file():
        print(f"[dtc-fdt] skip missing {lds}")
        return
    text = lds.read_text()
    if "fdt_overlay_merge;" in text:
        print("[dtc-fdt] version.lds already exports fdt_overlay_merge")
        return
    needle = "\t\tfdt_overlay_apply;\n"
    if needle not in text:
        print("[dtc-fdt] unexpected version.lds: missing fdt_overlay_apply")
        return
    lds.write_text(text.replace(needle, needle + "\t\tfdt_overlay_merge;\n", 1))
    print("[dtc-fdt] exported fdt_overlay_merge in version.lds")


def patch_android_bp() -> None:
    if not BP.is_file():
        print(f"[dtc-fdt] skip missing {BP}")
        return
    text = BP.read_text()
    if MARKER in text or (
        'name: "fdtput"' in text and 'name: "fdtoverlaymerge"' in text
    ):
        print("[dtc-fdt] Android.bp already has fdtput/fdtoverlaymerge")
        return
    needle = 'cc_binary_host {\n    name: "fdtdump",'
    if needle not in text:
        print("[dtc-fdt] unexpected Android.bp layout: missing fdtdump")
        return
    BP.write_text(text.replace(needle, BLOCK + "\n" + needle, 1))
    print("[dtc-fdt] added fdtput and fdtoverlaymerge host binaries")


def main() -> None:
    install_copy(PRE / "fdtoverlaymerge.c", DTC / "fdtoverlaymerge.c", "fdtoverlaymerge.c")
    install_copy(PRE / "fdt_overlay.c", DTC / "libfdt/fdt_overlay.c", "libfdt/fdt_overlay.c")
    patch_header()
    patch_version_lds()
    patch_android_bp()


if __name__ == "__main__":
    main()
