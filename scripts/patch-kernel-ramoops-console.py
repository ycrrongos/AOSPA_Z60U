#!/usr/bin/env python3
"""Carve console/record space out of pineapple ramoops (was 100% pmsg).

Stock pineapple.dtsi sets pmsg-size == mem size (2MiB), so console_size=0 and
record_size=0. After a logo hang + force-recovery, /sys/fs/pstore stays empty
and dmesg shows "pstore: Invalid compression size for deflate: 0".

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
DTSI = SOURCE / (
    "kernel/nubia/sm8650/arch/arm64/boot/dts/vendor/qcom/pineapple.dtsi"
)
MARKER = "/* AOSPA cerro: ramoops console+record for post-hang pstore */"

OLD = re.compile(
    r"ramoops_mem:\s*ramoops_region\s*\{"
    r"[^}]*?"
    r"compatible\s*=\s*\"ramoops\";"
    r"[^}]*?\}",
    re.S,
)

NEW = """ramoops_mem: ramoops_region {
		compatible = "ramoops";
		alloc-ranges = <0x0 0x00000000 0xffffffff 0xffffffff>;
		size = <0x0 0x200000>;
		""" + MARKER + """
		console-size = <0x80000>;
		record-size = <0x20000>;
		pmsg-size = <0x160000>;
		mem-type = <2>;
	}"""


def main() -> int:
    if not DTSI.is_file():
        print(f"[patch-kernel-ramoops-console] skip: missing {DTSI}", file=sys.stderr)
        return 0
    text = DTSI.read_text()
    if MARKER in text and "console-size = <0x80000>" in text:
        print("[patch-kernel-ramoops-console] already applied")
        return 0
    m = OLD.search(text)
    if not m:
        print("[patch-kernel-ramoops-console] ERROR: ramoops_region not found", file=sys.stderr)
        return 1
    block = m.group(0)
    if "pmsg-size = <0x200000>" not in block and "console-size" not in block:
        print(
            "[patch-kernel-ramoops-console] ERROR: unexpected ramoops block:\n"
            + block,
            file=sys.stderr,
        )
        return 1
    DTSI.write_text(text[: m.start()] + NEW + text[m.end() :])
    print(f"[patch-kernel-ramoops-console] patched {DTSI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
