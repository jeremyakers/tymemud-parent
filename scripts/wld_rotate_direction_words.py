#!/usr/bin/env python3
"""
Rotate *direction words* inside CircleMUD-style `.wld` files.

This is meant to be used after a bulk exit-direction rotation (e.g. Tar Valon 45°),
to keep room/exit descriptions that mention directions ("north", "southwest", etc.)
in sync with the new geometry.

Scope:
- Rotates direction words in:
  - room name line
  - room description block
  - exit description blocks (inside each D* exit)

Direction indices are defined in `MM32/src/constants.c`:
  0 north, 1 east, 2 south, 3 west, 6 northeast, 7 northwest, 8 southeast, 9 southwest

This script rotates *words*, not exits, so it is safe to run even with `--internal-only`
exit rotations (it won't touch the D* headers or destination vnums).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HEADER_RE = re.compile(r"^D(\d+)\s*$")


ROT_90_CW: dict[str, str] = {
    "north": "east",
    "east": "south",
    "south": "west",
    "west": "north",
    "northeast": "southeast",
    "southeast": "southwest",
    "southwest": "northwest",
    "northwest": "northeast",
}

ROT_90_CCW: dict[str, str] = {v: k for k, v in ROT_90_CW.items()}

ROT_45_CW: dict[str, str] = {
    "north": "northeast",
    "northeast": "east",
    "east": "southeast",
    "southeast": "south",
    "south": "southwest",
    "southwest": "west",
    "west": "northwest",
    "northwest": "north",
}

ROT_45_CCW: dict[str, str] = {v: k for k, v in ROT_45_CW.items()}


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


def _parse_vnums_spec(s: str) -> set[int]:
    # Same mini-syntax as zones: "9000,9026,9085" or "9000-9050"
    return _parse_zones_spec(s)


def _rot_map(name: str) -> dict[str, str]:
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


_DIR_WORD_RE = re.compile(
    r"\b(northwest|northeast|southwest|southeast|north|south|east|west)\b",
    re.IGNORECASE,
)


def _apply_case(src: str, dst: str) -> str:
    if src.isupper():
        return dst.upper()
    if src[:1].isupper():
        return dst[:1].upper() + dst[1:]
    return dst


def _rotate_line(line: str, rot: dict[str, str]) -> tuple[str, int]:
    changed = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal changed
        w = m.group(1)
        dst = rot.get(w.lower())
        if not dst:
            return w
        changed += 1
        return _apply_case(w, dst)

    new = _DIR_WORD_RE.sub(repl, line)
    return new, changed


def _skip_tilde_terminated(lines: list[str], i: int) -> int:
    while i < len(lines):
        if lines[i].strip() == "~":
            return i + 1
        if lines[i].endswith("~"):
            return i + 1
        i += 1
    return i


def rotate_words_in_wld_text(
    text: str,
    *,
    rotate: dict[str, str],
    exclude_vnums: set[int],
) -> tuple[str, int]:
    lines = text.splitlines()
    out = list(lines)
    changed = 0

    cur_vnum: int | None = None

    i = 0
    while i < len(lines):
        m = ROOM_HEADER_RE.match(lines[i])
        if m:
            cur_vnum = int(m.group(1))
            i += 1
            continue

        if cur_vnum is None or cur_vnum in exclude_vnums:
            i += 1
            continue

        # Room name line (single line, typically endswith "~")
        # We treat the *first* non-empty, non-exit header line after #vnum as room name.
        # In practice this is safe because exit blocks start later.
        if i > 0 and ROOM_HEADER_RE.match(lines[i - 1]):
            new, c = _rotate_line(lines[i], rotate)
            out[i] = new
            changed += c
            i += 1
            continue

        # Exit block: rotate only the exit description block (first ~-terminated block)
        m = EXIT_HEADER_RE.match(lines[i])
        if m:
            j = i + 1
            # exit description block
            while j < len(lines):
                new, c = _rotate_line(out[j], rotate)
                out[j] = new
                changed += c
                if out[j].strip() == "~" or out[j].endswith("~"):
                    j += 1
                    break
                j += 1
            # skip keywords (do not rotate)
            j = _skip_tilde_terminated(lines, j)
            # skip info line
            i = j + 1
            continue

        # Room description block lines: rotate any line that is not part of an exit block.
        # Heuristic: rotate until we hit a line that terminates the description ("~"),
        # but only when we're within the room header -> desc segment. We don't try to
        # fully parse the whole room record here; we just rotate direction words on
        # free-form text lines.
        # This is intentionally conservative: we only rotate when the line contains a
        # direction word to avoid touching unrelated sections.
        if _DIR_WORD_RE.search(lines[i]):
            new, c = _rotate_line(lines[i], rotate)
            out[i] = new
            changed += c

        i += 1

    return ("\n".join(out) + "\n", changed)


def main() -> int:
    ap = argparse.ArgumentParser(description="Rotate direction words inside .wld text blocks.")
    ap.add_argument("--wld-dir", type=Path, required=True, help="Directory containing <zone>.wld files")
    ap.add_argument("--zones", type=str, required=True, help="Zone list, e.g. '90,91,92' or '90-98'")
    ap.add_argument("--rotate", type=str, required=True, help="Rotation: 45cw/45ccw/90cw/90ccw")
    ap.add_argument(
        "--exclude-vnums",
        type=str,
        default="",
        help="Comma/range list of vnums to skip (e.g. '9000,9026,9085' or '9000-9050')",
    )
    ap.add_argument("--inplace", action="store_true", help="Write changes back to file(s)")
    args = ap.parse_args()

    rotate = _rot_map(args.rotate)
    zones = _parse_zones_spec(args.zones)
    exclude_vnums = _parse_vnums_spec(args.exclude_vnums) if args.exclude_vnums.strip() else set()

    total_changed = 0
    for z in sorted(zones):
        p = args.wld_dir / f"{z}.wld"
        if not p.exists():
            raise SystemExit(f"Missing file: {p}")
        txt = p.read_text(encoding="latin-1", errors="replace")
        new_txt, changed = rotate_words_in_wld_text(txt, rotate=rotate, exclude_vnums=exclude_vnums)
        total_changed += changed
        if args.inplace and new_txt != txt:
            p.write_text(new_txt, encoding="latin-1")
        print(f"{p}: rotated_words={changed}")

    print(f"TOTAL rotated_words={total_changed}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

