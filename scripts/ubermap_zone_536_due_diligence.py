#!/usr/bin/env python3
"""
Due diligence on zone 536:
- Confirm it's a 10x10 overland zone
- Summarize terrain tags (road/river/forest/hills/plains) by room name
- Summarize sector numbers from the header line (best-effort)
- Compare seam expectations for "east of Cairhien": west edge of 536 vs east edge of 537

Outputs:
- docs/ubermap/v2/zone_536_due_diligence.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
WLD_DIR = ROOT / "MM32/lib/world/wld"
OUT_MD = ROOT / "docs/ubermap/v2/zone_536_due_diligence.md"

ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HDR_RE = re.compile(r"^D([0-5])\s*$")

RIVER_TOKENS = ("river", "erinin", "alguenya", "gaelin", "alindrelle", "fork")
ROAD_TOKENS = (" road", "road ", "road~", "jangai", "caemlyn road")


@dataclass
class Room:
    vnum: int
    name: str
    sector: int | None
    exits: dict[int, int]


def consume_tilde_string(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines):
        if lines[i].endswith("~") or lines[i].strip() == "~":
            return i + 1
        i += 1
    return i


def parse_zone(z: int) -> dict[int, Room]:
    p = WLD_DIR / f"{z}.wld"
    lines = p.read_text(encoding="latin-1", errors="replace").splitlines()
    rooms: dict[int, Room] = {}
    i = 0
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        name = lines[i + 1] if i + 1 < len(lines) else ""
        # consume desc string (until "~" line)
        j = i + 2
        while j < len(lines) and lines[j].strip() != "~":
            j += 1
        j += 1  # move to sector line
        sector = None
        if j < len(lines):
            parts = lines[j].split()
            if len(parts) >= 3 and parts[2].lstrip("-").isdigit():
                sector = int(parts[2])
        j += 1
        exits: dict[int, int] = {}
        k = j
        while k < len(lines) and not ROOM_HDR_RE.match(lines[k]) and lines[k] != "$~":
            em = EXIT_HDR_RE.match(lines[k])
            if em:
                d = int(em.group(1))
                nxt = consume_tilde_string(lines, k + 1)
                nxt2 = consume_tilde_string(lines, nxt)
                if nxt2 < len(lines):
                    parts = lines[nxt2].split()
                    if len(parts) >= 3 and parts[-1].lstrip("-").isdigit():
                        dest = int(parts[-1])
                        exits[d] = dest
                k = nxt2 + 1
                continue
            k += 1
        rooms[vnum] = Room(vnum=vnum, name=name, sector=sector, exits=exits)
        i = k
    return rooms


def tags_for_name(name: str) -> set[str]:
    n = name.lower()
    tags: set[str] = set()
    if any(t in n for t in RIVER_TOKENS):
        tags.add("river")
    if any(t in n for t in ROAD_TOKENS):
        tags.add("road")
    if "forest" in n or "woods" in n:
        tags.add("forest")
    if "hill" in n or "hills" in n:
        tags.add("hills")
    if "farm" in n or "field" in n or "plains" in n or "grass" in n:
        tags.add("plains")
    return tags or {"unknown"}


def cell_of(vnum: int) -> tuple[int, int]:
    cell = vnum % 100
    return cell // 10, cell % 10


def seam_compare(west_zone: int, east_zone: int) -> list[str]:
    """Compare east edge of west_zone (col 9) to west edge of east_zone (col 0)."""
    wz = parse_zone(west_zone)
    ez = parse_zone(east_zone)
    lines: list[str] = []
    lines.append("| row | west(vnum,name,tags) | east(vnum,name,tags) |")
    lines.append("|---:|---|---|")
    for r in range(10):
        wv = west_zone * 100 + (r * 10 + 9)
        ev = east_zone * 100 + (r * 10 + 0)
        wr = wz.get(wv)
        er = ez.get(ev)
        if not wr or not er:
            lines.append(f"| {r} | {wv} <missing> | {ev} <missing> |")
            continue
        wt = ",".join(sorted(tags_for_name(wr.name)))
        et = ",".join(sorted(tags_for_name(er.name)))
        lines.append(f"| {r} | {wv} `{wr.name}` ({wt}) | {ev} `{er.name}` ({et}) |")
    return lines


def main() -> int:
    z = 536
    rooms = parse_zone(z)
    vnums = sorted(rooms.keys())
    ok_grid = len(vnums) >= 95 and min(vnums) >= z * 100 and max(vnums) <= z * 100 + 99

    tag_counts: dict[str, int] = {}
    sector_counts: dict[str, int] = {}
    cross_zone = 0
    for r in rooms.values():
        for t in tags_for_name(r.name):
            tag_counts[t] = tag_counts.get(t, 0) + 1
        s = str(r.sector) if r.sector is not None else "None"
        sector_counts[s] = sector_counts.get(s, 0) + 1
        for dest in r.exits.values():
            if dest >= 0 and dest // 100 != z:
                cross_zone += 1

    md: list[str] = []
    md.append("## Zone 536 due diligence")
    md.append("")
    md.append(f"- **File**: `MM32/lib/world/wld/536.wld`")
    md.append(f"- **10x10 overland shape**: {'yes' if ok_grid else 'no'} (rooms={len(rooms)})")
    md.append(f"- **Cross-zone exits**: {cross_zone}")
    md.append("")
    md.append("### Room-name terrain tags (heuristic)")
    md.append("")
    md.append("| tag | count |")
    md.append("|---|---:|")
    for k in sorted(tag_counts, key=lambda x: (-tag_counts[x], x)):
        md.append(f"| {k} | {tag_counts[k]} |")
    md.append("")
    md.append("### Sector numbers (best-effort parse of header line)")
    md.append("")
    md.append("| sector | count |")
    md.append("|---:|---:|")
    for k in sorted(sector_counts, key=lambda x: (-sector_counts[x], x)):
        md.append(f"| {k} | {sector_counts[k]} |")
    md.append("")
    md.append("### Seam hypothesis: 536 is east of Cairhien (zone 537)")
    md.append("")
    md.extend(seam_compare(537, 536))
    md.append("")
    md.append("Notes:")
    md.append("- This seam comparison is only about *terrain label plausibility* (road/river/forest/hills/plains) based on room names.")
    md.append("- If we decide to link 537↔536, we’ll also enforce reciprocal exits and (if needed) road/river directionality prose on the seam tiles.")
    md.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

