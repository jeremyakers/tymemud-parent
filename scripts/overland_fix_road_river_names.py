#!/usr/bin/env python3
"""
Fix overland road/river *titles + descriptions* when sectors are correct but the
payload text drifted (e.g., after zone payload swaps).

This script is intentionally conservative:
- Only touches rooms whose sector indicates ROAD or WATER but whose name does not.
- Preserves exits and all non-name/description payload.

Strategy:
- WATER: classify each water room as Alguenya vs Erinin by nearest-seed BFS on the
  water graph, seeded from known-correct upstream tiles.
- ROAD: for road rooms with bad titles/descriptions, generate a deterministic
  "The Road runs ..." title based on neighboring road tiles, and a generic road
  description.

Designed for the 537-640 restore fallout:
- Fix zone 638 water tiles (Alguenya + Erinin spillover from zone 608).
- Fix zone 539/540 road+river tiles losing 'Road'/'River' naming.
"""

from __future__ import annotations

import argparse
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")

# Directions (CircleMUD)
DIRS = {
    0: "north",
    1: "east",
    2: "south",
    3: "west",
    4: "up",
    5: "down",
    6: "northeast",
    7: "northwest",
    8: "southeast",
    9: "southwest",
}


@dataclass
class Room:
    vnum: int
    name: str
    desc_lines: list[str]  # includes trailing "~"
    sector: int
    exits: dict[int, int]
    # location in file lines:
    file: Path
    start: int
    end: int


def _read_lines(p: Path) -> list[str]:
    return p.read_text(encoding="latin-1", errors="replace").splitlines()


def _write_lines(p: Path, lines: list[str]) -> None:
    p.write_text("\n".join(lines) + "\n", encoding="latin-1")


def _parse_exit_to(lines: list[str], i: int) -> tuple[int | None, int]:
    # lines[i] is "D<d>"
    j = i + 1
    # skip desc (~-terminated)
    while j < len(lines) and not (lines[j].strip() == "~" or lines[j].endswith("~")):
        j += 1
    j += 1
    # skip keywords (~-terminated)
    while j < len(lines) and not (lines[j].strip() == "~" or lines[j].endswith("~")):
        j += 1
    j += 1
    if j >= len(lines):
        return None, j
    parts = lines[j].split()
    to = None
    if len(parts) >= 3:
        try:
            to = int(parts[2])
        except Exception:
            to = None
    return to, j + 1


def load_rooms(wld_dir: Path, zones: set[int]) -> dict[int, Room]:
    rooms: dict[int, Room] = {}
    for z in sorted(zones):
        p = wld_dir / f"{z}.wld"
        if not p.exists():
            continue
        lines = _read_lines(p)
        i = 0
        while i < len(lines):
            m = ROOM_HEADER_RE.match(lines[i].strip())
            if not m:
                i += 1
                continue
            v = int(m.group(1))
            start = i
            name = lines[i + 1]
            # desc block
            j = i + 2
            while j < len(lines) and lines[j].strip() != "~":
                j += 1
            # include terminator
            j += 1
            desc_span_start = i + 2
            desc_lines = lines[desc_span_start:j]
            zone_line = lines[j].strip()
            parts = zone_line.split()
            sector = int(parts[2]) if len(parts) >= 3 else -1
            exits: dict[int, int] = {}
            k = j + 1
            while k < len(lines) and lines[k].strip() != "S":
                if re.match(r"^D\d+\s*$", lines[k].strip()):
                    d = int(lines[k].strip()[1:])
                    to, k2 = _parse_exit_to(lines, k)
                    if to is not None:
                        exits[d] = to
                    k = k2
                    continue
                k += 1
            end = k + 1 if k < len(lines) else len(lines)
            rooms[v] = Room(
                vnum=v,
                name=name,
                desc_lines=desc_lines,
                sector=sector,
                exits=exits,
                file=p,
                start=start,
                end=end,
            )
            i = end
    return rooms


def is_water_sector(sector: int) -> bool:
    return sector in (6, 7, 8)


def is_road_sector(sector: int) -> bool:
    return sector in (10, 11)

def strip_mud_codes(s: str) -> str:
    """
    Strip MUD color codes of the form `X (backtick + one char) from a string.
    Keeps all other characters.
    """
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "`":
            i += 2
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def norm_letters(s: str) -> str:
    s2 = strip_mud_codes(s).lower()
    return "".join(ch for ch in s2 if "a" <= ch <= "z")


def looks_like_river_name(name: str) -> bool:
    n = norm_letters(name)
    return ("river" in n) or ("alguenya" in n) or ("erinin" in n)


def looks_like_road_name(name: str) -> bool:
    n = norm_letters(name)
    return "road" in n


def looks_like_river_desc(desc_lines: list[str]) -> bool:
    s = norm_letters("\n".join(desc_lines))
    return "river" in s or "water" in s or "current" in s


def looks_like_road_desc(desc_lines: list[str]) -> bool:
    s = norm_letters("\n".join(desc_lines))
    return "road" in s or "path" in s or "track" in s


def bfs_label_by_seeds(
    rooms: dict[int, Room],
    *,
    is_allowed,
    seeds: dict[int, str],
) -> dict[int, str]:
    """
    Multi-source BFS returning label per reachable vnum.
    If two seeds reach a node at the same distance, the earlier enqueued seed wins.
    """
    label: dict[int, str] = {}
    dist: dict[int, int] = {}
    q: deque[int] = deque()
    for v, lab in seeds.items():
        if v not in rooms:
            continue
        if not is_allowed(rooms[v]):
            continue
        label[v] = lab
        dist[v] = 0
        q.append(v)
    while q:
        cur = q.popleft()
        cd = dist[cur]
        for to in rooms[cur].exits.values():
            if to not in rooms:
                continue
            if not is_allowed(rooms[to]):
                continue
            nd = cd + 1
            if to not in dist or nd < dist[to]:
                dist[to] = nd
                label[to] = label[cur]
                q.append(to)
    return label


def road_dirs_to_other_roads(v: int, rooms: dict[int, Room]) -> list[int]:
    r = rooms[v]
    out: list[int] = []
    for d, to in r.exits.items():
        rr = rooms.get(to)
        if rr is None:
            continue
        if is_road_sector(rr.sector):
            out.append(d)
    return sorted(out)


def format_road_title(ds: list[int]) -> str:
    # Prefer cardinal directions, then diagonals.
    card = [d for d in ds if d in (0, 1, 2, 3)]
    diag = [d for d in ds if d in (6, 7, 8, 9)]
    chosen = (card or diag)[:2]
    if not chosen:
        return "`6The Road`7~"
    if len(chosen) == 1:
        return f"`6The Road runs `&{DIRS[chosen[0]].title()}`7~"
    a, b = chosen
    return f"`6The Road runs `&{DIRS[a].title()} `6and `&{DIRS[b].title()}`7~"


def format_road_desc(ds: list[int]) -> list[str]:
    if not ds:
        return ["A well-traveled road runs through the countryside here.", "~"]
    names = [DIRS[d] for d in ds if d in DIRS]
    if not names:
        return ["A well-traveled road runs through the countryside here.", "~"]
    if len(names) == 1:
        cont = f"The road continues {names[0]}."
    else:
        cont = f"The road continues {names[0]} and {names[1]}."
    return ["A well-traveled road runs through the countryside here.", cont, "~"]


def _find_room_header_idx(lines: list[str], vnum: int) -> int:
    needle = f"#{vnum}"
    for i, ln in enumerate(lines):
        if ln.strip() == needle:
            return i
    raise SystemExit(f"Could not find room header {needle} in file")


def set_room_name_desc_in_lines(
    lines: list[str],
    *,
    vnum: int,
    name: str | None,
    desc_lines: list[str] | None,
) -> None:
    """
    Update a room's name/desc in the provided file lines.
    This is robust to prior edits because it re-finds the room by vnum each time.
    """
    h = _find_room_header_idx(lines, vnum)
    if name is not None:
        lines[h + 1] = name
    if desc_lines is not None:
        i = h + 2
        j = i
        while j < len(lines) and lines[j].strip() != "~":
            j += 1
        j += 1
        lines[i:j] = desc_lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--zones", required=True, help="Comma/range list of zones to fix (e.g. 539,540,638)")
    ap.add_argument("--inplace", action="store_true")
    args = ap.parse_args()

    # parse zones
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

    # include upstream neighbor zones for seeding (safe even if missing)
    zones_for_graph = set(zones) | {509, 570, 608, 609}

    rooms = load_rooms(args.wld_dir, zones_for_graph)

    # Water labels: seed from known-good tiles.
    water_seeds = {
        60895: "alguenya",
        60890: "erinin",
        63863: "erinin",
    }

    water_label = bfs_label_by_seeds(
        rooms,
        is_allowed=lambda r: is_water_sector(r.sector),
        seeds=water_seeds,
    )

    # Cache exemplar payloads from seeds (name + desc)
    exemplar: dict[str, tuple[str, list[str]]] = {}
    for v, lab in water_seeds.items():
        rr = rooms.get(v)
        if rr is None:
            continue
        if looks_like_river_name(rr.name):
            exemplar[lab] = (rr.name, rr.desc_lines)

    # Cache file contents so we can apply multiple edits safely and write once per file.
    file_cache: dict[Path, list[str]] = {}

    changed = 0
    for v, r in sorted(rooms.items()):
        z = v // 100
        if z not in zones:
            continue

        if is_water_sector(r.sector):
            lab = water_label.get(v)
            # If this water component isn't connected to our seeds, fall back by zone.
            # For the specific restore issues, zones 539/540 water is the Erinin system.
            if lab is None:
                if z in (539, 540, 638):
                    lab = "erinin"
                else:
                    continue
            # If the room already explicitly names a river, trust that over BFS labeling.
            nlow = norm_letters(r.name)
            if "alguenya" in nlow:
                lab = "alguenya"
            elif "erinin" in nlow:
                lab = "erinin"

            # If it already looks correct, skip.
            if looks_like_river_name(r.name) and looks_like_river_desc(r.desc_lines):
                continue
            if lab not in exemplar:
                continue
            new_name, new_desc = exemplar[lab]
            # If the name is already river-like, only repair the description.
            # If the name is non-river (e.g. Open Plains), repair both.
            if looks_like_river_name(r.name) and not looks_like_river_desc(r.desc_lines):
                if not args.inplace:
                    print(f"DRY: water-desc-fix {v} {r.name}")
                else:
                    buf = file_cache.setdefault(r.file, _read_lines(r.file))
                    set_room_name_desc_in_lines(buf, vnum=v, name=None, desc_lines=new_desc)
                changed += 1
                continue

            if not looks_like_river_name(r.name):
                if not args.inplace:
                    print(f"DRY: water-fix {v} {r.name} -> {new_name}")
                else:
                    buf = file_cache.setdefault(r.file, _read_lines(r.file))
                    set_room_name_desc_in_lines(buf, vnum=v, name=new_name, desc_lines=new_desc)
                changed += 1
            continue

        if is_road_sector(r.sector):
            if looks_like_road_name(r.name) and looks_like_road_desc(r.desc_lines) and "river" not in r.name.lower():
                continue
            ds = road_dirs_to_other_roads(v, rooms)
            new_name = format_road_title(ds)
            new_desc = format_road_desc(ds)
            if not args.inplace:
                print(f"DRY: road-fix {v} {r.name} -> {new_name}")
            else:
                buf = file_cache.setdefault(r.file, _read_lines(r.file))
                set_room_name_desc_in_lines(buf, vnum=v, name=new_name, desc_lines=new_desc)
            changed += 1

    print(f"changed={changed} inplace={bool(args.inplace)}")
    if args.inplace:
        for p, lines in file_cache.items():
            _write_lines(p, lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

