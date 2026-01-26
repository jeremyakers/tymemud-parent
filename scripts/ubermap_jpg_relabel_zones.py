#!/usr/bin/env python3
"""
Overwrite zone labels on Building_Design_Notes/ubermap.jpg by *position*.

Goal:
- Make the image itself reflect the canonical layout rule:
  zone numbers increase from right to left (so leftmost in a row is largest zone id).
- Prevent recurring mistakes where humans (and scripts) follow the wrong printed label.

Approach:
- Detect the thick-border grid rectangles (same method as ubermap_jpg_extract_cells.py).
- Use that script's ZONES_ORDER mapping (visual order) to decide which zone id belongs to each rect.
- Paint a white label box above each rect and draw the correct zone number.

Notes:
- This script does NOT attempt OCR; it simply overwrites a small region where the label is expected.
- Always make a backup before overwriting the JPG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMG = ROOT / "Building_Design_Notes/ubermap.jpg"

# Reuse the grid detector and the canonical zone mapping.
import sys  # noqa: E402

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ubermap_jpg_extract_cells import ZONES_ORDER, find_grid_rects  # type: ignore  # noqa: E402


def _load_font(px: int) -> ImageFont.ImageFont:
    # Prefer a real TTF for legibility; fall back to default.
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(p, px)
        except Exception:
            pass
    return ImageFont.load_default()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", type=Path, default=DEFAULT_IMG, help="Input ubermap.jpg")
    ap.add_argument("--out", type=Path, required=True, help="Output JPG path")
    ap.add_argument("--font-px", type=int, default=26)
    ap.add_argument("--pad-x", type=int, default=10)
    ap.add_argument("--pad-y", type=int, default=6)
    ap.add_argument("--y-offset", type=int, default=34, help="Pixels above rect.y0 to place label box")
    args = ap.parse_args()

    im = Image.open(args.img).convert("RGB")
    rects = find_grid_rects(im)
    rects = rects[: len(ZONES_ORDER)]
    if len(rects) != len(ZONES_ORDER):
        raise SystemExit(f"expected {len(ZONES_ORDER)} grids, found {len(rects)}")

    dr = ImageDraw.Draw(im)
    font = _load_font(args.font_px)

    for zone, r in zip(ZONES_ORDER, rects, strict=True):
        text = str(zone)
        # Centered above the rect, slightly outside the border.
        cx = (r.x0 + r.x1) // 2
        y = max(0, r.y0 - args.y_offset)

        bbox = dr.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        x0 = max(0, cx - (tw // 2) - args.pad_x)
        y0 = y
        x1 = min(im.width - 1, cx + (tw // 2) + args.pad_x)
        y1 = min(im.height - 1, y + th + args.pad_y * 2)

        # Paint opaque background to cover any existing label text.
        dr.rectangle((x0, y0, x1, y1), fill=(255, 255, 255))
        # Border to make the label pop.
        dr.rectangle((x0, y0, x1, y1), outline=(0, 0, 0), width=2)

        tx = cx - (tw // 2)
        ty = y + args.pad_y
        dr.text((tx, ty), text, fill=(0, 0, 0), font=font)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    im.save(args.out, quality=95)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

