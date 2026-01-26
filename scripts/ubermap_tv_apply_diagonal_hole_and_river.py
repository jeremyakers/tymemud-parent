#!/usr/bin/env python3
"""
Apply Tar Valon diagonal hole + river-ring adjustments to overland .wld files.

This script encodes the *mechanical* meaning of an overland "hole":
- Disconnect the target vnums (remove all exits from those rooms)
- Remove any exits in other rooms that point *into* those vnums (no one-way leftovers)
- Mark the target vnums as unused/reserved by rewriting their name/desc (prefix: "!unused")
- Optionally set their sector_type to SECT_INSIDE (0) to keep them out of overland visuals

It also enforces the requested river ring by setting sector_type=SECT_WATER_SWIM (6)
for the specified river vnums.

Designed to be surgical and repeatable:
- Limits work to the zones implied by the provided vnums
- Can create per-file backups before writing
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


SECT_INSIDE = 0
SECT_WATER_SWIM = 6


def _is_room_header(s: str) -> bool:
    s = s.strip()
    return s.startswith("#") and s[1:].isdigit()


def _room_vnum_from_header(s: str) -> int:
    return int(s.strip()[1:])


def _is_exit_header(s: str) -> bool:
    s = s.strip()
    return len(s) >= 2 and s[0] == "D" and s[1:].isdigit()


def _skip_tilde_block(lines: list[str], i: int) -> int:
    """
    Skip a ~-terminated text block starting at i (inclusive).
    Returns the next index after the terminator.
    """
    while i < len(lines):
        if lines[i].strip() == "~":
            return i + 1
        if lines[i].rstrip("\n").endswith("~"):
            return i + 1
        i += 1
    return i


def _parse_exit_to_room(lines: list[str], i: int) -> tuple[int | None, int]:
    """
    Given i pointing to an exit header line 'D<dir>', parse the exit block and return:
    (to_vnum or None, next_i_after_block)
    """
    i += 1  # past D*
    i = _skip_tilde_block(lines, i)  # exit desc
    i = _skip_tilde_block(lines, i)  # keywords
    if i >= len(lines):
        return None, i
    parts = lines[i].split()
    to_vnum: int | None = None
    if len(parts) >= 3:
        try:
            to_vnum = int(parts[2])
        except ValueError:
            to_vnum = None
    i += 1  # info line
    return to_vnum, i


def _rewrite_title_and_desc_as_unused(
    *, title: str, desc_lines: list[str]
) -> tuple[str, list[str]]:
    """
    Return (new_title_line, new_desc_lines_without_terminator).

    Note: engine-side `tv_room_is_unused_placeholder()` in `genwld.c` keys off "!unused"
    to filter placeholders in TV-focused visualization. We match that prefix here.
    """
    _ = title  # unused: keep signature explicit for clarity
    new_title = "!unused overland hole~\n"
    new_desc = [
        "This overland cell is reserved for a city/insert and is not used as overland terrain.\n",
        "It is intentionally disconnected so it can be repurposed later.\n",
    ]
    return new_title, new_desc


def _set_sector_type_on_sector_line(
    sector_line: str, new_sector: int
) -> tuple[str, bool]:
    """
    Update the 3rd field (sector_type) on the standard 5-field WLD sector line:
      <zone> <flag> <sector> <x> <y>
    Returns (new_line, changed).
    """
    parts = sector_line.split()
    if len(parts) != 5 or not parts[0].isdigit() or not parts[2].isdigit():
        return sector_line, False
    old = parts[2]
    parts[2] = str(int(new_sector))
    new_line = " ".join(parts) + ("\n" if sector_line.endswith("\n") else "")
    return new_line, (old != parts[2])


def apply_changes_to_wld_text(
    text: str,
    *,
    hole_vnums: set[int],
    hole_vnums_all: set[int],
    river_vnums: set[int],
    rewrite_unused: bool,
    hole_sector: int | None,
    river_sector: int,
) -> tuple[str, dict[str, int]]:
    lines = text.splitlines(keepends=True)
    exits_removed_from_holes = 0
    exits_removed_into_holes = 0
    rooms_rewritten = 0
    hole_sector_changed = 0
    river_sector_changed = 0

    found_holes: set[int] = set()
    found_rivers: set[int] = set()

    out: list[str] = []
    i = 0
    cur_vnum: int | None = None
    while i < len(lines):
        if not _is_room_header(lines[i]):
            out.append(lines[i])
            i += 1
            continue

        # Room header
        cur_vnum = _room_vnum_from_header(lines[i])
        out.append(lines[i])
        i += 1

        # Room title (single line ending with ~)
        if i >= len(lines):
            break
        title_line = lines[i]
        i += 1

        # Room description block (until ~ terminator line or line ending with ~)
        desc_lines: list[str] = []
        while i < len(lines):
            ln = lines[i]
            i += 1
            if ln.strip() == "~" or ln.rstrip("\n").endswith("~"):
                desc_term = ln
                break
            desc_lines.append(ln)
        else:
            break

        is_hole = cur_vnum in hole_vnums
        is_river = cur_vnum in river_vnums

        if is_hole:
            found_holes.add(cur_vnum)
        if is_river:
            found_rivers.add(cur_vnum)

        if is_hole and rewrite_unused:
            title_line, desc_lines = _rewrite_title_and_desc_as_unused(
                title=title_line, desc_lines=desc_lines
            )
            rooms_rewritten += 1

        out.append(title_line)
        out.extend(desc_lines)
        # Always terminate description with a clean "~" line (we've replaced content if needed).
        out.append("~\n" if desc_term.endswith("\n") else "~")

        # Sector line
        if i >= len(lines):
            break
        sector_line = lines[i]
        i += 1
        if is_hole and hole_sector is not None:
            sector_line, changed = _set_sector_type_on_sector_line(
                sector_line, hole_sector
            )
            if changed:
                hole_sector_changed += 1
        elif is_river:
            sector_line, changed = _set_sector_type_on_sector_line(
                sector_line, river_sector
            )
            if changed:
                river_sector_changed += 1
        out.append(sector_line)

        # Remainder of room (exits + other room-body sections) until 'S'
        while i < len(lines):
            if lines[i].strip() == "S":
                out.append(lines[i])
                i += 1
                break
            if _is_exit_header(lines[i]):
                to_vnum, j = _parse_exit_to_room(lines, i)

                drop = False
                if cur_vnum in hole_vnums:
                    drop = True
                    exits_removed_from_holes += 1
                elif to_vnum is not None and to_vnum in hole_vnums_all:
                    drop = True
                    exits_removed_into_holes += 1

                if drop:
                    i = j
                    continue
                out.extend(lines[i:j])
                i = j
                continue

            out.append(lines[i])
            i += 1

    missing_holes = sorted(hole_vnums - found_holes)
    missing_rivers = sorted(river_vnums - found_rivers)
    if missing_holes or missing_rivers:
        msg = []
        if missing_holes:
            msg.append(f"missing hole vnums: {missing_holes}")
        if missing_rivers:
            msg.append(f"missing river vnums: {missing_rivers}")
        raise RuntimeError("; ".join(msg))

    summary = {
        "exits_removed_from_holes": exits_removed_from_holes,
        "exits_removed_into_holes": exits_removed_into_holes,
        "rooms_rewritten": rooms_rewritten,
        "hole_sector_changed": hole_sector_changed,
        "river_sector_changed": river_sector_changed,
    }
    return ("".join(out), summary)


def parse_vnums_csv(s: str) -> set[int]:
    out: set[int] = set()
    for part in (s or "").split(","):
        part = part.strip()
        if not part:
            continue
        out.add(int(part))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--wld-dir",
        type=Path,
        required=True,
        help="Directory containing <zone>.wld files",
    )
    ap.add_argument(
        "--hole-vnums",
        type=str,
        required=True,
        help="Comma-separated vnums to turn into an overland hole",
    )
    ap.add_argument(
        "--river-vnums",
        type=str,
        required=True,
        help="Comma-separated vnums to force to river sector",
    )
    ap.add_argument(
        "--rewrite-unused",
        action="store_true",
        help="Rewrite hole rooms title/desc to !unused placeholder",
    )
    ap.add_argument(
        "--hole-sector-inside",
        action="store_true",
        help="Set hole rooms sector_type to SECT_INSIDE (0)",
    )
    ap.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Copy each touched <zone>.wld here before writing",
    )
    ap.add_argument(
        "--inplace", action="store_true", help="Write changes back to the files"
    )
    args = ap.parse_args()

    hole_vnums = parse_vnums_csv(args.hole_vnums)
    river_vnums = parse_vnums_csv(args.river_vnums)
    if not hole_vnums:
        raise SystemExit("ERROR: --hole-vnums is empty")
    if not river_vnums:
        raise SystemExit("ERROR: --river-vnums is empty")
    if hole_vnums & river_vnums:
        raise SystemExit(
            f"ERROR: vnums overlap between hole and river sets: {sorted(hole_vnums & river_vnums)}"
        )

    zones = sorted({v // 100 for v in (hole_vnums | river_vnums)})
    if args.backup_dir is not None:
        args.backup_dir.mkdir(parents=True, exist_ok=True)

    touched_files = 0
    total = {
        "exits_removed_from_holes": 0,
        "exits_removed_into_holes": 0,
        "rooms_rewritten": 0,
        "hole_sector_changed": 0,
        "river_sector_changed": 0,
    }

    for z in zones:
        wld = args.wld_dir / f"{z}.wld"
        if not wld.exists():
            raise SystemExit(f"ERROR: missing zone file: {wld}")
        txt = wld.read_text(encoding="latin-1", errors="replace")
        hole_in_zone = {v for v in hole_vnums if v // 100 == z}
        river_in_zone = {v for v in river_vnums if v // 100 == z}
        new_txt, summary = apply_changes_to_wld_text(
            txt,
            hole_vnums=hole_in_zone,
            hole_vnums_all=hole_vnums,
            river_vnums=river_in_zone,
            rewrite_unused=bool(args.rewrite_unused),
            hole_sector=(SECT_INSIDE if args.hole_sector_inside else None),
            river_sector=SECT_WATER_SWIM,
        )
        if new_txt != txt:
            touched_files += 1
            if args.backup_dir is not None:
                shutil.copy2(wld, args.backup_dir / wld.name)
            if args.inplace:
                wld.write_text(new_txt, encoding="latin-1", errors="strict")
            else:
                # dry-run: print a minimal banner to stdout
                print(f"--- {wld} (dry-run) ---")
                sys.stdout.write(new_txt)
        for k, v in summary.items():
            total[k] += v

    print(
        " ".join(
            [
                f"zones={zones}",
                f"touched_files={touched_files}",
                f"exits_removed_from_holes={total['exits_removed_from_holes']}",
                f"exits_removed_into_holes={total['exits_removed_into_holes']}",
                f"rooms_rewritten={total['rooms_rewritten']}",
                f"hole_sector_changed={total['hole_sector_changed']}",
                f"river_sector_changed={total['river_sector_changed']}",
            ]
        ),
        flush=True,
    )
    if not args.inplace:
        print(
            "NOTE: dry-run only (no files written). Pass --inplace to write changes.",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
