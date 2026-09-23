#!/usr/bin/env python3
"""AOSPA cerro: ensure CONFIG_AWINIC_HAPTIC_HV=m in kernel oem fragment.

Voltage ships awinic haptic_hv as module `haptic.ko`. Without this config the
I2C node haptic_hv@5A never binds → HAL sees no FF device → no haptics.
Idempotent; SOURCE_DIR via argv or default source/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

MARKER = "# AOSPA cerro: awinic haptic_hv"
LINE = "CONFIG_AWINIC_HAPTIC_HV=m"


def ensure(path: Path) -> bool:
	text = path.read_text(encoding="utf-8", errors="replace")
	if "CONFIG_AWINIC_HAPTIC_HV=m" in text:
		# still ensure marker for detectability
		if MARKER not in text:
			path.write_text(text.rstrip() + f"\n\n{MARKER}\n", encoding="utf-8")
			return True
		return False
	# replace =y/=n or append
	lines = text.splitlines()
	out = []
	replaced = False
	for ln in lines:
		if ln.startswith("CONFIG_AWINIC_HAPTIC_HV="):
			out.append(LINE)
			replaced = True
		else:
			out.append(ln)
	if not replaced:
		out.append("")
		out.append("# Haptics")
		out.append(LINE)
		out.append(MARKER)
	elif MARKER not in "\n".join(out):
		out.append(MARKER)
	path.write_text("\n".join(out) + "\n", encoding="utf-8")
	return True


def main() -> int:
	ap = argparse.ArgumentParser()
	ap.add_argument(
		"source",
		nargs="?",
		default=None,
		help="SOURCE_DIR (default: <repo>/source)",
	)
	args = ap.parse_args()
	root = Path(__file__).resolve().parents[1]
	source = Path(args.source) if args.source else root / "source"
	candidates = [
		source
		/ "kernel/nubia/sm8650/arch/arm64/configs/oem/pineapple_diff.config",
		source / "kernel/nubia/sm8650/arch/arm64/configs/vendor/pineapple_diff.config",
	]
	# Also seed from prebuilts if missing entirely
	pre = root / "prebuilts-cerro/vibrator-voltage/pineapple_diff.config"
	changed = False
	hit = False
	for c in candidates:
		if c.is_file():
			hit = True
			if ensure(c):
				print(f"[patch-kernel-awinic-haptic] updated {c}")
				changed = True
			else:
				print(f"[patch-kernel-awinic-haptic] ok {c}")
	if not hit and pre.is_file():
		dest = candidates[0]
		dest.parent.mkdir(parents=True, exist_ok=True)
		dest.write_text(pre.read_text(encoding="utf-8"), encoding="utf-8")
		ensure(dest)
		print(f"[patch-kernel-awinic-haptic] seeded {dest} from prebuilts")
		changed = True
	if not hit and not pre.is_file():
		print("[patch-kernel-awinic-haptic] no pineapple_diff.config found", file=sys.stderr)
		return 1
	# Ensure driver sources exist (copy from prebuilts if tree lacks them)
	drv = source / "kernel/nubia/sm8650/drivers/misc/haptic_hv"
	src_drv = root / "prebuilts-cerro/vibrator-voltage/haptic_hv"
	if not (drv / "haptic_hv.c").is_file() and (src_drv / "haptic_hv.c").is_file():
		import shutil

		drv.parent.mkdir(parents=True, exist_ok=True)
		shutil.copytree(src_drv, drv, dirs_exist_ok=True)
		print(f"[patch-kernel-awinic-haptic] copied driver → {drv}")
		changed = True
	# Hook drivers/misc/Makefile if needed
	misc_mk = source / "kernel/nubia/sm8650/drivers/misc/Makefile"
	if misc_mk.is_file():
		mk = misc_mk.read_text(encoding="utf-8", errors="replace")
		if "haptic_hv" not in mk and "AWINIC_HAPTIC" not in mk:
			mk = mk.rstrip() + "\n\nobj-$(CONFIG_AWINIC_HAPTIC_HV) += haptic_hv/\n"
			misc_mk.write_text(mk + "\n", encoding="utf-8")
			print(f"[patch-kernel-awinic-haptic] hooked {misc_mk}")
			changed = True
	return 0 if True else 1


if __name__ == "__main__":
	sys.exit(main())
