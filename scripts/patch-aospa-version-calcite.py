#!/usr/bin/env python3
"""Force AOSPA_MAJOR_VERSION to calcite for unofficial cerro builds.

Upstream vendor/aospa/target/product/version.mk still says beryl while this
tree is calcite — zip names become aospa-beryl-… and confuse branch tracking.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
MK = SOURCE / "vendor/aospa/target/product/version.mk"
MARKER = "# AOSPA cerro: calcite branch (upstream version.mk may still say beryl)"


def main() -> None:
    if not MK.is_file():
        print(f"[aospa-version] skip missing {MK}")
        return
    text = MK.read_text()
    if MARKER in text and "AOSPA_MAJOR_VERSION := calcite" in text:
        print("[aospa-version] already calcite")
        return
    new, n = re.subn(
        r"^AOSPA_MAJOR_VERSION\s*:=.*$",
        MARKER + "\nAOSPA_MAJOR_VERSION := calcite",
        text,
        count=1,
        flags=re.M,
    )
    if n == 0:
        print("[aospa-version] AOSPA_MAJOR_VERSION line not found")
        return
    MK.write_text(new)
    print("[aospa-version] set AOSPA_MAJOR_VERSION := calcite")


if __name__ == "__main__":
    main()
