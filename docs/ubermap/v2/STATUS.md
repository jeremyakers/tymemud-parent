# Ubermap v2 — Status (living doc)

This is the current state of the **Ubermap v2** effort and the key artifacts/scripts other agents should rely on.

## What we have working today

- **Road/river feature extraction from** `Building_Design_Notes/Westlands-Background.svg`
  - Script: `scripts/ubermap_v2_extract_features_from_background_svg.py`
  - Outputs:
    - `docs/ubermap/v2/extracts/background_svg_road_river_cells.tsv` (full extracted cells)
    - `docs/ubermap/v2/extracts/background_svg_verify_537_540.tsv` (v1-slice verification report)
    - `docs/ubermap/v2/extracts/background_svg_debug_537_540.svg` (visual overlay for 537–540)

- **v1 “ground truth” extraction from** `ubermap.jpg`
  - Script: `scripts/ubermap_jpg_extract_cells.py`
  - Output (expected/ground truth TSV):
    - `docs/ubermap/v2/extracts/v1_ubermap_road_river_cells.tsv`
  - Note: the river-color heuristic was relaxed to correctly pick up **dark blue** river cells (zone 537 was the canary).

- **Verification approach for 537–540**
  - The extractor reports both **strict** and **tolerant** match metrics.
  - Tolerance uses a **Chebyshev distance** neighborhood (default 1 cell) to account for slight raster-vs-vector shifts.
  - Default extraction mode uses bounded **anchor search**; full-viewport brute force is available but CPU-intensive.

## How to read the debug overlay SVG

File: `docs/ubermap/v2/extracts/background_svg_debug_537_540.svg`

- **Filled (light tint)**: *expected* cells from v1 (`v1_ubermap_road_river_cells.tsv`)
- **Outlined only (no fill, stronger stroke)**: *extracted* cells from `Westlands-Background.svg`
- **Blue**: rivers
- **Brown**: roads

This lets you visually spot:
- expected-but-missed cells (filled only)
- extracted-but-not-expected cells (outline only)
- alignment drift (outline shifted vs fill)

## Known constraints / guardrails

- **Agent boundary**: engine/world work is done in `_agent_work/ubermap_agent/` to avoid interfering with other agents’ working trees.
- **Search cost**: `--search-mode=viewbox` can churn CPU for a long time; the default `--search-mode=anchor` is much faster.

## What’s next (highest priority)

1. **Consume the extracted road/river cells TSV in the v2 renderer**
   - Input: `docs/ubermap/v2/extracts/background_svg_road_river_cells.tsv`
   - Target: `scripts/ubermap_v2_render_from_westlands_map.py` should incorporate these features when producing:
     - `docs/ubermap/v2/westlands_v2_ubermap.svg`

2. **Expand verification beyond 537–540**
   - Add additional “golden slice” zones and rerun the same mechanical verification.

3. **TODO (world cleanup): remove/replace “Ethereal” scaffolding rooms + markers**
   - Several zones contain OOC placeholder rooms like `^Ethereal Tar Valon`, `^Ethereal Caemlyn`, etc.
   - These appear to be legacy builder scaffolding (“Ethereal Marker” resets in `*.zon` files).
   - Decide per-room whether to:
     - delete,
     - convert to IC content,
     - or gate behind builder-only access / non-walkable portals.
   - Keep the map exporter filtering these out so macro-validation focuses on real overland connectivity.

