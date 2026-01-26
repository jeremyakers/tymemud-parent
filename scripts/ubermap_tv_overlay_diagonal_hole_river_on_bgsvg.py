#!/usr/bin/env python3
"""
Tar Valon-focused overlay for the diagonal overland hole + river ring.

This renders on top of the pre-rendered Westlands-Background SVG PNG and draws:
- bgsvg-extracted road/river stroke cells for zones 468/469 (optional, from TSV)
- the *world-state* hole vnums (red X + outline) and river-ring vnums (cyan outline)

It verifies the current world files match expectations before rendering:
- hole vnums: sector_type == 0 and title begins with "!unused"
- river vnums: sector_type == 6
- no exits in zones 468/469 point into the hole vnums
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont  # type: ignore


ZONE_WANT = (468, 469)
SECT_INSIDE = 0
SECT_WATER_SWIM = 6


ROOM_RE = re.compile(r"^#(\d+)\s*$")
DIR_RE = re.compile(r"^D(\d+)\s*$")
INFO_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s+(-?\d+)\s*$")
SECTOR_RE = re.compile(r"^(\d+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$")


def _parse_verify_fit(path: Path) -> tuple[float, float, float]:
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


def _parse_viewbox_w(svg: Path) -> float:
    head = svg.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"', head)
    if not m:
        raise RuntimeError('could not parse viewBox="0 0 W H" from SVG')
    return float(m.group(1))


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
    # Fallback: scan raw text for the first translate (works for this file)
    head = svg.read_text(encoding="utf-8", errors="replace")
    m2 = re.search(
        r'transform="translate\(\s*([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s*\)"', head
    )
    if m2:
        return float(m2.group(1)), float(m2.group(2))
    raise RuntimeError("could not find outer translate(...) in SVG")


def _load_bgsvg_cells(tsv: Path) -> dict[int, dict[str, set[int]]]:
    out: dict[int, dict[str, set[int]]] = {
        z: {"river": set(), "road": set()} for z in ZONE_WANT
    }
    for ln in tsv.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or ln.lower().startswith("zone\t"):
            continue
        parts = ln.split("\t")
        if len(parts) < 3:
            continue
        z = int(parts[0])
        if z not in out:
            continue
        cell = int(parts[1])
        feat = parts[2].strip()
        if feat not in ("river", "road"):
            continue
        out[z][feat].add(cell)
    return out


def _iter_exits(wld_path: Path):
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    cur_room: int | None = None
    while i < len(lines):
        m = ROOM_RE.match(lines[i].strip())
        if m:
            cur_room = int(m.group(1))
            i += 1
            continue
        m = DIR_RE.match(lines[i].strip())
        if m and cur_room is not None:
            dir_idx = int(m.group(1))
            i += 1
            # exit desc until ~
            while (
                i < len(lines)
                and lines[i].strip() != "~"
                and not lines[i].endswith("~")
            ):
                i += 1
            if i < len(lines):
                i += 1
            # keywords until ~
            while (
                i < len(lines)
                and lines[i].strip() != "~"
                and not lines[i].endswith("~")
            ):
                i += 1
            if i < len(lines):
                i += 1
            if i < len(lines):
                m2 = INFO_RE.match(lines[i].strip())
                if m2:
                    to_vnum = int(m2.group(3))
                    yield cur_room, dir_idx, to_vnum
            i += 1
            continue
        i += 1


def _read_room_title_and_sector(
    wld_path: Path, vnum: int
) -> tuple[str | None, int | None]:
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        m = ROOM_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        cur = int(m.group(1))
        i += 1
        if cur != vnum:
            continue
        title = lines[i] if i < len(lines) else ""
        i += 1
        # skip desc to ~
        while i < len(lines) and lines[i].strip() != "~" and not lines[i].endswith("~"):
            i += 1
        if i < len(lines):
            i += 1
        if i < len(lines):
            sm = SECTOR_RE.match(lines[i].strip())
            if sm:
                return title, int(sm.group(3))
        return title, None
    return None, None


def _load_font(size: int):
    size = max(6, int(size))
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=size
        )
    except Exception:
        try:
            return ImageFont.load_default()
        except Exception:
            return None


def main() -> int:
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    ap.add_argument(
        "--svg",
        type=Path,
        default=root / "Building_Design_Notes" / "Westlands-Background.svg",
    )
    ap.add_argument(
        "--bg-png",
        type=Path,
        default=root / "tmp" / "westlands_background_full_w12000.png",
    )
    ap.add_argument(
        "--verify-tsv",
        type=Path,
        default=root
        / "docs"
        / "ubermap"
        / "v2"
        / "extracts"
        / "background_svg_verify_537_540.tsv",
    )
    ap.add_argument(
        "--bgsvg-tsv",
        type=Path,
        default=root / "tmp" / "bgsvg_v1slice_road_river_cells.tsv",
    )
    ap.add_argument(
        "--wld-dir",
        type=Path,
        required=True,
        help="Directory containing <zone>.wld files",
    )
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-small", type=Path, default=None)
    ap.add_argument("--small-width", type=int, default=1400)
    ap.add_argument("--pad-px", type=int, default=24)
    ap.add_argument(
        "--no-bgsvg",
        action="store_true",
        help="Do not draw bgsvg stroke cells (only world hole/river)",
    )
    ap.add_argument(
        "--label-bgsvg-vnums",
        action="store_true",
        help="Label bgsvg road/river stroke cells with their overland vnum (zone*100+cell).",
    )
    args = ap.parse_args()

    # Updated per user-confirmed fit:
    # - 46890 + 46978 are back to river
    # - 46977 is back to road (and should NOT be treated as river ring)
    # - remaining overland holes are fewer
    hole = {46880, 46979, 46989}
    river = {46881, 46870, 46969, 46968, 46988, 46999, 46890, 46978}
    road = {46977}

    # --- Verify world state first ---
    # 1) Title + sector sanity:
    # - Holes: must be marked !unused (sector is not enforced; holes are intentionally disconnected)
    # - Rivers: must be sector=6
    for v in sorted(hole | river | road):
        z = v // 100
        wld = args.wld_dir / f"{z}.wld"
        title, sec = _read_room_title_and_sector(wld, v)
        if sec is None:
            raise SystemExit(f"ERROR: could not read sector for {v} in {wld}")
        if v in hole:
            if title is None or not title.lower().lstrip().startswith("!unused"):
                raise SystemExit(
                    f"ERROR: hole vnum {v} title does not start with !unused: {title!r}"
                )
        elif v in river:
            if sec != SECT_WATER_SWIM:
                raise SystemExit(
                    f"ERROR: river vnum {v} sector={sec} expected={SECT_WATER_SWIM}"
                )
        else:
            # "Road" here means: revert to its builder/baseline sector for this cell.
            # We accept any non-water, non-inside overland sector (field/road/etc).
            if sec in (SECT_INSIDE, SECT_WATER_SWIM):
                raise SystemExit(
                    f"ERROR: road vnum {v} sector={sec} looks wrong (inside/water)"
                )

    # 2) No exits into hole vnums within zones 468/469
    for z in ZONE_WANT:
        wld = args.wld_dir / f"{z}.wld"
        for frm, d, to in _iter_exits(wld):
            if to in hole:
                raise SystemExit(f"ERROR: {wld} has exit into hole: {frm} D{d} -> {to}")

    # --- Build overlay ---
    if not args.bg_png.exists():
        raise SystemExit(f"Missing background PNG: {args.bg_png}")

    zone_w, x0_zone540, y0_zone540 = _parse_verify_fit(args.verify_tsv)
    # v1-slice anchor: zone 540 lives at (-1,2) in the derived layout.
    zx_540, zy_540 = (-1, 2)
    x_origin = x0_zone540 - (zx_540 * zone_w)
    y_origin = y0_zone540 - (zy_540 * zone_w)

    vb_w = _parse_viewbox_w(args.svg)
    tr_x, tr_y = _parse_outer_translate(args.svg)

    bg_full = Image.open(args.bg_png).convert("RGBA")
    scale = bg_full.size[0] / vb_w

    # Crop to zones 469 (0,0) and 468 (1,0)
    min_zx, max_zx = (0, 1)
    min_zy, max_zy = (0, 0)

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

    cell_w_raw = zone_w / 10.0

    # Colors/styles
    bgsvg_river = (0, 85, 255, 255)
    bgsvg_road = (107, 63, 0, 255)
    hole_col = (235, 40, 40, 255)
    river_col = (40, 235, 235, 255)
    stroke_w = 3

    # Helpers to draw one cell
    font = _load_font(14)

    def draw_cell(
        z: int, cell: int, *, outline: tuple[int, int, int, int], xmark: bool
    ) -> None:
        zx = 0 if z == 469 else 1
        zy = 0
        z_raw_x0 = x_origin + zx * zone_w
        z_raw_y0 = y_origin + zy * zone_w
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
        draw.rectangle([x0p, y0p, x1p, y1p], outline=outline, width=stroke_w)
        if xmark:
            pad = max(1, int(min(x1p - x0p, y1p - y0p) * 0.12))
            draw.line(
                [(x0p + pad, y0p + pad), (x1p - pad, y1p - pad)],
                fill=outline,
                width=stroke_w,
            )
            draw.line(
                [(x0p + pad, y1p - pad), (x1p - pad, y0p + pad)],
                fill=outline,
                width=stroke_w,
            )
        if font is not None:
            vnum = z * 100 + cell
            text = str(vnum)
            tw, th = draw.textbbox((0, 0), text, font=font)[2:]
            tx = x0p + max(1, (x1p - x0p - tw) // 2)
            ty = y0p + max(1, (y1p - y0p - th) // 2)
            draw.text((tx + 1, ty + 1), text, fill=(0, 0, 0, 220), font=font)
            draw.text((tx, ty), text, fill=(255, 255, 255, 240), font=font)

    def draw_bgsvg_cell(z: int, cell: int, *, outline: tuple[int, int, int, int]) -> None:
        """Draw a bgsvg-extracted stroke cell (road/river) in outline style, optionally labeled."""
        zx = 0 if z == 469 else 1
        zy = 0
        z_raw_x0 = x_origin + zx * zone_w
        z_raw_y0 = y_origin + zy * zone_w
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
            return
        draw.rectangle([x0p, y0p, x1p, y1p], outline=outline, width=2)
        if args.label_bgsvg_vnums and font is not None:
            vnum = z * 100 + cell
            text = str(vnum)
            try:
                tw, th = draw.textbbox((0, 0), text, font=font)[2:]
            except Exception:
                # Pillow fallback
                tw, th = draw.textsize(text, font=font)
            tx = x0p + max(1, (x1p - x0p - tw) // 2)
            ty = y0p + max(1, (y1p - y0p - th) // 2)
            draw.text((tx + 1, ty + 1), text, fill=(0, 0, 0, 220), font=font)
            draw.text((tx, ty), text, fill=(255, 255, 255, 240), font=font)

    # Optional bgsvg stroke cells for context
    if not args.no_bgsvg and args.bgsvg_tsv.exists():
        bg = _load_bgsvg_cells(args.bgsvg_tsv)
        for z in ZONE_WANT:
            # If a cell is both (should be rare), prefer river.
            cell_feat: dict[int, str] = {}
            for cell in bg[z]["road"]:
                cell_feat[cell] = "road"
            for cell in bg[z]["river"]:
                cell_feat[cell] = "river"
            for cell, feat in sorted(cell_feat.items()):
                if feat == "river":
                    draw_bgsvg_cell(z, cell, outline=bgsvg_river)
                else:
                    draw_bgsvg_cell(z, cell, outline=bgsvg_road)

    for v in sorted(river):
        z = v // 100
        draw_cell(z, v % 100, outline=river_col, xmark=False)
    for v in sorted(hole):
        z = v // 100
        draw_cell(z, v % 100, outline=hole_col, xmark=True)
    for v in sorted(road):
        z = v // 100
        draw_cell(z, v % 100, outline=(255, 165, 0, 255), xmark=False)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    crop.save(args.out)
    if args.out_small is not None:
        w = int(args.small_width)
        h = max(1, int(crop.size[1] * (w / crop.size[0])))
        crop.resize((w, h), Image.Resampling.LANCZOS).save(args.out_small)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
