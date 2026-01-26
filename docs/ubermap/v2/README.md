## Ubermap v2 (Westlands-wide) — design artifacts

v1 (“Ubermap.jpg”) is a **small sliver** of the full Westlands.

This folder holds the **v2 planning artifacts** for expanding the Ubermap to cover
all of `Building_Design_Notes/wheel_of_time___westland_map-fullview.jpg`.

### Files

- `westlands_v2_ubermap.svg`
  - “Ubermap.jpg-style” **v2 planning map** for the full Westlands
  - 26×20 zones; each zone is a 10×10 room grid
  - Zone IDs are rendered on-map; room cells are colored by inferred sector type
- `westlands_v2_ubermap_cells.tsv`
  - Per-room-cell TSV export used to generate the SVG
  - Columns include: `zone_id`, `(zx,zy)` zone coords, `(rx,ry)` room coords, `sector`, `feature`
- `westlands_v2_ubermap_zones.tsv`
  - Per-zone summary (counts of inferred sectors/features)
- `westlands_v2_grid.tsv`
  - Spreadsheet-friendly “source of truth”
  - One row per **zone-sized cell** (not per-room)
  - Columns: `gx`, `gy`, `label`, `zone_id`, `notes`
- `westlands_v2_overlay.svg`
  - Visual overlay of the grid on top of the full Westlands map
  - Generated from `westlands_v2_grid.tsv`
- `missing_zone_destinations.tsv`
  - Report of exit destinations whose **zone file is missing**
  - This answers whether “missing zone numbers” are actionable vs unused numbering.
  - Note: exit destinations of `-1` are ignored (they mean “no destination” / intentionally unlinked).
- `zone_536_due_diligence.md`
  - Due diligence summary for zone `536` (currently isolated from v1): terrain tag/sector summary + seam plausibility vs `537` east edge.
- `isolated_overland_zones.tsv`
  - Overland-like zones that exist but have **0 inbound + 0 outbound cross-zone exits** (broad scan; includes many legacy/unwired grids).
- `isolated_overland_zones_near_v1.tsv`
  - Narrowed subset of isolated overland zones near v1 numbering neighborhood (easier to reason about early v2 expansion).
- `unused_zone_intent_findings.md`
  - Summary of evidence from vboards/mudmail + file-level analysis about the likely intent of “built but unused” zones (e.g., `536`).

### Generation

Extract road/river features from `Westlands-Background.svg` and verify the v1 slice (zones 537–540):

```bash
# NOTE: This may churn CPU for a long time if you use --search-mode=viewbox.
uvx --with svgpathtools --with numpy python scripts/ubermap_v2_extract_features_from_background_svg.py

# Optional: fail the command if the overall match is too low (useful as a “gate”):
uvx --with svgpathtools --with numpy python scripts/ubermap_v2_extract_features_from_background_svg.py --min-f1 0.85
```

### Debug overlay legend (537–540)

The extractor can emit a visual debug overlay:

- File: `docs/ubermap/v2/extracts/background_svg_debug_537_540.svg`
- **Filled (light tint)**: v1 expected cells from `docs/ubermap/v2/extracts/v1_ubermap_road_river_cells.tsv`
- **Outlined only (no fill, stronger stroke)**: cells extracted from `Westlands-Background.svg`
- **Blue**: rivers, **Brown**: roads

### Status

See `docs/ubermap/v2/STATUS.md` for the current “what’s done / what’s next”.

Generate the “Ubermap.jpg-style” v2 planning map:

```bash
uvx --with pillow python scripts/ubermap_v2_render_from_westlands_map.py
```

Regenerate the overlay after editing the TSV:

```bash
uv run python scripts/ubermap_v2_generate_svg.py
```

Generate the “missing zone destination” report:

```bash
uv run python scripts/world_missing_zone_destinations.py --out docs/ubermap/v2/missing_zone_destinations.tsv
```

