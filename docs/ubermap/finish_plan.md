## Plan to finish the Ubermap

This plan is based on:

- The design constraints in `Building_Design_Notes/ubermap.jpg`
- Dotproject task `Ubermap` (task_id 44) from `docs/ubermap/dotproject_extract.md`
- Automated inventory of current zone state from `docs/ubermap/world_inventory.md`
- Supporting context in vboards + mudmail exports (see `docs/ubermap/vboards_extract.md`, `docs/ubermap/mudmail_extract.md`)

### 1) Lock down the target scope (the “current Ubermap”)

Dotproject task 44 enumerates the specific “current Ubermap” zones:

- **Not completed**: `469 468 509 508 538 540 539 570 569 567 608 607 638`
- **Needs editing**: `640`, `639`
- **Ready to be ported**: `610`

That list should be treated as the baseline MVP to finish first, before expanding to additional continents/areas.

### 2) Finish the placeholder-heavy zones first (highest leverage)

From `docs/ubermap/world_inventory.md`, these zones have extremely high counts of rooms still named **“The Open World”** (placeholders):

- **540**: 93 / 100 placeholder names
- **607**: 86 / 100 placeholder names
- **509**: 78 / 100 placeholder names
- **469**: 71 / 100 placeholder names
- **508**: 64 / 100 placeholder names
- **468**: 37 / 100 placeholder names

Approach for each:

- Use the `ubermap.jpg` legend to decide terrain class per cell.
- Ensure roads/riverways align across zone borders.
- Replace placeholder room names with terrain-appropriate names (keeping brief-mode readability).
- Replace placeholder descriptions with concise terrain descriptions; keep variation but don’t overwrite the “grid feel”.

### 3) Preserve already-complete zones (don’t churn)

Zones with **0 placeholders** in the scan are likely already “done-ish” and should mainly get a consistency pass:

- `538`, `539`, `568`, `569`, `570`, `610`, `639`, `640`

Still check these for:

- border connectivity correctness
- road/river continuity
- naming consistency (especially color-code conventions for 639/640, as noted by dotproject)

### 4) Fix data-quality issues before large-scale editing

The scan shows:

- **`608`** has `undefined~` markers (1 line)
- **`638`** and **`639`** have `undefined~` markers (2 lines each)
- **`640`** has **nonprintable bytes** (2) in its `.wld` file

Recommended order:

1. Repair nonprintable/garbled bytes (risk of tooling/parsing issues)
2. Replace `undefined~` placeholders with real strings (or remove the broken section if it’s a malformed record)

### 5) Verify and complete connectivity (critical)

There are explicit stubs in city zones:

- `MM32/lib/world/wld/15.wld`: “Connect the west exit to the ubermap.” → exit to `46851`
- `MM32/lib/world/wld/16.wld`: “Connect the southern entrance to the ubermap.” → exit to `46862`

Checklist:

- Every city edge that should link to Ubermap has a correct exit into the appropriate grid cell.
- Every such Ubermap entry point has a correct return exit back into the city.
- Cross-zone exits (e.g., `468xx` linking to `469xx`) align with the intended grid adjacency and match the map.

### Manual verification (builderport walk-through, 2026-01-04)

- **Boot blocker fixed**: `tyme3` was crashing on boot with `Format error, room #46877, direction D0` due to a malformed exit block in `MM32/lib/world/wld/468.wld`. The room entry was repaired so the server can load rooms successfully.
- **Login**: Connected to builderport (`:9696`) as `testimp` and used `goto` + `stat room` to validate.
- **City ↔ Ubermap stubs verified (bidirectional)**:
  - `15.wld` room `1578` (“Connect the west exit to the ubermap.”): **west → `46851`**, then **east → `1578`**.
  - `16.wld` room `1646` (“Connect the southern entrance to the ubermap.”): **south → `46862`**, then **north → `1646`**.
- **MVP zone spot-check (representative rooms)**: `goto`/`stat room` succeeded for: `46855 46955 50855 50955 53855 53955 54055 56755 56955 57055 60755 60855 61055 63855 63955 64055`.
- **Connector room prose un-stubbed**: Updated the two city connector rooms so they no longer show “Connect ... ubermap.” placeholder text:
  - `15.wld` room `1578`: now describes the western edge of Alindaer opening out toward the countryside (exit still **west → `46851`**).
  - `16.wld` room `1646`: now describes the southern edge of Alindaer running down into open fields (exit still **south → `46862`**).

### Scenic prose pass (Ubermap MVP, 2026-01-04)

- **Goal**: Remove templated/repeated “placeholder fill” sentences and replace with short, more literary
  WoT-flavored prose while staying consistent with “good” house style (roads: `539`, farms/forest: `568`,
  rivers: `567`) and wrapping descs to ~75–80 chars.
- **Execution**:
  - Added `scripts/ubermap_scenic_pass.py` (latin-1 safe, atomic writes, keeps `$~` terminator).
  - Ran scenic pass for MVP zones; no known template sentences remain in the target zones.
  - Recovered a truncated `608.wld` and ensured correct `$~` termination.
- **QA (builderport)**: Booted `tyme3` on `:9696` (log checked first) and `goto`/`look`/`stat room`
  spot-checked representative rooms in zones: `468 469 508 509 540 567 607 608 638`.

### Connectivity + format blockers (2026-01-04)

- **Fixed**: the known “`xx47` west mislink” case in zone `568`:
  - `56847` west incorrectly landed on `56844` → corrected to `56846`.
  - Verified in-game with `stat room`: `56847` west → `56846`, and `56846` east → `56847`.
- **Fixed**: world-format errors introduced by a lossy rewrite pass (these were hard boot blockers):
  - `MM32/lib/world/wld/570.wld`: restored missing exit headers for several farmhouse/interior exits (previously orphaned `1 0 <vnum>` lines).
  - `MM32/lib/world/wld/640.wld`: restored a missing `D0` door block for the “black tower gate” north exit in room `64063` (now shows as a closed/locked door in `stat room`).

### 6) Builder workflow + QA loop

From Builders vboard guidance:

- Save frequently, using:
  - `redit save zone#`
  - `zedit save zone #`
  - `oedit save zone #`

Proposed workflow per zone:

- Pick a zone and complete it cell-by-cell.
- After major edits, run a connectivity sanity check (at least border cells).
- Use consistent naming/terrain patterns.
- Only then move to the next zone.

### 7) Deliverables / done definition

“Ubermap MVP finished” when:

- All zones listed in dotproject task 44 have:
  - no placeholder “The Open World” names
  - descriptions for all rooms (or an explicit reason a room is intentionally blank)
  - clean strings (no `undefined~`, no nonprintable bytes)
  - correct cross-zone and city connectivity
  - roads/riverways aligned with `ubermap.jpg`

