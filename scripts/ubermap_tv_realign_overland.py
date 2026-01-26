#!/usr/bin/env python3
"""
Relocate (not just resector) Tar Valon overland roads/rivers in zones 468/469/508/509.

This script is intentionally conservative:
- Zones edited: 468/469/508/509 only.
- Other zones are read-only.
- Uses v1/bgs TSVs as the north-star “before/after” feature sets.
- For existing features (roads/rivers), we relocate the *payload* (title/desc/sector+tail)
  while preserving the destination's exits (grid connectivity).

Erinin relocation:
- Old path: start=46833, end=50873, constrained to v1 river cells.
- New path: start=46890, end=50873, constrained to bgsvg river cells.
- We map index-by-index along both paths and relocate payload from old[i] -> new[i].
  This DOES include the ring anchor tiles like 46890 (water tiles are allowed even if protected).

Road relocation:
- Minimal: only apply the bgsvg roads necessary to create/maintain the six spokes from the
  six bridge towns around Tar Valon, and only until those spokes meet existing v1 roads.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

SECT_INSIDE = 0
SECT_CITY = 1
SECT_FIELD = 2
SECT_WATER_SWIM = 6
SECT_MAIN_ROAD = 11

ZONE_SET = {468, 469, 508, 509}

# New Tar Valon ring river tiles: keep their curated ring text (do NOT overwrite payload).
TV_RING_RIVER = {46870, 46881, 46890, 46968, 46969, 46978, 46988, 46999}

# Manual road shaping overrides (user-directed).
# Note: bgsvg indicates 46841 is a road cell, but user explicitly requested it be open terrain to reduce crowding.
FORCE_TERRAIN = {46860, 46841}
# Cardinal-first “longer feel” pathing helpers for the Daghain spoke + west-to-north bend near 46832.
# NOTE: Do not force-road 46840/46850 anymore; user requested these be plain overland terrain.
FORCE_ROAD = {46823, 46832, 46833, 46851}

# For zone-relative coordinates we must keep the same anchoring as the v1-slice overlay
# (scripts/ubermap_overlay_on_bgsvg.py): derive coords from boundary-consistent exits,
# anchored at zone 469 = (0,0).
V1_ZONES = [
    469,
    468,
    509,
    508,
    540,
    539,
    538,
    537,
    570,
    569,
    568,
    567,
    610,
    609,
    608,
    607,
    640,
    639,
    638,
]
V1_ZONE_SET = set(V1_ZONES)


GENERIC_TITLE_FRAGMENTS = [
    "grassy expanse",
    "rolling grassland",
    "open plains",
    "quaint farmland",
    "farmlands",
    "rolling hills",
    "the road",
    "river",
    "erinin",
]

_COLOR_RE = re.compile(r"`.")
_DECOR_RE = re.compile(r"[#&^@]")


def _visible(s: str) -> str:
    """Best-effort strip MUD color/decoration codes so we can match human-visible text."""
    return _DECOR_RE.sub("", _COLOR_RE.sub("", s)).lower()


@dataclass
class Room:
    vnum: int
    header: str
    title: str
    desc_lines: list[str]
    desc_term: str
    sector_line: str
    exits: list[list[str]]
    tail: list[str]

    def sector_type(self) -> int | None:
        parts = self.sector_line.split()
        if len(parts) < 3:
            return None
        try:
            return int(parts[2])
        except Exception:
            return None

    def set_sector_type(self, new_sector: int) -> None:
        parts = self.sector_line.split()
        if len(parts) < 3 or not parts[2].isdigit():
            return
        parts[2] = str(int(new_sector))
        suffix = "\n" if self.sector_line.endswith("\n") else ""
        self.sector_line = " ".join(parts) + suffix

    def set_zone_id(self, z: int) -> None:
        parts = self.sector_line.split()
        if len(parts) < 1:
            return
        if not parts[0].isdigit():
            return
        parts[0] = str(int(z))
        suffix = "\n" if self.sector_line.endswith("\n") else ""
        self.sector_line = " ".join(parts) + suffix


def _is_room_header(line: str) -> bool:
    s = line.strip()
    return s.startswith("#") and s[1:].isdigit()


def _room_vnum(line: str) -> int:
    return int(line.strip()[1:])


def _is_exit_header(line: str) -> bool:
    s = line.strip()
    return len(s) >= 2 and s[0] == "D" and s[1:].isdigit()


def _consume_tilde_block(lines: list[str], i: int) -> int:
    while i < len(lines):
        if lines[i].strip() == "~" or lines[i].rstrip("\n").endswith("~"):
            return i + 1
        i += 1
    return i


def parse_wld(path: Path) -> tuple[list[Room], list[str]]:
    lines = path.read_text(encoding="latin-1", errors="replace").splitlines(keepends=True)
    rooms: list[Room] = []
    i = 0
    while i < len(lines):
        if not _is_room_header(lines[i]):
            i += 1
            continue
        header = lines[i]
        vnum = _room_vnum(header)
        i += 1
        if i >= len(lines):
            break
        title = lines[i]
        i += 1
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
        if i >= len(lines):
            break
        sector_line = lines[i]
        i += 1
        exits: list[list[str]] = []
        tail: list[str] = []
        while i < len(lines) and not _is_room_header(lines[i]):
            if _is_exit_header(lines[i]):
                block = [lines[i]]
                i += 1
                i2 = _consume_tilde_block(lines, i)
                block.extend(lines[i:i2])
                i = i2
                i2 = _consume_tilde_block(lines, i)
                block.extend(lines[i:i2])
                i = i2
                if i < len(lines):
                    block.append(lines[i])
                    i += 1
                exits.append(block)
                continue
            tail.append(lines[i])
            i += 1
        rooms.append(Room(vnum, header, title, desc_lines, desc_term, sector_line, exits, tail))
    return rooms, lines


def write_wld(path: Path, rooms: list[Room]) -> None:
    out: list[str] = []
    for r in rooms:
        out.append(r.header)
        out.append(r.title)
        out.extend(r.desc_lines)
        out.append(r.desc_term)
        out.append(r.sector_line)
        for ex in r.exits:
            out.extend(ex)
        out.extend(r.tail)
    path.write_text("".join(out), encoding="latin-1", errors="strict")


def load_protected(path: Path) -> set[int]:
    out: set[int] = set()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = raw.split("#", 1)[0].strip()
        if not s:
            continue
        try:
            out.add(int(s.split()[0]))
        except Exception:
            continue
    return out


def load_cells(tsv: Path) -> dict[int, dict[str, set[int]]]:
    out: dict[int, dict[str, set[int]]] = {}
    for ln in tsv.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.lower().startswith("zone\t"):
            continue
        parts = ln.split("\t")
        if len(parts) < 3:
            continue
        z = int(parts[0])
        if z not in ZONE_SET:
            continue
        cell = int(parts[1])
        feat = parts[2].strip()
        if feat not in ("river", "road"):
            continue
        out.setdefault(z, {"river": set(), "road": set()})[feat].add(cell)
    for z in ZONE_SET:
        out.setdefault(z, {"river": set(), "road": set()})
    return out


# Zone coord derivation (same logic as overlay script)
_ROOM_RE = re.compile(r"^#(\d+)\s*$")
_DIR_RE = re.compile(r"^D(\d+)\s*$")
_INFO_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s+(-?\d+)\s*$")


def _iter_exits_for_coords(wld_path: Path):
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    cur_room: int | None = None
    while i < len(lines):
        m = _ROOM_RE.match(lines[i].strip())
        if m:
            cur_room = int(m.group(1))
            i += 1
            continue
        m = _DIR_RE.match(lines[i].strip())
        if m and cur_room is not None:
            dir_idx = int(m.group(1))
            i += 1
            while i < len(lines) and lines[i].strip() != "~" and not lines[i].endswith("~"):
                i += 1
            if i < len(lines):
                i += 1
            while i < len(lines) and lines[i].strip() != "~" and not lines[i].endswith("~"):
                i += 1
            if i < len(lines):
                i += 1
            if i < len(lines):
                m2 = _INFO_RE.match(lines[i].strip())
                if m2:
                    to_vnum = int(m2.group(3))
                    yield cur_room, dir_idx, to_vnum
            i += 1
            continue
        i += 1


def derive_zone_coords(wld_dir: Path, zones: Iterable[int]) -> dict[int, tuple[int, int]]:
    zones = list(zones)
    zone_set = set(zones)
    adj: dict[int, list[tuple[int, int, int]]] = {z: [] for z in zones}
    for z in zones:
        wld = wld_dir / f"{z}.wld"
        for room, d, to in _iter_exits_for_coords(wld):
            if to <= 0:
                continue
            z_to = to // 100
            if z_to not in zone_set or z_to == z:
                continue
            cell = room % 100
            cell_to = to % 100
            if d == 0 and cell < 10 and cell_to == cell + 90:
                adj[z].append((z_to, 0, -1))
            elif d == 2 and cell >= 90 and cell_to == cell - 90:
                adj[z].append((z_to, 0, 1))
            elif d == 1 and cell % 10 == 9 and cell_to == cell - 9:
                adj[z].append((z_to, 1, 0))
            elif d == 3 and cell % 10 == 0 and cell_to == cell + 9:
                adj[z].append((z_to, -1, 0))

    coords: dict[int, tuple[int, int]] = {469: (0, 0)}
    q = [469]
    while q:
        z = q.pop(0)
        x, y = coords[z]
        for nbr, dx, dy in adj.get(z, []):
            nx, ny = x + dx, y + dy
            if nbr not in coords:
                coords[nbr] = (nx, ny)
                q.append(nbr)
            else:
                if coords[nbr] != (nx, ny):
                    raise RuntimeError(f"zone coord conflict: {z}->{nbr} existing={coords[nbr]} new={(nx, ny)}")
    missing = sorted(set(zones) - set(coords.keys()))
    if missing:
        raise RuntimeError(f"missing coords for zones: {missing}")
    return coords


def vnum_to_global(vnum: int, coords: dict[int, tuple[int, int]]) -> tuple[int, int]:
    z = vnum // 100
    cell = vnum % 100
    row, col = divmod(cell, 10)
    zx, zy = coords[z]
    gx = zx * 10 + col
    gy = zy * 10 + row
    return gx, gy


def global_to_vnum(gx: int, gy: int, coords: dict[int, tuple[int, int]]) -> int | None:
    zx = gx // 10
    zy = gy // 10
    col = gx % 10
    row = gy % 10
    inv = {v: k for k, v in coords.items()}
    z = inv.get((zx, zy))
    if z is None:
        return None
    if not (0 <= col < 10 and 0 <= row < 10):
        return None
    return z * 100 + row * 10 + col


def build_path(start: int, cells: set[int], coords: dict[int, tuple[int, int]]) -> list[int]:
    cells_set = set(cells)
    path: list[int] = []
    cur = start
    prev: int | None = None
    visited: set[int] = set()
    while cur in cells_set and cur not in visited:
        path.append(cur)
        visited.add(cur)
        gx, gy = vnum_to_global(cur, coords)
        neighbors: list[int] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nv = global_to_vnum(gx + dx, gy + dy, coords)
                if nv is None:
                    continue
                if nv in cells_set and nv != prev:
                    neighbors.append(nv)
        # pick next unvisited neighbor if any
        nxt = None
        unvisited = [n for n in neighbors if n not in visited]
        if unvisited:
            # deterministic order: sort by global coords
            unvisited.sort(key=lambda v: vnum_to_global(v, coords))
            nxt = unvisited[0]
        if nxt is None:
            break
        prev = cur
        cur = nxt
    return path


def find_path(
    *, start: int, end: int, allowed: set[int], coords: dict[int, tuple[int, int]], diagonals: bool
) -> list[int]:
    """
    Deterministic shortest path in the allowed set.
    - Uses 4-neighborhood by default; can include diagonals for bgsvg stair-step geometry.
    """
    if start == end:
        return [start]
    if start not in allowed or end not in allowed:
        raise RuntimeError(f"path endpoints must be in allowed set: start={start} end={end}")

    dirs: list[tuple[int, int]] = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    if diagonals:
        dirs += [(1, -1), (-1, -1), (1, 1), (-1, 1)]

    def neighbors(v: int) -> list[int]:
        gx, gy = vnum_to_global(v, coords)
        out: list[int] = []
        for dx, dy in dirs:
            nv = global_to_vnum(gx + dx, gy + dy, coords)
            if nv is None:
                continue
            if nv in allowed:
                out.append(nv)
        # stable ordering by global coords
        out.sort(key=lambda x: vnum_to_global(x, coords))
        return out

    q: list[int] = [start]
    prev: dict[int, int] = {start: start}
    qi = 0
    while qi < len(q):
        cur = q[qi]
        qi += 1
        for nb in neighbors(cur):
            if nb in prev:
                continue
            prev[nb] = cur
            if nb == end:
                qi = len(q)
                break
            q.append(nb)

    if end not in prev:
        raise RuntimeError(f"no path found from {start} to {end} in allowed set (size={len(allowed)})")

    path: list[int] = []
    cur = end
    while True:
        path.append(cur)
        if cur == start:
            break
        cur = prev[cur]
    path.reverse()
    return path


def is_unique_room(room: Room) -> bool:
    title = _visible(room.title)
    if title.lstrip().startswith("!unused"):
        return True
    if "ethereal tar valon" in title:
        return True
    if room.sector_type() in (SECT_WATER_SWIM, SECT_MAIN_ROAD):
        return False
    for frag in GENERIC_TITLE_FRAGMENTS:
        if frag in title:
            return False
    return True


def make_generic_room(template: Room, target: Room) -> None:
    target.title = template.title
    target.desc_lines = list(template.desc_lines)
    target.desc_term = template.desc_term
    target.set_sector_type(template.sector_type() or SECT_FIELD)
    target.tail = list(template.tail)


def _copy_payload_preserve_exits(*, src: Room, dst: Room) -> None:
    """Copy title/desc/sector/tail from src to dst, but keep dst exits."""
    dst.title = src.title
    dst.desc_lines = list(src.desc_lines)
    dst.desc_term = src.desc_term
    dst.set_sector_type(src.sector_type() or dst.sector_type() or SECT_FIELD)
    dst.tail = list(src.tail)


def _set_placeholder_road(room: Room) -> None:
    room.set_sector_type(SECT_MAIN_ROAD)
    # Preserve historic special titles like "Road to Tar Valon" if present.
    if "road to tar valon" not in _visible(room.title):
        room.title = "`6The Road`7~\n"
    # Fix bad placeholder that implies disconnected/hole.
    if (
        not room.desc_lines
        or any("disconnect me" in ln.lower() for ln in room.desc_lines)
        or any("village of darein" in ln.lower() for ln in room.desc_lines)
        or "darein" in _visible(room.title)
    ):
        room.desc_lines = ["`7This road segment needs a proper description.`7\n"]
        room.desc_term = "~\n"


def _nearest_generic_field(
    *, start_vnum: int, coords: dict[int, tuple[int, int]], room_index: dict[int, Room], protected: set[int], max_r: int = 12
) -> int | None:
    sx, sy = vnum_to_global(start_vnum, coords)
    best: tuple[int, int] | None = None
    best_v: int | None = None
    for r in range(1, max_r + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if abs(dx) != r and abs(dy) != r:
                    continue
                v = global_to_vnum(sx + dx, sy + dy, coords)
                if v is None or v in protected:
                    continue
                rr = room_index.get(v)
                if rr is None:
                    continue
                if rr.sector_type() != SECT_FIELD:
                    continue
                if is_unique_room(rr):
                    continue
                cand = (abs(dx) + abs(dy), v)
                if best is None or cand < best:
                    best = cand
                    best_v = v
        if best_v is not None:
            return best_v
    return None


def _relocate_room_payload(*, src: Room, dst: Room, report: list[str], note: str) -> None:
    """Move full payload (title/desc/sector/tail) from src to dst, preserving dst exits."""
    _copy_payload_preserve_exits(src=src, dst=dst)
    report.append(f"MOVE payload {src.vnum} -> {dst.vnum} ({note})")


def ensure_river_direction(room: Room, river_set: set[int], coords: dict[int, tuple[int, int]]) -> None:
    gx, gy = vnum_to_global(room.vnum, coords)
    dirs = []
    for name, dx, dy in (
        ("north", 0, -1),
        ("east", 1, 0),
        ("south", 0, 1),
        ("west", -1, 0),
        ("northeast", 1, -1),
        ("northwest", -1, -1),
        ("southeast", 1, 1),
        ("southwest", -1, 1),
    ):
        nv = global_to_vnum(gx + dx, gy + dy, coords)
        if nv is not None and nv in river_set:
            dirs.append(name)
    if not dirs:
        return
    if len(dirs) == 1:
        s = dirs[0]
    elif len(dirs) == 2:
        s = f"{dirs[0]} and {dirs[1]}"
    else:
        s = ", ".join(dirs[:-1]) + f", and {dirs[-1]}"
    line = f"`7The riverway continues {s}.`7\n"
    replaced = False
    for i, ln in enumerate(room.desc_lines):
        if "riverway continues" in ln.lower():
            room.desc_lines[i] = line
            replaced = True
            break
    if not replaced:
        room.desc_lines.append(line)


def _choose_adjacent_start(
    *,
    anchor: int,
    feature_set: set[int],
    coords: dict[int, tuple[int, int]],
    prefer_dx: int,
    prefer_dy: int,
) -> int:
    """Pick an adjacent feature cell to anchor, biased by desired direction."""
    ax, ay = vnum_to_global(anchor, coords)
    best: tuple[int, int, int] | None = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            v = global_to_vnum(ax + dx, ay + dy, coords)
            if v is None or v not in feature_set:
                continue
            score = 0
            if prefer_dx != 0:
                score += 2 if (dx == prefer_dx) else (1 if (dx * prefer_dx) > 0 else 0)
            if prefer_dy != 0:
                score += 2 if (dy == prefer_dy) else (1 if (dy * prefer_dy) > 0 else 0)
            dist = abs(dx) + abs(dy)
            cand = (score, -dist, v)
            if best is None or cand > best:
                best = cand
    if best is None:
        raise RuntimeError(f"no adjacent start feature cell found for anchor {anchor}")
    return best[2]


def _global_delta(a: int, b: int, coords: dict[int, tuple[int, int]]) -> tuple[int, int]:
    ax, ay = vnum_to_global(a, coords)
    bx, by = vnum_to_global(b, coords)
    return (bx - ax, by - ay)


def _relocate_unique_by_delta(
    *,
    src_vnum: int,
    dst_vnum: int,
    coords: dict[int, tuple[int, int]],
    protected: set[int],
    room_index: dict[int, Room],
    report: list[str],
) -> None:
    dst_room = room_index[dst_vnum]
    if not is_unique_room(dst_room):
        return
    dx, dy = _global_delta(src_vnum, dst_vnum, coords)
    if dx == 0 and dy == 0:
        return
    gx_d, gy_d = vnum_to_global(dst_vnum, coords)
    # Move exactly one delta step (same magnitude) first; if occupied, scan further along delta direction.
    for step in range(1, 16):
        nv = global_to_vnum(gx_d + dx * step, gy_d + dy * step, coords)
        if nv is None or nv in protected:
            continue
        cand = room_index.get(nv)
        if cand is None:
            continue
        if is_unique_room(cand):
            continue
        cand.title = dst_room.title
        cand.desc_lines = list(dst_room.desc_lines)
        cand.desc_term = dst_room.desc_term
        cand.set_sector_type(dst_room.sector_type() or SECT_FIELD)
        cand.tail = list(dst_room.tail)
        report.append(f"MOVE unique {dst_vnum} -> {nv} (delta {dx},{dy} step {step})")
        return
    raise RuntimeError(f"cannot relocate unique room at dst={dst_vnum} delta={dx},{dy}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--protected-vnums", type=Path, required=True)
    ap.add_argument("--v1-tsv", type=Path, required=True)
    ap.add_argument("--bgsvg-tsv", type=Path, required=True)
    ap.add_argument("--do-roads", action="store_true", help="Apply minimal road relocation pass.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-report", type=Path, default=None)
    args = ap.parse_args()

    protected = load_protected(args.protected_vnums)
    v1 = load_cells(args.v1_tsv)
    bg = load_cells(args.bgsvg_tsv)

    coords = derive_zone_coords(args.wld_dir, V1_ZONES)

    # Build Erinin paths (old vs new)
    old_river = set()
    new_river = set()
    for z in ZONE_SET:
        old_river |= {z * 100 + c for c in v1[z]["river"]}
        new_river |= {z * 100 + c for c in bg[z]["river"]}

    # User target: connect new TV river alignment into the existing river at 50892 (do not churn beyond).
    old_path = find_path(start=46833, end=50892, allowed=old_river, coords=coords, diagonals=True)
    new_path = find_path(start=46890, end=50892, allowed=new_river, coords=coords, diagonals=True)
    # Stop at the meeting tile, inclusive; we don't churn south of here.
    if old_path[-1] != 50892 or new_path[-1] != 50892:
        raise RuntimeError("Erinin paths did not end at 50892 (unexpected)")
    # Map index-by-index; if they differ in length, treat extras as net-new river tiles (should be rare).
    map_len = min(len(old_path), len(new_path))
    mapping = list(zip(old_path[:map_len], new_path[:map_len]))

    report: list[str] = []

    # Load rooms per zone
    zone_rooms: dict[int, list[Room]] = {}
    room_index: dict[int, Room] = {}
    for z in ZONE_SET:
        rooms, _ = parse_wld(args.wld_dir / f"{z}.wld")
        zone_rooms[z] = rooms
        for r in rooms:
            room_index[r.vnum] = r

    # Normalize zone-id field for ALL rooms (some payloads get moved across zones).
    for z, rooms in zone_rooms.items():
        for r in rooms:
            r.set_zone_id(z)

    # Find a generic template per zone
    generic_template: dict[int, Room] = {}
    for z, rooms in zone_rooms.items():
        for r in rooms:
            if r.sector_type() == SECT_FIELD and not is_unique_room(r):
                generic_template[z] = r
                break

    # Pick a stable generic-field payload per zone for explicit overrides (avoid Ethereal placeholder text).
    generic_payload_src: dict[int, Room] = {}
    for z in ZONE_SET:
        for r in zone_rooms[z]:
            if r.sector_type() == SECT_FIELD and not is_unique_room(r) and "ethereal" not in _visible(r.title):
                generic_payload_src[z] = r
                break

    for src, dst in mapping:
        if src == dst:
            continue
        src_room = room_index.get(src)
        dst_room = room_index.get(dst)
        if src_room is None or dst_room is None:
            report.append(f"SKIP missing room src={src} dst={dst}")
            continue
        # Respect protected vnums: never relocate payload onto them (except curated ring-river anchors).
        if dst in protected and dst not in TV_RING_RIVER:
            report.append(f"SKIP protected river dst={dst} (src={src})")
            continue
        # Do not overwrite holes or city inserts.
        if dst in protected and (
            dst_room.title.lower().lstrip().startswith("!unused") or dst_room.sector_type() == SECT_CITY
        ):
            raise RuntimeError(f"refusing to overwrite protected non-water dst={dst}")

        # Relocate unique occupant at destination if needed
        _relocate_unique_by_delta(
            src_vnum=src, dst_vnum=dst, coords=coords, protected=protected, room_index=room_index, report=report
        )
        # Copy payload from src to dst (keep dst exits).
        # For ring tiles: keep curated ring text; only enforce sector + direction line.
        if dst in TV_RING_RIVER:
            dst_room.set_sector_type(SECT_WATER_SWIM)
            report.append(f"RIVER sector-only dst {dst} (ring tile) from src {src}")
        else:
            _copy_payload_preserve_exits(src=src_room, dst=dst_room)
            dst_room.set_sector_type(SECT_WATER_SWIM)
            report.append(f"RIVER src {src} -> dst {dst}")
        # Clear src to generic if needed
        if src not in protected and src not in set(new_path):
            tmpl = generic_template.get(src // 100)
            if tmpl:
                make_generic_room(tmpl, src_room)
                report.append(f"CLEAR src {src} -> generic")

    # Fix river direction lines on new river tiles in zones
    desired_river_local = {v for v in new_river if (v // 100) in ZONE_SET}

    # Move any remaining old river tiles (including the old TV ring) onto any desired river tiles
    # that are still not water, then clear all leftover non-desired water tiles back to generic.
    river_sources: list[int] = [
        v
        for v, r in room_index.items()
        if (v // 100) in ZONE_SET
        and r.sector_type() == SECT_WATER_SWIM
        and v not in desired_river_local
        and v not in protected
    ]
    river_sources.sort()

    for v in sorted(desired_river_local):
        if v in protected:
            # protected ring tiles should already be river; do not overwrite their payload
            continue
        r = room_index.get(v)
        if r is None:
            continue
        if r.sector_type() == SECT_WATER_SWIM:
            continue
        if not river_sources:
            # If we run out of sources, just enforce sector + minimal placeholder; content can be polished later.
            r.set_sector_type(SECT_WATER_SWIM)
            if "river" not in r.title.lower():
                r.title = "`^River Erinin`7~\n"
            if not r.desc_lines:
                r.desc_lines = ["`7This river segment needs a proper description.`7\n"]
                r.desc_term = "~\n"
            report.append(f"RIVER new-sector-only {v} (no sources left)")
            continue
        src_v = river_sources.pop(0)
        src_r = room_index[src_v]
        _copy_payload_preserve_exits(src=src_r, dst=r)
        r.set_sector_type(SECT_WATER_SWIM)
        report.append(f"RIVER extra src {src_v} -> dst {v}")
        # Clear old source
        tmpl = generic_template.get(src_v // 100)
        if tmpl:
            make_generic_room(tmpl, src_r)
            report.append(f"CLEAR old-river {src_v} -> generic")

    # Now clear any remaining water tiles in our zones that are not desired (old TV ring, etc.)
    for v, r in list(room_index.items()):
        if (v // 100) not in ZONE_SET:
            continue
        if v in protected:
            continue
        if r.sector_type() != SECT_WATER_SWIM:
            continue
        if v in desired_river_local:
            continue
        tmpl = generic_template.get(v // 100)
        if tmpl:
            make_generic_room(tmpl, r)
            report.append(f"CLEAR stray-river {v} -> generic")

    # Fix river direction lines on desired river tiles in our zones
    for v in sorted(desired_river_local):
        r = room_index.get(v)
        if r and r.sector_type() == SECT_WATER_SWIM:
            ensure_river_direction(r, desired_river_local, coords)

    # --- Minimal road relocation pass (6 spokes) ---
    if args.do_roads:
        # Relocate the camp off 50947 BEFORE we overwrite that tile with a road.
        camp_src_vnum = 50947
        camp_room = room_index.get(camp_src_vnum)
        if camp_room is not None:
            camp_like = "camp" in _visible(camp_room.title) or any("camp" in _visible(ln) for ln in camp_room.desc_lines)
            if camp_like:
                dst_v = _nearest_generic_field(
                    start_vnum=camp_src_vnum, coords=coords, room_index=room_index, protected=protected
                )
                if dst_v is None:
                    raise RuntimeError("could not find a generic field destination to relocate the camp from 50947")
                dst_room = room_index[dst_v]
                _relocate_room_payload(src=camp_room, dst=dst_room, report=report, note="camp relocation off 50947")
                # Clear 50947 back to generic; it will be set to road if bgsvg wants it.
                tmpl = generic_template.get(509)
                if tmpl:
                    make_generic_room(tmpl, camp_room)
                    report.append("CLEAR 50947 camp -> generic")

        # Road sets (v1 vs bgsvg) across the whole v1 slice; we only EDIT our 4 zones.
        v1_all = load_cells(args.v1_tsv)
        bg_all = load_cells(args.bgsvg_tsv)
        v1_road_all: set[int] = set()
        bg_road_all: set[int] = set()
        for z in V1_ZONES:
            v1_road_all |= {z * 100 + c for c in v1_all.get(z, {"road": set(), "river": set()})["road"]}
            bg_road_all |= {z * 100 + c for c in bg_all.get(z, {"road": set(), "river": set()})["road"]}

        # Town anchors (not road tiles themselves)
        spoke_towns = {46882, 50909, 46998, 46977, 46861, 46959}

        # We set road sector on bgsvg road tiles in our zones (excluding protected/towns/water),
        # and clear road sector on v1 road tiles in our zones that bgsvg no longer wants.
        bg_road_local = {
            v
            for v in bg_road_all
            if (v // 100) in ZONE_SET and v not in protected and v not in spoke_towns
        }
        v1_road_local = {
            v
            for v in v1_road_all
            if (v // 100) in ZONE_SET and v not in protected and v not in spoke_towns
        }

        # Apply roads
        for v in sorted(bg_road_local):
            r = room_index.get(v)
            if r is None:
                continue
            # never overwrite water/city/inside (roads shouldn't exist there)
            if r.sector_type() in (SECT_WATER_SWIM, SECT_CITY, SECT_INSIDE):
                continue
            if is_unique_room(r):
                # best-effort unique relocation: move it one tile further away from TV center (46989 area),
                # but if that fails, abort (we don't silently destroy unique content).
                src_for_delta = min(v1_road_local, key=lambda s: abs(_global_delta(s, v, coords)[0]) + abs(_global_delta(s, v, coords)[1])) if v1_road_local else v
                _relocate_unique_by_delta(
                    src_vnum=src_for_delta, dst_vnum=v, coords=coords, protected=protected, room_index=room_index, report=report
                )
            _set_placeholder_road(r)
            report.append(f"ROAD set {v}")

        # Clear roads no longer desired by bgsvg (within our zones only)
        for v in sorted(v1_road_local - bg_road_local):
            r = room_index.get(v)
            if r is None:
                continue
            if r.sector_type() != SECT_MAIN_ROAD:
                continue
            tmpl = generic_template.get(v // 100)
            if tmpl:
                make_generic_room(tmpl, r)
                report.append(f"ROAD clear {v} -> generic")

        # Sanity: each spoke town should have at least one adjacent road tile in our zones
        for town in sorted(spoke_towns):
            gx, gy = vnum_to_global(town, coords)
            ok = False
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nv = global_to_vnum(gx + dx, gy + dy, coords)
                    if nv is None:
                        continue
                    if (nv // 100) in ZONE_SET and nv in bg_road_local:
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                raise RuntimeError(f"spoke town {town} has no adjacent bgsvg road tile in our zones")

    # --- Manual overrides requested by user ---
    # Force some tiles back to open terrain to reduce crowding.
    for v in sorted(FORCE_TERRAIN):
        if v in protected:
            continue
        r = room_index.get(v)
        if r is None:
            continue
        if v in {46841, 46860}:
            # These are special-case “de-crowding” overrides: always force them to plain open terrain,
            # regardless of what our generic template detection finds.
            r.set_sector_type(SECT_FIELD)
            r.title = "`2Open Plains`0~\n"
            r.desc_lines = [
                "`7The land here is open and windswept, with grasses stretching away in all directions.`7\n"
            ]
            r.desc_term = "~\n"
            report.append(f"OVERRIDE terrain {v} (forced open terrain)")
            continue
        z = v // 100
        src = generic_payload_src.get(z)
        if src is not None:
            _copy_payload_preserve_exits(src=src, dst=r)
            r.set_sector_type(SECT_FIELD)
            report.append(f"OVERRIDE terrain {v} (payload from {src.vnum})")
        else:
            # Worst-case fallback: ensure it's *not* Ethereal/placeholder text and is walkable terrain.
            r.set_sector_type(SECT_FIELD)
            r.title = "`2Open Plains`0~\n"
            r.desc_lines = [
                "`7The land here is open and windswept, with grasses stretching away in all directions.`7\n"
            ]
            r.desc_term = "~\n"
            report.append(f"OVERRIDE terrain {v} (fallback payload)")

    # Force some tiles to be roads so pathing is cardinal as preferred.
    for v in sorted(FORCE_ROAD):
        if v in protected:
            continue
        r = room_index.get(v)
        if r is None:
            continue
        if r.sector_type() in (SECT_WATER_SWIM, SECT_CITY, SECT_INSIDE):
            continue
        _set_placeholder_road(r)
        report.append(f"OVERRIDE road {v}")

    if args.out_report:
        args.out_report.write_text("\n".join(report) + "\n", encoding="utf-8")

    if not args.dry_run:
        for z, rooms in zone_rooms.items():
            write_wld(args.wld_dir / f"{z}.wld", rooms)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
