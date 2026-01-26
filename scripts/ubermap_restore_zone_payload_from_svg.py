#!/usr/bin/env python3
"""
Restore room *name + sector* payloads for specific zones from a previously generated ubermap SVG.

Why:
- The SVG contains a reliable snapshot of what the exporter believed each room's title + sector were.
- This lets us surgically restore accidental local overwrites of critical zones (e.g., TV area)
  without touching exits.

Scope:
- Updates ONLY:
  - room title line (the line immediately after '#<vnum>')
  - sector number in the "<zone> <flags> <sector> <x> <y>" line
- Preserves exits/doors/extra desc/etc.

Limitations:
- The SVG does NOT contain the original room description text; we do not modify descriptions here.
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")


@dataclass(frozen=True)
class SvgRoom:
    vnum: int
    title: str  # already stripped of [vnum] prefix
    sector_label: str


SECTOR_LABEL_TO_NUM = {
    "Field": 2,
    "Forest": 3,
    "Hills": 4,
    "Mountain": 5,
    "Water (Swim)": 6,
    "Water (No Swim)": 7,
    "Underwater": 8,
    "Flying": 9,
    "Dirt road": 10,
    "Main road": 11,
    "City": 1,
    "Inside": 0,
}


RECT_RE = re.compile(
    r'<rect[^>]*\sdata-vnum="(?P<vnum>\d+)"[^>]*>.*?<title>\[(?P=vnum)\]\s(?P<title>.*?)</title>.*?<desc>(?P<desc>.*?)</desc>.*?</rect>',
    re.DOTALL,
)

SECTOR_IN_DESC_RE = re.compile(r"sector=([^&\n<]+)")


def parse_svg(svg_path: Path, zones: set[int]) -> dict[int, SvgRoom]:
    text = svg_path.read_text(encoding="utf-8", errors="replace")
    out: dict[int, SvgRoom] = {}
    for m in RECT_RE.finditer(text):
        v = int(m.group("vnum"))
        z = v // 100
        if z not in zones:
            continue
        title_raw = html.unescape(m.group("title")).strip()
        desc_raw = html.unescape(m.group("desc"))
        m2 = SECTOR_IN_DESC_RE.search(desc_raw)
        if not m2:
            continue
        sector_label = m2.group(1).strip()
        out[v] = SvgRoom(vnum=v, title=title_raw, sector_label=sector_label)
    return out


def _find_zone_line_idx(room_lines: list[str]) -> int:
    for i, ln in enumerate(room_lines):
        if re.match(r"^\d+\s+\S+\s+\d+\s+\d+\s+\d+\s*$", ln.strip()):
            return i
    raise SystemExit("Could not find room 'zone flags sector x y' line")


def load_wld_rooms(lines: list[str]) -> dict[int, tuple[int, int]]:
    spans: dict[int, tuple[int, int]] = {}
    i = 0
    while i < len(lines):
        m = ROOM_HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue
        v = int(m.group(1))
        start = i
        j = i + 1
        while j < len(lines) and lines[j].strip() != "S":
            j += 1
        if j >= len(lines):
            raise SystemExit(f"Malformed .wld: room #{v} missing terminal 'S'")
        end = j + 1
        spans[v] = (start, end)
        i = end
    return spans


def apply_to_wld(wld_path: Path, svg_rooms: dict[int, SvgRoom]) -> int:
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    spans = load_wld_rooms(lines)
    changed = 0
    for v, sr in sorted(svg_rooms.items()):
        if v not in spans:
            continue
        if v // 100 != int(wld_path.stem):
            continue
        start, end = spans[v]
        room = lines[start:end]
        # title line is immediately after header
        new_title_line = sr.title + "~"
        if room[1] != new_title_line:
            room[1] = new_title_line
            changed += 1
        # sector line
        zi = _find_zone_line_idx(room)
        parts = room[zi].split()
        if len(parts) >= 3:
            desired = SECTOR_LABEL_TO_NUM.get(sr.sector_label)
            if desired is not None and int(parts[2]) != desired:
                parts[2] = str(desired)
                room[zi] = " ".join(parts)
                changed += 1
        lines[start:end] = room
    if changed:
        wld_path.write_text("\n".join(lines) + "\n", encoding="latin-1")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", type=Path, required=True, help="Source ubermap SVG snapshot")
    ap.add_argument("--wld-dir", type=Path, required=True, help="Target world/wld directory to patch")
    ap.add_argument("--zones", required=True, help="Comma/range list (e.g. 468,469,508,509)")
    args = ap.parse_args()

    zones: set[int] = set()
    for part in args.zones.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            lo, hi = int(a), int(b)
            if hi < lo:
                lo, hi = hi, lo
            zones.update(range(lo, hi + 1))
        else:
            zones.add(int(part))

    svg_rooms = parse_svg(args.svg, zones)
    if not svg_rooms:
        raise SystemExit("No matching rooms found in SVG for requested zones.")

    total = 0
    for z in sorted(zones):
        wld = args.wld_dir / f"{z}.wld"
        if not wld.exists():
            continue
        subset = {v: r for v, r in svg_rooms.items() if v // 100 == z}
        c = apply_to_wld(wld, subset)
        print(f"{wld}: changed={c}")
        total += c
    print(f"total_changed={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

