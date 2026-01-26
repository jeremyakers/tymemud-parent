#!/usr/bin/env python3
"""Audit Ubermap connectivity issues.

Focus:
- Validate .wld syntax basics ($~ terminator, room blocks, exit blocks).
- Verify all exit destinations exist.
- Verify reciprocal exits (dest has opposite-direction exit back to source).
- Detect Nico's historical bug: rooms ending in 47 have west mislinked to 44
  instead of 46 (i.e., vnum%100==47 and west->vnum-3 instead of vnum-1).

Usage:
  uv run python scripts/ubermap_connectivity_audit.py --zones 468,469,...,640
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WLD_DIR = ROOT / "MM32/lib/world/wld"

ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HDR_RE = re.compile(r"^D([0-3])\s*$")

RIVER_TOKENS = (
    "river",
    "erinin",
    "alguenya",
    "gaelin",
    "alindrelle",
    "fork",
)
ROAD_TOKENS = (
    " road",
    "road ",
    "road~",
    "jangai",
    "caemlyn road",
)


def opposite_dir(d: int) -> int:
    return {0: 2, 2: 0, 1: 3, 3: 1}[d]


@dataclass
class Room:
    vnum: int
    name_line: str  # includes trailing "~"
    desc_lines: list[str]
    sector_line: str
    exits: dict[int, int]  # dir -> dest vnum
    tail_lines: list[str]  # everything after exits/R/G/etc up to next room header


def parse_wld(path: Path) -> tuple[list[Room], list[str]]:
    """Parse a .wld file into rooms plus any non-fatal parse warnings."""
    warnings: list[str] = []
    # IMPORTANT: The MUD's loader uses get_line() which strips the last byte of
    # each line (assumes a trailing '\n'). If a file ends without a newline,
    # the final '$~' line can be mishandled and cause seemingly unrelated
    # "Format error ... after 'world' #<vnum>" crashes during boot.
    b = path.read_bytes()
    if b and not b.endswith(b"\n"):
        warnings.append(f"{path.name}: missing trailing newline at EOF (boot can fail even if '$~' is present)")
    raw = b.decode("latin-1", errors="replace")
    lines = raw.splitlines()

    if not lines:
        warnings.append(f"{path.name}: empty file")
        return [], warnings
    if lines[-1] != "$~":
        warnings.append(f"{path.name}: missing or malformed terminator (last line != '$~')")

    rooms: list[Room] = []
    i = 0

    def _consume_tilde_string(start: int) -> tuple[list[str], int]:
        """Consume 1+ lines until a line ends with '~' (inclusive).

        Exit blocks in this codebase use fread_string()-style '~'-terminated strings,
        which may span multiple lines. We only need to skip them safely.
        """
        out: list[str] = []
        j = start
        while j < len(lines):
            out.append(lines[j])
            if lines[j].endswith("~"):
                return out, j + 1
            j += 1
        return out, j

    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        if i + 1 >= len(lines):
            warnings.append(f"{path.name}: room #{vnum} missing name line")
            break
        name_line = lines[i + 1]

        # desc is a ~-terminated string (may be "~" for empty, may span lines).
        desc, j = _consume_tilde_string(i + 2)
        if not desc or not desc[-1].endswith("~"):
            warnings.append(f"{path.name}: room #{vnum} unterminated desc string")
            break

        if j >= len(lines):
            warnings.append(f"{path.name}: room #{vnum} missing sector line")
            break
        sector_line = lines[j]
        j += 1

        exits: dict[int, int] = {}
        tail: list[str] = []
        k = j
        while k < len(lines) and not ROOM_HDR_RE.match(lines[k]):
            if lines[k] == "$~":
                # end-of-file marker; stop parsing
                break
            em = EXIT_HDR_RE.match(lines[k])
            if em:
                d = int(em.group(1))
                # D<dir> is followed by:
                #  - a ~-terminated description string (may be "~" for empty, may span lines)
                #  - a ~-terminated keyword string (usually single line, may be "~" for empty)
                #  - a triple line: "<flags> <key> <dest_vnum>"
                desc_lines, nxt = _consume_tilde_string(k + 1)
                if not desc_lines or (desc_lines and not desc_lines[-1].endswith("~")):
                    warnings.append(f"{path.name}: room #{vnum} D{d} unterminated desc string")
                    k += 1
                    continue
                key_lines, nxt2 = _consume_tilde_string(nxt)
                if not key_lines or (key_lines and not key_lines[-1].endswith("~")):
                    warnings.append(f"{path.name}: room #{vnum} D{d} unterminated keyword string")
                    k += 1
                    continue
                if nxt2 >= len(lines):
                    warnings.append(f"{path.name}: room #{vnum} incomplete exit block D{d}")
                    k = nxt2
                    continue
                c = lines[nxt2]
                parts = c.split()
                if len(parts) == 3 and parts[2].lstrip("-").isdigit():
                    exits[d] = int(parts[2])
                else:
                    warnings.append(f"{path.name}: room #{vnum} D{d} bad dest triple: {c!r}")
                k = nxt2 + 1
                continue

            tail.append(lines[k])
            k += 1

        rooms.append(
            Room(
                vnum=vnum,
                name_line=name_line,
                desc_lines=desc,
                sector_line=sector_line,
                exits=exits,
                tail_lines=tail,
            )
        )
        i = k

    return rooms, warnings


def classify_room_for_map_fidelity(room: Room) -> set[str]:
    """Lightweight tagging for map-fidelity checks (names/descs), heuristic-only."""
    tags: set[str] = set()
    name = room.name_line.lower()
    desc = "\n".join(room.desc_lines).lower()
    # Map-fidelity critical tags should rely primarily on the *room name* to avoid
    # false positives from prose that mentions nearby features ("river in the distance").
    if any(t in name for t in RIVER_TOKENS):
        tags.add("river")
    if any(t in name for t in ROAD_TOKENS):
        tags.add("road")
    if "forest" in name or "woods" in name or "forest" in desc or "woods" in desc:
        tags.add("forest")
    if "hill" in name or "hills" in name or "hill" in desc or "hills" in desc:
        tags.add("hills")
    if (
        "farm" in name
        or "field" in name
        or "plains" in name
        or "grass" in name
        or "farm" in desc
        or "field" in desc
        or "plains" in desc
        or "grass" in desc
    ):
        tags.add("plains")
    return tags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", required=True, help="Comma-separated zone numbers (e.g. 468,469,608)")
    ap.add_argument(
        "--wld-dir",
        default=str(DEFAULT_WLD_DIR),
        help="Path to world/wld directory (defaults to MM32/lib/world/wld under this repo).",
    )
    ap.add_argument(
        "--index-all",
        action="store_true",
        help="Index all rooms in --wld-dir for dest-existence + reciprocity checks (reduces false positives).",
    )
    ap.add_argument(
        "--index-all-max-zone",
        type=int,
        default=None,
        help="When using --index-all, only index .wld files with numeric stem <= this value (reduces noise).",
    )
    ap.add_argument(
        "--fix-47",
        action="store_true",
        help="(Disabled) Previously attempted an auto-fix; kept only for backwards compatibility.",
    )
    ap.add_argument(
        "--report-map-fidelity-seams",
        action="store_true",
        help="Report cross-zone exits where road/river tags don't match between endpoints (heuristic).",
    )
    ap.add_argument(
        "--report-map-fidelity-candidates",
        action="store_true",
        help="Report rooms in the zone set that look like road/river tiles based on neighboring tags (heuristic).",
    )
    args = ap.parse_args()
    if args.fix_47:
        raise SystemExit(
            "--fix-47 is disabled because the earlier implementation was lossy for door exits/keywords. "
            "Please apply fixes surgically in the .wld file (or we can implement a safe in-place fixer)."
        )

    wld_dir = Path(args.wld_dir).resolve()
    zones = [int(z.strip()) for z in args.zones.split(",") if z.strip()]
    zones_set = set(zones)
    paths = [wld_dir / f"{z}.wld" for z in zones]

    all_rooms: dict[int, Room] = {}
    room_to_zone: dict[int, int] = {}
    per_zone_rooms: dict[int, list[Room]] = {}
    warnings: list[str] = []

    # Index all rooms (optional) so dest existence checks are meaningful even when
    # exits point outside the MVP zone set (e.g., city connectors).
    if args.index_all:
        for p in sorted(wld_dir.glob("*.wld")):
            zname = p.stem
            if not zname.isdigit():
                continue
            z = int(zname)
            if args.index_all_max_zone is not None and z > args.index_all_max_zone:
                continue
            rooms, warns = parse_wld(p)
            # Only surface syntax warnings for the explicitly requested zones.
            # We still index everything for accurate dest-existence checks.
            if z in zones_set:
                warnings.extend(warns)
            for r in rooms:
                all_rooms[r.vnum] = r
                room_to_zone[r.vnum] = z

    # Always parse + keep editable references for requested zones.
    for z, p in zip(zones, paths, strict=True):
        rooms, warns = parse_wld(p)
        warnings.extend(warns)
        per_zone_rooms[z] = rooms
        for r in rooms:
            all_rooms[r.vnum] = r
            room_to_zone[r.vnum] = z

    issues: list[str] = []
    fixes: list[str] = []

    # Check exits and reciprocity (only for rooms in requested zones).
    for z in zones:
        for room in per_zone_rooms.get(z, []):
            vnum = room.vnum
            for d, dest in room.exits.items():
                if dest not in all_rooms:
                    issues.append(
                        f"missing-dest: {vnum} D{d} -> {dest} (dest vnum not found in world index)"
                    )
                    continue
                # Reduce noise: only require reciprocity when the destination room
                # is also in the requested zone set (i.e., we're validating the
                # overland grid / Ubermap set, not city/utility connectors).
                dest_zone = room_to_zone.get(dest)
                if dest_zone is not None and dest_zone not in zones_set:
                    continue
                back = all_rooms[dest].exits.get(opposite_dir(d))
                # If dest's opposite-direction exit exists but points outside our
                # requested zone set, that's typically a deliberate "connector"
                # override (e.g., city gate using that direction to enter city).
                # Treat that as non-actionable for Ubermap reciprocity.
                if back is not None:
                    back_zone = room_to_zone.get(back)
                    if back_zone is not None and back_zone not in zones_set:
                        continue
                if back != vnum:
                    issues.append(
                        f"non-reciprocal: {vnum} D{d} -> {dest} but {dest} D{opposite_dir(d)} -> {back}"
                    )

    # Detect and optionally fix the "xx47 west should go to xx46" bug.
    for z in zones:
        for room in per_zone_rooms.get(z, []):
            vnum = room.vnum
            if vnum % 100 != 47:
                continue
            if 3 not in room.exits:
                continue
            west = room.exits[3]
            expected = vnum - 1
            if west == expected:
                continue
            # Flag common known case (west == vnum-3) as high confidence.
            if west == vnum - 3:
                issues.append(f"mislink-47: {vnum} west -> {west} (expected {expected})")
                if args.fix_47 and expected in all_rooms:
                    # Apply fix in memory (both directions)
                    room.exits[3] = expected
                    all_rooms[expected].exits[1] = vnum
                    fixes.append(
                        f"fixed-47: {vnum} west {west}->{expected} and {expected} east -> {vnum}"
                    )
            else:
                issues.append(f"suspicious-47: {vnum} west -> {west} (expected {expected})")

    if args.report_map_fidelity_seams:
        seam_issues: list[str] = []
        for z in zones:
            for room in per_zone_rooms.get(z, []):
                src = room.vnum
                src_zone = room_to_zone.get(src)
                if src_zone not in zones_set:
                    continue
                src_tags = classify_room_for_map_fidelity(room)
                for d, dest in room.exits.items():
                    dest_zone = room_to_zone.get(dest)
                    if dest_zone is None or dest_zone not in zones_set:
                        continue
                    if dest_zone == src_zone:
                        continue
                    dest_room = all_rooms.get(dest)
                    if dest_room is None:
                        continue
                    dest_tags = classify_room_for_map_fidelity(dest_room)
                    # Only focus on road/river mismatches (map legend-critical).
                    for t in ("road", "river"):
                        if (t in src_tags) ^ (t in dest_tags):
                            seam_issues.append(
                                f"map-seam-mismatch: {src}({sorted(src_tags)}) D{d} -> {dest}({sorted(dest_tags)})"
                            )
                            break

        print("\nMAP-FIDELITY SEAMS (heuristic):")
        for it in sorted(set(seam_issues)):
            print(f"  - {it}")
        print(f"  count: {len(set(seam_issues))}")

    if args.report_map_fidelity_candidates:
        # Precompute tags for all rooms in the zone set.
        tags_by_vnum: dict[int, set[str]] = {}
        for vnum, r in all_rooms.items():
            z = room_to_zone.get(vnum)
            if z is None or z not in zones_set:
                continue
            tags_by_vnum[vnum] = classify_room_for_map_fidelity(r)

        candidates: list[str] = []

        def _road_neighbor_count(vnum: int) -> int:
            r = all_rooms.get(vnum)
            if r is None:
                return 0
            c = 0
            for dest in r.exits.values():
                if dest in tags_by_vnum and "road" in tags_by_vnum[dest]:
                    c += 1
            return c

        def _river_neighbor_count(vnum: int) -> int:
            r = all_rooms.get(vnum)
            if r is None:
                return 0
            c = 0
            for dest in r.exits.values():
                if dest in tags_by_vnum and "river" in tags_by_vnum[dest]:
                    c += 1
            return c

        for vnum, tags in tags_by_vnum.items():
            # High-confidence "missing road" candidate: room itself not tagged road,
            # but has 2+ road-tagged neighbors within the zone set.
            if "road" not in tags:
                n = _road_neighbor_count(vnum)
                if n >= 2:
                    candidates.append(f"candidate-road: {vnum} tags={sorted(tags)} road_neighbors={n}")
            # High-confidence "missing river" candidate: same idea for riverways.
            if "river" not in tags:
                n = _river_neighbor_count(vnum)
                if n >= 2:
                    candidates.append(f"candidate-river: {vnum} tags={sorted(tags)} river_neighbors={n}")

        print("\nMAP-FIDELITY CANDIDATES (heuristic):")
        for it in sorted(candidates):
            print(f"  - {it}")
        print(f"  count: {len(candidates)}")

    print("WARNINGS:")
    for w in warnings:
        print(f"  - {w}")

    print("\nISSUES:")
    for it in issues:
        print(f"  - {it}")

    if fixes:
        print("\nFIXES:")
        for fx in fixes:
            print(f"  - {fx}")

    print("\nSUMMARY:")
    print(f"  zones: {len(zones)} rooms: {len(all_rooms)} warnings: {len(warnings)} issues: {len(issues)} fixes: {len(fixes)}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # Allow piping to head/tail without a noisy stacktrace.
        # (e.g., `... | head -n 50`)
        sys.exit(0)

