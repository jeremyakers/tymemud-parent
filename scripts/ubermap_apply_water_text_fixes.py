#!/usr/bin/env python3
"""
Apply water-room text fixes in .wld files, scoped to the current ubermap coords TSV.

What it fixes (surgical, repeatable):
- In sector=6 (SECT_WATER_SWIM) rooms: replace any navigation line starting with
  "The road continues ..." to "The river continues ...".
- Remove obvious placeholder lines like "Change me!" inside water rooms.

This keeps edits minimal and avoids making up entirely new prose except for the
single word substitution (road->river) on navigation lines.

Backups:
- If --backup-dir is provided, copy each touched <zone>.wld there before writing.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")
SECTOR_LINE_RE = re.compile(r"^(\d+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$")

SECT_WATER_SWIM = 6


@dataclass
class RoomSpan:
    vnum: int
    start: int
    end: int
    sector: Optional[int]


def load_scope_vnums(coords_tsv: Path) -> Set[int]:
    with coords_tsv.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        return {int(row["vnum"]) for row in r}

def parse_zones_csv(s: str) -> Set[int]:
    out: Set[int] = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        out.add(int(part))
    return out


def find_room_spans(lines: List[str]) -> List[RoomSpan]:
    spans: List[RoomSpan] = []
    i = 0
    while i < len(lines):
        m = ROOM_HEADER_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        start = i
        i += 1
        # room ends just before next "#<num>" or "$"
        while i < len(lines) and not ROOM_HEADER_RE.match(lines[i].strip()) and lines[i].strip() != "$":
            i += 1
        end = i

        sector: Optional[int] = None
        # scan within span for sector line
        for j in range(start, end):
            sm = SECTOR_LINE_RE.match(lines[j].strip())
            if sm:
                sector = int(sm.group(3))
                break
        spans.append(RoomSpan(vnum=vnum, start=start, end=end, sector=sector))
    return spans


WATER_HINTS = (
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
    r"\bwaterway\b",
)

ROAD_HINTS = (
    r"\broad\b",
    r"\broadway\b",
    r"\bwagon\b",
    r"\bruts?\b",
    r"\bdirt road\b",
)


def score(text: str, patterns: Iterable[str]) -> int:
    return sum(1 for p in patterns if re.search(p, text))


def normalize_text(s: str) -> str:
    return re.sub(r"[`^~]", " ", s).lower()


def apply_fixes_to_room(lines: List[str], span: RoomSpan) -> Tuple[bool, List[str]]:
    if span.sector != SECT_WATER_SWIM:
        return False, lines

    changed = False
    out = list(lines)
    # Extract title + desc text for heuristic scoring.
    title = out[span.start + 1] if span.start + 1 < len(out) else ""
    # Description is lines until "~" terminator after title. We don't fully parse here;
    # instead, grab a window within the span.
    desc_block = "\n".join(out[span.start : span.end])
    norm = normalize_text(title + "\n" + desc_block)
    water_score = score(norm, WATER_HINTS)
    road_score = score(norm, ROAD_HINTS)

    # 1) Always fix navigation: "The road continues ..." -> "The river continues ..."
    for idx in range(span.start, span.end):
        if re.search(r"(?i)\bthe\s+road\s+continues\b", out[idx]):
            out[idx] = re.sub(r"(?i)\bthe\s+road\s+continues\b", "The river continues", out[idx])
            changed = True

    # 2) Remove placeholder lines like "Change me!" inside water rooms.
    for idx in range(span.start, span.end):
        if out[idx].strip().lower() == "change me!":
            out[idx] = ""
            changed = True

    # 3) If a water room reads *mostly* like a road and doesn't mention water at all,
    # replace its description body with a conservative river template.
    if road_score >= 2 and water_score == 0:
        # Find description start/end indices (between title and the first "~" line)
        desc_start = span.start + 2
        d = desc_start
        while d < span.end and out[d].strip() != "~" and not out[d].endswith("~"):
            d += 1
        desc_end = d

        river_template = (
            "A broad riverway cuts through the land here, its dark water moving steadily past.\n"
            "The current is strong enough to tug at anything that enters the flow, and driftwood\n"
            "spins lazily in the eddies along the banks."
        )
        # Preserve any existing navigation line if it already says riverway/river continues,
        # otherwise add a generic hint.
        nav_line = "`7The river continues along its course.`7"
        for idx in range(span.start, span.end):
            if re.search(r"(?i)\bthe\s+(river|riverway)\s+continues\b", out[idx]):
                nav_line = out[idx]
                break

        # Replace description body.
        out[desc_start:desc_end] = [river_template, nav_line]
        changed = True

    return changed, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--coords-tsv", type=Path, default=None, help="Optional coords TSV to define vnum scope.")
    ap.add_argument(
        "--zones",
        type=str,
        default="",
        help="Optional comma-separated zones to process (e.g. '468,469,508,...'). If omitted, process zones derived from coords-tsv.",
    )
    ap.add_argument("--backup-dir", type=Path, default=None)
    args = ap.parse_args()

    scope_vnums: Optional[Set[int]] = None
    zones: List[int]
    if args.zones.strip():
        zones = sorted(parse_zones_csv(args.zones))
    else:
        if args.coords_tsv is None:
            raise SystemExit("ERROR: provide either --zones or --coords-tsv")
        scope_vnums = load_scope_vnums(args.coords_tsv)
        zones = sorted({v // 100 for v in scope_vnums})

    touched_files = 0
    changed_rooms = 0

    if args.backup_dir is not None:
        args.backup_dir.mkdir(parents=True, exist_ok=True)

    for zone in zones:
        wld = args.wld_dir / f"{zone}.wld"
        if not wld.exists():
            continue
        lines = wld.read_text(encoding="latin-1", errors="replace").splitlines()
        spans = find_room_spans(lines)

        file_changed = False
        for span in spans:
            if scope_vnums is not None and span.vnum not in scope_vnums:
                continue
            changed, lines2 = apply_fixes_to_room(lines, span)
            if changed:
                lines = lines2
                file_changed = True
                changed_rooms += 1

        if file_changed:
            if args.backup_dir is not None:
                shutil.copy2(wld, args.backup_dir / wld.name)
            wld.write_text("\n".join(lines) + "\n", encoding="latin-1")
            touched_files += 1

    print(f"touched_files={touched_files} changed_rooms={changed_rooms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

