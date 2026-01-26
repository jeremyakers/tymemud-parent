#!/usr/bin/env python3
"""
Generate a v2 "Ubermap-style" overlay for the full Westlands map.

Inputs:
- base image: Building_Design_Notes/wheel_of_time___westland_map-fullview.jpg
- grid spec (TSV): docs/ubermap/v2/westlands_v2_grid.tsv

The TSV format is:
  gx  gy  label  zone_id  notes

Where:
- gx,gy are integer grid coordinates
- label is a short anchor/region name (optional)
- zone_id is an integer or blank (optional)

Output:
- docs/ubermap/v2/westlands_v2_overlay.svg
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_IMG = ROOT / "Building_Design_Notes/wheel_of_time___westland_map-fullview.jpg"
DEFAULT_TSV = ROOT / "docs/ubermap/v2/westlands_v2_grid.tsv"
DEFAULT_OUT = ROOT / "docs/ubermap/v2/westlands_v2_overlay.svg"


@dataclass(frozen=True)
class Cell:
    gx: int
    gy: int
    label: str
    zone_id: str
    notes: str


def parse_tsv(path: Path) -> tuple[list[Cell], int, int]:
    cells: list[Cell] = []
    max_x = 0
    max_y = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith("gx\t"):
            continue
        parts = line.split("\t")
        while len(parts) < 5:
            parts.append("")
        gx = int(parts[0])
        gy = int(parts[1])
        label = parts[2].strip()
        zone_id = parts[3].strip()
        notes = parts[4].strip()
        cells.append(Cell(gx=gx, gy=gy, label=label, zone_id=zone_id, notes=notes))
        max_x = max(max_x, gx)
        max_y = max(max_y, gy)
    return cells, max_x + 1, max_y + 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-img", type=Path, default=DEFAULT_BASE_IMG)
    ap.add_argument("--grid-tsv", type=Path, default=DEFAULT_TSV)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--cols", type=int, default=None, help="Override grid columns")
    ap.add_argument("--rows", type=int, default=None, help="Override grid rows")
    args = ap.parse_args()

    base_img = args.base_img
    # We avoid embedding the raster; SVG references it by relative path.
    rel_href = Path("../../Building_Design_Notes") / base_img.name

    cells, inferred_cols, inferred_rows = parse_tsv(args.grid_tsv)
    cols = args.cols or inferred_cols
    rows = args.rows or inferred_rows

    # Image size is known (1600x1241), but we read it from `file` externally.
    # Keep it configurable by constants here:
    width = 1600
    height = 1241
    cell_w = width / cols
    cell_h = height / rows

    # Basic SVG.
    out: list[str] = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    out.append(f'  <image x="0" y="0" width="{width}" height="{height}" href="{rel_href.as_posix()}" />')

    # Grid lines (semi-transparent).
    out.append('  <g id="grid" stroke="rgba(0,0,0,0.35)" stroke-width="1">')
    for x in range(cols + 1):
        xx = x * cell_w
        out.append(f'    <line x1="{xx:.3f}" y1="0" x2="{xx:.3f}" y2="{height}" />')
    for y in range(rows + 1):
        yy = y * cell_h
        out.append(f'    <line x1="0" y1="{yy:.3f}" x2="{width}" y2="{yy:.3f}" />')
    out.append("  </g>")

    # Labels.
    out.append('  <g id="labels" font-family="monospace" font-size="11" fill="rgba(0,0,0,0.9)">')
    for c in cells:
        x = c.gx * cell_w + 4
        y = c.gy * cell_h + 14
        # show zone id if present, else just coords.
        ztxt = f"Z{c.zone_id}" if c.zone_id else ""
        ltxt = c.label
        out.append(f'    <text x="{x:.3f}" y="{y:.3f}" stroke="rgba(255,255,255,0.85)" stroke-width="3" paint-order="stroke">{c.gx},{c.gy} {ztxt} {ltxt}</text>')
    out.append("  </g>")

    out.append("</svg>")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

