## Westlands-Background.svg — Tar Valon local alignment (zones 469/468)

Goal: extract **road/river cell features** for the Tar Valon overland zones (`469` west, `468` east)
from `Building_Design_Notes/Westlands-Background.svg` so we can treat the background map as the
**“north star”** for river routing around Tar Valon (diagonal NW–SE).

### Coordinate space gotcha (important)

`svgpathtools.svg2paths2()` returns path coordinates in the **raw path-data coordinate space**
(i.e. *before* ancestor `<g transform=...>` is applied).

For Tar Valon, the label group (`aria-label="Tar Valon"`) has first-moveto coords:
- raw: `(359.35, 35.90)`

When rendered, labels are translated by a constant offset (from sampled label glyphs):
- abs ≈ raw + `(276.579, 203.090)`

Use **raw** coords for feature extraction; use **abs** coords for PNG crops / overlays.

### Local grid fit (good-enough for Tar Valon)

We fit a small axis-aligned grid for zones `469` and `468` by scanning `zone_w` and `(x0,y0)` in
raw coords, anchored near the Tar Valon label, and scoring against ubermap.jpg’s road/river cell
pattern (tolerance=1 cell). This provides a stable enough mapping to see the **diagonal river**
and road spokes around Tar Valon.

Best coarse fit (raw):
- `zone_w = 21.0`
- `x0 = 16.35`
- `y0 = -58.60`

Zone positions (from `docs/ubermap/v2/westlands_v2_grid.tsv`):
- zone `469`: `(gx=15, gy=4)` (Tar Valon west)
- zone `468`: `(gx=16, gy=4)` (Tar Valon east)

### Extracted features (from background SVG, using the fit above)

These are **cells** (`00..99`) in each 10×10 zone that contain sampled road/river strokes.

- zone `469`:
  - rivers: `03,04,14,15,25,35,45,46,56,67,78,89`
  - roads: `06,07,16,17,26,27,29,36,38,39,46,48,50,51,52,53,54,55,57,58,65,66,67,68,69,75,76,77,84,85,87,93,96`
- zone `468`:
  - rivers: `80,81,82,93`
  - roads: `00,01,10,60,61,71,72,73,83,84,85,95,96`

### Visual overlay artifact

The following image shows the fitted 2-zone rectangle (`469|468`) over the rendered background
map, with a 10×10 grid and extracted cells colored:

- overlay PNG: `tmp/bgsvg_tar_valon_zone468_469_overlay.png`

Blue cells are rivers; brown cells are roads. The main river segment across zone `469` is visibly
**diagonal NW→SE**.

