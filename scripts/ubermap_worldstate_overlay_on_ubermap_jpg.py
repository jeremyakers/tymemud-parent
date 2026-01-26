#!/usr/bin/env python3
"""
Render a worldstate overlay (from .wld sector truth) on top of ubermap.jpg.

Why:
- We need a fast visual sanity check that the *engine truth* (.wld sector numbers)
  matches the intended map layout from ubermap.jpg.
- This avoids relying on room titles (which may contain color codes and drift).

Inputs:
- ubermap.jpg
- wld-dir (MM32/lib/world/wld)
- optional expected terrain TSV (to label mismatches)

Output:
- A PNG with deep hatch overlays for: water / roads / forest / field / hills / mountain / city.
- Optionally label vnums on tiles of interest (mismatches or selected sector types).

Notes:
- Uses the same grid-rectangle detection as scripts/ubermap_jpg_extract_cells.py.
- Accounts for known swapped zone labels 539/540 using ZONES_ORDER from that script.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMG = ROOT / "Building_Design_Notes" / "ubermap.jpg"

# Import the zone order + grid detection from the existing extractor to avoid divergence.
# This file is executed as a script, so ensure repo root is on sys.path.
import sys  # noqa: E402

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ubermap_jpg_extract_cells import (  # type: ignore  # noqa: E402
    ZONES_ORDER,
    Rect,
    find_grid_rects,
)


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")


def parse_room_sectors(wld_path: Path) -> dict[int, int]:
    out: dict[int, int] = {}
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        m = ROOM_HEADER_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        # find the zone/flags/sector line after desc terminator
        j = i + 2
        while j < len(lines):
            ln = lines[j]
            if ln.strip() == "~" or ln.endswith("~"):
                j += 1
                break
            j += 1
        if j >= len(lines):
            break
        sector_line = lines[j].strip()
        parts = sector_line.split()
        if len(parts) >= 3:
            try:
                out[vnum] = int(parts[2])
            except Exception:
                pass
        i = j + 1
    return out


def load_expected(expected_tsv: Path) -> dict[int, int]:
    feat2sect = {
        "plains": 2,
        "forest_light": 3,
        "forest_dense": 3,
        "hills": 4,
        "dragonmount": 5,
        "mountain": 5,
        "river": 6,
        "road": 11,
        "town": 1,
        "insert": 1,
    }
    out: dict[int, int] = {}
    with expected_tsv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            z = int(row["zone"])
            cell = int(row["cell"])
            feat = row["feature"]
            if feat not in feat2sect:
                continue
            out[z * 100 + cell] = feat2sect[feat]
    return out


def hatch_tile(size: int, fg: tuple[int, int, int, int], bg: tuple[int, int, int, int] = (0, 0, 0, 0)) -> Image.Image:
    im = Image.new("RGBA", (size, size), bg)
    dr = ImageDraw.Draw(im)
    step = 6
    # diagonal hatch
    for x in range(-size, size * 2, step):
        dr.line((x, 0, x - size, size), fill=fg, width=2)
    return im


def sector_style(sector: int) -> tuple[str, tuple[int, int, int, int]]:
    # Return (label, hatch_rgba)
    if sector in (6, 7, 8):  # water
        return ("water", (0, 60, 200, 150))
    if sector in (10, 11):  # roads
        return ("road", (120, 70, 0, 160))
    if sector == 3:  # forest
        return ("forest", (0, 90, 0, 150))
    if sector == 2:  # field
        return ("field", (120, 120, 120, 90))
    if sector == 4:  # hills
        return ("hills", (0, 120, 120, 140))
    if sector == 5:  # mountain
        return ("mountain", (140, 140, 0, 150))
    if sector == 1:  # city
        return ("city", (0, 150, 180, 170))
    return ("other", (160, 0, 160, 120))


def paste_hatch(base: Image.Image, rect: tuple[int, int, int, int], hatch: Image.Image) -> None:
    x0, y0, x1, y1 = rect
    w = x1 - x0
    h = y1 - y0
    tile = hatch
    for y in range(y0, y1, tile.height):
        for x in range(x0, x1, tile.width):
            base.alpha_composite(tile, (x, y))


def main() -> int:
    ap = argparse.ArgumentParser(description="Overlay .wld sectors on ubermap.jpg")
    ap.add_argument("--img", type=Path, default=DEFAULT_IMG)
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--zones", type=str, required=True, help="Comma list or ranges (e.g. 537-540,567,638-640)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--expected-terrain-tsv", type=Path, default=None, help="Optional expected terrain TSV for mismatch highlighting")
    ap.add_argument("--label-mismatches", action="store_true")
    ap.add_argument("--label-alpha", type=int, default=235)
    args = ap.parse_args()

    # parse zone set
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

    img = Image.open(args.img).convert("RGBA")
    rects = find_grid_rects(img.convert("RGB"))
    if len(rects) != len(ZONES_ORDER):
        raise SystemExit(f"expected {len(ZONES_ORDER)} grids, found {len(rects)}")

    expected: dict[int, int] | None = None
    if args.expected_terrain_tsv is not None:
        expected = load_expected(args.expected_terrain_tsv)

    # tiny font for cell labels
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Precompute hatch tiles by sector group
    hatch_cache: dict[str, Image.Image] = {}

    out = img.copy()
    dr = ImageDraw.Draw(out)

    # Iterate zones in JPG visual order but only render requested zones
    for zone, grid in zip(ZONES_ORDER, rects, strict=True):
        if zone not in zones:
            continue

        wld = args.wld_dir / f"{zone}.wld"
        if not wld.exists():
            continue
        sectors = parse_room_sectors(wld)

        # Cell geometry inside the detected grid rect:
        # We assume a 10x10 layout and use proportional spacing.
        cell_w = grid.w() / 10.0
        cell_h = grid.h() / 10.0

        for row in range(10):
            for col in range(10):
                cell = row * 10 + col
                vnum = zone * 100 + cell
                sector = sectors.get(vnum)
                if sector is None:
                    continue

                label, rgba = sector_style(sector)
                if label not in hatch_cache:
                    hatch_cache[label] = hatch_tile(64, rgba)

                # shrink slightly to avoid overwriting grid borders
                x0 = int(grid.x0 + col * cell_w + 3)
                y0 = int(grid.y0 + row * cell_h + 3)
                x1 = int(grid.x0 + (col + 1) * cell_w - 3)
                y1 = int(grid.y0 + (row + 1) * cell_h - 3)
                paste_hatch(out, (x0, y0, x1, y1), hatch_cache[label])

                mismatch = False
                if expected is not None and vnum in expected:
                    mismatch = expected[vnum] != sector
                if mismatch:
                    # red outline
                    dr.rectangle((x0, y0, x1, y1), outline=(220, 0, 0, 220), width=3)
                    if args.label_mismatches and font is not None:
                        dr.text((x0 + 2, y0 + 2), str(vnum), fill=(0, 0, 0, args.label_alpha), font=font)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

