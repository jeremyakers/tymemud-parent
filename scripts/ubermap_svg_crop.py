#!/usr/bin/env python3
"""
Crop a huge Ubermap SVG around a room vnum and optionally rasterize it to PNG.

This replaces inline Python one-liners in the terminal: it's reusable and scriptable.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


RE_X = re.compile(r'\bx="([0-9.-]+)"')
RE_Y = re.compile(r'\by="([0-9.-]+)"')

RE_RECT = re.compile(
    r'<rect\s+[^>]*x="([0-9.-]+)"\s+y="([0-9.-]+)"\s+width="([0-9.-]+)"\s+height="([0-9.-]+)"'
)
RE_TEXT_XY = re.compile(r'<text\s+[^>]*x="([0-9.-]+)"\s+y="([0-9.-]+)"')
RE_LINE = re.compile(
    r'<line\s+[^>]*x1="([0-9.-]+)"\s+y1="([0-9.-]+)"\s+x2="([0-9.-]+)"\s+y2="([0-9.-]+)"'
)


def _find_text_center(svg_path: Path, vnum: int) -> tuple[float, float]:
    needle = f">{vnum}</text>"
    with svg_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if needle not in line:
                continue
            mx = RE_X.search(line)
            my = RE_Y.search(line)
            if mx and my:
                return float(mx.group(1)), float(my.group(1))
    raise RuntimeError(f"Could not find vnum {vnum} in SVG text nodes: {svg_path}")


def crop_svg(
    *,
    svg_path: Path,
    vnum: int,
    half_w: int,
    half_h: int,
    out_svg: Path,
    canvas_px: int,
) -> tuple[float, float]:
    cx, cy = _find_text_center(svg_path, vnum)
    minx, maxx = cx - half_w, cx + half_w
    miny, maxy = cy - half_h, cy + half_h

    kept: list[str] = []
    header_written = False
    with svg_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not header_written and line.lstrip().startswith("<svg"):
                kept.append(
                    f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'width="{canvas_px}" height="{canvas_px}" '
                    f'viewBox="{minx} {miny} {2*half_w} {2*half_h}">\n'
                )
                header_written = True
                continue
            if not header_written:
                continue
            if line.lstrip().startswith("</svg"):
                break

            m = RE_RECT.search(line)
            if m:
                x, y, w, h = map(float, m.groups())
                if (x + w) < minx or x > maxx or (y + h) < miny or y > maxy:
                    continue
                kept.append(line)
                continue

            m = RE_LINE.search(line)
            if m:
                x1, y1, x2, y2 = map(float, m.groups())
                if (minx <= x1 <= maxx and miny <= y1 <= maxy) or (minx <= x2 <= maxx and miny <= y2 <= maxy):
                    kept.append(line)
                continue

            m = RE_TEXT_XY.search(line)
            if m:
                x, y = map(float, m.groups())
                if minx <= x <= maxx and miny <= y <= maxy:
                    kept.append(line)
                continue

    kept.append("</svg>\n")
    out_svg.write_text("".join(kept), encoding="utf-8")
    return cx, cy


def rasterize_svg(*, in_svg: Path, out_png: Path, convert_bin: str) -> None:
    subprocess.check_call(
        [
            convert_bin,
            "-background",
            "white",
            "-alpha",
            "remove",
            str(in_svg),
            str(out_png),
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Crop Ubermap SVG around a vnum, optionally render to PNG.")
    ap.add_argument("--svg", required=True, type=Path, help="Path to the source SVG")
    ap.add_argument("--vnum", required=True, type=int, help="Room vnum to center on")
    ap.add_argument("--half-w", type=int, default=12000, help="Half-width of crop window in SVG units")
    ap.add_argument("--half-h", type=int, default=12000, help="Half-height of crop window in SVG units")
    ap.add_argument("--out-dir", type=Path, default=Path("tmp"), help="Output directory")
    ap.add_argument("--canvas-px", type=int, default=2400, help="Output SVG/PNG canvas size in pixels")
    ap.add_argument("--png", action="store_true", help="Also render PNG via ImageMagick 'convert'")
    ap.add_argument("--convert-bin", default="convert", help="ImageMagick convert binary (default: convert)")
    args = ap.parse_args()

    svg_path: Path = args.svg
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_svg = out_dir / f"ubermap_crop_{args.vnum}.svg"
    out_png = out_dir / f"ubermap_crop_{args.vnum}.png"

    cx, cy = crop_svg(
        svg_path=svg_path,
        vnum=args.vnum,
        half_w=args.half_w,
        half_h=args.half_h,
        out_svg=out_svg,
        canvas_px=args.canvas_px,
    )

    print(f"wrote {out_svg} center=({cx:.1f},{cy:.1f})")
    if args.png:
        rasterize_svg(in_svg=out_svg, out_png=out_png, convert_bin=args.convert_bin)
        print(f"wrote {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

