#!/usr/bin/env python3
"""
Apply explicit, human-reviewed sector_type overrides to world .wld files.

This is intentionally *not* heuristic: you provide the exact vnum->sector mapping.

Input TSV format:
  vnum    new_sector  note(optional)

The script will:
  - locate the room block by '#<vnum>'
  - find the sector/flags line after the description terminator
  - replace only the sector_type (3rd field) while preserving other fields
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Override:
    vnum: int
    new_sector: int
    note: str = ""


def parse_overrides(path: Path) -> Dict[int, Override]:
    overrides: Dict[int, Override] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row:
                continue
            if row[0].strip().startswith("#") or row[0].strip().lower() == "vnum":
                continue
            vnum = int(row[0].strip())
            new_sector = int(row[1].strip())
            note = row[2].strip() if len(row) >= 3 else ""
            overrides[vnum] = Override(vnum=vnum, new_sector=new_sector, note=note)
    return overrides


def apply_to_file(wld_path: Path, overrides: Dict[int, Override]) -> Tuple[int, int]:
    """
    Returns (rooms_seen, rooms_changed) for this file.
    """
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines(keepends=True)

    changed = 0
    seen = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#") and line[1:].strip().isdigit():
            vnum = int(line[1:].strip())
            ov = overrides.get(vnum)
            if not ov:
                i += 1
                continue
            seen += 1

            # Name line is i+1; description begins i+2; description ends at a line that is exactly "~\n" or "~".
            j = i + 2
            while j < len(lines):
                if lines[j].strip() == "~":
                    j += 1
                    break
                # Some rare files end description with a line containing '~' at end; treat that as terminator.
                if lines[j].rstrip("\n").endswith("~"):
                    j += 1
                    break
                j += 1
            if j >= len(lines):
                i += 1
                continue

            sector_idx = j
            parts = lines[sector_idx].strip().split()
            if len(parts) < 3:
                i += 1
                continue
            cur_sector = parts[2]
            if cur_sector != str(ov.new_sector):
                parts[2] = str(ov.new_sector)
                # Preserve trailing newline from original line.
                nl = "\n" if lines[sector_idx].endswith("\n") else ""
                lines[sector_idx] = " ".join(parts) + nl
                changed += 1
            i = sector_idx + 1
            continue
        i += 1

    if changed:
        wld_path.write_text("".join(lines), encoding="latin-1", errors="strict")
    return seen, changed


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply vnum->sector_type overrides to .wld files")
    ap.add_argument("--overrides", type=Path, required=True, help="TSV: vnum<TAB>new_sector<TAB>note(optional)")
    ap.add_argument("--wld-dir", type=Path, required=True, help="Directory containing <zone>.wld files")
    args = ap.parse_args()

    overrides = parse_overrides(args.overrides)
    if not overrides:
        raise SystemExit("No overrides found.")

    zones = sorted({v // 100 for v in overrides})
    total_seen = 0
    total_changed = 0
    for z in zones:
        wld = args.wld_dir / f"{z}.wld"
        if not wld.exists():
            print(f"missing_wld {wld}")
            continue
        seen, changed = apply_to_file(wld, overrides)
        total_seen += seen
        total_changed += changed
        print(f"{wld.name}\tseen={seen}\tchanged={changed}")

    print(f"TOTAL\tseen={total_seen}\tchanged={total_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

