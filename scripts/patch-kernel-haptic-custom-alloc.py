#!/usr/bin/env python3
"""Fix awinic haptic_hv custom FIFO heap underflow.

upload_custom_effect used kcalloc(length) but aw_haptic_container is
{ int len; uint8_t data[]; } — needs length + sizeof(int). Firmware RTP path
already used vmalloc(size + sizeof(int)). Matches Voltage kernel source bug;
without this, custom FIFO (richtap effect_stream) corrupts heap / may never
reach RTP_GO.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
HV = SOURCE / "kernel/nubia/sm8650/drivers/misc/haptic_hv/haptic_hv.c"
MARKER = "/* AOSPA cerro: custom FIFO alloc includes container header */"

OLD = """\tkvfree(aw_rtp);
\taw_rtp = kcalloc(custom_data.length, sizeof(u8), GFP_KERNEL);
\tif (!aw_rtp) {
\t\tret = -ENOMEM;
\t\tgoto exit;
\t}

\taw_rtp->len = custom_data.length;"""

NEW = f"""\tkvfree(aw_rtp);
{MARKER}
\taw_rtp = kvzalloc(sizeof(*aw_rtp) + custom_data.length, GFP_KERNEL);
\tif (!aw_rtp) {{
\t\tret = -ENOMEM;
\t\tgoto exit;
\t}}

\taw_rtp->len = custom_data.length;"""


def main() -> None:
    if not HV.is_file():
        print(f"[haptic-custom-alloc] skip missing {HV}")
        return
    text = HV.read_text()
    if MARKER in text:
        print("[haptic-custom-alloc] already patched")
        return
    if OLD not in text:
        print("[haptic-custom-alloc] unexpected upload_custom_effect layout")
        return
    HV.write_text(text.replace(OLD, NEW, 1))
    print("[haptic-custom-alloc] patched custom FIFO allocation")


if __name__ == "__main__":
    main()
