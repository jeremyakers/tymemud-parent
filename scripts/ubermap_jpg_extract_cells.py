#!/usr/bin/env python3
"""
Extract terrain classification from `Building_Design_Notes/ubermap.jpg`.

Output is a TSV of:
  zone  cell  feature [rgb_r rgb_g rgb_b dist2]   (terrain mode)
  zone  cell  feature                           (road_river mode)

Where:
  - cell is 00..99 (matching vnum%100)
  - feature in {road, river} for `road_river` mode
  - feature in {plains, nothing, insert, town, hills, dragonmount, mountain, river, road, forest_light, forest_dense, unknown}
    for `terrain` mode

Implementation notes:
- Uses Pillow (PIL). No OpenCV dependency.
- The ubermap.jpg layout is fixed; we locate the 19 grids using simple
  row/column scanning + connected-component grouping of the thick black
  grid borders.
- Classification samples multiple points around the center of each cell and
  maps RGB to the nearest palette entry (from the legend swatches).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


try:
    from PIL import Image  # type: ignore
    from PIL import ImageDraw  # type: ignore
except Exception as e:  # noqa: BLE001
    raise SystemExit(f"ERROR: Pillow is required (PIL). Import failed: {e}")


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMG = ROOT / "Building_Design_Notes/ubermap.jpg"

# Target zones in visual order (row-major) as they appear in the JPG.
ZONES_ORDER = [
    469,
    468,
    509,
    508,
    # NOTE: ubermap.jpg has a known swapped label for 539/540. The grid rectangles are
    # detected by borders; we must map them to the intended zone IDs.
    540,
    539,
    538,
    537,
    # NOTE: The ubermap.jpg has a known mislabeling around 569/570.
    # The grid rectangles are detected by borders; we must map them to the intended zone IDs.
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


@dataclass(frozen=True)
class Rect:
    x0: int
    y0: int
    x1: int
    y1: int

    def w(self) -> int:
        return self.x1 - self.x0

    def h(self) -> int:
        return self.y1 - self.y0


def rgb_dist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def nearest_feature(rgb: tuple[int, int, int]) -> str | None:
    """
    Heuristic color classifier for ubermap.jpg.

    We only classify:
    - riverway: strong blue
    - main road: dark brown

    Everything else returns None (plains/forest/hills/etc).
    """
    r, g, b = rgb
    # Reject near-black (grid lines / text).
    if r < 35 and g < 35 and b < 35:
        return None

    # Riverway: distinctly blue. Note: in the JPEG, river cells can be a deep/dark blue
    # (e.g. ~ (0,0,130)), so avoid an overly high absolute B threshold.
    if b > 105 and (b - max(r, g)) > 85 and r < 120 and g < 120:
        return "river"

    # Main road: dark brown (avoid bright orange plains).
    if r < 180 and g < 160 and b < 120 and r > 80 and g > 40 and b < 90:
        # brown tends to have r>=g>=b-ish
        if r >= g and g >= b:
            return "road"

    return None


# Legend palette swatch RGBs sampled directly from the left-side legend in ubermap.jpg.
# Order matches the legend top-to-bottom.
TERRAIN_PALETTE: dict[str, tuple[int, int, int]] = {
    "plains": (255, 129, 62),
    "nothing": (192, 192, 192),
    "insert": (1, 255, 252),
    "town": (132, 0, 1),
    "hills": (1, 255, 0),
    "dragonmount": (0, 254, 130),
    "mountain": (253, 255, 1),
    # Riverway appears in multiple blue shades in the JPEG (bright + deep/dark).
    # We keep the "canonical" bright-blue swatch here, but `nearest_terrain()` treats
    # river as a multi-swatch class.
    "river": (2, 0, 251),
    "road": (126, 64, 5),
    "forest_light": (0, 128, 6),
    "forest_dense": (3, 63, 64),
}

# Alternate river swatches observed in ubermap.jpg grid cells (deep/dark blue).
RIVER_SWATCHES: tuple[tuple[int, int, int], ...] = (
    TERRAIN_PALETTE["river"],  # bright blue
    (1, 0, 130),               # deep/dark blue
)


def nearest_terrain(rgb: tuple[int, int, int]) -> tuple[str, int]:
    """
    Return (feature, dist2) where feature is the closest legend swatch.

    This is intentionally conservative about black pixels (grid lines / numbers):
    the caller should filter those out before averaging.
    """
    best_feat = "unknown"
    best_d2 = 1 << 60
    for feat, ref in TERRAIN_PALETTE.items():
        if feat == "river":
            d2 = min(rgb_dist(rgb, sw) for sw in RIVER_SWATCHES)
        else:
            d2 = rgb_dist(rgb, ref)
        if d2 < best_d2:
            best_d2 = d2
            best_feat = feat
    return best_feat, int(best_d2)


def is_border_pixel(rgb: tuple[int, int, int]) -> bool:
    # Grid borders are near-black.
    return rgb[0] < 125 and rgb[1] < 125 and rgb[2] < 125


def find_grid_rects(img: Image.Image) -> list[Rect]:
    """
    Find the 19 large 10x10 grid rectangles by scanning for thick black borders.

    Strategy:
    - Downscale to speed up.
    - Build a mask of dark pixels.
    - Find connected components of dark pixels.
    - Keep components with bounding boxes roughly square and within expected size range.
    """

    # Downscale for speed; keep aspect ratio.
    scale = 2
    small = img.resize((img.width // scale, img.height // scale))
    px = small.load()

    w, h = small.size
    dark = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            dark[y][x] = is_border_pixel((r, g, b))

    seen = [[False] * w for _ in range(h)]

    def neighbors(x: int, y: int) -> Iterable[tuple[int, int]]:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                yield nx, ny

    rects: list[Rect] = []

    for y in range(h):
        for x in range(w):
            if not dark[y][x] or seen[y][x]:
                continue
            # BFS flood fill
            stack = [(x, y)]
            seen[y][x] = True
            minx = maxx = x
            miny = maxy = y
            count = 0
            while stack:
                cx, cy = stack.pop()
                count += 1
                if cx < minx:
                    minx = cx
                if cx > maxx:
                    maxx = cx
                if cy < miny:
                    miny = cy
                if cy > maxy:
                    maxy = cy
                for nx, ny in neighbors(cx, cy):
                    if dark[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))

            # Filter small specks.
            bw = maxx - minx + 1
            bh = maxy - miny + 1
            if count < 200:
                continue
            # Candidate grid border rectangles are roughly square and "large".
            if bw < 90 or bh < 90:
                continue
            ar = bw / bh
            if ar < 0.85 or ar > 1.15:
                continue

            # Expand a bit (border thickness) and scale back to full-res.
            pad = 2
            x0 = max(minx - pad, 0) * scale
            y0 = max(miny - pad, 0) * scale
            x1 = min(maxx + pad, w - 1) * scale
            y1 = min(maxy + pad, h - 1) * scale

            rects.append(Rect(x0, y0, x1, y1))

    # Keep only the largest N by area, then sort row-major.
    rects.sort(key=lambda r: r.w() * r.h(), reverse=True)
    rects = rects[: len(ZONES_ORDER)]
    rects.sort(key=lambda r: (r.y0, r.x0))
    return rects


def extract_cells(img: Image.Image, rect: Rect) -> list[tuple[int, str]]:
    """
    Return a list of (cell, feature) for road/river cells in this grid.

    Cell index is row-major 00..99.
    """
    px = img.load()
    # Avoid sampling on borders; shrink slightly.
    inset = 6
    x0 = rect.x0 + inset
    y0 = rect.y0 + inset
    x1 = rect.x1 - inset
    y1 = rect.y1 - inset
    cw = (x1 - x0) / 10.0
    ch = (y1 - y0) / 10.0

    out: list[tuple[int, str]] = []
    # Sample a few points around center to reduce JPEG noise.
    sample_offsets = ((0, 0), (-3, 0), (3, 0), (0, -3), (0, 3))

    for row in range(10):
        for col in range(10):
            cx = int(x0 + (col + 0.5) * cw)
            cy = int(y0 + (row + 0.5) * ch)
            votes = {"road": 0, "river": 0}
            for dx, dy in sample_offsets:
                sx = max(min(cx + dx, img.width - 1), 0)
                sy = max(min(cy + dy, img.height - 1), 0)
                r, g, b = px[sx, sy]
                feat = nearest_feature((r, g, b))
                if feat in votes:
                    votes[feat] += 1
            # Majority vote (>=3 of 5).
            for feat in ("river", "road"):
                if votes[feat] >= 3:
                    cell = row * 10 + col
                    out.append((cell, feat))
                    break
    return out


def extract_cells_terrain(img: Image.Image, rect: Rect) -> list[tuple[int, str, tuple[int, int, int], int]]:
    """
    Return a list of (cell, feature, avg_rgb, dist2) for all cells in this grid.
    """
    px = img.load()
    inset = 6
    x0 = rect.x0 + inset
    y0 = rect.y0 + inset
    x1 = rect.x1 - inset
    y1 = rect.y1 - inset
    cw = (x1 - x0) / 10.0
    ch = (y1 - y0) / 10.0

    # Sample multiple points around center to reduce JPEG noise and avoid digit overlays.
    sample_offsets = (
        (0, 0),
        (-4, 0),
        (4, 0),
        (0, -4),
        (0, 4),
        (-4, -4),
        (4, -4),
        (-4, 4),
        (4, 4),
    )

    out: list[tuple[int, str, tuple[int, int, int], int]] = []
    for row in range(10):
        for col in range(10):
            cx = int(x0 + (col + 0.5) * cw)
            cy = int(y0 + (row + 0.5) * ch)
            samples: list[tuple[int, int, int]] = []
            for dx, dy in sample_offsets:
                sx = max(min(cx + dx, img.width - 1), 0)
                sy = max(min(cy + dy, img.height - 1), 0)
                r, g, b = px[sx, sy]
                # Reject near-black (grid lines / numbers) and near-white background.
                if r < 35 and g < 35 and b < 35:
                    continue
                if r > 245 and g > 245 and b > 245:
                    continue
                samples.append((r, g, b))

            if not samples:
                feat = "unknown"
                avg = (0, 0, 0)
                d2 = 1 << 30
            else:
                # Robust classification: vote by nearest legend swatch per sample.
                # This avoids “overlay bias” where a central label/number skews the average RGB.
                votes: dict[str, int] = {}
                best_d2: dict[str, int] = {}
                for rgb in samples:
                    f, dist2 = nearest_terrain(rgb)
                    votes[f] = votes.get(f, 0) + 1
                    best_d2[f] = min(best_d2.get(f, 1 << 60), dist2)

                # Choose by: highest vote count, then best (lowest) dist2.
                feat = sorted(votes.keys(), key=lambda k: (-votes[k], best_d2.get(k, 1 << 60), k))[0]

                # Also provide an avg RGB for debugging/TSV output.
                ar = sum(s[0] for s in samples) // len(samples)
                ag = sum(s[1] for s in samples) // len(samples)
                ab = sum(s[2] for s in samples) // len(samples)
                avg = (int(ar), int(ag), int(ab))
                d2 = int(best_d2.get(feat, 1 << 30))

            cell = row * 10 + col
            out.append((cell, feat, avg, int(d2)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", type=Path, default=DEFAULT_IMG)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--debug-rects", action="store_true", help="Print detected grid rectangles and exit.")
    ap.add_argument(
        "--debug-out-dir",
        type=Path,
        default=None,
        help="If set, write per-zone 10x10 PNG debug grids showing the classified cell feature colors.",
    )
    ap.add_argument(
        "--mode",
        choices=("road_river", "terrain"),
        default="road_river",
        help="Output mode: road_river (default) or full terrain classification",
    )
    args = ap.parse_args()

    img = Image.open(args.img).convert("RGB")
    rects = find_grid_rects(img)
    if args.debug_rects:
        print(f"found_grids={len(rects)}")
        for i, r in enumerate(rects):
            print(f"{i}\t{r.x0}\t{r.y0}\t{r.x1}\t{r.y1}\t{r.w()}x{r.h()}")
        return 0
    if len(rects) != len(ZONES_ORDER):
        raise SystemExit(f"ERROR: expected {len(ZONES_ORDER)} grids, found {len(rects)}")

    if args.mode == "terrain":
        lines: list[str] = ["zone\tcell\tfeature\tr\tg\tb\tdist2"]
        debug_out: dict[int, list[tuple[int, str]]] = {}
        for zone, rect in zip(ZONES_ORDER, rects, strict=True):
            cells = extract_cells_terrain(img, rect)
            for cell, feat, (r, g, b), d2 in cells:
                lines.append(f"{zone}\t{cell:02d}\t{feat}\t{r}\t{g}\t{b}\t{d2}")
            debug_out[zone] = [(cell, feat) for (cell, feat, _rgb, _d2) in cells]

        if args.debug_out_dir is not None:
            args.debug_out_dir.mkdir(parents=True, exist_ok=True)
            # Render a compact 10x10 debug grid per zone.
            # This is intentionally schematic (not an overlay on the original JPG) so it’s easy to eyeball.
            cell_px = 32
            pad = 2
            for zone, cells in debug_out.items():
                w = (cell_px + pad) * 10 + pad
                h = (cell_px + pad) * 10 + pad
                im = Image.new("RGB", (w, h), (255, 255, 255))
                dr = ImageDraw.Draw(im)
                for cell, feat in cells:
                    row = cell // 10
                    col = cell % 10
                    x0 = pad + col * (cell_px + pad)
                    y0 = pad + row * (cell_px + pad)
                    x1 = x0 + cell_px
                    y1 = y0 + cell_px
                    color = TERRAIN_PALETTE.get(feat, (255, 0, 255))
                    # Use the canonical river swatch for display.
                    if feat == "river":
                        color = TERRAIN_PALETTE["river"]
                    dr.rectangle((x0, y0, x1, y1), fill=color, outline=(0, 0, 0))
                    dr.text((x0 + 3, y0 + 2), f"{cell:02d}", fill=(0, 0, 0))
                im.save(args.debug_out_dir / f"ubermap_jpg_debug_zone_{zone}.png")
    else:
        lines = ["zone\tcell\tfeature"]
        for zone, rect in zip(ZONES_ORDER, rects, strict=True):
            for cell, feat in extract_cells(img, rect):
                lines.append(f"{zone}\t{cell:02d}\t{feat}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out} rows={len(lines)-1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

