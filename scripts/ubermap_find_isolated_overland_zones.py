#!/usr/bin/env python3
"""
Find "overland-like" zones (10x10) that exist but are isolated:
- no cross-zone exits from the zone
- no inbound exits from other zones into the zone

This helps identify zones like 536 that may be intended for future expansion.

Output TSV:
  zone  rooms  outbound_cross_zone_exits  inbound_from_other_zones
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
WLD_DIR = ROOT / "MM32/lib/world/wld"

ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HDR_RE = re.compile(r"^D([0-5])\s*$")


def consume_tilde_string(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines):
        if lines[i].endswith("~") or lines[i].strip() == "~":
            return i + 1
        i += 1
    return i


def iter_exit_dests(wld_path: Path) -> list[tuple[int, int, int, int]]:
    b = wld_path.read_bytes()
    raw = b.decode("latin-1", errors="replace")
    lines = raw.splitlines()
    out: list[tuple[int, int, int, int]] = []
    cur_vnum: int | None = None
    i = 0
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if m:
            cur_vnum = int(m.group(1))
            i += 1
            continue
        em = EXIT_HDR_RE.match(lines[i])
        if em and cur_vnum is not None:
            d = int(em.group(1))
            j = consume_tilde_string(lines, i + 1)
            j = consume_tilde_string(lines, j)
            if j < len(lines):
                parts = lines[j].split()
                if len(parts) >= 3 and parts[-1].lstrip("-").isdigit():
                    dest = int(parts[-1])
                    if dest >= 0:
                        out.append((cur_vnum, d, dest, dest // 100))
            i = j + 1
            continue
        i += 1
    return out


def is_overland_10x10(path: Path) -> tuple[bool, int]:
    text = path.read_text(encoding="latin-1", errors="replace")
    room_hdrs = [ln for ln in text.splitlines() if ln.startswith("#") and ln[1:].strip().isdigit()]
    if len(room_hdrs) < 95:
        return False, len(room_hdrs)
    z = int(path.stem)
    vnums = [int(ln[1:].strip()) for ln in room_hdrs]
    in_range = sum(1 for v in vnums if z * 100 <= v <= z * 100 + 99)
    if in_range < 90:
        return False, len(room_hdrs)
    return True, len(room_hdrs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--min-zone", type=int, default=0)
    ap.add_argument("--max-zone", type=int, default=999)
    args = ap.parse_args()

    # Build inbound counts for all zones via exit destinations.
    inbound: dict[int, set[int]] = {}
    outbound_cross: dict[int, int] = {}
    rooms_count: dict[int, int] = {}

    overland_zones: set[int] = set()
    for p in sorted(WLD_DIR.glob("*.wld")):
        if not p.stem.isdigit():
            continue
        z = int(p.stem)
        if not (args.min_zone <= z <= args.max_zone):
            continue
        ok, rc = is_overland_10x10(p)
        if not ok:
            continue
        rooms_count[z] = rc
        overland_zones.add(z)

    for z in sorted(overland_zones):
        p = WLD_DIR / f"{z}.wld"
        cross = 0
        for src_vnum, _d, dest, dest_zone in iter_exit_dests(p):
            if dest_zone != z:
                cross += 1
            # inbound record
            inbound.setdefault(dest_zone, set()).add(z)
        outbound_cross[z] = cross

    rows: list[str] = ["zone\trooms\toutbound_cross_zone_exits\tinbound_from_other_zones"]
    for z in sorted(overland_zones):
        in_sources = {s for s in inbound.get(z, set()) if s != z}
        if outbound_cross.get(z, 0) == 0 and len(in_sources) == 0:
            rows.append(f"{z}\t{rooms_count.get(z, 0)}\t0\t0")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {args.out} isolated_overland_zones={len(rows)-1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

