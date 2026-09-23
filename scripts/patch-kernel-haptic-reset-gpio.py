#!/usr/bin/env python3
"""AOSPA cerro: set haptic reset-gpio to TLMM 120 in the common full node.

Partial cerro-only overlays of reset-gpio left &tlmm as 0xffffffff in DTBO,
so live DT kept common's gpio 90 and the motor reset line never toggled.
Changing the full node in zte-pineapple-common-overlay.dtsi is reliable.
"""
from __future__ import annotations

import sys
from pathlib import Path

COMMON_OLD = "\t\treset-gpio = <&tlmm 90 0>;"
COMMON_NEW = "\t\treset-gpio = <&tlmm 120 0>; /* AOSPA cerro: was 90 */"


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    common = root / (
        "kernel/nubia/sm8650-devicetrees/qcom/zte-pineapple-common-overlay.dtsi"
    )
    if not common.is_file():
        print(f"[haptic-reset-gpio] skip missing {common}")
        return 0
    text = common.read_text()
    if "AOSPA cerro: was 90" in text or COMMON_NEW.strip() in text:
        print(f"[haptic-reset-gpio] already 120 {common}")
        return 0
    if COMMON_OLD not in text:
        print(f"[haptic-reset-gpio] no reset-gpio 90 in {common}")
        return 1
    common.write_text(text.replace(COMMON_OLD, COMMON_NEW, 1))
    print(f"[haptic-reset-gpio] common reset 90→120 {common}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
