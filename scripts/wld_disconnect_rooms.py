#!/usr/bin/env python3
"""
Disconnect specific rooms in a `.wld` file by removing exits:
  - For target rooms: remove ALL D* exit blocks.
  - For all other rooms: remove any D* exit blocks whose destination is a target room.

Optional:
  - Rewrite target room name/desc to a standard placeholder.

This is useful for creating/reshaping an overland “hole” without leaving one-way exits.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HEADER_RE = re.compile(r"^D(\d+)\s*$")


def _parse_vnums_spec(s: str) -> set[int]:
    out: set[int] = set()
    for part in (s or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            lo = int(a.strip())
            hi = int(b.strip())
            if hi < lo:
                lo, hi = hi, lo
            for v in range(lo, hi + 1):
                out.add(v)
        else:
            out.add(int(part))
    return out


def _skip_tilde_block(lines: list[str], i: int) -> int:
    """
    Skip a ~-terminated block starting at i (inclusive) and return the next index.
    """
    while i < len(lines):
        if lines[i].strip() == "~":
            return i + 1
        if lines[i].rstrip("\n").endswith("~"):
            return i + 1
        i += 1
    return i


def disconnect_wld(
    text: str,
    *,
    targets: set[int],
    rewrite_targets: bool,
) -> tuple[str, int, int]:
    """
    Returns (new_text, exits_removed, rooms_rewritten).
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []

    exits_removed = 0
    rooms_rewritten = 0

    i = 0
    cur_vnum: int | None = None

    while i < len(lines):
        m = ROOM_HEADER_RE.match(lines[i].strip())
        if not m:
            out.append(lines[i])
            i += 1
            continue

        cur_vnum = int(m.group(1))
        out.append(lines[i])
        i += 1

        # name line
        if i >= len(lines):
            break
        name_out_idx = len(out)
        out.append(lines[i])
        i += 1

        # description block (until ~)
        desc_start_idx = i
        desc_end = _skip_tilde_block(lines, i)
        desc_lines = lines[desc_start_idx:desc_end]
        i = desc_end

        # sector line (single line)
        if i >= len(lines):
            break
        sector_line = lines[i]
        i += 1

        if rewrite_targets and cur_vnum in targets:
            # Overwrite name + desc, but keep sector line as-is.
            out[name_out_idx] = "`7This will be disconnected`7~\n"
            # Replace description with single-line + terminator.
            desc_lines = ["Disconnect me!\n", "~\n"]
            rooms_rewritten += 1

        out.extend(desc_lines)
        out.append(sector_line)

        # room body until 'S'
        while i < len(lines):
            s = lines[i].strip()
            if s == "S":
                out.append(lines[i])
                i += 1
                break

            m2 = EXIT_HEADER_RE.match(s)
            if not m2:
                out.append(lines[i])
                i += 1
                continue

            # Parse full exit block so we can read destination and remove it if needed.
            exit_block_start = i
            i += 1  # past D*

            # exit desc
            i = _skip_tilde_block(lines, i)
            # keywords
            i = _skip_tilde_block(lines, i)

            if i >= len(lines):
                # malformed; copy what we have and stop
                out.extend(lines[exit_block_start:i])
                break

            info_idx = i
            info = lines[info_idx].split()
            to_room = None
            if len(info) >= 3:
                try:
                    to_room = int(info[2])
                except ValueError:
                    to_room = None
            i += 1  # include info line

            drop = False
            if cur_vnum in targets:
                drop = True
            elif to_room is not None and to_room in targets:
                drop = True

            if drop:
                exits_removed += 1
                continue

            out.extend(lines[exit_block_start:i])

    return ("".join(out), exits_removed, rooms_rewritten)


def main() -> int:
    ap = argparse.ArgumentParser(description="Disconnect rooms in a .wld file by removing exits")
    ap.add_argument("--wld", type=Path, required=True, help="Path to <zone>.wld file")
    ap.add_argument("--targets", type=str, required=True, help="Comma/range list of vnums, e.g. '46937,46938,46947-46948'")
    ap.add_argument("--rewrite-targets", action="store_true", help="Rewrite target room name/desc to placeholder text")
    ap.add_argument("--inplace", action="store_true", help="Write changes back to file")
    args = ap.parse_args()

    targets = _parse_vnums_spec(args.targets)
    if not targets:
        raise SystemExit("No targets provided.")

    txt = args.wld.read_text(encoding="latin-1", errors="replace")
    new_txt, exits_removed, rooms_rewritten = disconnect_wld(
        txt,
        targets=targets,
        rewrite_targets=bool(args.rewrite_targets),
    )

    if args.inplace:
        if new_txt != txt:
            args.wld.write_text(new_txt, encoding="latin-1", errors="strict")
    else:
        print(new_txt, end="")

    print(
        f"{args.wld}: targets={len(targets)} exits_removed={exits_removed} rooms_rewritten={rooms_rewritten}",
        flush=True,
    )
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

