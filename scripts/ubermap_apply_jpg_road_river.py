#!/usr/bin/env python3
"""
Apply ubermap.jpg road/river classification to room *names*.

Input TSV: zone  cell  feature   (from ubermap_jpg_extract_cells.py)

For each expected road/river cell, update the corresponding room name in
MM32/lib/world/wld/<zone>.wld if it does not already indicate that feature.

This is intentionally conservative: only the name line is changed.
After running this, run the directionality pass to ensure descriptions mention
continuation directions.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WLD_DIR = ROOT / "MM32/lib/world/wld"


def is_road_name(name: str) -> bool:
    s = name.lower()
    return "road" in s or "jangai" in s or "caemlyn road" in s


def is_river_name(name: str) -> bool:
    s = name.lower()
    return "river" in s or "erinin" in s or "alguenya" in s or "gaelin" in s or "alindrelle" in s


def road_template(zone: int) -> str:
    if zone in (607, 608, 638):
        return "`3The road between Aringill and Cairhien`7~"
    if zone in (639, 640):
        return "`6Along the Caemlyn Road`7~"
    if zone in (537, 538, 540):
        return "`3The Jangai Road`7~"
    if zone in (468, 469, 508, 509):
        return "`6The Road`7~"
    if zone in (569, 570):
        return "`3The Caemlyn Road`7~"
    if zone == 567:
        return "`3A Main Road`7~"
    if zone in (609, 610):
        return "`3A Forest Road`7~"
    return "`3The Road`7~"


def river_template(zone: int) -> str:
    # Tar Valon region and Erinin/Alindrelle fork use Erinin naming frequently.
    if zone in (468, 469, 508, 509, 539):
        return "`^River Erinin`7~"
    # Aringill region and Alguenya corridor.
    if zone in (567, 607, 608, 609, 610, 638, 639, 640):
        return "`*The Alguenya`7~"
    # Cairhien-adjacent rivers vary; use neutral "Riverway" label.
    return "`^Riverway`7~"


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="latin-1", errors="strict")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected-tsv", type=Path, required=True)
    ap.add_argument("--wld-dir", type=Path, default=DEFAULT_WLD_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    expected: dict[int, str] = {}
    zones: set[int] = set()
    for line in args.expected_tsv.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("zone\t"):
            continue
        z_s, cell_s, feat = line.split("\t")
        z = int(z_s)
        cell = int(cell_s)
        vnum = z * 100 + cell
        expected[vnum] = feat
        zones.add(z)

    changed_rooms = 0
    changed_files = 0

    for z in sorted(zones):
        wld = args.wld_dir / f"{z}.wld"
        lines = wld.read_text(encoding="latin-1", errors="replace").splitlines()
        file_changed = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#") and line[1:].strip().isdigit():
                vnum = int(line[1:].strip())
                feat = expected.get(vnum)
                if feat and i + 1 < len(lines):
                    old = lines[i + 1]
                    if feat == "road" and not is_road_name(old):
                        lines[i + 1] = road_template(z)
                        file_changed = True
                        changed_rooms += 1
                    elif feat == "river" and not is_river_name(old):
                        lines[i + 1] = river_template(z)
                        file_changed = True
                        changed_rooms += 1
                i += 2
                continue
            i += 1

        if file_changed:
            out = "\n".join(lines) + "\n"
            if not args.dry_run:
                atomic_write(wld, out)
            changed_files += 1

    print(f"apply-jpg: changed_rooms={changed_rooms} changed_files={changed_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

