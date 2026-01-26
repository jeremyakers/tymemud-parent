# Tar Valon rotation — preserved 90° work + repeatable tooling

This folder exists to **preserve the previous Tar Valon “rotate 90°” attempt**
so it can be repeated (or adapted) even after we reset/revert world files.

## What’s in here

- **`rotate90_world_MM32-lib.patch`**
  - A `git diff` patch of the *world-data* changes (zone files) made during the
    90° attempt.
  - Apply from the `MM32/lib` repo root.

- **`rotate90_codegenwld_MM32-src.patch`**
  - A `git diff` patch of the `genwld.c` changes made to support TV-focused map
    debugging / rotation work.
  - Apply from the `MM32/src` repo root.

## Direction indices (engine truth)

Direction indices are defined in `MM32/src/constants.c`:

- `0` = north
- `1` = east
- `2` = south
- `3` = west
- `4` = up
- `5` = down
- `6` = northeast
- `7` = northwest
- `8` = southeast
- `9` = southwest

These indices correspond to `.wld` exit headers like `D0`, `D6`, etc.

## Rotation mappings (for `.wld` exits)

### 90° clockwise (CW)

- `N(0) → E(1) → S(2) → W(3) → N(0)`
- `NE(6) → SE(8) → SW(9) → NW(7) → NE(6)`

### 45° clockwise (CW)

- `N(0) → NE(6) → E(1) → SE(8) → S(2) → SW(9) → W(3) → NW(7) → N(0)`

> Note: `UP(4)` / `DOWN(5)` are not rotated.

## Re-applying the preserved 90° attempt (if needed)

### World data (`MM32/lib`)

From `MM32/lib`:

```bash
git apply /home/jeremy/cursor/tymemud/docs/ubermap/tar_valon_rotation/rotate90_world_MM32-lib.patch
```

### Engine/source (`MM32/src`)

From `MM32/src`:

```bash
git apply /home/jeremy/cursor/tymemud/docs/ubermap/tar_valon_rotation/rotate90_codegenwld_MM32-src.patch
```

## Repeatable rotation tooling

For a repeatable way to rotate internal exits in `.wld` files (without relying
on hand-edits), use:

- `scripts/wld_rotate_exits.py`

It supports 45°/90° rotations and can be restricted to:
- specific zones (e.g., 90–98),
- and/or **internal-only** exits (destination room in same zone), which is what
  we used to avoid breaking overland/bridge topology while rotating the city’s
  internal street grid.

## 45° clockwise rotation (Tar Valon 90–98) — repeatable “what worked”

Goal: rotate Tar Valon’s *internal* street grid by **45° clockwise**:

- `N → NE → E → SE → S → SW → W → NW → N`
- `UP/DOWN` unchanged

### What we did (and why)

- **Rotate exits with `--internal-only`**
  - This preserves truly external connectors (bridges/overland) so we can rewire those intentionally later.
  - **Important pitfall:** Tar Valon spans zones **90–98**, so some “internal city streets” are **cross-zone**
    (e.g. `9066 ↔ 9141`). If you use the default `--internal-only` behavior (“same zone file only”),
    those links will *not* rotate and the city won’t be consistently turned. Use `--internal-zone-set 90-98`.

- **Rotate direction words everywhere *except* the bridge gate rooms**
  - Those gate rooms contain player-facing text about the external bridges whose cross-zone directions are intentionally left untouched during an internal-only rotation.

### Commands used (worktree: `ubermap_agent`)

WLD directory:

- `/home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld`

Bridge-gate vnums excluded from direction-word rotation:

- `9000` (Alindaer gate → `48608`)
- `9026` (Osenrein gate → `48617`)
- `9040` (Daghain gate → `48614`)
- `9046` (Luagde gate → `48611`)
- `9076` (Jualdhe gate → `48602`)
- `9085` (Darein gate → `48605`)

Dry-run:

```bash
uv run python scripts/wld_rotate_exits.py \
  --zones 90-98 \
  --wld-dir /home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld \
  --rotate 45cw \
  --internal-only \
  --internal-zone-set 90-98

uv run python scripts/wld_rotate_direction_words.py \
  --zones 90-98 \
  --wld-dir /home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld \
  --rotate 45cw \
  --exclude-vnums "9000,9026,9040,9046,9076,9085"
```

Apply (in-place):

```bash
uv run python scripts/wld_rotate_exits.py \
  --zones 90-98 \
  --wld-dir /home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld \
  --rotate 45cw \
  --internal-only \
  --internal-zone-set 90-98 \
  --inplace

uv run python scripts/wld_rotate_direction_words.py \
  --zones 90-98 \
  --wld-dir /home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib/world/wld \
  --rotate 45cw \
  --exclude-vnums "9000,9026,9040,9046,9076,9085" \
  --inplace
```

Observed change counts (from tool output):

- Exit headers rotated: `TOTAL rotated_exits=1383`
- Direction words rotated: `TOTAL rotated_words=719`

## Overland “hole” semantics (Tar Valon work)

For Tar Valon alignment work, an overland “hole” means **disconnect those vnums
and treat them as unused/reserved** because they overlap a city/insert and must
not be used as overland terrain.

Canonical definition lives in:
`MM32/lib/docs/ubermap/northstar_alignment_backups/2026-01-12/README.md`
