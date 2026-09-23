#!/usr/bin/env python3
"""Drop Soong modules that duplicate AOSPA CLO definitions.

hardware/qcom-caf/common/Android.bp cannot be wrapped in soong_namespace:
Soong requires the namespace to be the first module, which would hide
qti_kernel_headers / audio_kernel_headers from hardware/qcom-caf/sm8650
(itself a namespace via os_pickup_qssi.bp). Keep those headers in the
root namespace; drop rfs/mountpoint/duplicate HIDL only.

fwk-detect + memtrack subdirs also duplicate CLO. Lineage health AIDL
duplicates vendor/aospa/interfaces/health — replace those Android.bp
with stubs (comment-wrapping fails: inner */ closes the outer comment).

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))

CAF_BP = SOURCE / "hardware/qcom-caf/common/Android.bp"
CAF_MARKER = (
    "// AOSPA cerro: dropped duplicate rfs/mountpoint/hidl "
    "(kernel headers stay in root namespace)"
)
DROP_HIDL = {
    "hidl_vendor_qti_hardware_iop_interface",
    "hidl_vendor_qti_hardware_limits_interface",
    "hidl_vendor_qti_hardware_sigma_miracast_interface",
}
STUB_TARGETS = (
    (
        SOURCE / "hardware/qcom-caf/common/fwk-detect/Android.bp",
        "disabled duplicate of vendor/qcom/opensource/core-utils/fwk-detect",
    ),
    (
        SOURCE / "hardware/qcom-caf/common/memtrack/Android.bp",
        "disabled duplicate of device/qcom/vendor-common/memtrack",
    ),
    (
        SOURCE / "hardware/lineage/interfaces/health/aidl/Android.bp",
        "disabled duplicate of vendor/aospa/interfaces/health",
    ),
    (
        SOURCE / "hardware/lineage/interfaces/health/aidl/default/Android.bp",
        "disabled duplicate of vendor/aospa/interfaces/health",
    ),
    (
        SOURCE / "hardware/lineage/interfaces/power-libperfmgr/Android.bp",
        "disabled; cerro uses android.hardware.power-service-qti, not pixel libperfmgr",
    ),
)


def git_restore(path: Path) -> bool:
    if not path.is_file():
        return False
    r = subprocess.run(
        ["git", "checkout", "--", path.name],
        cwd=path.parent,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"[soong-isolate] git checkout failed for {path}: {r.stderr.strip()}")
        return False
    print(f"[soong-isolate] restored {path.relative_to(SOURCE)} from git")
    return True


def split_top_level_blocks(text: str) -> list[str]:
    """Split Android.bp into comment/header chunks and brace-balanced modules."""
    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        while i < n and text[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        start = i
        if text.startswith("//", i):
            nl = text.find("\n", i)
            i = n if nl < 0 else nl + 1
            chunks.append(text[start:i])
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            if i < n and text[i] == "\n":
                i += 1
            chunks.append(text[start:i])
            continue
        brace = text.find("{", i)
        if brace < 0:
            chunks.append(text[i:])
            break
        depth = 0
        j = brace
        while j < n:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        if j < n and text[j] == "\n":
            j += 1
        chunks.append(text[start:j])
        i = j
    return chunks


def module_type_and_name(block: str) -> tuple[str | None, str | None]:
    stripped = block.lstrip()
    if stripped.startswith("//") or stripped.startswith("/*"):
        return None, None
    brace = stripped.find("{")
    if brace < 0:
        return None, None
    mtype = stripped[:brace].strip()
    name = None
    for line in stripped.splitlines():
        line = line.strip().rstrip(",")
        if line.startswith("name:"):
            raw = line.split(":", 1)[1].strip().strip(",")
            if raw.startswith('"') and raw.endswith('"'):
                name = raw[1:-1]
            break
    return mtype, name


def strip_caf_duplicates(text: str) -> str:
    kept: list[str] = []
    for block in split_top_level_blocks(text):
        mtype, name = module_type_and_name(block)
        if mtype in ("install_symlink", "mkdir"):
            continue
        if mtype == "prebuilt_hidl_interfaces" and name in DROP_HIDL:
            continue
        kept.append(block)
    out = "".join(kept)
    if not out.endswith("\n"):
        out += "\n"
    return out


KERNEL_DEFAULTS_MARKER = "// AOSPA cerro: Lineage CAF expects generated_kernel_header_defaults"
KERNEL_DEFAULTS = """
""" + KERNEL_DEFAULTS_MARKER + """
cc_defaults {
    name: "generated_kernel_header_defaults",
    generated_headers: ["generated_kernel_includes"],
    export_generated_headers: ["generated_kernel_includes"],
    vendor_available: true,
    recovery_available: true,
}

cc_library_headers {
    name: "generated_kernel_headers",
    defaults: ["generated_kernel_header_defaults"],
}
"""


def isolate_caf_common() -> None:
    if not CAF_BP.is_file():
        print(f"[soong-isolate] skip missing {CAF_BP}")
        return
    text = CAF_BP.read_text()
    if CAF_MARKER not in text:
        if "soong_namespace" in text[:500] and "rfs_apq_gnss" in text:
            git_restore(CAF_BP)
            text = CAF_BP.read_text()
        text = CAF_MARKER + "\n" + strip_caf_duplicates(text)
        CAF_BP.write_text(text)
        print("[soong-isolate] stripped duplicate modules from hardware/qcom-caf/common/Android.bp")
    else:
        print("[soong-isolate] CAF common already stripped")
    ensure_kernel_header_defaults()


def ensure_kernel_header_defaults() -> None:
    text = CAF_BP.read_text()
    wired = 'generated_headers: ["generated_kernel_includes"]'
    if KERNEL_DEFAULTS_MARKER in text and wired in text:
        print("[soong-isolate] kernel header defaults already wired to generated_kernel_includes")
        return

    old_stub = (
        KERNEL_DEFAULTS_MARKER
        + "\n"
        + "cc_defaults {\n"
        + '    name: "generated_kernel_header_defaults",\n'
        + "    vendor_available: true,\n"
        + "    recovery_available: true,\n"
        + "}\n"
        + "\n"
        + "cc_library_headers {\n"
        + '    name: "generated_kernel_headers",\n'
        + '    defaults: ["generated_kernel_header_defaults"],\n'
        + "}\n"
    )
    new_block = KERNEL_DEFAULTS.lstrip("\n")
    if old_stub in text:
        CAF_BP.write_text(text.replace(old_stub, new_block))
        print("[soong-isolate] upgraded kernel header defaults → generated_kernel_includes")
        return
    if KERNEL_DEFAULTS_MARKER in text:
        # Unknown prior form: strip from marker to EOF append area and rewrite.
        start = text.index(KERNEL_DEFAULTS_MARKER)
        CAF_BP.write_text(text[:start].rstrip() + "\n" + new_block)
        print("[soong-isolate] replaced kernel header defaults block → generated_kernel_includes")
        return
    CAF_BP.write_text(text.rstrip() + "\n" + new_block)
    print("[soong-isolate] added generated_kernel_header_defaults (headers_install)")


def is_stub(text: str, reason: str) -> bool:
    if reason not in text:
        return False
    for block in split_top_level_blocks(text):
        _, name = module_type_and_name(block)
        if name is not None:
            return False
    return True


def stub_file(path: Path, reason: str) -> None:
    if not path.is_file():
        print(f"[soong-isolate] skip missing {path}")
        return
    text = path.read_text()
    stub = f"// AOSPA cerro: {reason}\n"
    if is_stub(text, reason):
        print(f"[soong-isolate] already stubbed {path.relative_to(SOURCE)}")
        return
    if "AOSPA cerro:" in text:
        # Previous comment-wrap still parsed as modules; replace.
        path.write_text(stub)
        print(f"[soong-isolate] replaced broken wrap {path.relative_to(SOURCE)}")
        return
    path.write_text(stub)
    print(f"[soong-isolate] stubbed {path.relative_to(SOURCE)}")


def main() -> None:
    isolate_caf_common()
    for path, reason in STUB_TARGETS:
        stub_file(path, reason)


if __name__ == "__main__":
    main()
