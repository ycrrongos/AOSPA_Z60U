#!/usr/bin/env python3
"""Restore vendor_hal_qspmhal attributes missing from AOSPA QCOM sepolicy.

gmscore_app.te (sepolicy_vndr generic) does
  hal_client_domain(gmscore_app, vendor_hal_qspmhal)
which needs attribute vendor_hal_qspmhal_client. API 34 prebuilts still have
these; live generic/public/attributes dropped them → recovery_sepolicy.cil fails.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
ATTR = SOURCE / "device/qcom/sepolicy/generic/public/attributes"
MARKER = "# AOSPA cerro: restore vendor_hal_qspmhal attributes (API34 had them)"
BLOCK = """
""" + MARKER + """
attribute vendor_hal_qspmhal;
attribute vendor_hal_qspmhal_client;
attribute vendor_hal_qspmhal_server;

"""


def main() -> None:
    if not ATTR.is_file():
        print(f"[qspmhal-attr] skip missing {ATTR}")
        return
    text = ATTR.read_text()
    if MARKER in text or "attribute vendor_hal_qspmhal_client;" in text:
        print("[qspmhal-attr] already present")
        return
    needle = (
        "attribute vendor_hal_perf;\n"
        "attribute vendor_hal_perf_client;\n"
        "attribute vendor_hal_perf_server;\n"
    )
    if needle not in text:
        print("[qspmhal-attr] unexpected attributes layout: missing vendor_hal_perf block")
        return
    ATTR.write_text(text.replace(needle, needle + BLOCK, 1))
    print("[qspmhal-attr] restored vendor_hal_qspmhal{,_client,_server}")


if __name__ == "__main__":
    main()
