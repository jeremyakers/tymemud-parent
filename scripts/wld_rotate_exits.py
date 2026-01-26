#!/usr/bin/env python3
"""
Rotate CircleMUD-style `.wld` exits (D0..D9) by 45° or 90°.

Primary use:
  - Rotate *internal* exits within a zone (destination vnum is in the same zone).
  - Preserve cross-zone connectors so we can rewire them intentionally.

Direction indices are taken from MM32/src/constants.c:
  0 north, 1 east, 2 south, 3 west, 4 up, 5 down, 6 northeast, 7 northwest, 8 southeast, 9 southwest

Examples:
  # Rotate internal exits in-place in zone 90 by 90° clockwise:
  uv run python scripts/wld_rotate_exits.py --in MM32/lib/world/wld/90.wld --inplace --rotate 90cw

  # Rotate internal exits for multiple zones by 45° clockwise:
  uv run python scripts/wld_rotate_exits.py --zones 90-98 --wld-dir MM32/lib/world/wld --inplace --rotate 45cw

  # Rotate "internal" exits within a *zone set* (e.g. Tar Valon spans 90-98, so 9066<->9141
  # should rotate even though it's cross-zone):
  uv run python scripts/wld_rotate_exits.py --zones 90-98 --wld-dir MM32/lib/world/wld --inplace --rotate 45cw --internal-only --internal-zone-set 90-98
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HEADER_RE = re.compile(r"^D(\d+)\s*$")


ROT_90_CW: dict[int, int] = {
    0: 1,  # N -> E
    1: 2,  # E -> S
    2: 3,  # S -> W
    3: 0,  # W -> N
    6: 8,  # NE -> SE
    8: 9,  # SE -> SW
    9: 7,  # SW -> NW
    7: 6,  # NW -> NE
}

ROT_90_CCW: dict[int, int] = {v: k for k, v in ROT_90_CW.items()}

ROT_45_CW: dict[int, int] = {
    0: 6,  # N -> NE
    6: 1,  # NE -> E
    1: 8,  # E -> SE
    8: 2,  # SE -> S
    2: 9,  # S -> SW
    9: 3,  # SW -> W
    3: 7,  # W -> NW
    7: 0,  # NW -> N
}

ROT_45_CCW: dict[int, int] = {v: k for k, v in ROT_45_CW.items()}


def _parse_zones_spec(s: str) -> set[int]:
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
            for z in range(lo, hi + 1):
                out.add(z)
        else:
            out.add(int(part))
    return out


def _rot_map(name: str) -> dict[int, int]:
    name = name.strip().lower()
    if name in ("90cw", "cw90", "90"):
        return ROT_90_CW
    if name in ("90ccw", "ccw90", "-90"):
        return ROT_90_CCW
    if name in ("45cw", "cw45", "45"):
        return ROT_45_CW
    if name in ("45ccw", "ccw45", "-45"):
        return ROT_45_CCW
    raise SystemExit(f"Unsupported --rotate value: {name!r} (use 45cw/45ccw/90cw/90ccw)")


def _skip_tilde_terminated(lines: list[str], i: int) -> int:
    """
    Given an index i that points at the *first* line of a ~-terminated block,
    return the index of the first line after the terminator.
    """
    while i < len(lines):
        if lines[i].strip() == "~":
            return i + 1
        if lines[i].endswith("~"):
            return i + 1
        i += 1
    return i


def rotate_wld_text(
    text: str,
    *,
    rotate: dict[int, int],
    zones: set[int] | None,
    internal_only: bool,
    internal_zone_set: set[int] | None,
) -> tuple[str, int]:
    """
    Returns (new_text, changed_exit_count).
    """
    lines = text.splitlines()
    out = list(lines)

    cur_vnum: int | None = None
    cur_zone: int | None = None
    changed = 0

    i = 0
    while i < len(lines):
        m = ROOM_HEADER_RE.match(lines[i])
        if m:
            cur_vnum = int(m.group(1))
            cur_zone = cur_vnum // 100
            i += 1
            continue

        m = EXIT_HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue

        if cur_zone is None:
            # Malformed file; don't crash, just move on.
            i += 1
            continue

        d = int(m.group(1))
        new_d = rotate.get(d)
        if new_d is None:
            i += 1
            continue

        if zones is not None and cur_zone not in zones:
            i += 1
            continue

        # Parse the exit block to locate the destination vnum (third int on the info line).
        j = i + 1
        j = _skip_tilde_terminated(lines, j)  # exit description
        j = _skip_tilde_terminated(lines, j)  # keyword list
        if j >= len(lines):
            i += 1
            continue

        parts = lines[j].split()
        to_room = None
        if len(parts) >= 3:
            try:
                to_room = int(parts[2])
            except ValueError:
                to_room = None

        if internal_only:
            if to_room is None or to_room <= 0:
                i += 1
                continue
            to_zone = to_room // 100
            if internal_zone_set is not None:
                if to_zone not in internal_zone_set:
                    i += 1
                    continue
            else:
                if to_zone != cur_zone:
                    i += 1
                    continue

        out[i] = f"D{new_d}"
        changed += 1
        i += 1

    return ("\n".join(out) + "\n", changed)


def main() -> int:
    ap = argparse.ArgumentParser(description="Rotate .wld exits by 45° or 90° (CW/CCW).")
    ap.add_argument("--in", dest="in_path", type=Path, default=None, help="Single input .wld file path")
    ap.add_argument("--wld-dir", type=Path, default=None, help="Directory containing <zone>.wld files")
    ap.add_argument("--zones", type=str, default=None, help="Zone list, e.g. '90,91,92' or '90-98'")
    ap.add_argument("--rotate", type=str, required=True, help="Rotation: 45cw/45ccw/90cw/90ccw")
    ap.add_argument(
        "--internal-only",
        action="store_true",
        help="Rotate only exits whose destination is 'internal' (see --internal-zone-set).",
    )
    ap.add_argument(
        "--internal-zone-set",
        type=str,
        default=None,
        help=(
            "When used with --internal-only: treat an exit as 'internal' if its destination zone is in this set "
            "(e.g. '90-98' for Tar Valon). If omitted, internal means same zone file."
        ),
    )
    ap.add_argument("--inplace", action="store_true", help="Write changes back to file(s)")
    args = ap.parse_args()

    rotate = _rot_map(args.rotate)
    zones = _parse_zones_spec(args.zones) if args.zones else None
    internal_zone_set = _parse_zones_spec(args.internal_zone_set) if args.internal_zone_set else None

    if args.in_path is None and args.wld_dir is None:
        raise SystemExit("Provide either --in <file.wld> or --wld-dir <dir> + --zones ...")

    if args.in_path is not None and args.wld_dir is not None:
        raise SystemExit("Provide only one of --in or --wld-dir")

    internal_only = bool(args.internal_only)

    paths: list[Path] = []
    if args.in_path is not None:
        paths = [args.in_path]
    else:
        if zones is None:
            raise SystemExit("--wld-dir requires --zones")
        for z in sorted(zones):
            paths.append(args.wld_dir / f"{z}.wld")

    total_changed = 0
    for p in paths:
        if not p.exists():
            raise SystemExit(f"Missing file: {p}")
        txt = p.read_text(encoding="latin-1", errors="replace")
        new_txt, changed = rotate_wld_text(
            txt,
            rotate=rotate,
            zones=zones,
            internal_only=internal_only,
            internal_zone_set=internal_zone_set,
        )
        total_changed += changed
        if args.inplace:
            if new_txt != txt:
                p.write_text(new_txt, encoding="latin-1")
        else:
            # stdout-friendly: only emit a short report.
            pass
        print(f"{p}: rotated_exits={changed}")

    print(f"TOTAL rotated_exits={total_changed}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

