#!/usr/bin/env python3
"""
Surgically add missing exit blocks to existing room records in .wld files.

This does *not* rebuild the file; it inserts a minimal exit stanza directly
after the room's sector line, preserving existing formatting.

Exit block inserted:
  D<dir>
  ~
  ~
  0 0 <dest_vnum>
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class ExitSpec:
    room_vnum: int
    direction: int
    dest_vnum: int


def parse_spec(s: str) -> ExitSpec:
    # format: ROOM:D:DEST (e.g., 53746:2:53756)
    try:
        room_s, d_s, dest_s = s.split(":", 2)
        return ExitSpec(room_vnum=int(room_s), direction=int(d_s), dest_vnum=int(dest_s))
    except Exception as e:  # noqa: BLE001 - CLI parsing
        raise ValueError(f"Bad --add spec {s!r}; expected ROOM:D:DEST") from e


def find_room_sector_line_idx(lines: list[str], room_vnum: int) -> int:
    """Return index of the sector line for the room (line after desc '~')."""
    hdr = f"#{room_vnum}"
    for i, line in enumerate(lines):
        if line.strip() != hdr:
            continue
        # name line: i+1
        j = i + 2  # first desc line
        # description is a ~-terminated string (may span lines)
        while j < len(lines):
            if lines[j].endswith("~"):
                j += 1
                break
            j += 1
        if j >= len(lines):
            raise ValueError(f"Room #{room_vnum}: unterminated desc string")
        sector_idx = j
        if sector_idx >= len(lines):
            raise ValueError(f"Room #{room_vnum}: missing sector line")
        return sector_idx
    raise ValueError(f"Room #{room_vnum}: header not found")


def room_has_exit(lines: list[str], sector_idx: int, direction: int) -> bool:
    """Scan forward from sector line to the next room header and check for D<dir>."""
    needle = f"D{direction}"
    i = sector_idx + 1
    while i < len(lines):
        if lines[i].startswith("#"):
            return False
        if lines[i].strip() == needle:
            return True
        if lines[i] == "$~":
            return False
        i += 1
    return False


def insert_exit(lines: list[str], sector_idx: int, direction: int, dest_vnum: int) -> None:
    """Insert exit block immediately after sector line."""
    stanza = [f"D{direction}", "~", "~", f"0 0 {dest_vnum}"]
    insert_at = sector_idx + 1
    lines[insert_at:insert_at] = stanza


def ensure_terminator_and_newline(text: str) -> str:
    if not text.endswith("\n"):
        text += "\n"
    if not text.splitlines() or text.splitlines()[-1] != "$~":
        if not text.endswith("\n"):
            text += "\n"
        text += "$~\n"
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld", type=Path, required=True)
    ap.add_argument(
        "--add",
        action="append",
        default=[],
        help="Add an exit: ROOM:D:DEST (repeatable). Example: --add 53746:2:53756",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    specs = [parse_spec(s) for s in args.add]
    if not specs:
        print("No --add specs provided", file=sys.stderr)
        return 2

    wld: Path = args.wld
    raw = wld.read_text(encoding="latin-1", errors="replace")
    lines = raw.splitlines()

    changed = 0
    for spec in specs:
        sector_idx = find_room_sector_line_idx(lines, spec.room_vnum)
        if room_has_exit(lines, sector_idx, spec.direction):
            continue
        insert_exit(lines, sector_idx, spec.direction, spec.dest_vnum)
        changed += 1

    out = "\n".join(lines) + "\n"
    out = ensure_terminator_and_newline(out)

    if args.dry_run:
        print(f"dry-run: would add {changed} exits to {wld.name}")
        return 0

    wld.write_text(out, encoding="latin-1")
    print(f"added {changed} exits to {wld.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

