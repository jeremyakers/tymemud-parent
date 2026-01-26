#!/usr/bin/env python3
"""
List "overland grid" zones in MM32/lib/world/wld.

Heuristic:
- .wld contains at least 95 room headers (#<vnum>)
- vnums are mostly within zone*100..zone*100+99
- contains many sector lines like: "<zone> a 2 10 10"

Outputs a CSV of zone numbers (sorted) to stdout and optional --out file.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WLD_DIR = ROOT / "MM32/lib/world/wld"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, default=DEFAULT_WLD_DIR)
    ap.add_argument("--max-zone", type=int, default=999)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    zones: list[int] = []
    for p in sorted(args.wld_dir.glob("*.wld")):
        if not p.stem.isdigit():
            continue
        z = int(p.stem)
        if z > args.max_zone:
            continue
        text = p.read_text(encoding="latin-1", errors="replace")
        room_hdrs = [ln for ln in text.splitlines() if ln.startswith("#") and ln[1:].strip().isdigit()]
        if len(room_hdrs) < 95:
            continue
        vnums = [int(ln[1:].strip()) for ln in room_hdrs]
        in_range = sum(1 for v in vnums if z * 100 <= v <= z * 100 + 99)
        if in_range < 90:
            continue
        sector_hits = text.count(f"{z} a 2 10 10")
        if sector_hits < 80:
            continue
        zones.append(z)

    zones.sort()
    csv = ",".join(str(z) for z in zones)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(csv + "\n", encoding="utf-8")
    print(csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

