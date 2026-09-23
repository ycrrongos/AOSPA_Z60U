#!/usr/bin/env python3
"""Disable make check_elf on nubia vendor prebuilts (CAF-NS blind spots).

0031 fixed soong visibility (import parent CAF NS). Make check_elf still cannot
see most CAF-NS DT_NEEDED targets; selective disable whack-a-moles forever.
Match Voltage's practical approach for this tree: point-disable across nubia
extract prebuilts so vendorimage can build. Keep soong import fix separately.

Idempotent. SOURCE_DIR defaults to repo source/.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("SOURCE_DIR", ROOT / "source"))
MARKER = "// AOSPA cerro: check_elf allowlist misses namespaced CAF deps"
BPS = (
    SOURCE / "vendor/nubia/sm8650-common/Android.bp",
    SOURCE / "vendor/nubia/cerro/Android.bp",
)
MOD_RE = re.compile(
    r"(cc_prebuilt_(?:library_shared|library_static|binary|object)\s*\{)",
    re.M,
)
OLD_MARKERS = (
    MARKER,
    "// AOSPA cerro: make check_elf cannot see namespaced CAF deps",
    "// AOSPA cerro: check_elf allowlist misses namespaced libgralloc.qti",
)


def split_modules(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for m in MOD_RE.finditer(text):
        start = m.start()
        i = text.find("{", m.end() - 1)
        if i < 0:
            continue
        depth = 0
        j = i
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    spans.append((start, j + 1))
                    break
            j += 1
    return spans


def strip_disable(block: str) -> str:
    for mk in OLD_MARKERS:
        block = re.sub(
            r"[ \t]*" + re.escape(mk) + r"\n[ \t]*check_elf_files:\s*false,\n",
            "",
            block,
        )
    block = re.sub(r"[ \t]*check_elf_files:\s*false,\n", "", block)
    return block


def ensure_disable(block: str) -> str:
    block = strip_disable(block)
    m = re.search(r'(name:\s*"[^"]+",\n)', block)
    if not m:
        return block
    insert = m.group(1) + f"    {MARKER}\n    check_elf_files: false,\n"
    return block[: m.start()] + insert + block[m.end() :]


def patch_file(path: Path) -> None:
    if not path.is_file():
        print(f"[nubia-elf] skip missing {path}")
        return
    text = path.read_text()
    spans = split_modules(text)
    if not spans:
        print(f"[nubia-elf] no prebuilts in {path.relative_to(SOURCE)}")
        return
    parts: list[str] = []
    last = 0
    added = 0
    for start, end in spans:
        parts.append(text[last:start])
        block = text[start:end]
        new_block = ensure_disable(block)
        if new_block != block:
            added += 1
        parts.append(new_block)
        last = end
    parts.append(text[last:])
    new_text = "".join(parts)
    if new_text == text:
        print(f"[nubia-elf] {path.relative_to(SOURCE)} already disabled ({len(spans)} prebuilts)")
        return
    path.write_text(new_text)
    print(f"[nubia-elf] {path.relative_to(SOURCE)} disabled={added}/{len(spans)}")


def main() -> None:
    for bp in BPS:
        patch_file(bp)


if __name__ == "__main__":
    main()
