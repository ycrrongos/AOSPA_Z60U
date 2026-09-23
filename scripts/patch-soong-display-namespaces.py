#!/usr/bin/env python3
"""CLO vendor display imports → CAF sm8650; expose display for PRODUCT_PACKAGES.

Context
-------
`hardware/qcom-caf/sm8650/Android.bp` → `common/os_pickup_qssi.bp` defines the
parent soong_namespace for the whole CAF tree.

AOSPA calcite has `vendor/qcom/opensource/commonsys-intf/display` but **not**
`vendor/qcom/opensource/display` (Voltage does). 0003/0031 emptied the CAF NS
imports → composer / libdisplayconfig.qti never entered the product graph →
SF abort (0036 qseecomd, 0037 HWC).

0037 approach (Voltage-aligned, AOSPA-safe)
-------------------------------------------
1. Ensure commonsys-intf/display is a soong_namespace (Voltage has empty NS).
2. os_pickup_qssi: import that NS only (skip missing opensource/display).
3. Strip nested gralloc/libdebug NS (0031) so Adreno can import parent CAF NS.
4. vendor/qcom/common: rewrite hardware/qcom/display* imports → CAF parent.
5. Device tree adds `hardware/qcom-caf/sm8650` to PRODUCT_SOONG_NAMESPACES
   (common.mk) so PRODUCT_PACKAGES can pull composer/allocator/mapper.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))

NS_MARKER = "// AOSPA cerro: soong_namespace for vendor/qcom/common display imports"
NS_BLOCK_RE = re.compile(
    re.escape(NS_MARKER) + r"\nsoong_namespace \{\n(?:.*?\n)*?\}\n\n",
    re.DOTALL,
)

QSSI_BP = SOURCE / "hardware/qcom-caf/common/os_pickup_qssi.bp"
QSSI_MARKER = "// AOSPA cerro: CAF sm8650 NS imports commonsys-intf display (no opensource/display)"
QSSI_BODY = """soong_namespace {
    imports: [
        "vendor/qcom/opensource/commonsys-intf/display",
    ],
}
"""

COMMONSYs_INTF_NS = "vendor/qcom/opensource/commonsys-intf/display"
COMMONSYs_INTF_BP = SOURCE / "vendor/qcom/opensource/commonsys-intf/display/Android.bp"
COMMONSYs_MARKER = "// AOSPA cerro: soong_namespace (Voltage-aligned; required for CAF import)"

# Extra Android.bp that always need commonsys-intf (even without display.config-V string).
EXTRA_COMMONSYS_INTF_IMPORT = (
    SOURCE / "vendor/nubia/sm8650-common/Android.bp",
    SOURCE / "vendor/nubia/cerro/Android.bp",
)

CAF_NS_FILES = (
    SOURCE / "hardware/qcom-caf/sm8650/display/gralloc/Android.bp",
    SOURCE / "hardware/qcom-caf/sm8650/display/libdebug/Android.bp",
)

VENDOR_COMMON = SOURCE / "vendor/qcom/common"
CAF_PARENT = "hardware/qcom-caf/sm8650"

IMPORT_REPLACEMENTS = (
    ('"hardware/qcom/display"', f'"{CAF_PARENT}"'),
)
DROP_IMPORT_RELS = {
    "hardware/qcom/display/gralloc",
    "hardware/qcom/display/libdebug",
    "hardware/qcom-caf/sm8650/display/gralloc",
    "hardware/qcom-caf/sm8650/display/libdebug",
}

NEEDS_CAF_PARENT = (
    "libgralloc.qti",
    "libdisplaydebug",
    "libgralloctypes",
    "libqdutils",
    "libqdMetaData",
)


def strip_gralloc_namespace(path: Path) -> None:
    if not path.is_file():
        print(f"[soong-display] skip missing {path}")
        return
    text = path.read_text()
    if NS_MARKER not in text and not text.lstrip().startswith("soong_namespace"):
        print(f"[soong-display] already no nested NS {path.relative_to(SOURCE)}")
        return
    new, n = NS_BLOCK_RE.subn("", text, count=1)
    if n == 0 and text.lstrip().startswith("soong_namespace"):
        idx = text.find("soong_namespace")
        brace = text.find("{", idx)
        depth = 0
        j = brace
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        new = text[j:].lstrip("\n")
        n = 1
    if n:
        path.write_text(new if new.endswith("\n") else new + "\n")
        print(f"[soong-display] removed nested soong_namespace {path.relative_to(SOURCE)}")
    else:
        print(f"[soong-display] could not strip NS from {path}")


def patch_commonsys_intf_namespace() -> None:
    if not COMMONSYs_INTF_BP.is_file():
        print(f"[soong-display] skip missing {COMMONSYs_INTF_BP}")
        return
    text = COMMONSYs_INTF_BP.read_text()
    if COMMONSYs_MARKER in text or text.lstrip().startswith("soong_namespace"):
        print("[soong-display] commonsys-intf/display already namespaced")
        return
    prefix = COMMONSYs_MARKER + "\nsoong_namespace {\n}\n\n"
    COMMONSYs_INTF_BP.write_text(prefix + text)
    print("[soong-display] added soong_namespace to commonsys-intf/display")


def patch_qssi() -> None:
    if not QSSI_BP.is_file():
        print(f"[soong-display] skip missing {QSSI_BP}")
        return
    desired = QSSI_MARKER + "\n" + QSSI_BODY
    cur = QSSI_BP.read_text()
    if cur.strip() == desired.strip():
        print("[soong-display] os_pickup_qssi.bp already patched (commonsys-intf import)")
        return
    # Also replace older empty-NS patch
    QSSI_BP.write_text(desired if desired.endswith("\n") else desired + "\n")
    print("[soong-display] patched os_pickup_qssi.bp (commonsys-intf import)")


def namespace_exists(rel: str) -> bool:
    bp = SOURCE / rel / "Android.bp"
    if not bp.is_file():
        return False
    return "soong_namespace" in bp.read_text()[:4096]


def rewrite_imports_block(text: str) -> str | None:
    """Find first imports: [ ... ] after soong_namespace; return new text or None."""
    ns = text.find("soong_namespace")
    if ns < 0:
        return None
    imp = text.find("imports:", ns)
    if imp < 0:
        # soong_namespace { } with no imports — insert
        brace = text.find("{", ns)
        if brace < 0:
            return None
        insert = (
            '{\n    imports: [\n'
            f'        "{CAF_PARENT}",\n'
            "    ],\n"
        )
        return text[:brace] + insert + text[brace + 1 :]
    lb = text.find("[", imp)
    rb = text.find("]", lb)
    if lb < 0 or rb < 0:
        return None
    block = text[lb : rb + 1]
    lines = []
    for raw in block.strip("[]").splitlines():
        s = raw.strip().rstrip(",")
        if not s or s.startswith("//"):
            continue
        s = s.strip('"')
        if s in DROP_IMPORT_RELS:
            continue
        for old, new in IMPORT_REPLACEMENTS:
            if f'"{s}"' == old or s == old.strip('"'):
                s = new.strip('"')
        if s not in lines:
            lines.append(s)
    if CAF_PARENT not in lines and any(
        x in text for x in NEEDS_CAF_PARENT
    ):
        # ensure parent present when this file references CAF modules
        pass
    new_block = "[\n" + "".join(f'        "{x}",\n' for x in lines) + "    ]"
    return text[:lb] + new_block + text[rb + 1 :]


def ensure_import(text: str, ns: str) -> str:
    """Add ns to the first soong_namespace imports list if missing.

    Only inspect that imports block — do not treat a later string match
    elsewhere in a huge Android.bp as "already imported".
    """
    m = re.search(r"soong_namespace\s*\{\s*imports\s*:\s*\[(.*?)\]", text, re.S)
    if not m:
        return text
    inner = m.group(1)
    if f'"{ns}"' in inner:
        return text
    # Keep trailing newline before closing ] for readable Android.bp diffs.
    insert = f'\n        "{ns}",'
    return text[: m.end(1)] + insert + "\n    " + text[m.end(1) :].lstrip()


def patch_vendor_common() -> None:
    if not VENDOR_COMMON.is_dir():
        print(f"[soong-display] skip missing {VENDOR_COMMON}")
        return
    n_files = 0
    for bp in VENDOR_COMMON.rglob("Android.bp"):
        text = bp.read_text()
        orig = text
        if "hardware/qcom/display" in text or "hardware/qcom-caf/sm8650/display" in text:
            for old, new in IMPORT_REPLACEMENTS:
                text = text.replace(old, new)
            for drop in DROP_IMPORT_RELS:
                text = re.sub(
                    rf'\s*"{re.escape(drop)}",?\n',
                    "\n",
                    text,
                )
        # gps-legacy needs device NS
        if "libgps.utils" in text and "device/nubia/sm8650-common" not in text:
            text = ensure_import(text, "device/nubia/sm8650-common")
        # modules that need CAF parent import
        if any(m in text for m in NEEDS_CAF_PARENT):
            if f'"{CAF_PARENT}"' not in text and "soong_namespace" in text[:800]:
                text = ensure_import(text, CAF_PARENT)
            elif f'"{CAF_PARENT}"' not in text and "imports:" not in text[:800]:
                # top-level import statement style
                if re.search(r'^import\s+"', text, re.M):
                    if f'import "{CAF_PARENT}"' not in text:
                        text = f'import "{CAF_PARENT}"\n' + text
                else:
                    text = f'import "{CAF_PARENT}"\n\n' + text
        # display.config AIDL lives in commonsys-intf NS
        if "display.config-V" in text and "soong_namespace" in text[:800]:
            text = ensure_import(text, COMMONSYs_INTF_NS)
        if text != orig:
            bp.write_text(text if text.endswith("\n") else text + "\n")
            n_files += 1
            print(f"[soong-display] patched imports {bp.relative_to(SOURCE)}")
    print(f"[soong-display] vendor/qcom/common files touched: {n_files}")


def disable_nubia_fm_prebuilt() -> None:
    """AOSPA ships FM on system_ext; drop colliding vendor prebuilt module name.

    Must tolerate check_elf_files injected after name: by patch-soong-nubia-elf-check.
    """
    needle = '    name: "vendor.qti.hardware.fm@1.0",'
    marker = "// AOSPA cerro: use AOSPA system_ext FM; vendor extract would collide"
    for bp in SOURCE.glob("vendor/nubia/*/Android.bp"):
        text = bp.read_text()
        if needle not in text:
            continue
        m = re.search(
            re.escape(needle) + r".*?\n    owner:",
            text,
            re.S,
        )
        if not m:
            print(f"[soong-display] FM module shape unexpected in {bp.relative_to(SOURCE)}")
            continue
        replacement = (
            needle
            + "\n    // AOSPA cerro: check_elf allowlist misses namespaced CAF deps\n"
            + "    check_elf_files: false,\n"
            + f"    {marker}\n"
            + "    enabled: false,\n"
            + "    owner:"
        )
        if m.group(0) == replacement:
            print(f"[soong-display] FM prebuilt already disabled in {bp.relative_to(SOURCE)}")
            continue
        text = text[: m.start()] + replacement + text[m.end() :]
        bp.write_text(text if text.endswith("\n") else text + "\n")
        print(f"[soong-display] disabled vendor.qti.hardware.fm@1.0 in {bp.relative_to(SOURCE)}")


def _commonsys_intf_targets() -> list[Path]:
    """Android.bp that DT_NEEDED / shared_libs display.config AIDL."""
    seen: set[Path] = set()
    out: list[Path] = []
    roots = (
        SOURCE / "vendor/qcom/common",
        SOURCE / "vendor/nubia",
    )
    for root in roots:
        if not root.is_dir():
            continue
        for bp in root.rglob("Android.bp"):
            try:
                text = bp.read_text(errors="ignore")
            except OSError:
                continue
            if "display.config-V" not in text and bp not in EXTRA_COMMONSYS_INTF_IMPORT:
                continue
            if "soong_namespace" not in text[:1200]:
                continue
            if bp in seen:
                continue
            seen.add(bp)
            out.append(bp)
    for bp in EXTRA_COMMONSYS_INTF_IMPORT:
        if bp.is_file() and bp not in seen:
            out.append(bp)
    return out


def patch_commonsys_intf_imports() -> None:
    """Prebuilts that link display.config AIDL need commonsys-intf NS import."""
    for bp in _commonsys_intf_targets():
        text = bp.read_text()
        new = ensure_import(text, COMMONSYs_INTF_NS)
        if new == text:
            print(f"[soong-display] already imports commonsys-intf in {bp.relative_to(SOURCE)}")
            continue
        bp.write_text(new if new.endswith("\n") else new + "\n")
        print(f"[soong-display] import commonsys-intf → {bp.relative_to(SOURCE)}")


def main() -> None:
    import sys

    fm_only = "--fm-only" in sys.argv
    if not fm_only:
        patch_commonsys_intf_namespace()
        patch_qssi()
        for path in CAF_NS_FILES:
            strip_gralloc_namespace(path)
        patch_vendor_common()
        patch_commonsys_intf_imports()
    # After nubia-elf-check (apply.sh --fm-only) or best-effort here.
    disable_nubia_fm_prebuilt()


if __name__ == "__main__":
    main()
