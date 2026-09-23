#!/usr/bin/env python3
"""Add Lineage-style libqtivibratoreffect_headers to AOSPA CLO vibrator.

cerro overlay builds libqtivibratoreffect.nubia_sm8650-richtap against that
header module. AOSPA vendor/qcom/opensource/vibrator only exports includes
from the shared lib, not a cc_library_headers.

Do not overlay the whole Lineage vibrator tree (AIDL layout differs).

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
BP = SOURCE / "vendor/qcom/opensource/vibrator/effect/Android.bp"
MARKER = "// AOSPA cerro: headers module for nubia richtap effect lib"
HEADERS = f"""
{MARKER}
cc_library_headers {{
    name: "libqtivibratoreffect_headers",
    vendor: true,
    export_include_dirs: ["."],
}}
"""


def main() -> None:
    if not BP.is_file():
        print(f"[vibrator-headers] skip missing {BP}")
        return
    text = BP.read_text()
    if MARKER in text or 'name: "libqtivibratoreffect_headers"' in text:
        print("[vibrator-headers] Android.bp already has libqtivibratoreffect_headers")
        return
    needle = 'Common_CFlags += ["-Werror"]\n'
    if needle not in text:
        print("[vibrator-headers] unexpected Android.bp layout, append at top")
        BP.write_text(HEADERS.lstrip() + text)
        return
    BP.write_text(text.replace(needle, needle + HEADERS, 1))
    print("[vibrator-headers] added libqtivibratoreffect_headers")


if __name__ == "__main__":
    main()
