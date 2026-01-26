#!/usr/bin/env python3
"""
World-state overlay on Westlands-Background.svg (rendered PNG).

This overlay is the sanity check we should have been using:
- It reads *actual* room sectors from .wld files (engine inputs).
- It draws those road/river tiles on top of the background map.
- It optionally draws bgsvg stroke cells (north star) as outlines for comparison.

Legend (default):
- Hatch-only = world-state (from .wld sector types)
  - river: sector 6 (Water Swim)
  - road: sector 11 (Main Road)
- Outline stroke = bgsvg-extracted cells (from TSV): blue river, brown road, purple both
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont  # type: ignore

ROOT = Path(__file__).resolve().parents[1]

SVG_DEFAULT = ROOT / "Building_Design_Notes" / "Westlands-Background.svg"
BGPNG_DEFAULT = ROOT / "tmp" / "westlands_background_full_w12000.png"
VERIFY_DEFAULT = ROOT / "docs" / "ubermap" / "v2" / "extracts" / "background_svg_verify_537_540.tsv"
BGSVG_TSV_DEFAULT = ROOT / "tmp" / "bgsvg_v1slice_road_river_cells.tsv"

# v1 slice zone ids visible in ubermap.jpg (same as scripts/ubermap_overlay_on_bgsvg.py)
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

SECT_WATER_SWIM = 6
SECT_MAIN_ROAD = 11
SECT_CITY = 1

FEATURES = ("river", "road")

_ROOM_RE = re.compile(r"^#(\d+)\s*$")
_DIR_RE = re.compile(r"^D(\d+)\s*$")
_INFO_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s+(-?\d+)\s*$")


def _load_bgsvg_cells(tsv: Path) -> dict[int, dict[str, set[int]]]:
    out: dict[int, dict[str, set[int]]] = {z: {"river": set(), "road": set()} for z in V1_ZONES}
    if not tsv.exists():
        return out
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
        out[z][feat].add(cell)
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


def _derive_zone_coords(*, wld_dir: Path) -> dict[int, tuple[int, int]]:
    """
    Derive relative zone coords using only boundary-consistent N/E/S/W exits.
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
            # boundary-consistent cardinal links
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
    best_w = None
    x0 = None
    y0 = None
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "best_zone_w=" in ln and "row_origin_540=" in ln:
            m = re.search(r"best_zone_w=([0-9.]+)", ln)
            m2 = re.search(r"row_origin_540=\(([+-]?[0-9.]+),\s*([+-]?[0-9.]+)\)", ln)
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
        raise RuntimeError('could not parse viewBox="0 0 W H" from SVG')
    return float(m.group(1)), float(m.group(2))


def _parse_outer_translate(svg: Path) -> tuple[float, float]:
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
    head = svg.read_text(encoding="utf-8", errors="replace")
    m2 = re.search(r'transform="translate\(\s*([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s*\)"', head)
    if m2:
        return float(m2.group(1)), float(m2.group(2))
    raise RuntimeError("could not find outer translate(...) in SVG")


def _make_hatch_tile(*, w: int, h: int, color: tuple[int, int, int, int], step: int) -> Image.Image:
    w = max(1, int(w))
    h = max(1, int(h))
    step = max(3, int(step))
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile, "RGBA")
    for i in range(-h, w + h, step):
        d.line([(i, 0), (i + h, h)], fill=color, width=1)
    return tile


def _paste_hatch_tile(
    base: Image.Image,
    *,
    rect: tuple[int, int, int, int],
    color: tuple[int, int, int, int],
    step: int,
    cache: dict[tuple[int, int, tuple[int, int, int, int], int], Image.Image],
) -> None:
    x0, y0, x1, y1 = rect
    w = x1 - x0
    h = y1 - y0
    if w <= 1 or h <= 1:
        return
    key = (w, h, color, int(step))
    tile = cache.get(key)
    if tile is None:
        tile = _make_hatch_tile(w=w, h=h, color=color, step=step)
        cache[key] = tile
    base.alpha_composite(tile, dest=(x0, y0))


def _load_world_sectors(*, wld_dir: Path) -> dict[int, dict[int, int]]:
    """
    Return zones[z][cell] = sector_type for the v1-slice zones.
    """
    out: dict[int, dict[int, int]] = {}
    for z in V1_ZONES:
        wld = wld_dir / f"{z}.wld"
        if not wld.exists():
            continue
        lines = wld.read_text(encoding="latin-1", errors="replace").splitlines()
        i = 0
        cur: int | None = None
        while i < len(lines):
            m = _ROOM_RE.match(lines[i].strip())
            if not m:
                i += 1
                continue
            cur = int(m.group(1))
            i += 1
            if i >= len(lines):
                break
            i += 1  # title
            # desc until ~
            while i < len(lines) and lines[i].strip() != "~" and not lines[i].endswith("~"):
                i += 1
            if i < len(lines):
                i += 1
            if i >= len(lines):
                break
            # sector line: "<zone> <flags> <sector> <x> <y>"
            parts = lines[i].split()
            if len(parts) >= 3 and parts[2].lstrip("-").isdigit():
                sector = int(parts[2])
                out.setdefault(z, {})[cur % 100] = sector
            i += 1
    # ensure all zones exist
    for z in V1_ZONES:
        out.setdefault(z, {})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Overlay world-state (wld sectors) vs bgsvg stroke cells on background PNG.")
    ap.add_argument("--svg", type=Path, default=SVG_DEFAULT)
    ap.add_argument("--bg-png", type=Path, default=BGPNG_DEFAULT)
    ap.add_argument("--verify-tsv", type=Path, default=VERIFY_DEFAULT)
    ap.add_argument("--bgsvg-tsv", type=Path, default=BGSVG_TSV_DEFAULT)
    ap.add_argument("--wld-dir", type=Path, required=True, help="Directory containing <zone>.wld files")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-small", type=Path, default=None)
    ap.add_argument("--small-width", type=int, default=1400)
    ap.add_argument("--pad-px", type=int, default=40)
    ap.add_argument("--stroke-width", type=int, default=3)
    ap.add_argument("--hatch-step", type=int, default=5, help="Hatch density (smaller = deeper/denser).")
    ap.add_argument(
        "--wld-style",
        choices=("hatch", "fill+hatch"),
        default="hatch",
        help="How to render .wld sectors: hatch-only (default) or old fill+hatch.",
    )
    ap.add_argument("--label-vnums", action="store_true")
    ap.add_argument("--no-bgsvg", action="store_true", help="Do not draw bgsvg strokes; world-state only.")
    args = ap.parse_args()

    if not args.bg_png.exists():
        raise SystemExit(f"Missing background PNG: {args.bg_png}")
    if not args.verify_tsv.exists():
        raise SystemExit(f"Missing verify TSV: {args.verify_tsv}")

    coords = _derive_zone_coords(wld_dir=args.wld_dir)
    zone_w, x0_zone540, y0_zone540 = _parse_verify_fit(args.verify_tsv)
    zx_540, zy_540 = coords[540]
    x_origin = x0_zone540 - (zx_540 * zone_w)
    y_origin = y0_zone540 - (zy_540 * zone_w)

    vb_w, _vb_h = _parse_viewbox(args.svg)
    tr_x, tr_y = _parse_outer_translate(args.svg)

    bg_full = Image.open(args.bg_png).convert("RGBA")
    scale = bg_full.size[0] / vb_w

    # v1 slice bounds in zone coords
    min_zx = min(x for x, _ in coords.values())
    max_zx = max(x for x, _ in coords.values())
    min_zy = min(y for _, y in coords.values())
    max_zy = max(y for _, y in coords.values())

    raw_x0 = x_origin + (min_zx * zone_w)
    raw_y0 = y_origin + (min_zy * zone_w)
    raw_x1 = x_origin + ((max_zx + 1) * zone_w)
    raw_y1 = y_origin + ((max_zy + 1) * zone_w)

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

    # Fonts
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

    # World-state styling (hatch-only by default so bg map features remain visible underneath)
    fill_river = (47, 103, 199, 40)
    fill_road = (185, 138, 75, 40)
    # Slightly darker overall hatch to read clearly over bg.
    hatch_river = (20, 80, 220, 235)
    hatch_road = (110, 60, 0, 235)
    # City hatch: match ubermap SVG "City" fill (cyan), but hatch-only.
    hatch_city = (0, 255, 255, 235)

    # bgsvg strokes
    stroke_river = (0, 85, 255, 255)
    stroke_road = (107, 63, 0, 255)
    stroke_both = (106, 0, 255, 255)

    cell_w_raw = zone_w / 10.0
    stroke_w = max(1, int(args.stroke_width))

    world = _load_world_sectors(wld_dir=args.wld_dir)
    bgsvg = _load_bgsvg_cells(args.bgsvg_tsv) if not args.no_bgsvg else {z: {"river": set(), "road": set()} for z in V1_ZONES}

    hatch_cache: dict[tuple[int, int, tuple[int, int, int, int], int], Image.Image] = {}

    # Draw each zone/cell
    for z in V1_ZONES:
        zx, zy = coords[z]
        z_raw_x0 = x_origin + zx * zone_w
        z_raw_y0 = y_origin + zy * zone_w
        for cell in range(100):
            r, c = divmod(cell, 10)
            c_raw_x0 = z_raw_x0 + c * cell_w_raw
            c_raw_y0 = z_raw_y0 + r * cell_w_raw
            c_raw_x1 = c_raw_x0 + cell_w_raw
            c_raw_y1 = c_raw_y0 + cell_w_raw

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

            sector = world.get(z, {}).get(cell)
            is_river = sector == SECT_WATER_SWIM
            is_road = sector == SECT_MAIN_ROAD
            is_city = sector == SECT_CITY

            if is_river:
                if args.wld_style == "fill+hatch":
                    draw.rectangle([x0p, y0p, x1p, y1p], fill=fill_river, outline=None)
                _paste_hatch_tile(crop, rect=(x0p, y0p, x1p, y1p), color=hatch_river, step=int(args.hatch_step), cache=hatch_cache)
            elif is_road:
                if args.wld_style == "fill+hatch":
                    draw.rectangle([x0p, y0p, x1p, y1p], fill=fill_road, outline=None)
                _paste_hatch_tile(crop, rect=(x0p, y0p, x1p, y1p), color=hatch_road, step=int(args.hatch_step), cache=hatch_cache)
            elif is_city:
                _paste_hatch_tile(crop, rect=(x0p, y0p, x1p, y1p), color=hatch_city, step=int(args.hatch_step), cache=hatch_cache)

            # bgsvg stroke outlines for comparison
            b_r = cell in bgsvg.get(z, {}).get("river", set())
            b_d = cell in bgsvg.get(z, {}).get("road", set())
            if b_r or b_d:
                if b_r and b_d:
                    scol = stroke_both
                elif b_r:
                    scol = stroke_river
                else:
                    scol = stroke_road
                draw.rectangle([x0p, y0p, x1p, y1p], outline=scol, width=stroke_w)

            if args.label_vnums and font is not None and (is_river or is_road or is_city or b_r or b_d):
                vnum = z * 100 + cell
                text = str(vnum)
                cw = max(1, x1p - x0p)
                ch = max(1, y1p - y0p)
                size = max(7, min(14, int(min(cw, ch) * 0.30)))
                fnt = _load_font(size)
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
                        draw.text((tx + ox, ty + oy), text, fill=(0, 0, 0, 220), font=fnt)
                    draw.text((tx, ty), text, fill=(255, 255, 255, 240), font=fnt)

    # Legend
    legend = [
        "World-state overlay on Westlands-Background (cropped to v1 slice)",
        "Hatch = world-state sectors (.wld): river=6, road=11",
        "Stroke = bgsvg extracted cells (north star)",
        "Numbers = vnum (when enabled)",
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
        draw.rectangle([lx - 4, ly - 4, lx - 4 + box_w, ly - 4 + box_h], fill=(0, 0, 0, 160), outline=(255, 255, 255, 180), width=1)
        yy = ly
        for s in legend:
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

