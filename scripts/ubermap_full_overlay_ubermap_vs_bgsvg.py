#!/usr/bin/env python3
"""
Render a single full-image overlay on top of `Building_Design_Notes/ubermap.jpg`:

- Fill = ubermap.jpg-derived road/river cells (v1 expected)
- Stroke = Westlands-Background.svg-derived road/river cells (pre-extracted TSV)

This exists to avoid ad-hoc, huge inline python heredocs and to make the overlay
reproducible and reviewable.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMG = ROOT / "Building_Design_Notes" / "ubermap.jpg"
DEFAULT_V1_TSV = ROOT / "docs" / "ubermap" / "v2" / "extracts" / "v1_ubermap_road_river_cells.tsv"
DEFAULT_BGSVG_TSV = ROOT / "tmp" / "bgsvg_v1slice_road_river_cells.tsv"

FEATURES = ("river", "road")


def _load_cells(tsv: Path) -> dict[int, dict[str, set[int]]]:
    out: dict[int, dict[str, set[int]]] = {}
    for ln in tsv.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.lower().startswith("zone\t"):
            continue
        parts = ln.split("\t")
        if len(parts) < 3:
            continue
        z = int(parts[0])
        cell = int(parts[1])
        feat = parts[2].strip()
        if feat not in FEATURES:
            continue
        out.setdefault(z, {"river": set(), "road": set()})[feat].add(cell)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Render full ubermap.jpg overlay (fill=v1, stroke=bgsvg)")
    ap.add_argument("--img", type=Path, default=DEFAULT_IMG, help="Input ubermap.jpg")
    ap.add_argument("--v1-tsv", type=Path, default=DEFAULT_V1_TSV, help="TSV: zone/cell/feature from ubermap.jpg")
    ap.add_argument("--bgsvg-tsv", type=Path, default=DEFAULT_BGSVG_TSV, help="TSV: zone/cell/feature from bgsvg extraction")
    ap.add_argument("--out", type=Path, required=True, help="Output PNG")
    ap.add_argument("--out-small", type=Path, default=None, help="Optional downscaled PNG for quick viewing")
    ap.add_argument("--small-width", type=int, default=900, help="Width for --out-small (default: 900px)")
    ap.add_argument(
        "--no-fill",
        action="store_true",
        help="Do not draw fill cells (keeps the underlying ubermap.jpg visible).",
    )
    args = ap.parse_args()

    # Import grid detection from the canonical extractor so we always match its behavior.
    # This repo doesn't define `scripts` as a Python package, so add the scripts dir to sys.path.
    sys.path.insert(0, str(ROOT / "scripts"))
    import ubermap_jpg_extract_cells as uj  # type: ignore

    img = Image.open(args.img).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    rects = uj.find_grid_rects(img.convert("RGB"))
    zones_order = list(getattr(uj, "ZONES_ORDER"))
    if len(rects) != len(zones_order):
        raise SystemExit(f"grid detection mismatch: rects={len(rects)} zones_order={len(zones_order)}")

    bg = _load_cells(args.bgsvg_tsv)
    v1 = _load_cells(args.v1_tsv) if not args.no_fill else {}

    # Colors (match per-zone overlays)
    fill_river = (47, 103, 199, 90)
    fill_road = (185, 138, 75, 90)
    fill_both = (176, 124, 255, 90)

    stroke_river = (0, 85, 255, 255)
    stroke_road = (107, 63, 0, 255)
    stroke_both = (106, 0, 255, 255)

    inset = 6
    for zone, rect in zip(zones_order, rects, strict=True):
        got = bg.get(zone, {"river": set(), "road": set()})

        x0 = rect.x0 + inset
        y0 = rect.y0 + inset
        x1 = rect.x1 - inset
        y1 = rect.y1 - inset
        cw = (x1 - x0) / 10.0
        ch = (y1 - y0) / 10.0

        if font is not None:
            draw.text((rect.x0 + 4, rect.y0 + 4), str(zone), fill=(255, 255, 255, 255), font=font)

        for row in range(10):
            for col in range(10):
                cell = row * 10 + col
                cx0 = int(x0 + col * cw)
                cy0 = int(y0 + row * ch)
                cx1 = int(x0 + (col + 1) * cw)
                cy1 = int(y0 + (row + 1) * ch)

                if not args.no_fill:
                    # Fill: v1 expected.
                    # (This is optional because it can obscure the underlying ubermap.jpg.)
                    exp = v1.get(zone, {"river": set(), "road": set()})
                    in_r = cell in exp.get("river", set())
                    in_d = cell in exp.get("road", set())
                    fill = None
                    if in_r and in_d:
                        fill = fill_both
                    elif in_r:
                        fill = fill_river
                    elif in_d:
                        fill = fill_road
                    if fill is not None:
                        draw.rectangle([cx0, cy0, cx1, cy1], fill=fill, outline=None)

                # Stroke: bgsvg extracted.
                g_r = cell in got.get("river", set())
                g_d = cell in got.get("road", set())
                stroke = None
                if g_r and g_d:
                    stroke = stroke_both
                elif g_r:
                    stroke = stroke_river
                elif g_d:
                    stroke = stroke_road
                if stroke is not None:
                    draw.rectangle([cx0 + 1, cy0 + 1, cx1 - 1, cy1 - 1], outline=stroke, width=2)

    legend = [
        "Overlay: ubermap.jpg vs Westlands-Background.svg",
        "Fill = ubermap.jpg extracted cells (v1 expected)" if not args.no_fill else "Fill = (disabled)",
        "Stroke = bgsvg extracted cells",
        "Blue=river  Brown=road  Purple=both",
    ]

    if font is not None:
        lx, ly = 12, 12
        pad = 6
        line_h = 12
        max_w = 0
        for s in legend:
            max_w = max(max_w, int(draw.textlength(s, font=font)))
        box_w = max_w + pad * 2
        box_h = len(legend) * line_h + pad * 2
        draw.rectangle(
            [lx - 4, ly - 4, lx - 4 + box_w, ly - 4 + box_h],
            fill=(0, 0, 0, 160),
            outline=(255, 255, 255, 180),
            width=1,
        )
        yy = ly
        for s in legend:
            draw.text((lx, yy), s, fill=(255, 255, 255, 255), font=font)
            yy += line_h

    args.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.out)

    if args.out_small is not None:
        small_w = max(50, int(args.small_width))
        scale = small_w / img.size[0]
        small_h = int(img.size[1] * scale)
        img.resize((small_w, small_h), resample=Image.Resampling.BILINEAR).save(args.out_small)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

