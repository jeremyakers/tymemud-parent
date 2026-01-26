# Tar Valon relinking pass (post-45° rotation) — notes + repeatable steps

This doc tracks the *overland* work required to re-anchor Tar Valon around the new diagonal river ring
(`Westlands-Background.svg` north-star strict), and records what worked so we don’t repeat mistakes.

## Canonical SVG output (where to look)

- **Canonical**: `/home/jeremy/cursor/tymemud/tmp/ubermap_agent_468_640_pluslinked_z0.svg`
- A timestamped copy is also created each run.

## Tooling

### Room ops helper

We use `scripts/wld_room_ops.py` to make repeatable, surgical `.wld` edits:

- **Disconnect “hole” vnums** (remove inbound exits + clear the room’s exits):
  - `wld_room_ops.py disconnect --wld-file <zone.wld> --vnums <list> --inplace`
- **Set sector type** (e.g. water):
  - `wld_room_ops.py set-sector --wld-file <zone.wld> --vnums <list> --sector 6 --inplace`
- **Copy name/desc only** (preserves destination exits/grid):
  - `wld_room_ops.py copy-text --wld-file <dst.wld> --src-wld-file <src.wld> --src-vnum X --dst-vnum Y --inplace`
- **Restore old vnums back to builder** (for “reset to normal terrain”):
  - `wld_room_ops.py restore-from-git --repo-dir <MM32/lib> --wld-file <zone.wld> --ref builder --vnums <list> --inplace`

## Pass 1 — hole + river ring + placeholder relocations

### Hole vnums (reserved + disconnected)

Semantics: make these real holes in the overland grid (no inbound/outbound exits):

- `46880`
- `46979`
- `46989`

### New river-ring tiles (moved river, keep same river “style”)

These were converted to water sector and given Tar Valon ring text:

- `46870`, `46881`, `46890`
- `46968`, `46969`, `46978`, `46988`, `46999`

### Placeholder relocations (copy room *data*, not vnum)

These were moved by copying **name+desc only** to the new vnum (preserving the destination’s exits),
then restoring the old vnum back to builder terrain:

- **Camp**: `46998` → `50947`
- **Darein**: `46850` → `46998` (old `46850` restored)
- **Jualdhe**: `46958` → `46977` (old `46958` restored)
- **Luagde**: `46919` → `46959` (old `46919` restored)
- **Daghain**: `46810` → `46861` (old `46810` restored)
- **Osenrein**: `46812` → `46882` (old `46812` restored)
- **Houses Nestled Among Hills**: `46811` → `46871` (old `46811` restored)

### Export

After the pass, the full SVG was regenerated and written to the canonical tmp path above.

## Pass 2 — Alindaer relink + Osenrein road connection

### Alindaer relink (move overland connection from old location → 50919)

Old Alindaer overland links in zone 468/469 were removed and the Alindaer gate was moved to
the south approach near `50919`. Key edits:

- **Overland (old location)**:
  - `46842` D2 now points to `46852` (removes `1520`)
  - `46851` D1 now points to `46852` (removes `1578`)
  - `46853` D3 now points to `46852` (removes `1564`)
  - `46948` D2 now points to `46958` (removes `1520`)
  - `46999` no longer links south to `50909` (hole created)

- **Alindaer zone (15.wld)**:
  - `1564` no longer exits east to `46853`
  - `1578` now exits west to `50919` (new overland connection)

- **Overland (new location)**:
  - `50909` is disconnected (hole for city insert)
  - `50919` now exits **north** to `1578`
  - Old Alindaer placeholder at `46852` converted to normal terrain text
  - Old Alindaer slot `56958` restored to builder terrain

### Osenrein road connection (Cairhien approach)

Osenrein now connects into the road network (Cairhien approach) via `46892`:

- `46882` exits:
  - **north** → `46872`
  - **east** → `46883`
  - **south** → `46892` (road connection)
  - **west** → `48615` (bridge to Tar Valon)

- `48615` (bridge overlay) now connects to `46882` instead of the old `46812`.

### Export

After this pass, the full SVG was regenerated and written to the canonical tmp path above.

