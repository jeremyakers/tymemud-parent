#!/usr/bin/env python3
"""
Apply Tar Valon road/river classification (from Westlands-Background.svg extraction) to .wld files.

This is a *north-star strict* helper intended for the Tar Valon region:
- Input TSV: zone  cell  feature   (from scripts/ubermap_tv_bgsvg_extract_cells.py)
- For each expected road/river cell, update:
  - sector_type (river -> 6, road -> 11)
  - room name line (only if it doesn't already look like road/river)

Safety rules:
- NEVER modify rooms whose current sector_type is SECT_CITY (1). This prevents accidentally
  renaming towns/inserts like Darein/Jualdhe/Luagde/Daghain/Osenrein.
- Does not attempt to remove road/river from non-expected tiles; it only applies positives.

Usage:
  python scripts/ubermap_tv_apply_bgsvg_road_river.py \
    --expected-tsv tmp/bgsvg_tv_468_469_cells.tsv \
    --wld-dir /home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld \
    --backup-dir /home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/docs/ubermap/northstar_alignment_backups/2026-01-14
"""

from __future__ import annotations

import argparse
from pathlib import Path


SECT_CITY = 1
SECT_WATER_SWIM = 6
SECT_MAIN_ROAD = 11


def is_road_name(name_line: str) -> bool:
    s = name_line.lower()
    return "road" in s or "jangai" in s or "caemlyn road" in s


def is_river_name(name_line: str) -> bool:
    s = name_line.lower()
    # includes "erinin surrounds tar valon", etc.
    return "river" in s or "erinin" in s or "alguenya" in s or "gaelin" in s or "alindrelle" in s


def road_template(_zone: int) -> str:
    return "`6The Road`7~"


def river_template(_zone: int) -> str:
    return "`^River Erinin`7~"


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="latin-1", errors="strict")
    tmp.replace(path)


def parse_sector_type(sector_line: str) -> int | None:
    parts = sector_line.split()
    if len(parts) < 3:
        return None
    try:
        return int(parts[2])
    except Exception:
        return None


def set_sector_type(sector_line: str, new_sector: int) -> tuple[str, bool]:
    parts = sector_line.split()
    if len(parts) < 3:
        return sector_line, False
    if not parts[2].isdigit():
        return sector_line, False
    old = parts[2]
    parts[2] = str(int(new_sector))
    return " ".join(parts), (old != parts[2])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected-tsv", type=Path, required=True)
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--backup-dir", type=Path, default=None)
    ap.add_argument(
        "--exclude-vnums",
        type=Path,
        default=None,
        help="Optional file listing vnums to exclude from auto-sectoring (one vnum per line; # comments allowed).",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    excluded: set[int] = set()
    if args.exclude_vnums is not None and args.exclude_vnums.exists():
        for raw in args.exclude_vnums.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.split("#", 1)[0].strip()
            if not s or s.startswith("#"):
                continue
            s = s.split()[0]
            try:
                excluded.add(int(s))
            except ValueError:
                continue

    expected: dict[int, str] = {}
    zones: set[int] = set()
    for line in args.expected_tsv.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("zone\t"):
            continue
        z_s, cell_s, feat = line.split("\t")
        z = int(z_s)
        cell = int(cell_s)
        vnum = z * 100 + cell
        if vnum in excluded:
            continue
        if feat not in ("road", "river"):
            continue
        expected[vnum] = feat
        zones.add(z)

    changed_rooms = 0
    changed_files = 0

    if args.backup_dir is not None and not args.dry_run:
        args.backup_dir.mkdir(parents=True, exist_ok=True)

    for z in sorted(zones):
        wld = args.wld_dir / f"{z}.wld"
        if not wld.exists():
            continue
        lines = wld.read_text(encoding="latin-1", errors="replace").splitlines()
        out = list(lines)
        file_changed = False

        i = 0
        while i < len(out):
            line = out[i]
            if not (line.startswith("#") and line[1:].strip().isdigit()):
                i += 1
                continue
            vnum = int(line[1:].strip())
            feat = expected.get(vnum)
            if not feat:
                i += 1
                continue
            if i + 1 >= len(out):
                break

            name_line = out[i + 1]

            # Find the sector line (first line after the desc "~" terminator).
            j = i + 2
            while j < len(out) and out[j].strip() != "~" and not out[j].endswith("~"):
                j += 1
            if j >= len(out):
                break
            j += 1  # move to sector line
            if j >= len(out):
                break

            cur_sector = parse_sector_type(out[j])
            if cur_sector is None:
                i += 1
                continue

            # Safety: do not touch city/town/inserts.
            if cur_sector == SECT_CITY:
                i += 1
                continue

            # Apply sector + name changes.
            if feat == "river":
                new_sector = SECT_WATER_SWIM
                if not is_river_name(name_line):
                    out[i + 1] = river_template(z)
                    file_changed = True
                    changed_rooms += 1
                new_sector_line, changed = set_sector_type(out[j], new_sector)
                if changed:
                    out[j] = new_sector_line
                    file_changed = True
                    changed_rooms += 1
            elif feat == "road":
                new_sector = SECT_MAIN_ROAD
                if not is_road_name(name_line):
                    out[i + 1] = road_template(z)
                    file_changed = True
                    changed_rooms += 1
                new_sector_line, changed = set_sector_type(out[j], new_sector)
                if changed:
                    out[j] = new_sector_line
                    file_changed = True
                    changed_rooms += 1

            i += 1

        if file_changed:
            if args.backup_dir is not None and not args.dry_run:
                (args.backup_dir / wld.name).write_text(
                    wld.read_text(encoding="latin-1", errors="replace"),
                    encoding="latin-1",
                    errors="strict",
                )
            if not args.dry_run:
                atomic_write(wld, "\n".join(out) + "\n")
            changed_files += 1

    print(f"tv-apply-bgsvg-road-river: changed_rooms={changed_rooms} changed_files={changed_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

