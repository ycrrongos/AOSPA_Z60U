#!/usr/bin/env python3
"""Wire CLO vibrator AIDL to Voltage-style soong_config + FIFO oneshot.

AOSPA calcite vibrator.impl hard-links libqtivibratoreffect and never defines
USE_EFFECT_STREAM. cerro awinic haptic_hv rejects FF_CONSTANT ("Only support
custom FIFO data"); Voltage/Lineage use soong_config effect_lib +
use_effect_stream so EVIOCSFF gets richtap effect_stream payloads.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
BP = SOURCE / "vendor/qcom/opensource/vibrator/aidl/Android.bp"
CPP = SOURCE / "vendor/qcom/opensource/vibrator/aidl/Vibrator.cpp"
BP_MARKER = "// AOSPA cerro: Voltage-style soong_config for richtap effect stream"
ONESHOT_MARKER = "// AOSPA cerro: awinic rejects FF_CONSTANT — use FIFO effect stream for oneshot"

OLD_BP = """cc_library_shared {
    name: "vendor.qti.hardware.vibrator.impl",
    vendor: true,
    cflags: Common_CFlags,
    srcs: [
        "Vibrator.cpp",
        "VibratorOffload.cpp",
    ],
    shared_libs: [
        "libcutils",
        "libutils",
        "liblog",
        "libqtivibratoreffect",
        "libqtivibratoreffectoffload",
        "libbinder_ndk",
        "android.hardware.vibrator-V2-ndk",
    ],
    export_include_dirs: ["include"]
}"""

NEW_BP = f"""{BP_MARKER}
cc_library_shared {{
    name: "vendor.qti.hardware.vibrator.impl",
    vendor: true,
    cflags: Common_CFlags + select(soong_config_variable("qti_vibrator", "use_effect_stream"), {{
        true: ["-DUSE_EFFECT_STREAM"],
        default: [],
    }}),
    srcs: [
        "Vibrator.cpp",
        "VibratorOffload.cpp",
    ],
    shared_libs: [
        "libcutils",
        "libutils",
        "liblog",
        "libqtivibratoreffectoffload",
        "libbinder_ndk",
        "android.hardware.vibrator-V2-ndk",
    ] + select(soong_config_variable("qti_vibrator", "effect_lib"), {{
        any @ value: [value],
        default: ["libqtivibratoreffect"],
    }}),
    header_libs: [
        "libqtivibratoreffect_headers",
    ],
    export_include_dirs: ["include"]
}}"""

OLD_ONESHOT = """        } else {
            effect.type = FF_CONSTANT;
            effect.u.constant.level = mCurrMagnitude;
            effect.replay.length = timeoutMs;
        }"""

NEW_ONESHOT = f"""        }} else {{
{ONESHOT_MARKER}
#ifdef USE_EFFECT_STREAM
            stream = get_effect_stream(0);
            effect.type = FF_PERIODIC;
            effect.u.periodic.waveform = FF_CUSTOM;
            effect.u.periodic.magnitude = mCurrMagnitude;
            if (stream != NULL) {{
                effect.u.periodic.custom_data = (int16_t *)stream;
                effect.u.periodic.custom_len = sizeof(*stream);
            }} else {{
                effect.u.periodic.custom_data = data;
                effect.u.periodic.custom_len = sizeof(int16_t) * CUSTOM_DATA_LEN;
            }}
            effect.replay.length = timeoutMs;
#else
            effect.type = FF_CONSTANT;
            effect.u.constant.level = mCurrMagnitude;
            effect.replay.length = timeoutMs;
#endif
        }}"""


def patch_bp() -> None:
    if not BP.is_file():
        print(f"[vibrator-effect-stream] skip missing {BP}")
        return
    text = BP.read_text()
    if BP_MARKER in text:
        print("[vibrator-effect-stream] Android.bp already patched")
        return
    if OLD_BP not in text:
        print("[vibrator-effect-stream] unexpected Android.bp layout")
        return
    BP.write_text(text.replace(OLD_BP, NEW_BP, 1))
    print("[vibrator-effect-stream] patched Android.bp soong_config")


def patch_oneshot() -> None:
    if not CPP.is_file():
        print(f"[vibrator-effect-stream] skip missing {CPP}")
        return
    text = CPP.read_text()
    if ONESHOT_MARKER in text:
        print("[vibrator-effect-stream] Vibrator.cpp oneshot already patched")
        return
    if OLD_ONESHOT not in text:
        print("[vibrator-effect-stream] unexpected Vibrator.cpp oneshot layout")
        return
    CPP.write_text(text.replace(OLD_ONESHOT, NEW_ONESHOT, 1))
    print("[vibrator-effect-stream] patched oneshot → FIFO effect stream")


def main() -> None:
    patch_bp()
    patch_oneshot()


if __name__ == "__main__":
    main()
