#!/usr/bin/env python3
"""Keep vendor_hal_qspmhal attributes exactly once for AOSPA/shadedark.

History:
- Older trees dropped them from device/qcom/sepolicy/generic → recovery_sepolicy
  failed (gmscore_app needs vendor_hal_qspmhal_client). We patched generic.
- Newer shadedark / device/qcom/common already declares them in
  common/sepolicy/common/public/attributes. Leaving the generic patch in
  place then causes: Duplicate declaration of type vendor_hal_qspmhal.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
GENERIC = SOURCE / "device/qcom/sepolicy/generic/public/attributes"
COMMON = SOURCE / "device/qcom/common/sepolicy/common/public/attributes"
MARKER = "# AOSPA cerro: restore vendor_hal_qspmhal attributes (API34 had them)"
BLOCK = (
    "\n"
    + MARKER
    + """
attribute vendor_hal_qspmhal;
attribute vendor_hal_qspmhal_client;
attribute vendor_hal_qspmhal_server;

"""
)
BLOCK_RE = re.compile(
    r"\n?# AOSPA cerro: restore vendor_hal_qspmhal attributes \(API34 had them\)\n"
    r"attribute vendor_hal_qspmhal;\n"
    r"attribute vendor_hal_qspmhal_client;\n"
    r"attribute vendor_hal_qspmhal_server;\n?",
)


def common_has_qspmhal() -> bool:
    if not COMMON.is_file():
        return False
    return "attribute vendor_hal_qspmhal_client;" in COMMON.read_text()


def main() -> None:
    if not GENERIC.is_file():
        print(f"[qspmhal-attr] skip missing {GENERIC}")
        return

    text = GENERIC.read_text()
    if common_has_qspmhal():
        new, n = BLOCK_RE.subn("", text)
        # Also strip a bare duplicate block without relying only on marker
        if "attribute vendor_hal_qspmhal_client;" in new and n == 0:
            # Upstream generic may still list them; leave alone if common also
            # has them — duplicate across trees is the failure mode we fix by
            # removing our injected marker block only.
            pass
        if n:
            GENERIC.write_text(new)
            print(
                "[qspmhal-attr] common already has qspmhal; "
                f"removed {n} injected block(s) from generic"
            )
        else:
            print("[qspmhal-attr] common already has qspmhal; generic clean")
        return

    if MARKER in text or "attribute vendor_hal_qspmhal_client;" in text:
        print("[qspmhal-attr] already present in generic (common missing)")
        return

    needle = (
        "attribute vendor_hal_perf;\n"
        "attribute vendor_hal_perf_client;\n"
        "attribute vendor_hal_perf_server;\n"
    )
    if needle not in text:
        print("[qspmhal-attr] unexpected attributes layout: missing vendor_hal_perf block")
        return
    GENERIC.write_text(text.replace(needle, needle + BLOCK, 1))
    print("[qspmhal-attr] restored vendor_hal_qspmhal{,_client,_server} into generic")


if __name__ == "__main__":
    main()
