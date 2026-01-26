#!/usr/bin/env python3
"""
Generate an Ubermap-v2 "planning map" (SVG + TSV) from the full Westlands JPG.

Goal:
  - Produce something you can open and visually inspect like `ubermap.jpg`, but for v2:
    - a grid of zones (each zone is 10x10 rooms)
    - zone numbers rendered on the map
    - each room cell colored by an inferred "sector type" (plains/forest/hills/mountains/water)
    - TSV exports for analysis/editing

Notes:
  - Terrain classification is heuristic based on average pixel color in the source map.
    It is intended as a starting point for an editable plan, not a perfect truth.
  - The grid sizing here is chosen to:
      26 cols x 20 rows zones  =>  260 x 200 rooms
    which fits well into 1600x1241 and uses zone IDs in the 406-925 range:
      zone_id = TOP_LEFT_ZONE - x - (y * ZONE_COLS)
    This makes "east = -1 zone id", matching v1 expectations (e.g. 537 east neighbor is 536).

Usage (recommended with uvx so Pillow is available):
  uvx --with pillow python scripts/ubermap_v2_render_from_westlands_map.py

Outputs:
  docs/ubermap/v2/westlands_v2_ubermap.svg
  docs/ubermap/v2/westlands_v2_ubermap_cells.tsv
  docs/ubermap/v2/westlands_v2_ubermap_zones.tsv
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC_MAP = ROOT / "Building_Design_Notes" / "wheel_of_time___westland_map-fullview.jpg"
V1_UBERMAP_IMG = ROOT / "Building_Design_Notes" / "ubermap.jpg"
OUT_DIR = ROOT / "docs" / "ubermap" / "v2"


ZONE_COLS = 26
ZONE_ROWS = 20
ROOMS_PER_ZONE = 10

TOP_LEFT_ZONE = 925  # zone_id at (zx=0, zy=0)
DEFAULT_V1_EXPECTED_TSV = OUT_DIR / "extracts" / "v1_ubermap_road_river_cells.tsv"


class MissingDependency(RuntimeError):
    pass


def _require_pillow():
    try:
        from PIL import Image  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise MissingDependency(
            "Pillow is required. Run with:\n"
            "  uvx --with pillow python scripts/ubermap_v2_render_from_westlands_map.py"
        ) from e


def _require_numpy():
    try:
        import numpy as np  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise MissingDependency(
            "NumPy is required for v1 slice matching. Run with:\n"
            "  uvx --with pillow --with numpy python scripts/ubermap_v2_render_from_westlands_map.py"
        ) from e


def zone_id_for(zx: int, zy: int) -> int:
    return TOP_LEFT_ZONE - zx - (zy * ZONE_COLS)


@dataclass(frozen=True)
class Cell:
    zx: int
    zy: int
    rx: int
    ry: int
    zone_id: int
    sector: str  # PLAINS/FOREST/HILLS/MOUNTAINS/WATER
    feature: str  # NONE/ROAD/RIVER
    rgb: tuple[int, int, int]


def clamp(n: float, lo: float, hi: float) -> float:
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Return HSV in [0..1] ranges (h in 0..1, s in 0..1, v in 0..1)."""
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    mx = max(rf, gf, bf)
    mn = min(rf, gf, bf)
    df = mx - mn

    # Hue
    if df == 0:
        h = 0.0
    elif mx == rf:
        h = ((gf - bf) / df) % 6.0
    elif mx == gf:
        h = ((bf - rf) / df) + 2.0
    else:
        h = ((rf - gf) / df) + 4.0
    h /= 6.0

    # Saturation
    s = 0.0 if mx == 0 else (df / mx)

    # Value
    v = mx
    return (clamp(h, 0.0, 1.0), clamp(s, 0.0, 1.0), clamp(v, 0.0, 1.0))


def classify_patch(pixels: list[tuple[int, int, int]]) -> tuple[tuple[int, int, int], str, str]:
    """
    Return (avg_rgb, sector, feature) for a cell patch.

    Sector is an approximation of what we'd build from the map:
      - WATER (rivers/lakes)
      - MOUNTAINS
      - HILLS
      - FOREST
      - PLAINS (default)

    Feature identifies thin strokes that would be averaged away in mean-RGB:
      - RIVER: "blue-dominant" pixel ratio crosses a threshold
      - ROAD: low-saturation light pixel ratio crosses a threshold
    """
    if not pixels:
        return ((0, 0, 0), "PLAINS", "NONE")

    # Average RGB (still used for broad terrain).
    sr = sum(p[0] for p in pixels)
    sg = sum(p[1] for p in pixels)
    sb = sum(p[2] for p in pixels)
    n = len(pixels)
    avg_rgb = (sr // n, sg // n, sb // n)
    ar, ag, ab = avg_rgb
    ah, a_s, a_v = rgb_to_hsv(ar, ag, ab)

    # Feature ratios (these are intentionally tuned to find thin strokes).
    water_like = 0
    road_like = 0
    for r, g, b in pixels:
        h, s, v = rgb_to_hsv(r, g, b)
        # Blue-dominant pixels.
        if b > r + 25 and b > g + 18 and v > 0.22:
            water_like += 1
        # Low-saturation light-ish pixels (common for cartographic road strokes).
        if s < 0.14 and 0.45 < v < 0.92 and abs(r - g) < 18 and abs(g - b) < 18:
            road_like += 1

    water_ratio = water_like / n
    road_ratio = road_like / n

    # If enough of the cell is water-like, call it a river/water cell even if the mean isn't blue.
    # This catches thin rivers that otherwise get averaged into plains/forest.
    if water_ratio >= 0.10:
        return (avg_rgb, "WATER", "RIVER")

    # MOUNTAINS: very dark or dark brown/gray.
    if a_v < 0.22:
        return (avg_rgb, "MOUNTAINS", "NONE")

    # FOREST: green-dominant with some saturation.
    # hue for green is roughly 0.25..0.45
    if (0.22 <= ah <= 0.45) and a_s > 0.20 and ag > ar + 10 and ag > ab + 10:
        return (avg_rgb, "FOREST", "NONE")

    # HILLS: brown-ish / earth tones.
    # hues around yellow/orange (0.08..0.18) with moderate saturation.
    if (0.05 <= ah <= 0.18) and a_s > 0.15 and ar >= ag >= ab:
        return (avg_rgb, "HILLS", "NONE")

    # If enough of the cell looks like road stroke, mark ROAD.
    if road_ratio >= 0.06:
        return (avg_rgb, "PLAINS", "ROAD")

    # Default
    return (avg_rgb, "PLAINS", "NONE")


SECTOR_COLOR = {
    "PLAINS": "#d9c27a",  # tan
    "FOREST": "#2f8f3a",  # green
    "HILLS": "#b98a4b",  # brown
    "MOUNTAINS": "#666666",  # gray
    "WATER": "#2f67c7",  # blue
}


def hex_rgb(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def compute_cells():
    _require_pillow()
    from PIL import Image  # type: ignore

    if not SRC_MAP.exists():
        raise FileNotFoundError(str(SRC_MAP))

    im = Image.open(SRC_MAP).convert("RGB")
    w, h = im.size

    room_cols = ZONE_COLS * ROOMS_PER_ZONE
    room_rows = ZONE_ROWS * ROOMS_PER_ZONE

    for zy in range(ZONE_ROWS):
        for zx in range(ZONE_COLS):
            zid = zone_id_for(zx, zy)
            for ry in range(ROOMS_PER_ZONE):
                for rx in range(ROOMS_PER_ZONE):
                    gx = zx * ROOMS_PER_ZONE + rx
                    gy = zy * ROOMS_PER_ZONE + ry

                    # Map global cell to image pixel rect
                    x0 = int(round(gx * w / room_cols))
                    x1 = int(round((gx + 1) * w / room_cols))
                    y0 = int(round(gy * h / room_rows))
                    y1 = int(round((gy + 1) * h / room_rows))
                    if x1 <= x0:
                        x1 = x0 + 1
                    if y1 <= y0:
                        y1 = y0 + 1

                    patch = im.crop((x0, y0, x1, y1))
                    px = patch.load()
                    pixels: list[tuple[int, int, int]] = []
                    # Downsample within the patch so this stays fast.
                    step_x = max(1, patch.width // 6)
                    step_y = max(1, patch.height // 6)
                    for yy in range(0, patch.height, step_y):
                        for xx in range(0, patch.width, step_x):
                            r, g, b = px[xx, yy]
                            pixels.append((int(r), int(g), int(b)))

                    avg, sector, feature = classify_patch(pixels)
                    yield Cell(
                        zx=zx,
                        zy=zy,
                        rx=rx,
                        ry=ry,
                        zone_id=zid,
                        sector=sector,
                        feature=feature,
                        rgb=avg,
                    )


def read_v1_expected(tsv_path: Path) -> dict[int, dict[str, set[int]]]:
    """
    Load v1 expected features from `scripts/ubermap_jpg_extract_cells.py` output TSV:
      zone  cell  feature
    Returns: {zone_id: {"road": {cell,..}, "river": {cell,..}}}
    """
    out: dict[int, dict[str, set[int]]] = {}
    if not tsv_path.exists():
        return out
    for line in tsv_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("zone\t"):
            continue
        z_s, cell_s, feat = line.split("\t")
        if feat not in {"road", "river"}:
            continue
        z = int(z_s)
        cell = int(cell_s)
        out.setdefault(z, {"road": set(), "river": set()})[feat].add(cell)
    return out


def _to_gray_np(img) -> "object":
    _require_numpy()
    import numpy as np  # type: ignore

    g = img.convert("L")
    return np.array(g, dtype=np.int16)


def _to_match_gray_np(img) -> "object":
    """
    Preprocess an image into grayscale suitable for template matching:
    - de-emphasize very dark (gridlines) and very bright (labels) pixels by clamping to mid-gray
    """
    _require_numpy()
    import numpy as np  # type: ignore

    rgb = np.array(img.convert("RGB"), dtype=np.int16)
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    dark = (r < 45) & (g < 45) & (b < 45)
    bright = (r > 235) & (g > 235) & (b > 235)
    mask = dark | bright
    rgb[mask] = 128

    # Luma (approx)
    gray = (rgb[:, :, 0] * 30 + rgb[:, :, 1] * 59 + rgb[:, :, 2] * 11) // 100
    return gray.astype(np.int16)


def locate_v1_grids_on_westlands() -> tuple[
    tuple[int, int],
    float,
    "object",
    tuple[int, int, int, int],
    dict[int, tuple[int, int, int, int]],
]:
    """
    Locate the v1 ubermap grid-crop (containing all 19 10x10 grids) on the full Westlands map.

    Returns:
      - (x, y) top-left on Westlands map (pixel coords)
      - scale factor applied to the v1 crop to best match the Westlands map
      - v1 template image (PIL.Image)
      - v1 template bbox in v1-image coords: (x0,y0,x1,y1)
      - per-zone rects within the v1 image: {zone_id: (x0,y0,x1,y1)} in v1-image pixel coords

    This is used ONLY for validation/calibration, not as a v2 “source”.
    """
    _require_pillow()
    _require_numpy()
    from PIL import Image  # type: ignore

    # Import the existing v1 grid detector so we reuse the same assumptions as v1 extraction.
    # When executed as a script, `scripts/` isn't automatically importable, so add ROOT to sys.path.
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from scripts.ubermap_jpg_extract_cells import ZONES_ORDER, find_grid_rects  # type: ignore

    if not V1_UBERMAP_IMG.exists():
        raise FileNotFoundError(str(V1_UBERMAP_IMG))
    if not SRC_MAP.exists():
        raise FileNotFoundError(str(SRC_MAP))

    v1 = Image.open(V1_UBERMAP_IMG).convert("RGB")
    west = Image.open(SRC_MAP).convert("RGB")

    rects = find_grid_rects(v1)
    if len(rects) != len(ZONES_ORDER):
        raise RuntimeError(f"expected {len(ZONES_ORDER)} v1 grids, found {len(rects)}")

    # Zone rects in v1 image coordinates.
    zone_rects: dict[int, tuple[int, int, int, int]] = {}
    for zone, r in zip(ZONES_ORDER, rects, strict=True):
        zone_rects[zone] = (r.x0, r.y0, r.x1, r.y1)

    # Use a subset of the v1 slice as the template so it fits in Westlands, but is still unique.
    # The row containing zones 540-537 is a good anchor for verification.
    template_zones = [537, 538, 539, 540]
    missing = [z for z in template_zones if z not in zone_rects]
    if missing:
        raise RuntimeError(f"template zones missing from v1 rect list: {missing}")

    tz_x0 = min(zone_rects[z][0] for z in template_zones)
    tz_y0 = min(zone_rects[z][1] for z in template_zones)
    tz_x1 = max(zone_rects[z][2] for z in template_zones)
    tz_y1 = max(zone_rects[z][3] for z in template_zones)
    template_bbox = (tz_x0, tz_y0, tz_x1, tz_y1)

    # Inset to avoid strong black borders.
    inset = 12
    v1_template = v1.crop((tz_x0 + inset, tz_y0 + inset, tz_x1 - inset, tz_y1 - inset))

    # Multi-scale coarse match (downscale for speed).
    import numpy as np  # type: ignore

    west_small = west.resize((west.width // 2, west.height // 2))
    best = {"score": None, "x": 0, "y": 0, "scale": 1.0}

    # Grid cell scale between v1 ubermap.jpg and Westlands varies (different source sizes),
    # so try several plausible scales.
    scales = [0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10]
    west_arr = _to_match_gray_np(west_small)
    for s in scales:
        tw = max(40, int(v1_template.width * s / 2))
        th = max(40, int(v1_template.height * s / 2))
        templ = v1_template.resize((tw, th))
        templ_arr = _to_match_gray_np(templ)

        if th >= west_arr.shape[0] or tw >= west_arr.shape[1]:
            continue

        # Step to keep runtime sane.
        step = 2
        for y in range(0, west_arr.shape[0] - th, step):
            window_rows = west_arr[y : y + th]
            for x in range(0, west_arr.shape[1] - tw, step):
                win = window_rows[:, x : x + tw]
                # SAD
                score = int(np.sum(np.abs(win - templ_arr)))
                if best["score"] is None or score < best["score"]:
                    best = {"score": score, "x": x, "y": y, "scale": s}

    # Map back to full-resolution westlands coordinates.
    # west_small is 1/2 scale; so multiply coords by 2.
    # best (x,y) is the v1-template top-left in west_small coordinates.
    wx = int(best["x"] * 2)
    wy = int(best["y"] * 2)

    return (wx, wy), float(best["scale"]), v1_template, template_bbox, zone_rects


def classify_westlands_patch(im, x0: int, y0: int, x1: int, y1: int) -> tuple[str, str]:
    """
    Classify a rectangle on the Westlands image into (sector, feature) using the same
    logic as v2 cell classification.
    """
    patch = im.crop((x0, y0, x1, y1)).convert("RGB")
    px = patch.load()
    pixels: list[tuple[int, int, int]] = []
    step_x = max(1, patch.width // 6)
    step_y = max(1, patch.height // 6)
    for yy in range(0, patch.height, step_y):
        for xx in range(0, patch.width, step_x):
            r, g, b = px[xx, yy]
            pixels.append((int(r), int(g), int(b)))
    _, sector, feature = classify_patch(pixels)
    return sector, feature


def write_v1_geo_verify_report(out_path: Path) -> None:
    """
    Use image matching to locate the v1 slice inside the Westlands map and then
    compare expected road/river cells for zones 537-540 against Westlands-derived detection.
    """
    _require_pillow()
    from PIL import Image  # type: ignore

    v1_expected = read_v1_expected(DEFAULT_V1_EXPECTED_TSV)
    if not v1_expected:
        return

    (wx, wy), scale, v1_template, template_bbox, zone_rects = locate_v1_grids_on_westlands()
    west = Image.open(SRC_MAP).convert("RGB")

    zones = [537, 538, 539, 540]
    out_path.write_text(
        f"# v1_template_match zones=537-540 westlands_xy=({wx},{wy}) scale={scale:.3f} template_size=({v1_template.width}x{v1_template.height}) template_bbox_v1={template_bbox}\n"
        "zone\tfeature\tv1_count\twestlands_count\tmissing_in_westlands\textra_in_westlands\n",
        encoding="utf-8",
    )

    # For each zone, sample each of the 100 cells by mapping the v1 grid rect to the westlands.
    with out_path.open("a", encoding="utf-8") as f:
        for z in zones:
            if z not in zone_rects:
                continue
            zx0, zy0, zx1, zy1 = zone_rects[z]
            tx0, ty0, _, _ = template_bbox
            # Map v1 rect -> westlands by translating relative to template bbox top-left.
            wz0 = wx + int((zx0 - tx0) * scale)
            wy0 = wy + int((zy0 - ty0) * scale)
            wz1 = wx + int((zx1 - tx0) * scale)
            wy1 = wy + int((zy1 - ty0) * scale)

            # Insets inside the grid border.
            inset = int(max(2, 6 * scale))
            gx0 = wz0 + inset
            gy0 = wy0 + inset
            gx1 = wz1 - inset
            gy1 = wy1 - inset
            cw = (gx1 - gx0) / 10.0
            ch = (gy1 - gy0) / 10.0

            found = {"river": set(), "road": set()}
            for row in range(10):
                for col in range(10):
                    x0 = int(gx0 + col * cw)
                    x1 = int(gx0 + (col + 1) * cw)
                    y0 = int(gy0 + row * ch)
                    y1 = int(gy0 + (row + 1) * ch)
                    _, feature = classify_westlands_patch(west, x0, y0, x1, y1)
                    cell = row * 10 + col
                    if feature == "RIVER":
                        found["river"].add(cell)
                    elif feature == "ROAD":
                        found["road"].add(cell)

            for feat in ("river", "road"):
                v1_cells = v1_expected.get(z, {}).get(feat, set())
                west_cells = found[feat]
                missing = sorted(v1_cells - west_cells)
                extra = sorted(west_cells - v1_cells)
                f.write(
                    f"{z}\t{feat}\t{len(v1_cells)}\t{len(west_cells)}\t"
                    f"{','.join(str(x) for x in missing)}\t{','.join(str(x) for x in extra)}\n"
                )


def write_cells_tsv(cells: Iterable[Cell], out_path: Path) -> None:
    out_path.write_text(
        "zone_id\tzx\tzy\trx\try\tsector\tfeature\tavg_rgb_hex\n",
        encoding="utf-8",
    )
    with out_path.open("a", encoding="utf-8") as f:
        for c in cells:
            f.write(
                f"{c.zone_id}\t{c.zx}\t{c.zy}\t{c.rx}\t{c.ry}\t{c.sector}\t{c.feature}\t{hex_rgb(c.rgb)}\n"
            )


def write_zones_tsv(cells: Iterable[Cell], out_path: Path) -> None:
    # Aggregate counts per zone
    counts: dict[int, dict[str, int]] = {}
    for c in cells:
        z = counts.setdefault(c.zone_id, {})
        z[c.sector] = z.get(c.sector, 0) + 1
        if c.feature != "NONE":
            z[c.feature] = z.get(c.feature, 0) + 1

    out_path.write_text(
        "zone_id\tzx\tzy\tplains\tforest\thills\tmountains\twater\troad\n",
        encoding="utf-8",
    )
    with out_path.open("a", encoding="utf-8") as f:
        for zy in range(ZONE_ROWS):
            for zx in range(ZONE_COLS):
                zid = zone_id_for(zx, zy)
                z = counts.get(zid, {})
                f.write(
                    f"{zid}\t{zx}\t{zy}\t"
                    f"{z.get('PLAINS', 0)}\t{z.get('FOREST', 0)}\t{z.get('HILLS', 0)}\t"
                    f"{z.get('MOUNTAINS', 0)}\t{z.get('WATER', 0)}\t{z.get('ROAD', 0)}\n"
                )


def write_svg(
    cells: list[Cell],
    out_path: Path,
    *,
    v1_expected: Mapping[int, Mapping[str, set[int]]] | None = None,
) -> None:
    _require_pillow()
    from PIL import Image  # type: ignore

    im = Image.open(SRC_MAP)
    w, h = im.size

    room_cols = ZONE_COLS * ROOMS_PER_ZONE
    room_rows = ZONE_ROWS * ROOMS_PER_ZONE
    cell_w = w / room_cols
    cell_h = h / room_rows

    def cell_xy(zx: int, zy: int, rx: int, ry: int) -> tuple[float, float]:
        gx = zx * ROOMS_PER_ZONE + rx
        gy = zy * ROOMS_PER_ZONE + ry
        return (gx * cell_w, gy * cell_h)

    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
    )
    parts.append("<title>Westlands Ubermap v2 (planning grid)</title>")

    # Background
    parts.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="#111"/>')

    # Cells
    for c in cells:
        x, y = cell_xy(c.zx, c.zy, c.rx, c.ry)
        fill = SECTOR_COLOR.get(c.sector, "#ff00ff")
        parts.append(
            f'<rect x="{x:.3f}" y="{y:.3f}" width="{cell_w:.3f}" height="{cell_h:.3f}" fill="{fill}" />'
        )
        if c.feature == "ROAD":
            # Draw a tiny mark to indicate road candidate.
            parts.append(
                f'<rect x="{x + cell_w*0.35:.3f}" y="{y + cell_h*0.35:.3f}" '
                f'width="{cell_w*0.30:.3f}" height="{cell_h*0.30:.3f}" fill="#eaeaea" opacity="0.65" />'
            )
        elif c.feature == "RIVER":
            # Draw a tiny mark to indicate river candidate.
            parts.append(
                f'<rect x="{x + cell_w*0.35:.3f}" y="{y + cell_h*0.35:.3f}" '
                f'width="{cell_w*0.30:.3f}" height="{cell_h*0.30:.3f}" fill="#a8d8ff" opacity="0.75" />'
            )

    # Zone grid lines + labels
    zone_w = cell_w * ROOMS_PER_ZONE
    zone_h = cell_h * ROOMS_PER_ZONE

    # Thin internal room grid is intentionally omitted for readability at full-map scale.
    # Draw zone boundaries
    for zy in range(ZONE_ROWS + 1):
        y = zy * zone_h
        parts.append(f'<line x1="0" y1="{y:.3f}" x2="{w}" y2="{y:.3f}" stroke="#000" stroke-width="1.5" />')
    for zx in range(ZONE_COLS + 1):
        x = zx * zone_w
        parts.append(f'<line x1="{x:.3f}" y1="0" x2="{x:.3f}" y2="{h}" stroke="#000" stroke-width="1.5" />')

    # Labels
    for zy in range(ZONE_ROWS):
        for zx in range(ZONE_COLS):
            zid = zone_id_for(zx, zy)
            x = zx * zone_w + 3
            y = zy * zone_h + 12
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" font-family="monospace" font-size="12" '
                f'fill="#ffffff" stroke="#000000" stroke-width="0.7">{zid}</text>'
            )

    # Legend (top-left)
    lx = 6
    ly = 18
    parts.append(
        f'<text x="{lx}" y="{ly}" font-family="sans-serif" font-size="14" fill="#fff" stroke="#000" stroke-width="0.7">'
        "Legend</text>"
    )
    ly += 6
    for label, color in [
        ("PLAINS", SECTOR_COLOR["PLAINS"]),
        ("FOREST", SECTOR_COLOR["FOREST"]),
        ("HILLS", SECTOR_COLOR["HILLS"]),
        ("MOUNTAINS", SECTOR_COLOR["MOUNTAINS"]),
        ("WATER", SECTOR_COLOR["WATER"]),
        ("RIVER (candidate)", "#a8d8ff"),
        ("ROAD (candidate)", "#eaeaea"),
    ]:
        ly += 16
        parts.append(f'<rect x="{lx}" y="{ly-12}" width="12" height="12" fill="{color}" stroke="#000" />')
        parts.append(
            f'<text x="{lx+18}" y="{ly-2}" font-family="sans-serif" font-size="12" fill="#fff" stroke="#000" stroke-width="0.6">{label}</text>'
        )

    # v1 validation inset (537-540 only): show where v1 expects rivers/roads in those zones.
    # This is a visual regression check for the v1 slice, not a v2 “source of truth”.
    if v1_expected:
        inset_zones = [537, 538, 539, 540]
        cell_px = 6
        gap = 10
        inset_w = (cell_px * 10) * len(inset_zones) + gap * (len(inset_zones) - 1)
        inset_h = cell_px * 10
        ix0 = 6
        iy0 = h - inset_h - 20

        parts.append(
            f'<text x="{ix0}" y="{iy0 - 6}" font-family="sans-serif" font-size="12" '
            f'fill="#fff" stroke="#000" stroke-width="0.6">v1 expected roads/rivers (zones 537–540)</text>'
        )
        for idx, z in enumerate(inset_zones):
            zx = ix0 + idx * (cell_px * 10 + gap)
            zy = iy0
            parts.append(
                f'<text x="{zx}" y="{zy - 2}" font-family="monospace" font-size="10" '
                f'fill="#fff" stroke="#000" stroke-width="0.6">{z}</text>'
            )
            road = v1_expected.get(z, {}).get("road", set())
            river = v1_expected.get(z, {}).get("river", set())
            for cell in range(100):
                row = cell // 10
                col = cell % 10
                fill = "#222"
                if cell in river and cell in road:
                    fill = "#b07cff"  # overlap
                elif cell in river:
                    fill = "#2f67c7"
                elif cell in road:
                    fill = "#eaeaea"
                parts.append(
                    f'<rect x="{zx + col * cell_px}" y="{zy + row * cell_px}" width="{cell_px}" height="{cell_px}" '
                    f'fill="{fill}" stroke="#000" stroke-width="0.2" />'
                )

    parts.append("</svg>")
    out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg_out = OUT_DIR / "westlands_v2_ubermap.svg"
    cells_out = OUT_DIR / "westlands_v2_ubermap_cells.tsv"
    zones_out = OUT_DIR / "westlands_v2_ubermap_zones.tsv"
    geo_verify_out = OUT_DIR / "westlands_v2_v1_geo_verify_537_540.tsv"

    # Compute once; we need cells multiple times (SVG + TSV aggregations).
    cells = list(compute_cells())

    v1_expected = read_v1_expected(DEFAULT_V1_EXPECTED_TSV)
    write_svg(cells, svg_out, v1_expected=v1_expected if v1_expected else None)
    write_cells_tsv(cells, cells_out)
    write_zones_tsv(cells, zones_out)
    # Optional: geo verification currently relies on template matching, which is not robust
    # against “edited” or stylistically different source maps. Leave it as an opt-in artifact.
    # If the v1 expected TSV exists, we regenerate the geo report for debugging, but it should
    # be treated as experimental until OCR/symbol detection is added (phase 3).
    if v1_expected:
        write_v1_geo_verify_report(geo_verify_out)

    print(f"Wrote: {svg_out}")
    print(f"Wrote: {cells_out}")
    print(f"Wrote: {zones_out}")
    if geo_verify_out.exists():
        print(f"Wrote: {geo_verify_out}")


if __name__ == "__main__":
    main()

