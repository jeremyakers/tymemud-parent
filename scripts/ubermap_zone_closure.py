#!/usr/bin/env python3
"""
Compute the zone-closure set reachable from a seed set of zones.

Purpose: define the "Ubermap-connected world set" mechanically, so audits/fixes
cover everything connected to the Ubermap grid + its city connectors.

Algorithm:
- Parse all .wld files up to max_zone (default 999).
- Build zone adjacency graph via exits (room -> dest room).
- BFS from seed zones (default: Ubermap JPG/MVP zones).
- Output sorted zone list to stdout (CSV) and optionally to a file.

Notes:
- Uses latin-1 decode with replacement for robustness; does not mutate files.
- Treats any dest vnum as integer; ignores malformed stanzas best-effort.
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WLD_DIR = ROOT / "MM32/lib/world/wld"

# Default seed: the 19 JPG/MVP zones.
DEFAULT_SEEDS = [
    468,
    469,
    508,
    509,
    537,
    538,
    539,
    540,
    567,
    568,
    569,
    570,
    607,
    608,
    609,
    610,
    638,
    639,
    640,
]


def parse_exits(wld_path: Path) -> set[int]:
    """
    Return set of destination vnums referenced by exits in a .wld file.

    Very lightweight parser:
    - Find lines like "D0".."D5"
    - Skip two ~-terminated strings (desc and keywords)
    - Next non-empty line should be "flags key dest"
    - dest is last int
    """

    dests: set[int] = set()
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if len(line) == 2 and line.startswith("D") and line[1].isdigit():
            # skip desc (~) and keywords (~)
            i += 1
            # desc
            while i < len(lines) and lines[i].strip() != "~":
                i += 1
            i += 1
            # keywords
            while i < len(lines) and lines[i].strip() != "~":
                i += 1
            i += 1
            if i < len(lines):
                parts = lines[i].strip().split()
                if len(parts) >= 3:
                    try:
                        dests.add(int(parts[-1]))
                    except ValueError:
                        pass
            i += 1
            continue
        i += 1
    return dests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, default=DEFAULT_WLD_DIR)
    ap.add_argument("--max-zone", type=int, default=999)
    ap.add_argument("--seeds", type=str, default=",".join(map(str, DEFAULT_SEEDS)))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]

    # Build adjacency per zone.
    zone_to_dests: dict[int, set[int]] = {}
    for z in range(0, args.max_zone + 1):
        wld = args.wld_dir / f"{z}.wld"
        if not wld.exists():
            continue
        dest_vnums = parse_exits(wld)
        dest_zones = {v // 100 for v in dest_vnums if v >= 0}
        zone_to_dests[z] = dest_zones

    seen: set[int] = set()
    q: deque[int] = deque()
    for z in seeds:
        if z in zone_to_dests:
            seen.add(z)
            q.append(z)

    while q:
        z = q.popleft()
        for dz in zone_to_dests.get(z, set()):
            if dz not in seen and dz in zone_to_dests:
                seen.add(dz)
                q.append(dz)

    zones = sorted(seen)
    csv = ",".join(str(z) for z in zones)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(csv + "\n", encoding="utf-8")
    print(csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

