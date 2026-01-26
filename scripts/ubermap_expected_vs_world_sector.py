#!/usr/bin/env python3
"""
Compare ubermap.jpg-derived expected terrain to current world sector types.

This script is READ-ONLY with respect to world files: it produces a TSV report
of mismatches so humans can manually verify and apply surgical edits.

Input:
  - A TSV produced by scripts/ubermap_jpg_extract_cells.py --mode terrain

Output:
  - TSV rows describing where (expected_sector != current_sector)
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple


FEATURE_TO_EXPECTED_SECTOR: dict[str, Optional[int]] = {
    # ubermap.jpg legend → CircleMUD sector types (MM32/src/structs.h)
    "plains": 2,  # SECT_FIELD
    "forest_light": 3,  # SECT_FOREST
    "forest_dense": 3,  # SECT_FOREST
    "hills": 4,  # SECT_HILLS
    "dragonmount": 5,  # treat as SECT_MOUNTAIN (very steep)
    "mountain": 5,  # SECT_MOUNTAIN
    "river": 6,  # SECT_WATER_SWIM
    "road": 11,  # SECT_MAIN_ROAD
    "town": 1,  # SECT_CITY
    "insert": 1,  # SECT_CITY
    # Not a terrain sector; usually a disconnected/reserved cell.
    "nothing": None,
    "unknown": None,
}


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")


def iter_rooms(wld_path: Path) -> Iterator[Tuple[int, str, str, str]]:
    """
    Yield (vnum, name_line, desc_text, sector_line) for each room in a .wld file.

    Notes:
    - We keep raw name_line (includes trailing '~') because it is a stable anchor.
    - desc_text is returned as a single string with '\n' separators (no trailing '~').
    """
    txt = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(txt):
        m = ROOM_HEADER_RE.match(txt[i].strip())
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        if i + 1 >= len(txt):
            break
        name_line = txt[i + 1].rstrip("\n")

        # Description is lines until a line that ends with '~' OR a line that is just '~'.
        desc_lines: list[str] = []
        j = i + 2
        while j < len(txt):
            line = txt[j]
            if line.strip() == "~":
                j += 1
                break
            # Some files may place '~' at end-of-line; treat that as terminator too.
            if line.endswith("~"):
                desc_lines.append(line[:-1])
                j += 1
                break
            desc_lines.append(line)
            j += 1
        if j >= len(txt):
            break
        sector_line = txt[j].strip()
        desc_text = "\n".join(desc_lines)

        yield (vnum, name_line, desc_text, sector_line)

        # Advance to next room; keep scanning for next "#"
        i = j + 1


def parse_sector_type(sector_line: str) -> Optional[int]:
    """
    Parse the 'sector_type' integer from a room's sector/flags line.

    Expected format (MM32 db.c parse_room):
      <zone> <flags> <sector> [<width> <height>]
    """
    parts = sector_line.split()
    if len(parts) < 3:
        return None
    try:
        return int(parts[2])
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare ubermap.jpg terrain to world sector types")
    ap.add_argument("--expected-tsv", type=Path, required=True, help="TSV from ubermap_jpg_extract_cells.py --mode terrain")
    ap.add_argument("--wld-dir", type=Path, required=True, help="MM32/lib/world/wld directory")
    ap.add_argument("--out", type=Path, required=True, help="Output mismatch TSV")
    ap.add_argument(
        "--coords-tsv",
        type=Path,
        default=None,
        help="Optional ubermap_coords TSV; if provided, only rooms with physical=1 are compared",
    )
    args = ap.parse_args()

    expected: Dict[int, Tuple[int, str, int]] = {}
    with args.expected_tsv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            zone = int(row["zone"])
            cell = int(row["cell"])
            feat = row["feature"]
            dist2 = int(row.get("dist2", "0") or "0")
            vnum = zone * 100 + cell
            expected[vnum] = (zone, feat, dist2)

    physical_ok: Optional[set[int]] = None
    if args.coords_tsv is not None:
        physical_ok = set()
        with args.coords_tsv.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f, delimiter="\t")
            for row in r:
                try:
                    if (row.get("physical") or "") != "1":
                        continue
                    physical_ok.add(int(row["vnum"]))
                except Exception:
                    continue

    out_lines: list[list[str]] = []
    out_lines.append(
        [
            "vnum",
            "zone",
            "cell",
            "feature",
            "dist2",
            "current_sector",
            "expected_sector",
            "name",
            "sector_line",
        ]
    )

    zones = sorted({z for (z, _, _) in expected.values()})
    for z in zones:
        wld = args.wld_dir / f"{z}.wld"
        if not wld.exists():
            continue
        for vnum, name_line, _desc, sector_line in iter_rooms(wld):
            exp = expected.get(vnum)
            if not exp:
                continue
            if physical_ok is not None and vnum not in physical_ok:
                continue
            zone, feat, dist2 = exp
            exp_sector = FEATURE_TO_EXPECTED_SECTOR.get(feat, None)
            if exp_sector is None:
                continue
            cur_sector = parse_sector_type(sector_line)
            if cur_sector is None:
                continue
            if cur_sector != exp_sector:
                cell = vnum % 100
                out_lines.append(
                    [
                        str(vnum),
                        str(zone),
                        f"{cell:02d}",
                        feat,
                        str(dist2),
                        str(cur_sector),
                        str(exp_sector),
                        name_line.replace("\t", " ").strip(),
                        sector_line.replace("\t", " ").strip(),
                    ]
                )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join("\t".join(r) for r in out_lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out} mismatches={len(out_lines)-1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

