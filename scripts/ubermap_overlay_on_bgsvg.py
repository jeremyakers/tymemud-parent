#!/usr/bin/env python3
"""
Overlay road/river cell grids on a *rendered* Westlands-Background.svg image.

Goal
----
Produce a visual that makes it easy to judge how well the 10×10 cell hits align
with the actual vector linework on the background map.

We draw:
- bgsvg-derived cells: strong strokes (blue/brown/purple)
- ubermap.jpg-derived (v1 expected) cells: very light translucent fill + diagonal hatch

Outputs are cropped to the region that corresponds to the v1 slice shown in
Building_Design_Notes/ubermap.jpg (the 19 zone-grids).
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
SVG_DEFAULT = ROOT / "Building_Design_Notes" / "Westlands-Background.svg"
BGPNG_DEFAULT = ROOT / "tmp" / "westlands_background_full_w12000.png"

V1_TSV_DEFAULT = ROOT / "docs" / "ubermap" / "v2" / "extracts" / "v1_ubermap_road_river_cells.tsv"
BGSVG_TSV_DEFAULT = ROOT / "tmp" / "bgsvg_v1slice_road_river_cells.tsv"
VERIFY_DEFAULT = ROOT / "docs" / "ubermap" / "v2" / "extracts" / "background_svg_verify_537_540.tsv"

FEATURES = ("river", "road")

# v1 slice zone ids visible in ubermap.jpg
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

# WLD parsing (for deriving zone relative coords from actual cross-zone exits)
_ROOM_RE = re.compile(r"^#(\d+)\s*$")
_DIR_RE = re.compile(r"^D(\d+)\s*$")
_INFO_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s+(-?\d+)\s*$")


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
        if z not in V1_ZONE_SET:
            continue
        cell = int(parts[1])
        feat = parts[2].strip()
        if feat not in FEATURES:
            continue
        out.setdefault(z, {"river": set(), "road": set()})[feat].add(cell)
    # ensure all zones exist
    for z in V1_ZONES:
        out.setdefault(z, {"river": set(), "road": set()})
    return out


def _iter_exits(wld_path: Path):
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
            # exit desc until ~
            while i < len(lines) and lines[i].strip() != "~" and not lines[i].endswith("~"):
                i += 1
            if i < len(lines):
                i += 1
            # keywords until ~
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


def _derive_v1_zone_coords(*, wld_dir: Path) -> dict[int, tuple[int, int]]:
    """
    Derive relative zone coords for the v1 slice using only boundary-consistent N/E/S/W exits.
    Anchor: zone 469 = (0,0).
    """
    adj: dict[int, list[tuple[int, int, int]]] = {z: [] for z in V1_ZONES}
    for z in V1_ZONES:
        wld = wld_dir / f"{z}.wld"
        for room, d, to in _iter_exits(wld):
            if to <= 0:
                continue
            z_to = to // 100
            if z_to not in V1_ZONE_SET or z_to == z:
                continue
            cell = room % 100
            cell_to = to % 100
            # only accept boundary-consistent cardinal links
            if d == 0:  # north
                if cell < 10 and cell_to == cell + 90:
                    adj[z].append((z_to, 0, -1))
            elif d == 2:  # south
                if cell >= 90 and cell_to == cell - 90:
                    adj[z].append((z_to, 0, 1))
            elif d == 1:  # east
                if cell % 10 == 9 and cell_to == cell - 9:
                    adj[z].append((z_to, 1, 0))
            elif d == 3:  # west
                if cell % 10 == 0 and cell_to == cell + 9:
                    adj[z].append((z_to, -1, 0))

    coords: dict[int, tuple[int, int]] = {469: (0, 0)}
    q: deque[int] = deque([469])
    while q:
        z = q.popleft()
        x, y = coords[z]
        for nbr, dx, dy in adj.get(z, []):
            nx, ny = x + dx, y + dy
            if nbr not in coords:
                coords[nbr] = (nx, ny)
                q.append(nbr)
            else:
                if coords[nbr] != (nx, ny):
                    raise RuntimeError(f"zone coord conflict: {z}->{nbr} existing={coords[nbr]} new={(nx, ny)}")

    missing = sorted(V1_ZONE_SET - set(coords.keys()))
    if missing:
        raise RuntimeError(f"missing coords for zones: {missing}")
    return coords


def _parse_verify_fit(path: Path) -> tuple[float, float, float]:
    """
    Parse best_zone_w and row_origin_540 from background_svg_verify_537_540.tsv.
    Returns (zone_w, row_origin_x_for_zone540, row_origin_y_for_zone540).
    """
    best_w = None
    x0 = None
    y0 = None
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "best_zone_w=" in ln and "row_origin_540=" in ln:
            m = re.search(r"best_zone_w=([0-9.]+)", ln)
            m2 = re.search(r"row_origin_540=\(([0-9.]+),([0-9.]+)\)", ln)
            if m and m2:
                best_w = float(m.group(1))
                x0 = float(m2.group(1))
                y0 = float(m2.group(2))
                break
    if best_w is None or x0 is None or y0 is None:
        raise RuntimeError("could not parse best_zone_w/row_origin_540 from verify TSV")
    return best_w, x0, y0


def _parse_viewbox(svg: Path) -> tuple[float, float]:
    head = svg.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', head)
    if not m:
        raise RuntimeError("could not parse viewBox=\"0 0 W H\" from SVG")
    return float(m.group(1)), float(m.group(2))


def _parse_outer_translate(svg: Path) -> tuple[float, float]:
    """
    Grab the outermost <g transform=\"translate(x y)\"> directly under the root.
    This matches the map group's top-level translation in Westlands-Background.svg.
    """
    tree = ET.parse(svg)
    root = tree.getroot()
    for child in list(root):
        tag = child.tag.split("}", 1)[-1]
        if tag != "g":
            continue
        tr = child.attrib.get("transform", "")
        m = re.match(r"translate\(\s*([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s*\)", tr)
        if m:
            return float(m.group(1)), float(m.group(2))
    # Fallback: scan raw text for the first translate (works for this file)
    head = svg.read_text(encoding="utf-8", errors="replace")
    m2 = re.search(r'transform="translate\(\s*([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s*\)"', head)
    if m2:
        return float(m2.group(1)), float(m2.group(2))
    raise RuntimeError("could not find outer translate(...) in SVG")


def _draw_hatch(draw: ImageDraw.ImageDraw, rect: tuple[int, int, int, int], color: tuple[int, int, int, int], step: int) -> None:
    """
    Draw a diagonal hatch *clipped to the rectangle*.

    PIL's ImageDraw doesn't support clipping. To avoid hatch bleed outside the
    intended square (user-visible as stray lines), we render the hatch into a
    small RGBA tile sized to the rect and paste it onto the destination.
    """
    raise RuntimeError("_draw_hatch() is deprecated; use _paste_hatch_tile().")


def _make_hatch_tile(*, w: int, h: int, color: tuple[int, int, int, int], step: int) -> Image.Image:
    w = max(1, int(w))
    h = max(1, int(h))
    step = max(3, int(step))
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile, "RGBA")
    # Diagonal hatch: slope +1 (top-left to bottom-right).
    # Draw across an expanded range; tile bounds will clip.
    for i in range(-h, w + h, step):
        d.line([(i, 0), (i + h, h)], fill=color, width=1)
    return tile


def _paste_hatch_tile(
    base: Image.Image,
    *,
    rect: tuple[int, int, int, int],
    color: tuple[int, int, int, int],
    step: int,
    _cache: dict[tuple[int, int, tuple[int, int, int, int], int], Image.Image],
) -> None:
    x0, y0, x1, y1 = rect
    w = x1 - x0
    h = y1 - y0
    if w <= 1 or h <= 1:
        return
    key = (w, h, color, int(step))
    tile = _cache.get(key)
    if tile is None:
        tile = _make_hatch_tile(w=w, h=h, color=color, step=step)
        _cache[key] = tile
    base.alpha_composite(tile, dest=(x0, y0))


def main() -> int:
    ap = argparse.ArgumentParser(description="Overlay bgsvg/v1 cell grids on a rendered Westlands-Background image.")
    ap.add_argument("--svg", type=Path, default=SVG_DEFAULT, help="Westlands-Background.svg")
    ap.add_argument("--bg-png", type=Path, default=BGPNG_DEFAULT, help="Rendered full background PNG (e.g. tmp/westlands_background_full_w12000.png)")
    ap.add_argument("--verify-tsv", type=Path, default=VERIFY_DEFAULT, help="background_svg_verify_537_540.tsv (for zone_w+origin)")
    ap.add_argument("--v1-tsv", type=Path, default=V1_TSV_DEFAULT, help="v1 ubermap.jpg expected cells TSV")
    ap.add_argument("--bgsvg-tsv", type=Path, default=BGSVG_TSV_DEFAULT, help="bgsvg extracted cells TSV (v1-slice)")
    ap.add_argument("--wld-dir", type=Path, default=ROOT / "MM32" / "lib" / "world" / "wld", help="Directory containing <zone>.wld files")
    ap.add_argument("--out", type=Path, required=True, help="Output PNG")
    ap.add_argument("--out-small", type=Path, default=None, help="Optional downscaled PNG")
    ap.add_argument("--small-width", type=int, default=1200, help="Width for --out-small (default: 1200px)")
    ap.add_argument("--pad-px", type=int, default=40, help="Crop padding in pixels")
    ap.add_argument("--stroke-width", type=int, default=3, help="Stroke width for bgsvg cells")
    ap.add_argument("--fill-alpha", type=int, default=24, help="Alpha (0-255) for v1 translucent fill")
    ap.add_argument("--hatch-alpha", type=int, default=120, help="Alpha (0-255) for v1 hatch lines")
    ap.add_argument("--hatch-step", type=int, default=8, help="Pixel spacing for v1 hatch lines")
    ap.add_argument(
        "--hatch-only",
        action="store_true",
        help="Do not draw any v1 fill; draw only hatch (keeps background linework visible).",
    )
    ap.add_argument(
        "--label-bgsvg-vnums",
        action="store_true",
        help="Label every bgsvg-stroked cell with its vnum (zone*100+cell).",
    )
    ap.add_argument(
        "--label-all-vnums",
        action="store_true",
        help="Label every road/river cell (v1 hatch+fill OR bgsvg stroke) with its vnum (zone*100+cell).",
    )
    ap.add_argument(
        "--label-alpha",
        type=int,
        default=235,
        help="Alpha (0-255) for bgsvg vnum labels (default: 235).",
    )
    args = ap.parse_args()

    if not args.bg_png.exists():
        raise SystemExit(f"Missing background PNG: {args.bg_png}")

    v1 = _load_cells(args.v1_tsv)
    bg = _load_cells(args.bgsvg_tsv)

    coords = _derive_v1_zone_coords(wld_dir=args.wld_dir)
    inv = {v: k for k, v in coords.items()}
    min_zx = min(x for x, _ in coords.values())
    max_zx = max(x for x, _ in coords.values())
    min_zy = min(y for _, y in coords.values())
    max_zy = max(y for _, y in coords.values())

    zone_w, x0_zone540, y0_zone540 = _parse_verify_fit(args.verify_tsv)
    zx_540, zy_540 = coords[540]
    x_origin = x0_zone540 - (zx_540 * zone_w)
    y_origin = y0_zone540 - (zy_540 * zone_w)

    vb_w, _vb_h = _parse_viewbox(args.svg)
    tr_x, tr_y = _parse_outer_translate(args.svg)

    bg_full = Image.open(args.bg_png).convert("RGBA")
    scale = bg_full.size[0] / vb_w

    # Bounding rect in raw coords for the v1 slice.
    raw_x0 = x_origin + (min_zx * zone_w)
    raw_y0 = y_origin + (min_zy * zone_w)
    raw_x1 = x_origin + ((max_zx + 1) * zone_w)
    raw_y1 = y_origin + ((max_zy + 1) * zone_w)

    # Convert raw -> abs (apply translate) -> pixels.
    abs_x0 = raw_x0 + tr_x
    abs_y0 = raw_y0 + tr_y
    abs_x1 = raw_x1 + tr_x
    abs_y1 = raw_y1 + tr_y

    px0 = int(abs_x0 * scale) - int(args.pad_px)
    py0 = int(abs_y0 * scale) - int(args.pad_px)
    px1 = int(abs_x1 * scale) + int(args.pad_px)
    py1 = int(abs_y1 * scale) + int(args.pad_px)

    px0 = max(0, min(bg_full.size[0] - 1, px0))
    py0 = max(0, min(bg_full.size[1] - 1, py0))
    px1 = max(px0 + 1, min(bg_full.size[0], px1))
    py1 = max(py0 + 1, min(bg_full.size[1], py1))

    crop = bg_full.crop((px0, py0, px1, py1))
    draw = ImageDraw.Draw(crop, "RGBA")

    # Fonts: prefer a scalable TTF if present for legible in-cell labels; fall back to default.
    def _load_font(size: int):
        size = max(6, int(size))
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=size)
        except Exception:
            try:
                return ImageFont.load_default()
            except Exception:
                return None

    font = _load_font(12)

    # Colors
    # bgsvg strokes (strong)
    stroke_river = (0, 85, 255, 255)
    stroke_road = (107, 63, 0, 255)
    stroke_both = (106, 0, 255, 255)

    # v1 fill/hatch (light)
    a_fill = max(0, min(255, int(args.fill_alpha)))
    a_hatch = max(0, min(255, int(args.hatch_alpha)))
    fill_river = (47, 103, 199, a_fill)
    fill_road = (185, 138, 75, a_fill)
    fill_both = (176, 124, 255, a_fill)
    hatch_river = (47, 103, 199, a_hatch)
    hatch_road = (185, 138, 75, a_hatch)
    hatch_both = (176, 124, 255, a_hatch)

    # For each zone+cell, compute pixel rect in the crop and draw.
    cell_w_raw = zone_w / 10.0
    stroke_w = max(1, int(args.stroke_width))
    label_alpha = max(0, min(255, int(args.label_alpha)))
    label_fg = (255, 255, 255, label_alpha)
    label_outline = (0, 0, 0, min(255, int(label_alpha * 0.95)))

    hatch_cache: dict[tuple[int, int, tuple[int, int, int, int], int], Image.Image] = {}
    font_cache: dict[int, object] = {}
    for z in V1_ZONES:
        zx, zy = coords[z]
        # zone raw rect
        z_raw_x0 = x_origin + zx * zone_w
        z_raw_y0 = y_origin + zy * zone_w

        for cell in range(100):
            r, c = divmod(cell, 10)
            c_raw_x0 = z_raw_x0 + c * cell_w_raw
            c_raw_y0 = z_raw_y0 + r * cell_w_raw
            c_raw_x1 = c_raw_x0 + cell_w_raw
            c_raw_y1 = c_raw_y0 + cell_w_raw

            # raw -> abs -> px (crop-local)
            c_abs_x0 = c_raw_x0 + tr_x
            c_abs_y0 = c_raw_y0 + tr_y
            c_abs_x1 = c_raw_x1 + tr_x
            c_abs_y1 = c_raw_y1 + tr_y

            x0p = int(c_abs_x0 * scale) - px0
            y0p = int(c_abs_y0 * scale) - py0
            x1p = int(c_abs_x1 * scale) - px0
            y1p = int(c_abs_y1 * scale) - py0

            if x1p <= 0 or y1p <= 0 or x0p >= crop.size[0] or y0p >= crop.size[1]:
                continue

            # v1 expected: light fill + hatch
            v_r = cell in v1[z]["river"]
            v_d = cell in v1[z]["road"]
            if v_r or v_d:
                if v_r and v_d:
                    fcol = fill_both
                    hcol = hatch_both
                elif v_r:
                    fcol = fill_river
                    hcol = hatch_river
                else:
                    fcol = fill_road
                    hcol = hatch_road
                if not args.hatch_only:
                    draw.rectangle([x0p, y0p, x1p, y1p], fill=fcol, outline=None)
                _paste_hatch_tile(
                    crop,
                    rect=(x0p, y0p, x1p, y1p),
                    color=hcol,
                    step=int(args.hatch_step),
                    _cache=hatch_cache,
                )

            # bgsvg: strong stroke
            b_r = cell in bg[z]["river"]
            b_d = cell in bg[z]["road"]
            if b_r or b_d:
                if b_r and b_d:
                    scol = stroke_both
                elif b_r:
                    scol = stroke_river
                else:
                    scol = stroke_road
                draw.rectangle([x0p, y0p, x1p, y1p], outline=scol, width=stroke_w)

                if args.label_bgsvg_vnums:
                    vnum = z * 100 + cell
                    text = str(vnum)
                    # Choose font size relative to cell size in pixels.
                    cw = max(1, x1p - x0p)
                    ch = max(1, y1p - y0p)
                    size = max(7, min(14, int(min(cw, ch) * 0.30)))
                    fnt = font_cache.get(size)
                    if fnt is None:
                        fnt = _load_font(size)
                        font_cache[size] = fnt
                    if fnt is not None:
                        # Center the label; add a thin outline for contrast.
                        try:
                            tw = int(draw.textlength(text, font=fnt))
                            th = int(size)
                        except Exception:
                            tw = len(text) * size // 2
                            th = size
                        tx = x0p + (cw - tw) // 2
                        ty = y0p + (ch - th) // 2
                        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            draw.text((tx + ox, ty + oy), text, fill=label_outline, font=fnt)
                        draw.text((tx, ty), text, fill=label_fg, font=fnt)

            # Optional: label all road/river cells (v1 OR bgsvg). Prefer the bgsvg label if present.
            if args.label_all_vnums and (v_r or v_d or b_r or b_d) and not args.label_bgsvg_vnums:
                vnum = z * 100 + cell
                text = str(vnum)
                cw = max(1, x1p - x0p)
                ch = max(1, y1p - y0p)
                size = max(7, min(14, int(min(cw, ch) * 0.30)))
                fnt = font_cache.get(size)
                if fnt is None:
                    fnt = _load_font(size)
                    font_cache[size] = fnt
                if fnt is not None:
                    try:
                        tw = int(draw.textlength(text, font=fnt))
                        th = int(size)
                    except Exception:
                        tw = len(text) * size // 2
                        th = size
                    tx = x0p + (cw - tw) // 2
                    ty = y0p + (ch - th) // 2
                    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        draw.text((tx + ox, ty + oy), text, fill=label_outline, font=fnt)
                    draw.text((tx, ty), text, fill=label_fg, font=fnt)

    # Legend
    legend = [
        "Overlay on Westlands-Background (cropped to v1 slice)",
        "Hatch only = ubermap.jpg cells (v1 expected)" if args.hatch_only else "Hatch+light fill = ubermap.jpg cells (v1 expected)",
        "Stroke = bgsvg extracted cells (v1-slice fit)",
        (
            "Numbers = vnum (all road/river cells)"
            if args.label_all_vnums
            else ("Numbers = vnum (bgsvg cells only)" if args.label_bgsvg_vnums else "")
        ),
        "Blue=river  Brown=road  Purple=both",
    ]
    if font is not None:
        lx, ly = 12, 12
        pad = 6
        line_h = 12
        max_w = 0
        for s in [x for x in legend if x]:
            max_w = max(max_w, int(draw.textlength(s, font=font)))
        box_w = max_w + pad * 2
        legend_lines = [x for x in legend if x]
        box_h = len(legend_lines) * line_h + pad * 2
        draw.rectangle([lx - 4, ly - 4, lx - 4 + box_w, ly - 4 + box_h], fill=(0, 0, 0, 140), outline=(255, 255, 255, 160), width=1)
        yy = ly
        for s in legend_lines:
            draw.text((lx, yy), s, fill=(255, 255, 255, 255), font=font)
            yy += line_h

    args.out.parent.mkdir(parents=True, exist_ok=True)
    crop.save(args.out)

    if args.out_small is not None:
        w = max(100, int(args.small_width))
        scale2 = w / crop.size[0]
        h = int(crop.size[1] * scale2)
        crop.resize((w, h), resample=Image.Resampling.BILINEAR).save(args.out_small)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

