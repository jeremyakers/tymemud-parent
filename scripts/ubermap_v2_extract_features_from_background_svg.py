#!/usr/bin/env python3
"""
Extract road/river cell features from Building_Design_Notes/Westlands-Background.svg.

Per user key:
  - rivers: blue strokes
  - roads: solid brown strokes
  - dotted lines: national boundaries (ignore)
  - elevation lines: brown-ish but different shade (try to ignore by hue/width heuristics)

This script is explicitly meant to produce a *mechanical verification* for the v1 slice
(zones 537–540) before we trust any v2 full-map rendering.

Outputs:
  - docs/ubermap/v2/extracts/background_svg_road_river_cells.tsv  (zone/cell/feature)
  - docs/ubermap/v2/extracts/background_svg_verify_537_540.tsv   (expected vs extracted)
  - docs/ubermap/v2/extracts/background_svg_debug_537_540.svg    (visual debug overlay)

Run:
  # NOTE: This may churn CPU for a long time if you use --search-mode=viewbox.
  uvx --with svgpathtools --with numpy python scripts/ubermap_v2_extract_features_from_background_svg.py
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SVG_IN = ROOT / "Building_Design_Notes" / "Westlands-Background.svg"
# Read-only: prefer the dedicated agent worktree copy for world files so we don't touch
# another agent's working repo under ROOT/MM32.
WLD_DIR = ROOT / "_agent_work" / "ubermap_agent" / "MM32" / "lib" / "world" / "wld"
if not WLD_DIR.exists():
    WLD_DIR = ROOT / "MM32" / "lib" / "world" / "wld"

OUT_DIR = ROOT / "docs" / "ubermap" / "v2" / "extracts"
OUT_CELLS = OUT_DIR / "background_svg_road_river_cells.tsv"
OUT_VERIFY = OUT_DIR / "background_svg_verify_537_540.tsv"
OUT_DEBUG_SVG = OUT_DIR / "background_svg_debug_537_540.svg"
V1_EXPECTED_TSV = OUT_DIR / "v1_ubermap_road_river_cells.tsv"

ZONE_COLS = 26
ZONE_ROWS = 20
ROOMS_PER_ZONE = 10
TOP_LEFT_ZONE = 925


def _require_deps():
    try:
        import numpy as np  # noqa: F401
        from svgpathtools import svg2paths2  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            "Missing deps. Run:\n"
            "  uvx --with svgpathtools --with numpy python scripts/ubermap_v2_extract_features_from_background_svg.py\n"
            f"Import error: {e}"
        )


def zone_id_for(zx: int, zy: int) -> int:
    return TOP_LEFT_ZONE - zx - (zy * ZONE_COLS)


def zone_xy_for_id(zone_id: int) -> tuple[int, int]:
    """
    Invert zone_id_for() for the fixed grid. Raises if out of range.
    """
    # zone_id = TOP_LEFT_ZONE - zx - ZONE_COLS*zy
    d = TOP_LEFT_ZONE - zone_id
    zy = d // ZONE_COLS
    zx = d - (zy * ZONE_COLS)
    if not (0 <= zx < ZONE_COLS and 0 <= zy < ZONE_ROWS):
        raise ValueError(f"zone_id {zone_id} out of grid range")
    return zx, zy


def _hex_to_rgb(s: str) -> tuple[int, int, int] | None:
    s = s.strip()
    if not s:
        return None
    if s.lower() == "none":
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


def _parse_style(style: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in style.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def _get_attr(attrs: dict, key: str) -> str | None:
    if key in attrs and attrs[key] is not None:
        return str(attrs[key])
    style = attrs.get("style")
    if style:
        sd = _parse_style(style)
        if key in sd:
            return sd[key]
    return None


def _is_dotted(attrs: dict) -> bool:
    da = _get_attr(attrs, "stroke-dasharray")
    if not da:
        return False
    # Any dasharray means not a solid road; boundaries are dotted.
    return da.lower() != "none"


def _stroke_width(attrs: dict) -> float | None:
    sw = _get_attr(attrs, "stroke-width")
    if not sw:
        return None
    try:
        return float(sw)
    except ValueError:
        return None


def _classify_path(attrs: dict) -> str | None:
    """
    Return "river" or "road" for relevant paths, else None.

    Heuristics:
      - ignore dashed/dotted
      - rivers: blue-ish hue, medium saturation
      - roads: brown-ish hue, medium saturation
      - ignore filled shapes (terrain) by requiring fill=none for roads/rivers
    """
    if _is_dotted(attrs):
        return None

    stroke = _get_attr(attrs, "stroke")
    rgb = _hex_to_rgb(stroke) if stroke else None
    if rgb is None:
        return None

    fill = (_get_attr(attrs, "fill") or "").strip().lower()
    if fill and fill != "none":
        return None

    h, s, v = _rgb_to_hsv(*rgb)
    # hue in degrees:
    hd = h * 360.0
    sw = _stroke_width(attrs)

    # Rivers: blue-ish.
    if 185.0 <= hd <= 235.0 and s >= 0.25 and v >= 0.25:
        return "river"

    # Roads: solid brown-ish. Elevation lines are often lighter/grayish and/or very thin.
    if 15.0 <= hd <= 55.0 and s >= 0.25 and 0.10 <= v <= 0.75:
        # Prefer widths that look like "linework" not large fills.
        if sw is None or sw <= 0.35:
            return "road"
    return None


@dataclass(frozen=True)
class Anchor:
    caemlyn: tuple[float, float]
    cairhien: tuple[float, float]
    zone_w: float
    zone_h: float


def _load_text_anchors(svg_path: Path) -> Anchor:
    """
    Find 'Caemlyn' and 'Cairhien' label coordinates from the SVG.

    This SVG stores many labels as vector glyph paths under a `<g aria-label="...">`
    rather than `<text x= y=>`. We approximate the label position by reading the first
    moveto coordinate from the first path inside that group.
    """
    import xml.etree.ElementTree as ET
    import re

    tree = ET.parse(svg_path)
    root = tree.getroot()

    caemlyn = None
    cairhien = None
    want = {"Caemlyn", "Cairhien"}
    moveto_re = re.compile(r"^[mM]\s*([+-]?\d+(?:\.\d+)?)\s*,?\s*([+-]?\d+(?:\.\d+)?)")

    for el in root.iter():
        tag = el.tag.split("}", 1)[-1]
        if tag != "g":
            continue
        label = el.attrib.get("aria-label")
        if label not in want:
            continue
        # Find first <path d="mX Y ..."> inside.
        for child in el.iter():
            ctag = child.tag.split("}", 1)[-1]
            if ctag != "path":
                continue
            d = child.attrib.get("d", "")
            m = moveto_re.match(d.strip())
            if not m:
                continue
            x = float(m.group(1))
            y = float(m.group(2))
            if label == "Caemlyn":
                caemlyn = (x, y)
            elif label == "Cairhien":
                cairhien = (x, y)
            break
        if caemlyn and cairhien:
            break

    if not caemlyn or not cairhien:
        raise RuntimeError("Could not locate 'Caemlyn' and 'Cairhien' text anchors in SVG.")

    # Zone width: 539 -> 537 is 2 zones.
    zone_w = abs(cairhien[0] - caemlyn[0]) / 2.0
    zone_h = zone_w
    return Anchor(caemlyn=caemlyn, cairhien=cairhien, zone_w=zone_w, zone_h=zone_h)


def _zone_rects_537_540(a: Anchor) -> dict[int, tuple[float, float, float, float]]:
    """
    Build rects (x0,y0,x1,y1) for zones 540..537 in one row, centered on Cairhien/Caemlyn anchors.
    """
    # Put zone 537 centered on Cairhien anchor y, and keep the row horizontal.
    cx, cy = a.cairhien
    y0 = cy - a.zone_h / 2.0
    y1 = cy + a.zone_h / 2.0

    def rect_for_center(center_x: float) -> tuple[float, float, float, float]:
        return (center_x - a.zone_w / 2.0, y0, center_x + a.zone_w / 2.0, y1)

    # zone 539 center is 2 zones west of 537 center
    c537 = (cx, cy)
    c539 = (cx - 2.0 * a.zone_w, cy)

    # sanity: nudge using Caemlyn anchor x (keep cy)
    # if the derived center is far from the label, use the label x.
    if abs(c539[0] - a.caemlyn[0]) > a.zone_w * 0.75:
        c539 = (a.caemlyn[0], cy)
        # adjust c537 accordingly so 539->537 remains 2 zones
        c537 = (c539[0] + 2.0 * a.zone_w, cy)

    rects = {
        537: rect_for_center(c537[0]),
        538: rect_for_center(c539[0] + 1.0 * a.zone_w),
        539: rect_for_center(c539[0]),
        540: rect_for_center(c539[0] - 1.0 * a.zone_w),
    }
    return rects


def _rects_from_row_origin(x0: float, y0: float, zone_w: float, zone_h: float) -> dict[int, tuple[float, float, float, float]]:
    """
    Create rects for a single row of 4 zones laid out west->east: 540,539,538,537.
    """
    rects: dict[int, tuple[float, float, float, float]] = {}
    for i, z in enumerate([540, 539, 538, 537]):
        zx0 = x0 + i * zone_w
        rects[z] = (zx0, y0, zx0 + zone_w, y0 + zone_h)
    return rects


def _score_rects(
    rects: dict[int, tuple[float, float, float, float]],
    points: dict[str, list[tuple[float, float]]],
    expected: dict[int, dict[str, set[int]]],
) -> tuple[float, dict[int, dict[str, set[int]]]]:
    """
    Score how well extracted points match v1 expected cells for zones 537–540.
    Returns (score, found_cells).
    """
    def _score_from_counts(*, hits: int, missing: int, extras: int) -> float:
        """
        Optimize for the same metric we report in verification: overall F1.
        Add a tiny tie-breaker on hits so we don't prefer degenerate low-coverage solutions.
        """
        tp = float(hits)
        fp = float(extras)
        fn = float(missing)
        precision = 0.0 if (tp + fp) == 0.0 else (tp / (tp + fp))
        recall = 0.0 if (tp + fn) == 0.0 else (tp / (tp + fn))
        f1 = 0.0 if (precision + recall) == 0.0 else (2.0 * precision * recall / (precision + recall))
        return (1000.0 * f1) + (0.01 * float(hits))

    found: dict[int, dict[str, set[int]]] = {z: {"road": set(), "river": set()} for z in rects.keys()}

    # Populate found cells from points for each feature.
    for feat, pts in points.items():
        for x, y in pts:
            for z, r in rects.items():
                cell = _cell_for_point_in_zone(x, y, r)
                if cell is not None:
                    found[z][feat].add(cell)

    # Score: reward hits, penalize extras + missing.
    hits = 0
    missing = 0
    extras = 0
    for z in [537, 538, 539, 540]:
        for feat in ("river", "road"):
            exp = expected.get(z, {}).get(feat, set())
            got = found.get(z, {}).get(feat, set())
            hits += len(exp & got)
            missing += len(exp - got)
            extras += len(got - exp)

    score = _score_from_counts(hits=hits, missing=missing, extras=extras)
    return score, found


def _prep_expected_arrays(expected: dict[int, dict[str, set[int]]]) -> dict[int, dict[str, "np.ndarray"]]:
    """
    Convert expected sets to bool arrays for fast scoring.
    """
    import numpy as np

    def _dilate_10x10(arr: "np.ndarray", t: int) -> "np.ndarray":
        """
        Chebyshev dilation on a 10x10 cell grid stored as a 100-length bool array.
        """
        if t <= 0:
            return arr
        g = arr.reshape((10, 10))
        out = np.zeros_like(g, dtype=bool)
        for dy in range(-t, t + 1):
            for dx in range(-t, t + 1):
                y0 = max(0, 0 + dy)
                y1 = min(10, 10 + dy)
                x0 = max(0, 0 + dx)
                x1 = min(10, 10 + dx)
                out[y0:y1, x0:x1] |= g[y0 - dy : y1 - dy, x0 - dx : x1 - dx]
        return out.reshape((100,))

    out: dict[int, dict[str, "np.ndarray"]] = {}
    for z in [537, 538, 539, 540]:
        out[z] = {}
        for feat in ("river", "road"):
            arr = np.zeros(100, dtype=bool)
            for c in expected.get(z, {}).get(feat, set()):
                if 0 <= c < 100:
                    arr[c] = True
            tol = int(getattr(_prep_expected_arrays, "_cell_tolerance", 0))
            out[z][feat] = np.stack([arr, _dilate_10x10(arr, tol)], axis=0)
    return out


def _score_row_origin_numpy(
    *,
    x0: float,
    y0: float,
    zone_w: float,
    zone_h: float,
    points_xy: dict[str, "np.ndarray"],
    expected_arr: dict[int, dict[str, "np.ndarray"]],
) -> tuple[float, dict[int, dict[str, set[int]]]]:
    """
    Score a specific row placement (x0,y0) for zones 540..537 using numpy vectorization.

    Returns (score, found_cells) where found_cells is only for the best candidate reporting/debug.
    """
    import numpy as np

    def _dilate_10x10(arr: "np.ndarray", t: int) -> "np.ndarray":
        if t <= 0:
            return arr
        g = arr.reshape((10, 10))
        out = np.zeros_like(g, dtype=bool)
        for dy in range(-t, t + 1):
            for dx in range(-t, t + 1):
                y0 = max(0, 0 + dy)
                y1 = min(10, 10 + dy)
                x0 = max(0, 0 + dx)
                x1 = min(10, 10 + dx)
                out[y0:y1, x0:x1] |= g[y0 - dy : y1 - dy, x0 - dx : x1 - dx]
        return out.reshape((100,))

    found: dict[int, dict[str, set[int]]] = {z: {"road": set(), "river": set()} for z in (537, 538, 539, 540)}

    hits = 0
    missing = 0
    extras = 0

    # zones laid out west->east: 540,539,538,537
    zones = [540, 539, 538, 537]
    for feat, xy in points_xy.items():
        if xy.size == 0:
            continue
        xs = xy[:, 0]
        ys = xy[:, 1]

        for i, z in enumerate(zones):
            zx0 = x0 + (i * zone_w)
            zx1 = zx0 + zone_w
            zy0 = y0
            zy1 = y0 + zone_h

            m = (xs >= zx0) & (xs < zx1) & (ys >= zy0) & (ys < zy1)
            if not np.any(m):
                got_arr = np.zeros(100, dtype=bool)
            else:
                x_rel = (xs[m] - zx0) / zone_w
                y_rel = (ys[m] - zy0) / zone_h
                col = np.floor(x_rel * 10.0).astype(int)
                row = np.floor(y_rel * 10.0).astype(int)
                ok = (col >= 0) & (col <= 9) & (row >= 0) & (row <= 9)
                if not np.any(ok):
                    got_arr = np.zeros(100, dtype=bool)
                else:
                    cell = (row[ok] * 10) + col[ok]
                    cell_u = np.unique(cell)
                    got_arr = np.zeros(100, dtype=bool)
                    got_arr[cell_u] = True

            exp_stack = expected_arr[z][feat]
            exp_base = exp_stack[0]
            exp_dil = exp_stack[1]
            tol = int(getattr(_score_row_origin_numpy, "_cell_tolerance", 0))
            got_dil = _dilate_10x10(got_arr, tol)

            # Tolerant scoring:
            # - hit: predicted cell is within tol of any expected cell
            # - missing: expected cell has no predicted cell within tol
            # - extra: predicted cell has no expected cell within tol
            hits += int(np.sum(got_arr & exp_dil))
            missing += int(np.sum(exp_base & (~got_dil)))
            extras += int(np.sum(got_arr & (~exp_dil)))

            # Only keep found cells for best candidate debug/report.
            if np.any(got_arr):
                found[z][feat] = {int(i) for i in np.flatnonzero(got_arr)}

    # Optimize for overall F1 (with tiny tie-breaker on hits).
    tp = float(hits)
    fp = float(extras)
    fn = float(missing)
    precision = 0.0 if (tp + fp) == 0.0 else (tp / (tp + fp))
    recall = 0.0 if (tp + fn) == 0.0 else (tp / (tp + fn))
    f1 = 0.0 if (precision + recall) == 0.0 else (2.0 * precision * recall / (precision + recall))
    score = (1000.0 * f1) + (0.01 * float(hits))
    return score, found


def _auto_fit_row_rects(
    *,
    zone_w: float,
    zone_h: float,
    anchor_hint: tuple[float, float] | None,
    viewbox: tuple[float, float, float, float] | None,
    points_xy: dict[str, "np.ndarray"],
    expected: dict[int, dict[str, set[int]]],
    expected_arr: dict[int, dict[str, "np.ndarray"]],
    radius_zones: float,
) -> tuple[dict[int, tuple[float, float, float, float]], dict[int, dict[str, set[int]]], float]:
    """
    Find a best-fit row placement (x0,y0) for zones 540..537 by maximizing overlap with v1 expected.
    This is a mechanical verification fit, not a world-building "truth" fit.
    """
    if viewbox is not None:
        vb_x, vb_y, vb_w, vb_h = viewbox
        x0_min = vb_x
        y0_min = vb_y
        x0_max = vb_x + vb_w - (4.0 * zone_w)
        y0_max = vb_y + vb_h - zone_h
    else:
        assert anchor_hint is not None
        ax, ay = anchor_hint
        # Search window around the hint (Cairhien label is a decent rough region).
        x_span = zone_w * radius_zones
        y_span = zone_h * radius_zones
        x0_min = ax - x_span
        x0_max = ax + x_span
        y0_min = ay - y_span
        y0_max = ay + y_span

    best_score = None
    best_rects: dict[int, tuple[float, float, float, float]] | None = None
    best_found: dict[int, dict[str, set[int]]] | None = None

    # Coarse step, then refine around best.
    coarse_step = max(1.0, zone_w / 6.0)
    for y0 in frange(y0_min, y0_max, coarse_step):
        for x0 in frange(x0_min, x0_max, coarse_step):
            rects = _rects_from_row_origin(x0=x0, y0=y0, zone_w=zone_w, zone_h=zone_h)
            score, found = _score_row_origin_numpy(
                x0=x0, y0=y0, zone_w=zone_w, zone_h=zone_h, points_xy=points_xy, expected_arr=expected_arr
            )
            if best_score is None or score > best_score:
                best_score = score
                best_rects = rects
                best_found = found

    assert best_score is not None and best_rects is not None and best_found is not None

    # Refine around best
    bx0 = best_rects[540][0]
    by0 = best_rects[540][1]
    fine_step = max(0.5, coarse_step / 4.0)
    x0_min2 = bx0 - 2.0 * coarse_step
    x0_max2 = bx0 + 2.0 * coarse_step
    y0_min2 = by0 - 2.0 * coarse_step
    y0_max2 = by0 + 2.0 * coarse_step
    for y0 in frange(y0_min2, y0_max2, fine_step):
        for x0 in frange(x0_min2, x0_max2, fine_step):
            rects = _rects_from_row_origin(x0=x0, y0=y0, zone_w=zone_w, zone_h=zone_h)
            score, found = _score_row_origin_numpy(
                x0=x0, y0=y0, zone_w=zone_w, zone_h=zone_h, points_xy=points_xy, expected_arr=expected_arr
            )
            if score > best_score:
                best_score = score
                best_rects = rects
                best_found = found

    # Ultra-fine refine: tighten alignment to cell boundaries. This is still relatively cheap
    # because we only score 4 zones (540..537) and the work is numpy-vectorized.
    bx0 = best_rects[540][0]
    by0 = best_rects[540][1]
    ultra_step = max(0.1, fine_step / 5.0)
    x0_min3 = bx0 - 2.0 * fine_step
    x0_max3 = bx0 + 2.0 * fine_step
    y0_min3 = by0 - 2.0 * fine_step
    y0_max3 = by0 + 2.0 * fine_step
    for y0 in frange(y0_min3, y0_max3, ultra_step):
        for x0 in frange(x0_min3, x0_max3, ultra_step):
            rects = _rects_from_row_origin(x0=x0, y0=y0, zone_w=zone_w, zone_h=zone_h)
            score, found = _score_row_origin_numpy(
                x0=x0, y0=y0, zone_w=zone_w, zone_h=zone_h, points_xy=points_xy, expected_arr=expected_arr
            )
            if score > best_score:
                best_score = score
                best_rects = rects
                best_found = found

    return best_rects, best_found, float(best_score)


def _auto_fit_row_rects_multi_scale(
    *,
    zone_w_hint: float,
    viewbox: tuple[float, float, float, float] | None,
    points_xy: dict[str, "np.ndarray"],
    expected: dict[int, dict[str, set[int]]],
    expected_arr: dict[int, dict[str, "np.ndarray"]],
    anchor_hint: tuple[float, float] | None,
    radius_zones: float,
    max_workers: int,
) -> tuple[dict[int, tuple[float, float, float, float]], dict[int, dict[str, set[int]]], float, float]:
    """
    Search across zone sizes as well as placement. Returns (rects, found, best_score, best_zone_w).
    """
    if viewbox is not None:
        _, _, vb_w, vb_h = viewbox
        # Reasonable bounds: zone must be smaller than 1/4 width and not too tiny.
        min_w = max(12.0, vb_w / 80.0)
        max_w = min(160.0, vb_w / 4.0)
    else:
        min_w = 12.0
        max_w = 160.0

    # Search near hint first, then broaden.
    candidates: list[float] = []
    for step in (1.0, 2.0, 3.0):
        lo = max(min_w, zone_w_hint * 0.6)
        hi = min(max_w, zone_w_hint * 1.4)
        w = lo
        while w <= hi:
            candidates.append(round(w, 3))
            w += step
        break
    # Add a few broader candidates in case hint is off.
    w = max(min_w, zone_w_hint * 0.35)
    while w <= min(max_w, zone_w_hint * 2.0):
        candidates.append(round(w, 3))
        w += 5.0

    candidates = sorted(set(candidates))

    best_score = None
    best_rects = None
    best_found = None
    best_w = None

    # Evaluate zone width candidates in parallel. We prefer threads so the large numpy arrays
    # are shared (no pickling). The scoring work is numpy-heavy and releases the GIL.
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _eval_one(w: float) -> tuple[float, float, dict[int, tuple[float, float, float, float]], dict[int, dict[str, set[int]]]]:
        rects, found, score = _auto_fit_row_rects(
            zone_w=w,
            zone_h=w,
            anchor_hint=anchor_hint,
            viewbox=viewbox,
            points_xy=points_xy,
            expected=expected,
            expected_arr=expected_arr,
            radius_zones=radius_zones,
        )
        return score, w, rects, found

    workers = max(1, int(max_workers))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_eval_one, w) for w in candidates]
        for fut in as_completed(futs):
            score, w, rects, found = fut.result()
            if best_score is None or score > best_score:
                best_score = score
                best_rects = rects
                best_found = found
                best_w = w

    assert best_score is not None and best_rects is not None and best_found is not None and best_w is not None
    return best_rects, best_found, float(best_score), float(best_w)


def frange(start: float, stop: float, step: float) -> Iterable[float]:
    x = start
    # safety cap
    i = 0
    while x <= stop and i < 1000000:
        yield x
        x += step
        i += 1


def _iter_sample_points(path, sample_step: float) -> Iterable[tuple[float, float]]:
    """
    Sample points along an svgpathtools Path.
    """
    length = max(float(path.length(error=1e-3)), 0.0)
    if length == 0.0:
        return []
    n = max(20, int(length / sample_step))
    for i in range(n + 1):
        t = i / n
        z = path.point(t)
        yield (float(z.real), float(z.imag))


def _load_v1_expected(tsv_path: Path) -> dict[int, dict[str, set[int]]]:
    out: dict[int, dict[str, set[int]]] = {}
    if not tsv_path.exists():
        return out

    lines = tsv_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        return out

    # Expected header: zone\tcell\tfeature
    for raw in lines[1:]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 3:
            continue

        z_s = parts[0].strip()
        cell_s = parts[1].strip()
        feat_s = parts[2].strip().lower()
        if not z_s.isdigit():
            continue

        try:
            z = int(z_s)
            cell = int(cell_s)
        except ValueError:
            continue

        if feat_s not in {"road", "river"}:
            continue
        if not (0 <= cell < 100):
            continue

        out.setdefault(z, {"road": set(), "river": set()})[feat_s].add(cell)

    return out


def _iter_room_names(wld_path: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    lines = wld_path.read_text(encoding="latin-1", errors="replace").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#") and line[1:].strip().isdigit():
            vnum = int(line[1:].strip())
            if i + 1 < len(lines):
                out[vnum] = lines[i + 1]
            i += 2
            continue
        i += 1
    return out


def _is_road_name(name: str) -> bool:
    s = name.lower()
    return "road" in s or "jangai" in s or "caemlyn road" in s


def _is_river_name(name: str) -> bool:
    s = name.lower()
    return "river" in s or "erinin" in s or "alguenya" in s or "gaelin" in s or "alindrelle" in s


def _world_expected_for_zones(zones: Iterable[int]) -> dict[int, dict[str, set[int]]]:
    """
    Build expected road/river cells from existing world room names for the given zones.
    """
    out: dict[int, dict[str, set[int]]] = {}
    for z in zones:
        wld = WLD_DIR / f"{z}.wld"
        names = _iter_room_names(wld)
        exp = {"road": set(), "river": set()}
        for vnum, name in names.items():
            if vnum // 100 != z:
                continue
            cell = vnum % 100
            if _is_river_name(name):
                exp["river"].add(cell)
            if _is_road_name(name):
                exp["road"].add(cell)
        out[z] = exp
    return out


def _f1(hits: int, missing: int, extras: int) -> tuple[float, float, float]:
    """
    Return (precision, recall, f1) given counts.
    """
    tp = float(hits)
    fp = float(extras)
    fn = float(missing)
    precision = 0.0 if (tp + fp) == 0.0 else (tp / (tp + fp))
    recall = 0.0 if (tp + fn) == 0.0 else (tp / (tp + fn))
    f1 = 0.0 if (precision + recall) == 0.0 else (2.0 * precision * recall / (precision + recall))
    return precision, recall, f1


def _cell_for_point_in_zone(x: float, y: float, rect: tuple[float, float, float, float]) -> int | None:
    x0, y0, x1, y1 = rect
    if x < x0 or x >= x1 or y < y0 or y >= y1:
        return None
    rx = (x - x0) / (x1 - x0)
    ry = (y - y0) / (y1 - y0)
    col = int(rx * 10.0)
    row = int(ry * 10.0)
    if col < 0 or col > 9 or row < 0 or row > 9:
        return None
    return row * 10 + col


def _write_debug_svg(rects: dict[int, tuple[float, float, float, float]], found: dict[int, dict[str, set[int]]], expected: dict[int, dict[str, set[int]]]) -> None:
    # Simple debug SVG with 4 zone rects and 10x10 overlays (expected vs found).
    # Use the coordinate space of the input SVG.
    zlist = [540, 539, 538, 537]
    x0 = min(rects[z][0] for z in zlist)
    y0 = min(rects[z][1] for z in zlist)
    x1 = max(rects[z][2] for z in zlist)
    y1 = max(rects[z][3] for z in zlist)

    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1-x0} {y1-y0}">')
    parts.append('<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>')
    parts.append('<text x="{:.3f}" y="{:.3f}" font-family="sans-serif" font-size="6">v1 expected vs background-svg extracted</text>'.format(x0 + 2, y0 + 8))

    for z in zlist:
        zx0, zy0, zx1, zy1 = rects[z]
        zw = zx1 - zx0
        zh = zy1 - zy0
        parts.append(f'<rect x="{zx0:.3f}" y="{zy0:.3f}" width="{zw:.3f}" height="{zh:.3f}" fill="none" stroke="#000" stroke-width="0.6"/>')
        parts.append(f'<text x="{zx0+1.5:.3f}" y="{zy0+6:.3f}" font-family="monospace" font-size="6">{z}</text>')

        exp_r = expected.get(z, {}).get("river", set())
        exp_d = expected.get(z, {}).get("road", set())
        got_r = found.get(z, {}).get("river", set())
        got_d = found.get(z, {}).get("road", set())

        for cell in range(100):
            row = cell // 10
            col = cell % 10
            cx0 = zx0 + (col * zw / 10.0)
            cy0 = zy0 + (row * zh / 10.0)
            cw = zw / 10.0
            ch = zh / 10.0

            # Base: expected (v1)
            fill = "none"
            if cell in exp_r and cell in exp_d:
                fill = "#b07cff"
            elif cell in exp_r:
                fill = "#2f67c7"
            elif cell in exp_d:
                fill = "#b98a4b"
            if fill != "none":
                parts.append(f'<rect x="{cx0:.3f}" y="{cy0:.3f}" width="{cw:.3f}" height="{ch:.3f}" fill="{fill}" opacity="0.30" stroke="none"/>')

            # Overlay: extracted (background svg)
            stroke = None
            if cell in got_r and cell in got_d:
                stroke = "#6a00ff"
            elif cell in got_r:
                stroke = "#0055ff"
            elif cell in got_d:
                stroke = "#6b3f00"
            if stroke:
                parts.append(f'<rect x="{cx0:.3f}" y="{cy0:.3f}" width="{cw:.3f}" height="{ch:.3f}" fill="none" stroke="{stroke}" stroke-width="0.35"/>')

    parts.append("</svg>")
    OUT_DEBUG_SVG.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> int:
    _require_deps()
    import numpy as np  # noqa: F401
    from svgpathtools import svg2paths2  # type: ignore

    ap = argparse.ArgumentParser(description="Extract road/river features from Westlands-Background.svg and verify vs v1 slice (537–540).")
    ap.add_argument(
        "--search-mode",
        choices=("anchor", "viewbox"),
        default="anchor",
        help="How to search for the 540..537 row placement. "
        "'anchor' (default) searches a bounded window around Cairhien/Caemlyn anchors (fast). "
        "'viewbox' searches the full SVG viewBox (may churn CPU for a long time).",
    )
    ap.add_argument(
        "--radius-zones",
        type=float,
        default=6.0,
        help="Search window radius in zone widths/heights around the anchor hint (anchor mode).",
    )
    ap.add_argument(
        "--max-workers",
        type=int,
        default=max(1, (os.cpu_count() or 1)),
        help="Max worker threads used for multi-scale zone-width candidate evaluation.",
    )
    ap.add_argument(
        "--expected-v1-tsv",
        type=str,
        default=str(V1_EXPECTED_TSV),
        help="Path to v1 expected road/river cells TSV (zone/cell/feature). Used for zones 537–540 verification.",
    )
    ap.add_argument(
        "--min-f1",
        type=float,
        default=0.0,
        help="If > 0, exit non-zero unless overall F1 across zones 537–540 (roads+rivers) is >= this threshold.",
    )
    ap.add_argument(
        "--cell-tolerance",
        type=int,
        default=1,
        help="Cell tolerance (Chebyshev distance) when scoring against v1 expected. "
        "This helps align hand-drawn v1 vs background SVG when features land near cell borders.",
    )
    ap.add_argument(
        "--allow-v1-expected-gaps",
        action="store_true",
        help="Allow v1 expected TSV to be missing obvious features present in world room names "
        "(e.g., rivers in 537–540). By default we fail early to avoid presenting misleading overlays.",
    )
    args = ap.parse_args()

    if not SVG_IN.exists():
        raise SystemExit(f"Missing: {SVG_IN}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    anchor = _load_text_anchors(SVG_IN)

    paths, attrs_list, svg_attrs = svg2paths2(str(SVG_IN))
    viewbox = None
    vb = svg_attrs.get("viewBox") if isinstance(svg_attrs, dict) else None
    if vb:
        try:
            parts = [float(x) for x in str(vb).replace(",", " ").split()]
            if len(parts) == 4:
                viewbox = (parts[0], parts[1], parts[2], parts[3])
        except Exception:
            viewbox = None
    expected_v1 = _load_v1_expected(Path(args.expected_v1_tsv))
    if all(z in expected_v1 for z in (537, 538, 539, 540)):
        expected = {z: expected_v1[z] for z in (537, 538, 539, 540)}
        expected_source = f"v1_tsv:{args.expected_v1_tsv}"
    else:
        expected = _world_expected_for_zones([537, 538, 539, 540])
        expected_source = "world_room_names_fallback"

    # Sanity check: if the world names strongly indicate a river presence but the v1 TSV has none,
    # the overlay becomes misleading. Fail early unless explicitly overridden.
    if not args.allow_v1_expected_gaps and expected_source.startswith("v1_tsv:"):
        world_expected = _world_expected_for_zones([537, 538, 539, 540])
        bad: list[str] = []
        for z in (537, 538, 539, 540):
            if world_expected.get(z, {}).get("river") and not expected.get(z, {}).get("river"):
                bad.append(str(z))
        if bad:
            raise SystemExit(
                "ERROR: v1 expected TSV has 0 river cells for zone(s) "
                + ",".join(bad)
                + " but world room names indicate rivers exist. "
                "Regenerate v1_ubermap_road_river_cells.tsv or pass --allow-v1-expected-gaps."
            )
    tol = max(0, int(args.cell_tolerance))
    setattr(_prep_expected_arrays, "_cell_tolerance", tol)
    setattr(_score_row_origin_numpy, "_cell_tolerance", tol)
    expected_arr = _prep_expected_arrays(expected)

    # Pre-sample points by feature once (cheap to reuse for auto-fit).
    points: dict[str, list[tuple[float, float]]] = {"road": [], "river": []}
    sample_step = max(0.75, anchor.zone_w / 70.0)
    for path, attrs in zip(paths, attrs_list, strict=True):
        feat = _classify_path(attrs)
        if feat is None:
            continue
        for x, y in _iter_sample_points(path, sample_step=sample_step):
            points[feat].append((x, y))

    # Convert to numpy arrays for fast scoring.
    points_xy = {
        "road": np.asarray(points["road"], dtype=float).reshape((-1, 2)),
        "river": np.asarray(points["river"], dtype=float).reshape((-1, 2)),
    }

    # Start with an anchor-derived rect guess, then auto-fit a row placement to maximize v1 agreement.
    rects_guess = _zone_rects_537_540(anchor)
    score_guess, _found_guess = _score_rects(rects_guess, points, expected)

    # Fit row placement (540..537). Default is a bounded anchor search; viewBox search is optional
    # and may churn CPU for a long time.
    vb_for_fit = viewbox if args.search_mode == "viewbox" else None
    rects, found, best_score, best_zone_w = _auto_fit_row_rects_multi_scale(
        zone_w_hint=anchor.zone_w,
        viewbox=vb_for_fit,
        points_xy=points_xy,
        expected=expected,
        expected_arr=expected_arr,
        anchor_hint=anchor.cairhien,
        radius_zones=float(args.radius_zones),
        max_workers=int(args.max_workers),
    )

    # With a row fit for 540..537 and known zone coords for those zone IDs, compute global grid origin.
    zx_540, zy_540 = zone_xy_for_id(540)
    x_origin = rects[540][0] - (zx_540 * best_zone_w)
    y_origin = rects[540][1] - (zy_540 * best_zone_w)

    # Now emit full-grid cells by mapping points into the global 26x20 zone grid.
    full: dict[int, dict[str, set[int]]] = {}
    for feat, pts in points.items():
        for x, y in pts:
            zx = int((x - x_origin) / best_zone_w)
            zy = int((y - y_origin) / best_zone_w)
            if not (0 <= zx < ZONE_COLS and 0 <= zy < ZONE_ROWS):
                continue
            z = zone_id_for(zx, zy)
            # Room cell within zone
            z_x0 = x_origin + zx * best_zone_w
            z_y0 = y_origin + zy * best_zone_w
            rx = int(((x - z_x0) / best_zone_w) * ROOMS_PER_ZONE)
            ry = int(((y - z_y0) / best_zone_w) * ROOMS_PER_ZONE)
            if not (0 <= rx < ROOMS_PER_ZONE and 0 <= ry < ROOMS_PER_ZONE):
                continue
            cell = ry * 10 + rx
            full.setdefault(z, {"road": set(), "river": set()})[feat].add(cell)

    # Write extracted cells TSV
    lines = ["zone\tcell\tfeature"]
    for z in sorted(full.keys()):
        for feat in ("river", "road"):
            for cell in sorted(full[z][feat]):
                lines.append(f"{z}\t{cell:02d}\t{feat}")
    OUT_CELLS.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Verify vs expected (prefer v1 ubermap.jpg extracted cells TSV).
    verify_lines = [
        f"# anchor caemlyn={anchor.caemlyn} cairhien={anchor.cairhien} zone_w={anchor.zone_w:.3f} zone_h={anchor.zone_h:.3f}",
        f"# row_fit best_score={best_score:.3f} best_zone_w={best_zone_w:.3f} guess_score={score_guess:.3f} row_origin_540=({rects[540][0]:.3f},{rects[540][1]:.3f})",
        f"# grid_origin x_origin={x_origin:.3f} y_origin={y_origin:.3f} top_left_zone={TOP_LEFT_ZONE} cols={ZONE_COLS} rows={ZONE_ROWS}",
        f"# search_mode={args.search_mode} radius_zones={args.radius_zones:.3f} max_workers={args.max_workers}",
        f"# expected_source={expected_source}",
        "zone\tfeature\tv1_count\textracted_count\tmissing\textra",
    ]

    def _dilate_set(cells: set[int], t: int) -> set[int]:
        if t <= 0 or not cells:
            return set(cells)
        out: set[int] = set()
        for cell in cells:
            r = cell // 10
            c = cell % 10
            for dr in range(-t, t + 1):
                for dc in range(-t, t + 1):
                    rr = r + dr
                    cc = c + dc
                    if 0 <= rr < 10 and 0 <= cc < 10:
                        out.add(rr * 10 + cc)
        return out

    # Strict + tolerant metrics across 537–540.
    strict_hits = 0
    strict_missing = 0
    strict_extras = 0
    total_hits = 0
    total_missing = 0
    total_extras = 0
    for z in (537, 538, 539, 540):
        for feat in ("river", "road"):
            exp = expected.get(z, {}).get(feat, set())
            got = full.get(z, {}).get(feat, set())
            # Strict
            strict_hits += len(exp & got)
            strict_missing += len(exp - got)
            strict_extras += len(got - exp)

            # Tolerant
            exp_dil = _dilate_set(exp, tol)
            got_dil = _dilate_set(got, tol)
            total_hits += len(got & exp_dil)
            total_missing += len(exp - got_dil)
            total_extras += len(got - exp_dil)

    p_all, r_all, f1_all = _f1(total_hits, total_missing, total_extras)
    p_s, r_s, f1_s = _f1(strict_hits, strict_missing, strict_extras)
    verify_lines.insert(
        4,
        f"# metrics_all(tolerant) precision={p_all:.4f} recall={r_all:.4f} f1={f1_all:.4f} hits={total_hits} missing={total_missing} extras={total_extras} cell_tolerance={tol}",
    )
    verify_lines.insert(
        5,
        f"# metrics_strict precision={p_s:.4f} recall={r_s:.4f} f1={f1_s:.4f} hits={strict_hits} missing={strict_missing} extras={strict_extras}",
    )
    for z in [537, 538, 539, 540]:
        for feat in ("river", "road"):
            exp = expected.get(z, {}).get(feat, set())
            got = full.get(z, {}).get(feat, set())
            missing = sorted(exp - got)
            extra = sorted(got - exp)
            verify_lines.append(
                f"{z}\t{feat}\t{len(exp)}\t{len(got)}\t{','.join(str(c) for c in missing)}\t{','.join(str(c) for c in extra)}"
            )
    OUT_VERIFY.write_text("\n".join(verify_lines) + "\n", encoding="utf-8")

    _write_debug_svg(rects, {z: full.get(z, {"road": set(), "river": set()}) for z in rects.keys()}, expected)

    print(f"Wrote: {OUT_CELLS}")
    print(f"Wrote: {OUT_VERIFY}")
    print(f"Wrote: {OUT_DEBUG_SVG}")
    if float(args.min_f1) > 0.0 and f1_all < float(args.min_f1):
        print(f"FAIL: overall f1={f1_all:.4f} < --min-f1 {float(args.min_f1):.4f}", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

