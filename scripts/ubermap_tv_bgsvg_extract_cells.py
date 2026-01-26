#!/usr/bin/env python3
"""
Extract Tar Valon overland road/river cells (zones 469/468) from Westlands-Background.svg.

Why this exists
--------------
We want `Building_Design_Notes/Westlands-Background.svg` to be our “north star” for
road/river routing around Tar Valon (notably the NW↔SE diagonal river geometry).

This script:
  - samples vector stroke paths in the SVG (roads/rivers),
  - maps them onto the 10×10 cell grid for zones 469 (west) and 468 (east),
  - writes a TSV + an optional PNG overlay for visual verification.

Important coordinate note
-------------------------
`svgpathtools.svg2paths2()` yields path coordinates in the *raw* SVG coordinate space (i.e.,
without ancestor `<g transform=...>` applied). The mapping constants below were derived using
that same raw space, and then translated for overlay rendering.

Usage (recommended)
-------------------
1) Ensure you have a rendered background PNG (any sufficiently large resolution works).
   Example already used in this repo:
     tmp/westlands_background_full_w12000.png

2) Run extraction + overlay:
   uvx --with svgpathtools --with numpy --with pillow \
     python scripts/ubermap_tv_bgsvg_extract_cells.py \
       --png tmp/westlands_background_full_w12000.png \
       --out-tsv tmp/bgsvg_tv_468_469_cells.tsv \
       --out-overlay tmp/bgsvg_tv_468_469_overlay.png
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from svgpathtools import svg2paths2  # type: ignore


SVG_DEFAULT = Path("Building_Design_Notes/Westlands-Background.svg")

# Tar Valon overland zones (from docs/ubermap/v2/westlands_v2_grid.tsv).
ZONES = {
    469: (15, 4),  # west
    468: (16, 4),  # east
}

# Local fit (raw coords) documented in docs/ubermap/tar_valon_rotation/westlands_background_tv_alignment.md
ZONE_W = 21.0
X0_RAW = 16.35
Y0_RAW = -58.60

# Observed constant translation between label glyph raw coords and rendered coords.
# (Used only for overlay placement on a rendered PNG.)
DX_ABS = 276.579
DY_ABS = 203.090


def _parse_style(style: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (style or "").split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def _hex_to_rgb(s: str) -> tuple[int, int, int] | None:
    s = (s or "").strip()
    if not s or s.lower() == "none":
        return None
    if s.startswith("#") and len(s) == 7:
        try:
            return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))
        except ValueError:
            return None
    return None


def _rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    mx = max(rf, gf, bf)
    mn = min(rf, gf, bf)
    df = mx - mn
    if df == 0:
        h = 0.0
    elif mx == rf:
        h = ((gf - bf) / df) % 6.0
    elif mx == gf:
        h = ((bf - rf) / df) + 2.0
    else:
        h = ((rf - gf) / df) + 4.0
    h /= 6.0
    s = 0.0 if mx == 0 else (df / mx)
    v = mx
    return (h, s, v)


def _stroke_width(attrs: dict[str, str]) -> float | None:
    style = _parse_style(attrs.get("style", "") or "")
    sw = attrs.get("stroke-width") or style.get("stroke-width")
    if sw is None:
        return None
    try:
        return float(str(sw).strip())
    except ValueError:
        return None


def _classify_path(attrs: dict[str, str]) -> str | None:
    style = _parse_style(attrs.get("style", "") or "")
    stroke = attrs.get("stroke") or style.get("stroke")
    rgb = _hex_to_rgb(str(stroke)) if stroke else None
    if rgb is None:
        return None
    h, s, v = _rgb_to_hsv(*rgb)
    hd = h * 360.0
    sw = _stroke_width(attrs)

    # Rivers: blue-ish.
    if 185.0 <= hd <= 235.0 and s >= 0.25 and v >= 0.25:
        return "river"

    # Roads: solid brown-ish. Elevation lines are often lighter/grayish and/or very thin.
    if 15.0 <= hd <= 55.0 and s >= 0.25 and 0.10 <= v <= 0.75:
        if sw is None or sw <= 0.35:
            return "road"

    return None


def _sample_points(path, step: float) -> tuple[np.ndarray, np.ndarray]:
    try:
        L = float(path.length(error=1e-3))
    except Exception:
        return (np.array([], dtype=np.float64), np.array([], dtype=np.float64))
    if not math.isfinite(L) or L <= 0:
        return (np.array([], dtype=np.float64), np.array([], dtype=np.float64))
    n = max(2, int(L / step))
    ts = np.linspace(0.0, 1.0, n, dtype=np.float64)
    pts = np.array([path.point(t) for t in ts])
    return (pts.real.astype(np.float64), pts.imag.astype(np.float64))


def _extract_cells(xs: np.ndarray, ys: np.ndarray, gx: int, gy: int) -> set[int]:
    if xs.size == 0:
        return set()
    zx = np.floor((xs - X0_RAW) / ZONE_W).astype(np.int32)
    zy = np.floor((ys - Y0_RAW) / ZONE_W).astype(np.int32)
    m = (zx == gx) & (zy == gy)
    if not np.any(m):
        return set()
    xs2 = xs[m]
    ys2 = ys[m]
    lx = (xs2 - (X0_RAW + gx * ZONE_W)) / ZONE_W
    ly = (ys2 - (Y0_RAW + gy * ZONE_W)) / ZONE_W
    cx = np.clip((lx * 10.0).astype(np.int32), 0, 9)
    cy = np.clip((ly * 10.0).astype(np.int32), 0, 9)
    cell = (cy * 10 + cx).astype(np.int32)
    return set(int(c) for c in np.unique(cell))


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract Tar Valon road/river cells from Westlands-Background.svg")
    ap.add_argument("--svg", type=Path, default=SVG_DEFAULT)
    ap.add_argument("--png", type=Path, required=True, help="Rendered background PNG used for overlay")
    ap.add_argument("--out-tsv", type=Path, required=True)
    ap.add_argument("--out-overlay", type=Path, default=None)
    ap.add_argument(
        "--overlay-outline-only",
        action="store_true",
        help="Draw road/river cells as outlines (no fill), matching the preferred overlay style.",
    )
    ap.add_argument(
        "--overlay-label-vnums",
        action="store_true",
        help="Label every road/river cell with its vnum (zone*100 + cell).",
    )
    args = ap.parse_args()

    paths, attrs_list, _ = svg2paths2(str(args.svg))

    road_x: list[np.ndarray] = []
    road_y: list[np.ndarray] = []
    river_x: list[np.ndarray] = []
    river_y: list[np.ndarray] = []

    # dense enough for 10x10 cell hits
    step = 0.9
    for p, attrs in zip(paths, attrs_list, strict=True):
        feat = _classify_path(attrs)
        if feat not in ("road", "river"):
            continue
        xs, ys = _sample_points(p, step)
        if xs.size == 0:
            continue
        if feat == "road":
            road_x.append(xs)
            road_y.append(ys)
        else:
            river_x.append(xs)
            river_y.append(ys)

    rx = np.concatenate(road_x) if road_x else np.array([], dtype=np.float64)
    ry = np.concatenate(road_y) if road_y else np.array([], dtype=np.float64)
    wx = np.concatenate(river_x) if river_x else np.array([], dtype=np.float64)
    wy = np.concatenate(river_y) if river_y else np.array([], dtype=np.float64)

    extracted: dict[int, dict[str, set[int]]] = {z: {"road": set(), "river": set()} for z in ZONES}
    for z, (gx, gy) in ZONES.items():
        extracted[z]["road"] = _extract_cells(rx, ry, gx, gy)
        extracted[z]["river"] = _extract_cells(wx, wy, gx, gy)

    # Write TSV as one row per cell for easy downstream joins.
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["zone", "cell", "feature"])
        for z in sorted(extracted.keys()):
            for feat in ("river", "road"):
                for cell in sorted(extracted[z][feat]):
                    w.writerow([z, f"{cell:02d}", feat])

    print(f"wrote {args.out_tsv}")

    if args.out_overlay is not None:
        head = args.svg.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', head)
        if not m:
            raise SystemExit("Could not parse SVG viewBox for overlay scale")
        vw = float(m.group(1))

        img = Image.open(args.png).convert("RGBA")
        scale = img.size[0] / vw
        draw = ImageDraw.Draw(img, "RGBA")
        font = ImageFont.load_default()

        # Convert raw-origin to rendered-origin via constant translation (labels+map group).
        x0 = X0_RAW + DX_ABS
        y0 = Y0_RAW + DY_ABS

        C_ZONE = (255, 0, 255, 220)
        C_GRID = (0, 0, 0, 80)
        C_RIVER_FILL = (0, 90, 255, 110)
        C_ROAD_FILL = (140, 80, 20, 110)
        C_RIVER_OUTLINE = (0, 90, 255, 220)
        C_ROAD_OUTLINE = (140, 80, 20, 220)
        C_LABEL = (0, 0, 0, 220)

        minx = 1e9
        miny = 1e9
        maxx = -1e9
        maxy = -1e9

        for z, (gx, gy) in ZONES.items():
            zx0 = x0 + gx * ZONE_W
            zy0 = y0 + gy * ZONE_W
            zx1 = zx0 + ZONE_W
            zy1 = zy0 + ZONE_W

            px0, py0 = zx0 * scale, zy0 * scale
            px1, py1 = zx1 * scale, zy1 * scale

            draw.rectangle([px0, py0, px1, py1], outline=C_ZONE, width=3)

            cw = (px1 - px0) / 10.0
            ch = (py1 - py0) / 10.0

            # If a cell is both (should be rare), prefer river.
            cell_feat: dict[int, str] = {}
            for cell in extracted[z]["road"]:
                cell_feat[cell] = "road"
            for cell in extracted[z]["river"]:
                cell_feat[cell] = "river"

            for cell, feat in sorted(cell_feat.items()):
                cx = cell % 10
                cy = cell // 10
                cx0 = px0 + cx * cw
                cy0 = py0 + cy * ch
                cx1 = cx0 + cw
                cy1 = cy0 + ch

                if feat == "river":
                    fill = None if args.overlay_outline_only else C_RIVER_FILL
                    outline = C_RIVER_OUTLINE
                else:
                    fill = None if args.overlay_outline_only else C_ROAD_FILL
                    outline = C_ROAD_OUTLINE

                if args.overlay_outline_only:
                    draw.rectangle([cx0, cy0, cx1, cy1], fill=None, outline=outline, width=3)
                else:
                    draw.rectangle([cx0, cy0, cx1, cy1], fill=fill, outline=None)

                if args.overlay_label_vnums:
                    vnum = z * 100 + cell
                    label = str(vnum)
                    try:
                        bbox = draw.textbbox((0, 0), label, font=font)  # Pillow >= 8.0
                        tw = bbox[2] - bbox[0]
                        th = bbox[3] - bbox[1]
                    except Exception:
                        tw, th = draw.textsize(label, font=font)  # Pillow fallback
                    tx = (cx0 + cx1) / 2.0 - tw / 2.0
                    ty = (cy0 + cy1) / 2.0 - th / 2.0
                    draw.text((tx, ty), label, font=font, fill=C_LABEL)

            for i in range(1, 10):
                draw.line([px0 + i * cw, py0, px0 + i * cw, py1], fill=C_GRID, width=1)
                draw.line([px0, py0 + i * ch, px1, py0 + i * ch], fill=C_GRID, width=1)

            minx = min(minx, px0)
            miny = min(miny, py0)
            maxx = max(maxx, px1)
            maxy = max(maxy, py1)

        pad = 240
        cx0 = max(0, int(minx - pad))
        cy0 = max(0, int(miny - pad))
        cx1 = min(img.size[0], int(maxx + pad))
        cy1 = min(img.size[1], int(maxy + pad))

        args.out_overlay.parent.mkdir(parents=True, exist_ok=True)
        img.crop((cx0, cy0, cx1, cy1)).save(args.out_overlay)
        print(f"wrote {args.out_overlay}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

