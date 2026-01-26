#!/usr/bin/env python3
"""
Ubermap directionality pass:

For road/river rooms, ensure the room description explicitly indicates which
direction(s) the road/river continues (north/east/south/west).

Scope is intentionally limited to the Ubermap MVP/JPG-seed zones.

Notes:
- Writes are latin-1 safe.
- Uses atomic writes (temp + rename).
- Preserves existing formatting; inserts a single short line before the room
  description terminator if needed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
WLD_DIR_DEFAULT = ROOT / "MM32/lib/world/wld"

ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HDR_RE = re.compile(r"^D([0-3])\s*$")

DIR_WORD = {0: "north", 1: "east", 2: "south", 3: "west"}

ROAD_NAME_TOKENS = ("road", "jangai", "caemlyn road")
RIVER_NAME_TOKENS = ("river", "erinin", "alguenya", "gaelin", "alindrelle")


def _consume_tilde_string(lines: list[str], start: int) -> tuple[list[str], int]:
    out: list[str] = []
    i = start
    while i < len(lines):
        out.append(lines[i])
        if lines[i].endswith("~"):
            return out, i + 1
        i += 1
    return out, i


@dataclass
class RoomRec:
    vnum: int
    name_idx: int
    desc_start_idx: int
    desc_end_idx: int  # exclusive (first line after desc string)
    sector_idx: int
    exits: dict[int, int]


def parse_rooms(lines: list[str]) -> list[RoomRec]:
    rooms: list[RoomRec] = []
    i = 0
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        name_idx = i + 1
        if name_idx >= len(lines):
            break
        desc_start = i + 2
        desc_lines, j = _consume_tilde_string(lines, desc_start)
        if not desc_lines or not desc_lines[-1].endswith("~"):
            break
        if j >= len(lines):
            break
        sector_idx = j
        # scan exits until next room header / EOF marker
        exits: dict[int, int] = {}
        k = sector_idx + 1
        while k < len(lines):
            if lines[k] == "$~":
                break
            if ROOM_HDR_RE.match(lines[k]):
                break
            em = EXIT_HDR_RE.match(lines[k])
            if em:
                d = int(em.group(1))
                _, nxt = _consume_tilde_string(lines, k + 1)
                _, nxt2 = _consume_tilde_string(lines, nxt)
                if nxt2 < len(lines):
                    parts = lines[nxt2].split()
                    if len(parts) == 3 and parts[2].lstrip("-").isdigit():
                        exits[d] = int(parts[2])
                k = nxt2 + 1
                continue
            k += 1
        rooms.append(
            RoomRec(
                vnum=vnum,
                name_idx=name_idx,
                desc_start_idx=desc_start,
                desc_end_idx=j,
                sector_idx=sector_idx,
                exits=exits,
            )
        )
        i = k
    return rooms


def room_kind(name_line: str) -> set[str]:
    name = name_line.lower()
    out: set[str] = set()
    if any(t in name for t in ROAD_NAME_TOKENS):
        out.add("road")
    if any(t in name for t in RIVER_NAME_TOKENS):
        out.add("river")
    return out


def desc_already_has_directionality(desc: str, kind: str) -> bool:
    s = desc.lower()
    # Require an explicit directional cue, not just a stray "north".
    # We accept either:
    # - "continues north" / "runs north" / "leads north"
    # - "north and south"/etc
    has_dir = any(w in s for w in (" north", " south", " east", " west"))
    if not has_dir:
        return False
    if kind == "road":
        return "road" in s and any(w in s for w in ("continues", "runs", "leads"))
    if kind == "river":
        return "river" in s and any(w in s for w in ("continues", "runs", "flows"))
    return False


def format_dir_list(dirs: list[int]) -> str:
    words = [DIR_WORD[d] for d in sorted(set(dirs))]
    if not words:
        return ""
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} and {words[1]}"
    return f"{', '.join(words[:-1])}, and {words[-1]}"


def ensure_terminator_and_newline(text: str) -> str:
    if not text.endswith("\n"):
        text += "\n"
    if not text.splitlines() or text.splitlines()[-1] != "$~":
        text += "$~\n"
    return text


def atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="latin-1", errors="strict")
    tmp.replace(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--zones",
        default="468,469,508,509,537,538,539,540,567,568,569,570,607,608,609,610,638,639,640",
        help="Comma-separated zone numbers to process (defaults to JPG-seed/MVP).",
    )
    ap.add_argument("--wld-dir", type=Path, default=WLD_DIR_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    zones = [int(z.strip()) for z in args.zones.split(",") if z.strip()]
    wld_dir: Path = args.wld_dir.resolve()
    paths = [wld_dir / f"{z}.wld" for z in zones]

    # Build a vnum->name map so we can detect road/river continuation via exits.
    vnum_to_name: dict[int, str] = {}
    file_lines: dict[int, list[str]] = {}
    file_rooms: dict[int, list[RoomRec]] = {}

    for z, p in zip(zones, paths, strict=True):
        raw = p.read_text(encoding="latin-1", errors="replace")
        lines = raw.splitlines()
        file_lines[z] = lines
        rooms = parse_rooms(lines)
        file_rooms[z] = rooms
        for r in rooms:
            if r.name_idx < len(lines):
                vnum_to_name[r.vnum] = lines[r.name_idx]

    changed_rooms = 0
    changed_files = 0

    for z in zones:
        lines = file_lines[z]
        rooms = file_rooms[z]
        file_changed = False

        # IMPORTANT: we mutate `lines` by inserting text, so process rooms in
        # reverse file order to avoid stale indices corrupting later stanzas.
        for r in sorted(rooms, key=lambda rr: rr.desc_end_idx, reverse=True):
            name_line = vnum_to_name.get(r.vnum, "")
            kinds = room_kind(name_line)
            if not kinds:
                continue

            # Build continuation dirs by checking whether the destination room is the same kind.
            dest_dirs_by_kind: dict[str, list[int]] = {"road": [], "river": []}
            for d, dest in r.exits.items():
                dest_name = vnum_to_name.get(dest, "")
                dest_kinds = room_kind(dest_name)
                for k in ("road", "river"):
                    if k in kinds and k in dest_kinds:
                        dest_dirs_by_kind[k].append(d)

            desc_lines = lines[r.desc_start_idx : r.desc_end_idx]
            desc_full = "\n".join(desc_lines)

            insert_lines: list[str] = []
            if "road" in kinds and not desc_already_has_directionality(desc_full, "road"):
                dwords = format_dir_list(dest_dirs_by_kind["road"] or list(r.exits.keys()))
                if dwords:
                    insert_lines.append(f"`7The road continues {dwords}.`7")

            if "river" in kinds and not desc_already_has_directionality(desc_full, "river"):
                dwords = format_dir_list(dest_dirs_by_kind["river"] or list(r.exits.keys()))
                if dwords:
                    insert_lines.append(f"`7The riverway continues {dwords}.`7")

            if not insert_lines:
                continue

            # Insert immediately before the final desc terminator line (which endswith "~").
            term_idx = r.desc_end_idx - 1
            if term_idx < r.desc_start_idx:
                continue
            # Avoid adding duplicates if rerun.
            existing_block = "\n".join(lines[r.desc_start_idx : r.desc_end_idx])
            if any(ins in existing_block for ins in insert_lines):
                continue

            lines[term_idx:term_idx] = insert_lines
            file_changed = True
            changed_rooms += 1

        if file_changed:
            out = "\n".join(lines) + "\n"
            out = ensure_terminator_and_newline(out)
            if not args.dry_run:
                atomic_write(wld_dir / f"{z}.wld", out)
            changed_files += 1

    print(f"directionality: changed_rooms={changed_rooms} changed_files={changed_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

