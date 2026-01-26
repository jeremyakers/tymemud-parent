#!/usr/bin/env python3
"""
Text-based consistency audit for ubermap world rooms.

Goal: Catch *data issues* where a room's sector type likely disagrees with the
room's title/description (e.g., "Bridge over the River" but sector=FOREST).

This audit is intentionally heuristic: it produces a TSV for humans to review.

Scope:
- By default, audits only vnums present in a coords TSV (the current ubermap
  physical export scope), which keeps the report focused and fast.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")


@dataclass(frozen=True)
class Room:
    vnum: int
    title: str
    desc: str
    zone: int
    flags_token: str
    sector: int


def iter_rooms(wld_path: Path) -> Iterator[Room]:
    """
    Yield Room entries from a CircleMUD-style .wld file.

    We parse:
    - vnum
    - title line (raw, includes trailing '~')
    - full description (joined by '\n')
    - sector line: "<zone> <flags_token> <sector> <x> <y>"
    """
    txt = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(txt):
        m = ROOM_HEADER_RE.match(txt[i].strip())
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        if i + 1 >= len(txt):
            break
        title = txt[i + 1].rstrip("\n")

        # Description: ends at a line that is exactly "~" OR endswith "~".
        desc_lines: list[str] = []
        j = i + 2
        while j < len(txt):
            line = txt[j]
            if line.strip() == "~":
                j += 1
                break
            if line.endswith("~"):
                desc_lines.append(line[:-1])
                j += 1
                break
            desc_lines.append(line)
            j += 1
        desc = "\n".join(desc_lines).strip()

        # Sector line
        zone = -1
        flags_token = ""
        sector = -1
        k = j
        while k < len(txt):
            parts = txt[k].split()
            if len(parts) >= 3 and parts[0].isdigit() and parts[2].isdigit():
                zone = int(parts[0])
                flags_token = parts[1]
                sector = int(parts[2])
                break
            if txt[k].startswith("#") and k != i:
                break
            k += 1
        if zone >= 0 and sector >= 0:
            yield Room(vnum=vnum, title=title, desc=desc, zone=zone, flags_token=flags_token, sector=sector)
        i = k + 1


def load_scope_vnums(coords_tsv: Path) -> Set[int]:
    with coords_tsv.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        return {int(row["vnum"]) for row in r}


def normalize_text(s: str) -> str:
    # Strip color codes/backticks somewhat by removing backticks and carets; keep readable words.
    return re.sub(r"[`^~]", " ", s).lower()


# Minimal mapping used by our current Ubermap sector audit scripts.
SECT_CITY = 1
SECT_FIELD = 2
SECT_FOREST = 3
SECT_HILLS = 4
SECT_MOUNTAIN = 5
SECT_WATER_SWIM = 6
SECT_MAIN_ROAD = 11


WATER_HINTS = [
    r"\briver\b",
    r"\bwater\b",
    r"\bcurren(t|ts)\b",
    r"\bswift\b",
    r"\bchoppy\b",
    r"\bdepth(s)?\b",
    r"\bsandbar(s)?\b",
    r"\bdriftwood\b",
    r"\bships?\b",
    r"\bsail(ing|s|ed)?\b",
    r"\bdock(s)?\b",
    r"\bwharf\b",
]

BRIDGE_HINTS = [
    r"\bbridge\b",
    r"\bspan(s|ned|ning)?\b",
    r"\bcross(ing|es|ed)?\b",
    r"\bwalkway\b",
    r"\barches?\b",
]

ROAD_HINTS = [
    r"\broad\b",
    r"\btrail\b",
    r"\bpath\b",
    r"\bwagon\b",
    r"\bruts?\b",
    r"\bdirt road\b",
]

CITY_HINTS = [
    r"\bvillage\b",
    r"\btown\b",
    r"\bcity\b",
    r"\bmarket(place)?\b",
    r"\bshops?\b",
    r"\bstreets?\b",
    r"\bguard towers?\b",
]


def count_matches(text: str, patterns: Iterable[str]) -> int:
    n = 0
    for p in patterns:
        if re.search(p, text):
            n += 1
    return n


def suggest_from_text(title: str, desc: str) -> Tuple[str, Dict[str, int]]:
    t = normalize_text(title + " " + desc)
    scores = {
        "water": count_matches(t, WATER_HINTS),
        "bridge": count_matches(t, BRIDGE_HINTS),
        "road": count_matches(t, ROAD_HINTS),
        "city": count_matches(t, CITY_HINTS),
    }
    # Prefer explicit bridge/river/road words when present.
    best = sorted(scores.keys(), key=lambda k: (-scores[k], k))[0]
    return best, scores


def problems_for(room: Room) -> Tuple[List[str], str, Dict[str, int]]:
    suggest, scores = suggest_from_text(room.title, room.desc)
    probs: list[str] = []

    # Only flag when there is meaningful signal.
    signal = max(scores.values()) if scores else 0
    if signal == 0:
        return [], suggest, scores

    if room.sector == SECT_WATER_SWIM and (scores["road"] > 0 or scores["bridge"] > 0) and scores["water"] == 0:
        probs.append("sector_water_but_text_suggests_road_or_bridge")
    if room.sector == SECT_MAIN_ROAD and scores["water"] > 0 and scores["road"] == 0:
        probs.append("sector_road_but_text_suggests_water")
    if room.sector in (SECT_FIELD, SECT_FOREST, SECT_HILLS, SECT_MOUNTAIN) and scores["water"] >= 2:
        probs.append("sector_land_but_text_strongly_suggests_water")
    if room.sector in (SECT_FIELD, SECT_FOREST, SECT_HILLS, SECT_MOUNTAIN) and scores["bridge"] >= 2:
        probs.append("sector_land_but_text_strongly_suggests_bridge")
    if room.sector in (SECT_FIELD, SECT_FOREST, SECT_HILLS, SECT_MOUNTAIN) and scores["road"] >= 2:
        probs.append("sector_land_but_text_strongly_suggests_road")
    if room.sector in (SECT_FIELD, SECT_FOREST, SECT_HILLS, SECT_MOUNTAIN, SECT_WATER_SWIM, SECT_MAIN_ROAD) and scores["city"] >= 2:
        # city text should rarely appear in non-city sectors on the macro map
        probs.append("sector_non_city_but_text_strongly_suggests_city")
    if room.sector == SECT_CITY and (scores["water"] >= 2 or scores["road"] >= 2) and scores["city"] == 0:
        probs.append("sector_city_but_text_strongly_suggests_non_city")

    return probs, suggest, scores


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--coords-tsv", type=Path, required=True, help="Coords TSV to define scope (vnums).")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    scope_vnums = load_scope_vnums(args.coords_tsv)
    scope_zones = {v // 100 for v in scope_vnums}

    rows: list[dict[str, str]] = []
    for zone in sorted(scope_zones):
        wld_path = args.wld_dir / f"{zone}.wld"
        if not wld_path.exists():
            continue
        for room in iter_rooms(wld_path):
            if room.vnum not in scope_vnums:
                continue
            probs, suggest, scores = problems_for(room)
            if not probs:
                continue
            desc_first = room.desc.split("\n", 1)[0][:140] if room.desc else ""
            rows.append(
                {
                    "vnum": str(room.vnum),
                    "zone": str(room.zone),
                    "sector": str(room.sector),
                    "flags_token": room.flags_token,
                    "problem": ";".join(probs),
                    "suggest": suggest,
                    "score_water": str(scores.get("water", 0)),
                    "score_bridge": str(scores.get("bridge", 0)),
                    "score_road": str(scores.get("road", 0)),
                    "score_city": str(scores.get("city", 0)),
                    "title": room.title,
                    "desc_first_line": desc_first,
                }
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "vnum",
            "zone",
            "sector",
            "flags_token",
            "problem",
            "suggest",
            "score_water",
            "score_bridge",
            "score_road",
            "score_city",
            "title",
            "desc_first_line",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for row in sorted(rows, key=lambda r: (int(r["zone"]), int(r["vnum"]))):
            w.writerow(row)

    print(f"wrote {args.out} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

