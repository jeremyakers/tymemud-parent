# Progress Tracking
## Current State
**Status:** Active development and maintenance
**Last Update:** 2026-01-16
## 2026-01-04: Ubermap MVP (MM32/lib) world fixes + isolation
- **MM32/lib PR:** `https://github.com/jeremyakers/tymemud-lib/pull/1` (branch: `fix/ubermap-mvp-world-fixes`)
- **Fixes included:** boot blockers in MVP zones (notably `570`/`640`), known `56847` west mislink (`56847` → `56846`), and Alindaer stub prose cleanup (`15/16`).
- **Isolation for multi-agent work:** worktrees at `/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib` and `/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/src`.

## 2026-01-04: Ubermap continuation — placeholder cleanup + seam repairs (MM32/lib)
- **MM32/lib PR:** `https://github.com/jeremyakers/tymemud-lib/pull/4` (branch: `fix/ubermap-639-640-colorcode`)
- **Fixes included:**
  - Remove remaining `The Open World` placeholder names/descriptions in zones `537`, `611`, `670`
  - Add missing seam exits in `50994` (links to `50984` and `53904`)
  - Fix `61147/61148` west-adjacency mislinks
- **Validation:** boot gate on `:9696` (no `Format error`), plus in-game spot checks via `mud_client_helper` as `testimp` (`goto/look/exits` in `50994, 53904, 53736, 61147, 64063, 67000`).

## 2026-01-05: MM32 combat (compressed status)
- **Milestones 0–4:** stability/log cleanup, typed damage + armor DR, wounds/death triggers, targeting UX, predictability checks — validated via `make test`, smoke, and SIT targeting/predictability.
- **Details archived:** `memory-bank/archive/2026-01.md`

## 2026-01-05: Ubermap map-fidelity — road/river cells vs JPG (MM32/lib)
- **MM32/lib PR:** `https://github.com/jeremyakers/tymemud-lib/pull/49` (branch: `fix/ubermap-mapfidelity-jpg-road-river`)
- **Fixes included:** room *titles* updated so cells marked as **main road**/**riverway** in `Building_Design_Notes/ubermap.jpg` explicitly read as road/river; directionality prose refreshed; restore overland reciprocity in `#53766`.
- **Validation:** connectivity audit (JPG-seed zones) 0 issues; boot-gated on `:9696` (no `Format error` / `Fatal error`).

## 2026-01-05: Ubermap — finish placeholder cleanup + full overland audit (MM32/lib)
- **MM32/lib PR:** `https://github.com/jeremyakers/tymemud-lib/pull/50` (branch: `fix/ubermap-fill-placeholders-405-467-612-625`)
- **Fixes included:** remove remaining overland `The Open World` placeholders in zones `405–467` and `612–625`; resolve remaining non-reciprocal exits found by a full >=400 overland connectivity audit (`611`, `706`).
- **Validation:** connectivity audit (>=400 overland zones) 0 issues; `boot_gate.sh` PASS on `:9696`; in-game `testimp` goto/look/exits spot checks (logs-first).

## 2026-01-05: Ubermap v2 (Westlands-wide) — design artifacts
- **Added:** `docs/ubermap/v2/` with a Westlands-wide overlay grid:
  - `westlands_v2_grid.tsv` (spreadsheet-friendly source of truth)
  - `westlands_v2_overlay.svg` (generated overlay on `wheel_of_time___westland_map-fullview.jpg`)
  - `missing_zone_destinations.tsv` (exit destinations to missing zone files; currently 0 missing)

## 2026-01-13: Tar Valon diagonal rotation (MM32/lib) — north-star strict alignment
- **Objective:** rotate Tar Valon + bridge/town ring to match `Building_Design_Notes/tar-valon-final.svg`
  while anchoring the city footprint over a reduced 3-vnum overland hole.
- **Worktree:** consolidated into `/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/` (lib+src)
- **Status:** city zones `90–98` rotated; bridge overlay zone `486` rotated/rewired; remaining work is
  relocating the remaining Ethereal town placeholders + approach roads so the solver centers TV.

### 2026-01-13 (cont.): Luagde + Daghain placeholder moves + bridge anchoring
- **Luagde placeholder** moved to `46959` (now `^Ethereal Luagde`), and the Luagde bridge now connects
  `46959 <-> 48609 <-> 48610 <-> 48611 <-> 9046` (bidirectional).
- **Old Luagde placeholder** `46919` reverted to normal overland (no longer connects to the Luagde bridge).
- **Daghain placeholder** moved to `46861` (now `^Ethereal Daghain`), and the Daghain bridge now connects
  `46861 <-> 48612 <-> 48613 <-> 48614 <-> 9040` (bidirectional).
- **Old Daghain placeholder** `46810` reverted to normal overland (no longer connects to the Daghain bridge).
- **Bridge underlay overrides updated to center rooms** in `MM32/src/genwld.c`:
  - `48610 -> 46969` (Luagde bridge center over river ring)
  - `48613 -> 46870` (Daghain bridge center over river ring)
  - plus center overrides for the other TV bridges for consistent anchoring.

## Recent Accomplishments (older details archived)
- See `memory-bank/archive/2026-01.md`

## 2026-01-28: BuilderPort Protocol v1 Implementation (`wld_editor_api_agent`)
- **Plan Created:** `docs/plans/builder_port_v1_implementation.md`
- **Engine Implementation:** Completed handshake, transactions, structured data, and mutators in `statusport.c`.
- **Web Migration:** Updated `wld_editor_api.php` to v1 protocol; added gitignored `wld_editor_config.php`.
- **Status:** Phase 1 & 2 Completed. Ready for Phase 3 (Validation & Cleanup).

## Known Issues

- `MM32/src/oedit.c:oedit_disp_extradesc_menu`: format-string refactor introduced
  `%s%.100s%s` but the trailing reset-color `nrm` args were not supplied
  (varargs mismatch/UB). Fix is to add `nrm` after the keyword and description
  values; note this fix was reverted in working tree and may need re-applying.

## Technical Debt

- Verify all other pfiles_main operations include port column (audit completed -
  all verified correct)

## Immediate Roadmap

- **Ubermap:** shift to seam reciprocity + map-fidelity (roads/riverways vs `Building_Design_Notes/ubermap.jpg`) with **larger PR batches**.
- Continue monitoring for SQL query patterns that might omit port column.
- Maintain code quality standards per `MANIFESTO.md`.
