#!/usr/bin/env python3
"""
Audit overland zones 537–640 against ubermap.jpg-derived expected terrain.

This is a READ/REPORT tool:
- It does NOT modify any world files.
- It emits TSV snapshots of current world state (sector/title/exits) for:
  - a primary wld-dir (typically a git worktree)
  - an optional reference wld-dir (typically /home/jeremy/cursor/tymemud/MM32/lib/world/wld)

Key design points (per project guidance):
- Never rely on keyword matches against color-coded names; we always key by vnum.
- We emit both raw title and a color-stripped title for human review.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")
EXIT_DIR_RE = re.compile(r"^D([0-9])\s*$")
EXIT_TO_RE = re.compile(r"^\s*\d+\s+\d+\s+(-?\d+)\s*$")

# Matches common MUD color code prefixes used in this codebase.
# - Backtick codes: `0..`9, `^, `&, `#, `@, etc.
# - Ampersand codes: &0..&9 etc.
COLOR_CODE_RE = re.compile(r"(`.|\&.)")


def strip_color(s: str) -> str:
    return COLOR_CODE_RE.sub("", s)


@dataclass(frozen=True)
class RoomSnap:
    vnum: int
    zone: int
    cell: int
    sector: int | None
    sector_line: str
    title_raw: str
    title_stripped: str
    exit_count: int
    exit_non_overland_count: int
    extra_desc_count: int


def _parse_sector(sector_line: str) -> int | None:
    parts = sector_line.split()
    if len(parts) < 3:
        return None
    try:
        return int(parts[2])
    except Exception:
        return None


def iter_room_snaps(wld_path: Path) -> Iterator[RoomSnap]:
    txt = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(txt):
        m = ROOM_HEADER_RE.match(txt[i].strip())
        if not m:
            i += 1
            continue

        vnum = int(m.group(1))
        zone = vnum // 100
        cell = vnum % 100
        if i + 1 >= len(txt):
            break
        title_raw = txt[i + 1]

        # Description: consume until the terminator '~' (either as a line by itself, or EOL).
        j = i + 2
        while j < len(txt):
            line = txt[j]
            if line.strip() == "~":
                j += 1
                break
            if line.endswith("~"):
                j += 1
                break
            j += 1
        if j >= len(txt):
            break

        sector_line = txt[j].strip()
        sector = _parse_sector(sector_line)
        j += 1

        exit_count = 0
        exit_non_overland = 0
        extra_desc_count = 0

        # Parse room body until 'S' end marker or next room header.
        k = j
        while k < len(txt):
            line = txt[k].strip()
            if line == "S":
                k += 1
                break
            if ROOM_HEADER_RE.match(line):
                break

            mdir = EXIT_DIR_RE.match(line)
            if mdir:
                # Scan ahead a few lines to find the "0 0 <to_room>" line for this exit.
                to_room: int | None = None
                for look in range(1, 8):
                    if k + look >= len(txt):
                        break
                    mto = EXIT_TO_RE.match(txt[k + look].strip())
                    if mto:
                        try:
                            to_room = int(mto.group(1))
                        except Exception:
                            to_room = None
                        break
                exit_count += 1
                if to_room is not None:
                    # Overland zones we care about are 537–640 inclusive.
                    tz = to_room // 100 if to_room >= 0 else -1
                    if not (537 <= tz <= 640):
                        exit_non_overland += 1
                k += 1
                continue

            if line == "E":
                extra_desc_count += 1

            k += 1

        yield RoomSnap(
            vnum=vnum,
            zone=zone,
            cell=cell,
            sector=sector,
            sector_line=sector_line,
            title_raw=title_raw,
            title_stripped=strip_color(title_raw),
            exit_count=exit_count,
            exit_non_overland_count=exit_non_overland,
            extra_desc_count=extra_desc_count,
        )

        i = k


def write_snapshot(wld_dir: Path, zones: list[int], out_path: Path) -> None:
    rows: list[list[str]] = []
    rows.append(
        [
            "vnum",
            "zone",
            "cell",
            "sector",
            "exit_count",
            "exit_non_overland_count",
            "extra_desc_count",
            "title_raw",
            "title_stripped",
            "sector_line",
        ]
    )
    for z in zones:
        wld = wld_dir / f"{z}.wld"
        if not wld.exists():
            continue
        for snap in iter_room_snaps(wld):
            rows.append(
                [
                    str(snap.vnum),
                    str(snap.zone),
                    f"{snap.cell:02d}",
                    "" if snap.sector is None else str(snap.sector),
                    str(snap.exit_count),
                    str(snap.exit_non_overland_count),
                    str(snap.extra_desc_count),
                    snap.title_raw.replace("\t", " "),
                    snap.title_stripped.replace("\t", " "),
                    snap.sector_line.replace("\t", " "),
                ]
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Snapshot world state for zones 537–640")
    ap.add_argument("--expected-terrain-tsv", type=Path, required=True)
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ref-wld-dir", type=Path, default=None)
    ap.add_argument("--ref-out", type=Path, default=None)
    args = ap.parse_args()

    # Determine zones from expected TSV (so we stay aligned to whatever ubermap.jpg contains).
    zones_set: set[int] = set()
    with args.expected_terrain_tsv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            try:
                z = int(row["zone"])
            except Exception:
                continue
            if 537 <= z <= 640:
                zones_set.add(z)
    zones = sorted(zones_set)

    write_snapshot(args.wld_dir, zones, args.out)
    print(f"wrote {args.out} zones={len(zones)}")

    if args.ref_wld_dir is not None:
        if args.ref_out is None:
            raise SystemExit("--ref-wld-dir requires --ref-out")
        write_snapshot(args.ref_wld_dir, zones, args.ref_out)
        print(f"wrote {args.ref_out} zones={len(zones)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

