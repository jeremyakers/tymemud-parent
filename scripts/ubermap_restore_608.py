#!/usr/bin/env python3
"""Restore MM32/lib/world/wld/608.wld if missing/truncated.

We do not have git history in this workspace, so a failed write can destroy a
zone file. This script reconstructs zone 608 ("north of Aringill") by:

1) Inferring cross-zone links into 608xx from *other* zone files:
   - We scan all `MM32/lib/world/wld/*.wld` (excluding 608.wld)
   - When we see an exit destination in [60800..60899], we record the source room
     and direction, then create the reciprocal exit in 608.

2) Filling the remaining exits with a standard 10x10 grid linkage within 608.

3) Writing a minimal but valid room record format that tyme3 can load.

This is a recovery tool; the scenic pass should be run after restoration.

Usage:
  uv run python scripts/ubermap_restore_608.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import re

ROOT = Path(__file__).resolve().parents[1]
WLD_DIR = ROOT / "MM32/lib/world/wld"
ZONE = 608
OUT_PATH = WLD_DIR / f"{ZONE}.wld"

ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")


def opposite_dir(d: int) -> int:
    # 0<->2, 1<->3
    return {0: 2, 2: 0, 1: 3, 3: 1}[d]


@dataclass(frozen=True)
class ExitRef:
    src_vnum: int
    dir: int
    dest_vnum: int


def iter_room_blocks(lines: list[str]) -> list[tuple[int, int, int]]:
    """Yield (room_vnum, dir, dest_vnum) exit triples for all exits in the file."""
    out: list[tuple[int, int, int]] = []
    i = 0
    cur_room: int | None = None
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if m:
            cur_room = int(m.group(1))
            i += 1
            continue

        if cur_room is None:
            i += 1
            continue

        # Exit block begins with D0..D3 on its own line
        if len(lines[i]) == 2 and lines[i].startswith("D") and lines[i][1].isdigit():
            d = int(lines[i][1])
            # Next two lines are exit desc and keywords (both terminated by "~")
            # Then "0 <key> <dest>"
            if i + 3 < len(lines):
                dest_line = lines[i + 3]
                parts = dest_line.split()
                if len(parts) == 3 and parts[0] == "0" and parts[1].lstrip("-").isdigit() and parts[2].isdigit():
                    dest = int(parts[2])
                    out.append((cur_room, d, dest))
            i += 1
            continue

        i += 1

    return out


def infer_boundary_links() -> dict[int, dict[int, int]]:
    """Return mapping: dest_vnum(608xx) -> {dir_in_608: src_vnum}."""
    links: dict[int, dict[int, int]] = {}

    for path in sorted(WLD_DIR.glob("*.wld")):
        if path.name == f"{ZONE}.wld":
            continue
        raw = path.read_text(encoding="latin-1", errors="replace")
        lines = raw.splitlines()
        for src_room, src_dir, dest in iter_room_blocks(lines):
            if 60800 <= dest <= 60899:
                # dest is in 608; create reciprocal in 608 in opposite direction
                d_in_608 = opposite_dir(src_dir)
                links.setdefault(dest, {})[d_in_608] = src_room

    return links


def grid_neighbor(vnum: int, d: int) -> int | None:
    cell = vnum % 100
    row = cell // 10
    col = cell % 10
    if d == 0:  # north
        if row == 0:
            return None
        return vnum - 10
    if d == 2:  # south
        if row == 9:
            return None
        return vnum + 10
    if d == 1:  # east
        if col == 9:
            return None
        return vnum + 1
    if d == 3:  # west
        if col == 0:
            return None
        return vnum - 1
    raise ValueError(d)


def _name_map_from_mm32_lib_git(ref: str = "HEAD") -> dict[int, str]:
    """
    Best-effort: pull historical 608 room name lines from the MM32/lib git repo.

    This is meant for recovery cases where 608.wld is missing/truncated locally,
    but git history still contains the intended room names (forest/plains/river/road/etc).
    """
    lib_repo = ROOT / "MM32/lib"
    try:
        blob = subprocess.check_output(
            ["git", "-C", str(lib_repo), "show", f"{ref}:world/wld/608.wld"],
            text=True,
            errors="replace",
        )
    except Exception:
        return {}

    lines = blob.splitlines()
    names: dict[int, str] = {}
    for i, line in enumerate(lines[:-1]):
        if line.startswith("#608") and len(line) == 6:
            try:
                vnum = int(line[1:])
            except ValueError:
                continue
            names[vnum] = lines[i + 1]
    return names


def make_room(vnum: int, boundary: dict[int, dict[int, int]], name_map: dict[int, str]) -> list[str]:
    # Minimal outdoors room, keeping formatting consistent with existing files.
    out: list[str] = [f"#{vnum}"]
    # IMPORTANT: do not hardcode a single misleading name for every cell.
    # Prefer historical names when available; otherwise fall back to a neutral outdoor name.
    out.append(name_map.get(vnum, "`3Plains`7~"))
    out.append("`3Open land rolls away in gentle swells, grass whispering in the wind.`7")
    out.append("`7The wide sky makes distance feel closer than it truly is.`7")
    out.append("~")

    # Sector line: match common outdoor grid sizing
    out.append("608 a 2 10 10")

    exits: dict[int, int] = {}
    # Boundary links from other zones have priority.
    for d, src in boundary.get(vnum, {}).items():
        exits[d] = src
    # Fill remaining with internal grid neighbors.
    for d in (0, 1, 2, 3):
        if d in exits:
            continue
        nb = grid_neighbor(vnum, d)
        if nb is not None:
            exits[d] = nb

    for d in (0, 1, 2, 3):
        if d not in exits:
            continue
        out.append(f"D{d}")
        out.append("~")
        out.append("~")
        out.append(f"0 0 {exits[d]}")

    # Standard trailer blocks seen across these zones (keeps loader happy).
    out.append("R")
    out.append("In the Wake of an Army~")
    out.append("     `2It is immediately evident that a large number of troops")
    out.append("have passed through this area, recently.  The terrain has been")
    out.append("beaten and disturbed by great quantities of tracks, and the")
    out.append("foliage has taken a great pounding...`7")
    out.append("~")
    out.append("G")
    out.append(" 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0")
    out.append("S")

    return out


def main() -> None:
    boundary = infer_boundary_links()
    name_map = _name_map_from_mm32_lib_git("HEAD")

    rooms: list[str] = []
    for cell in range(100):
        vnum = 60800 + cell
        rooms.extend(make_room(vnum, boundary, name_map))

    # World files must end with the "$~" terminator (no trailing blank lines).
    out = "\n".join(rooms) + "\n$~\n"
    OUT_PATH.write_text(out, encoding="latin-1")
    print(f"Restored {OUT_PATH} with {100} rooms (boundary links inferred).")


if __name__ == "__main__":
    main()

