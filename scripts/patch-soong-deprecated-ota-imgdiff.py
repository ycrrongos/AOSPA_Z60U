#!/usr/bin/env python3
"""Disable deprecated-ota device tests that break AOSPA health AIDL graph.

Voltage `bootable/deprecated-ota` brings `non_ab_unit_tests`, which pulls both
android.hardware.health V4 and V5 via libupdater_device_defaults — soong rejects
that on calcite. We only need host `imgdiff` / `libimgdiff`.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
BP = SOURCE / "bootable/deprecated-ota/tests/Android.bp"
MARKER = "// AOSPA cerro: device unit tests disabled (health V4+V5 clash); host imgdiff only"
NEEDLE = 'cc_test {\n    name: "non_ab_unit_tests",'


def main() -> None:
    if not BP.is_file():
        print(f"[deprecated-ota] skip missing {BP}")
        return
    text = BP.read_text()
    if MARKER in text and "enabled: false" in text[text.find("non_ab_unit_tests") : text.find("non_ab_unit_tests") + 400]:
        print("[deprecated-ota] non_ab_unit_tests already disabled")
        return
    if NEEDLE not in text:
        print("[deprecated-ota] non_ab_unit_tests block not found, skip")
        return
    text = text.replace(
        NEEDLE,
        f"cc_test {{\n    {MARKER}\n    name: \"non_ab_unit_tests\",\n    enabled: false,",
        1,
    )
    BP.write_text(text)
    print("[deprecated-ota] disabled non_ab_unit_tests (keep host imgdiff)")


if __name__ == "__main__":
    main()
