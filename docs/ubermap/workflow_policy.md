## Ubermap workflow policy (how we validate changes)

This document exists to prevent “drift” in how we generate and review the Ubermap outputs.

### Core principle

The Ubermap SVG is **a debugging/auditing tool**, not a goal in itself. When something looks wrong, we treat it as either:

- **Engine/layout bug** (ordering/state/solver logic), or
- **World data bug** (mislinked exits, wrong sectors, incorrect room text), or
- **Design artifact bug** (`ubermap.jpg` label/layout mismatch).

We fix the *cause*, not the symptom.

### “Do not show broken maps” rule (required)

Before presenting a new SVG as “ready for review”, we must:

- **Regenerate exports** using export-only mode (`tyme3 -E`).
- **Check regression indicators**:
  - **`ubermap_long_edges_468_640_pluslinked.tsv`**: should not contain unexpected long edges. If it contains many rows (beyond header), investigate why the solver let those edges stretch.
  - **`ubermap_direction_mismatch_edges_468_640_pluslinked.tsv`**: must not contain extreme coordinate deltas (huge `actual_dx/actual_dy`). If it does, treat as a hard regression.
- **If a regression is detected**:
  - Identify the responsible change (usually in `src/genwld.c`).
  - **Revert it**, try a different tactic, regenerate, and re-check.

### Overland grid invariants (required)

- **Macro overland tiles must stay on a strict grid** (no shearing within a zone).
- **Cross-zone borders must stay adjacent** (no “zone tears” where a border exit becomes a massive diagonal).
- If the grid tears, treat it as a logic bug in the layout process (not “acceptable map noise”).

### Deferred work: Tar Valon (explicitly deferred)

Tar Valon currently exhibits a major layout issue (appears rotated ~90° compared to intended harbor/bridge orientation). We will **not** do incremental tweaks while this is unresolved.

- **Status**: deferred
- **Next action**: dedicated rework pass focused on correct orientation + consistent bridge/river placement.

