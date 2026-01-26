#!/usr/bin/env python3
"""
Compare ubermap.jpg road/river cells to current world room names.

Inputs:
- TSV from scripts/ubermap_jpg_extract_cells.py:
    zone <tab> cell <tab> feature

Output:
- Writes a TSV of mismatches:
    zone  cell  vnum  expected_feature  room_name
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WLD_DIR = ROOT / "MM32/lib/world/wld"


def iter_room_names(wld_path: Path) -> dict[int, str]:
    """Parse vnum -> name_line (including trailing ~) for a .wld file."""
    out: dict[int, str] = {}
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#") and line[1:].strip().isdigit():
            vnum = int(line[1:].strip())
            if i + 1 < len(lines):
                out[vnum] = lines[i + 1]
            i += 2
            continue
        i += 1
    return out


def is_road_name(name: str) -> bool:
    s = name.lower()
    return "road" in s or "jangai" in s or "caemlyn road" in s


def is_river_name(name: str) -> bool:
    s = name.lower()
    return "river" in s or "erinin" in s or "alguenya" in s or "gaelin" in s or "alindrelle" in s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected-tsv", type=Path, required=True)
    ap.add_argument("--wld-dir", type=Path, default=DEFAULT_WLD_DIR)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    expected: list[tuple[int, int, str]] = []
    for line in args.expected_tsv.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("zone\t"):
            continue
        z_s, cell_s, feat = line.split("\t")
        expected.append((int(z_s), int(cell_s), feat))

    zones = sorted({z for z, _, _ in expected})
    names: dict[int, str] = {}
    for z in zones:
        wld = args.wld_dir / f"{z}.wld"
        names.update(iter_room_names(wld))

    mismatches: list[str] = ["zone\tcell\tvnum\texpected\troom_name"]
    for z, cell, feat in expected:
        vnum = z * 100 + cell
        name = names.get(vnum, "")
        if not name:
            mismatches.append(f"{z}\t{cell:02d}\t{vnum}\t{feat}\t<MISSING>")
            continue
        ok = is_road_name(name) if feat == "road" else is_river_name(name)
        if not ok:
            # escape tabs
            safe_name = name.replace("\t", " ")
            mismatches.append(f"{z}\t{cell:02d}\t{vnum}\t{feat}\t{safe_name}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(mismatches) + "\n", encoding="utf-8")
    print(f"wrote {args.out} mismatches={len(mismatches)-1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

