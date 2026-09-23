#!/usr/bin/env python3
# Copyright (C) 2026 AOSPA cerro
#
# After merge_dtbs.py, MTP pineapple-audio fragments still win over
# zte-cerro/zte-pineapple-common for sound + lpass-cdc. That leaves:
#   qcom,num-macros = 4  (WSA macros disabled → lpass-cdc never registers)
#   qcom,wsa-max-devs = 2
#   qcom,audio-routing with WSA/HAP widgets → snd_soc_register_card -ENODEV
#   asoc-codec-names still listing swr-haptics / wsa-codec* → card probe fails
#     even after macros/routing are fixed (cerro uses AW882xx, not WSA)
#
# Lineage zte overlays already carry the correct values earlier in the
# same DTBO; this script copies those over the later MTP copies in-place
# without a dtc round-trip (round-trip corrupts voltage cells).
#
# IMPORTANT: Do NOT shrink FDT property lengths with FDT_NOP padding.
# NOP-shrink of qcom,audio-routing hangs StartAudioService / second screen.
# For null-padded cerro routing (clean template + trailing NULs), keep the
# original length and fill leftover bytes with real AMIC widget pairs.
#
# IMPORTANT: Do NOT zero asoc-codec phandles (dtbo-WORKING-asoc2 style).
# That soft-bricks / USB-disconnect bootloops on cerro. Only rewrite
# names + routing + u32 macros.

from __future__ import annotations

import argparse
import logging
import struct
import sys
from pathlib import Path

# Real widgets from zte-cerro routing; 6*18 + 2*16 = 140 fills a 1172-1032 gap.
_PAD_P18 = b"AMIC1\0Analog Mic1\0"  # 18
_PAD_P16 = b"AMIC1\0MIC BIAS1\0"  # 16
_PAD_140 = _PAD_P18 * 6 + _PAD_P16 * 2

_GOOD_NAMES = b"msm-stub-codec.1\0lpass-cdc\0wcd939x_codec\0"
_STUB_NAME = b"msm-stub-codec.1\0"


def _find_props(data: bytearray, prop_name: bytes):
	magic, totalsize, off_dt_struct, off_dt_strings, off_mem_rsvmap, version, last_comp, boot_cpuid, size_dt_strings, size_dt_struct = struct.unpack_from(
		">10I", data, 0
	)
	if magic != 0xD00DFEED:
		raise ValueError("bad FDT magic")
	strings = bytes(data[off_dt_strings : off_dt_strings + size_dt_strings])
	nameoffs = []
	start = 0
	while True:
		i = strings.find(prop_name + b"\0", start)
		if i < 0:
			break
		# Exact match only (avoid asoc-codec matching asoc-codec-names)
		nameoffs.append(i)
		start = i + 1
	out = []
	p = off_dt_struct
	end = off_dt_struct + size_dt_struct
	while p + 4 <= end:
		tag = struct.unpack_from(">I", data, p)[0]
		if tag == 0x9:
			break
		if tag == 0x1:
			p += 4
			while data[p] != 0:
				p += 1
			p = (p + 4) & ~3
			continue
		if tag == 0x2:
			p += 4
			continue
		if tag == 0x3:
			length, nameoff = struct.unpack_from(">II", data, p + 4)
			val_off = p + 12
			prop_end = val_off + ((length + 3) & ~3)
			if nameoff in nameoffs:
				# Reject prefix collisions: asoc-codec vs asoc-codec-names
				end_name = strings.find(b"\0", nameoff)
				exact = strings[nameoff:end_name]
				if exact == prop_name:
					out.append(
						{
							"tag_off": p,
							"val_off": val_off,
							"length": length,
							"prop_end": prop_end,
						}
					)
			p = prop_end
			continue
		if tag == 0x4:
			p += 4
			continue
		break
	return out


def _widgets(val: bytes):
	parts = val.split(b"\0")
	if parts and parts[-1] == b"":
		parts = parts[:-1]
	return parts


def _fill_routing(clean: bytes, length: int) -> bytes | None:
	if length < len(clean):
		return None
	if length - len(clean) == len(_PAD_140):
		return clean + _PAD_140
	ws = [p for p in _widgets(clean) if p]
	if len(ws) % 2:
		ws = ws[:-1]
	if not ws:
		return None
	pairs = []
	for k in range(0, len(ws), 2):
		pairs.append(ws[k] + b"\0" + ws[k + 1] + b"\0")
	out = bytearray()
	pi = 0
	while True:
		piece = pairs[pi % len(pairs)]
		if len(out) + len(piece) > length:
			break
		out += piece
		pi += 1
	if len(out) != length:
		return None
	parts = _widgets(bytes(out))
	if any(p == b"" for p in parts) or len(parts) % 2:
		return None
	return bytes(out)


def _strip_codec_names(fdt: bytearray) -> bool:
	changed = False
	for ent in _find_props(fdt, b"asoc-codec-names"):
		val = bytes(fdt[ent["val_off"] : ent["val_off"] + ent["length"]])
		if b"wsa-codec" not in val and b"swr-haptics" not in val:
			continue
		if ent["length"] < len(_GOOD_NAMES):
			continue
		rem = ent["length"] - len(_GOOD_NAMES)
		pad = b""
		while len(pad) + len(_STUB_NAME) <= rem:
			pad += _STUB_NAME
		pad += b"\0" * (rem - len(pad))
		fdt[ent["val_off"] : ent["val_off"] + ent["length"]] = _GOOD_NAMES + pad
		changed = True
		logging.info("stripped wsa/swr from asoc-codec-names (%d)", ent["length"])
	return changed


def _iter_fdts(data: bytearray):
	i = 0
	while True:
		j = data.find(b"\xd0\x0d\xfe\xed", i)
		if j < 0:
			break
		totalsize = struct.unpack_from(">I", data, j + 4)[0]
		if totalsize < 40 or j + totalsize > len(data):
			i = j + 4
			continue
		yield j, totalsize
		i = j + totalsize


def fix_cerro_audio_dtbo(path: Path) -> bool:
	data = bytearray(path.read_bytes())
	changed = False

	def set_u32(name: bytes, old: int, new: int) -> None:
		nonlocal changed
		for ent in _find_props(data, name):
			if ent["length"] != 4:
				continue
			cur = struct.unpack_from(">I", data, ent["val_off"])[0]
			if cur == old:
				struct.pack_into(">I", data, ent["val_off"], new)
				changed = True
				logging.info("%s: %s %d -> %d @ %d", path.name, name.decode(), old, new, ent["val_off"])

	set_u32(b"qcom,wsa-max-devs", 2, 0)
	set_u32(b"qcom,num-macros", 4, 3)

	# Pass 1: collect a clean (no WSA/HAP) routing template across all FDTs.
	clean: bytes | None = None
	for j, totalsize in _iter_fdts(data):
		fdt = bytearray(data[j : j + totalsize])
		for ent in _find_props(fdt, b"qcom,audio-routing"):
			val = bytes(fdt[ent["val_off"] : ent["val_off"] + ent["length"]])
			if b"AMIC" not in val or b"WSA" in val or b"HAP" in val:
				continue
			parts = _widgets(val)
			empties = sum(1 for p in parts if p == b"")
			# Prefer fully-populated clean; also accept null-padded (strip empties).
			if empties == 0 and len(parts) % 2 == 0:
				if clean is None or ent["length"] < len(clean):
					clean = val
			elif empties > 0:
				nonzero = [p for p in parts if p]
				if len(nonzero) >= 2 and len(nonzero) % 2 == 0:
					cand = b"\0".join(nonzero) + b"\0"
					if clean is None or len(cand) < len(clean):
						clean = cand

	if clean is None:
		logging.warning("%s: no clean audio-routing template found", path.name)
	else:
		logging.info("%s: clean routing template len=%d", path.name, len(clean))

	# Pass 2: replace WSA/HAP (or null-padded) routings; always strip codec names.
	for j, totalsize in _iter_fdts(data):
		fdt = bytearray(data[j : j + totalsize])
		fdt_changed = False

		if clean is not None:
			for ent in _find_props(fdt, b"qcom,audio-routing"):
				val = bytes(fdt[ent["val_off"] : ent["val_off"] + ent["length"]])
				needs = (
					b"WSA" in val
					or b"HAP" in val
					or (b"\0\0" in val and b"AMIC" in val)
				)
				if not needs:
					continue
				out = _fill_routing(clean, ent["length"])
				if out is None:
					logging.warning(
						"%s@%#x: cannot fill routing len=%d from clean %d",
						path.name,
						j,
						ent["length"],
						len(clean),
					)
					continue
				fdt[ent["val_off"] : ent["val_off"] + ent["length"]] = out
				fdt_changed = True
				changed = True
				logging.info(
					"%s@%#x: replaced audio-routing len=%d (no WSA/HAP)",
					path.name,
					j,
					ent["length"],
				)

		if _strip_codec_names(fdt):
			fdt_changed = True
			changed = True

		if fdt_changed:
			data[j : j + totalsize] = fdt

	# Do NOT zero asoc-codec phandles — soft-brick / USB bootloop on cerro.

	if changed:
		path.write_bytes(data)
	return changed


def main(argv=None) -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("paths", nargs="+", type=Path, help="merged *zte-cerro*.dtbo paths")
	parser.add_argument("-v", "--verbose", action="count", default=0)
	args = parser.parse_args(argv)
	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format="%(message)s",
	)
	n = 0
	for p in args.paths:
		if fix_cerro_audio_dtbo(p):
			n += 1
	logging.info("fixed %d/%d dtbo(s)", n, len(args.paths))
	return 0


if __name__ == "__main__":
	sys.exit(main())
