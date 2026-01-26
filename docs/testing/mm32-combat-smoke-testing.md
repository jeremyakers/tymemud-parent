# MM32 Combat Smoke Testing (mud_client)

This repo includes a lightweight “log into the game and run some combat
commands” smoke workflow that’s faster to iterate with than full SIT work.

## Tools involved

- `MM32/src/tests/mud_client.py`
  - Telnet client that logs output to `mud_client_<session>.log`
  - Reads commands from `mud_client_<session>.cmd`
  - **Supports blank lines** as “press ENTER” actions
- `MM32/src/tests/mud_client_helper.sh`
  - Convenience wrapper: `start`, `stop`, `send`, `tail`, `status`
  - **`send ""`** is allowed and writes a blank line to the cmd file
- `MM32/src/tests/combat_smoke.sh`
  - Orchestrates **three sessions**:
    - `testimp` (imm): admin setup only
    - `combatA` (mortal): performs attacks
    - `combatB` (mortal): receives attacks / fights back
  - Runs:
    - mortal-vs-mob (spawned by `testimp`)
    - mortal-vs-mortal (turn-based engine exercised)
  - Copies all `mud_client_*.log/.cmd/.pid` files into:
    - `MM32/src/tests/test_logs/combat_smoke_YYYYMMDD_HHMMSS/`

## How to run

From the repo root:

```bash
cd MM32/src/tests
./combat_smoke.sh
ls -1dt test_logs/combat_smoke_* | head -1
```

## What the smoke run does (high level)

1. Checks for an already-running server on port **6969**.
   - If a server is already running, the script **prints an error and exits
     non-zero** (so you can manually investigate/stop the old server before
     retrying).
   - If no server is running, it starts MM32 server on port **6969**.
2. Starts 3 `mud_client` sessions: `testimp`, `combatA`, `combatB`.
3. Logs in (or creates characters if missing).
   - If a combat character is stuck in character creation (`pcreate`), the
     script finishes with the `done` command and presses ENTER through pagers.
4. Uses `testimp` to:
   - `transfer` combat chars to `testimp`
   - `purge` the room to remove interference
   - force combat mortals **awake and standing** (some mortals log in asleep,
     which causes commands like `wield`/`slash`/`unarmed` to fail with
     “In your dreams, or what?”)
   - grant forms to combat chars via `setform`
5. Runs combat sequences and leaves logs for review.

## Related SIT coverage (recommended)

Smoke is fast and great for iteration, but **SIT exercises the live engine more
deterministically** and is the main “did we break behavior?” guardrail.

From `MM32/src/tests/`:

```bash
# Targeting UX (region/bodypart aim token parsing)
python3 -u test_comprehensive_sit.py --test targeting --timeout 300

# Predictability warning/penalty smoke (repeating the same command class)
python3 -u test_comprehensive_sit.py --test predictability --timeout 300
```

## Forms used (from DB `form_base`)

These are intentionally chosen because they exist in MM32 DB and are unarmed-friendly:
- **Unarmed attack**: `Ram` (class `unarmed`)
- **Dodge defense**: `Withdraw` (class `dodge`)
- **Parry defense**: `Parry To Left` / `Parry To Right` (class `parry`)

`combat_smoke.sh` currently **intentionally weakens `combatB` defenses** by
setting some defenses to lower learned values so we reliably see at least some
successful hits (while still exercising the defense path).

## Scenarios covered

`combat_smoke.sh` currently exercises:

- **Targeting UX** (aim token parsing): `unarmed <target> head` pre-autocombat
- **Sword**: equips `combatA` with vnum `3700` and runs `slash` + `thrust`
- **Spear**: equips `combatA` with vnum `3766` and runs `thrust`
- **Staff**: equips `combatA` with vnum `3747` (walking staff) and runs `thrust`
  (ensures a generic thrust form works for staff)
- **MM2 breadth (more weapon families)**:
  - **Dagger**: equips `combatA` with vnum `3715` and forces MM2 slash/thrust
    form text to appear (e.g. `Cat Chases its Tail`, `Bees swarming`, `a thrust`,
    `a hit`).
  - **Axe**: equips `combatA` with vnum `3738` and exercises MM2 forms
    (e.g. `Lizard in the Thornbush`, `a hit`).
  - **Mace**: equips `combatA` with vnum `3727` and exercises MM2 forms
    (e.g. `Kingsfisher Takes a Silverback`, `a hit`).
  - **Flail**: equips `combatA` with vnum `3729` and exercises MM2 forms
    (e.g. `Kingsfisher Takes a Silverback`, `a hit`).
  - **Polearm**: equips `combatA` with vnum `3737` (halberd) and forces MM2 thrust
    forms to appear (`a thrust`, `a hit`).
- **PvP sanity**: `combatA` vs `combatB`
- **Unarmed sanity**: ensures `combatB` is truly unarmed (`remove all`/`drop all`)
  and observes unarmed-kit form text

### Determinism notes (why the script does “imm admin things”)

- After the PvE gauntlet, a mortal can end up downed/sleeping. The script uses
  `restore` and `force ... wake/stand` before PvP so the scripted `wield`/attack
  commands always execute.

## What to look for in logs

Open the latest directory:

```bash
DIR="$(ls -1dt MM32/src/tests/test_logs/combat_smoke_* | head -1)"
less "$DIR/mud_client_combatA.log"
```

Useful grep signals:

```bash
grep -Rni "Calling damage_line_bodyparts" "$DIR"/mud_client_*.log
grep -Rni "bleeds" "$DIR"/mud_client_*.log
grep -Rni "No approproate forms found" "$DIR"/mud_client_*.log
grep -RniE "Cat Chases its Tail|Lizard in the Thornbush|Kingsfisher Takes a Silverback|\\ba thrust\\b|\\ba hit\\b" \
  "$DIR"/mud_client_combatA.log
```

- **Damage pipeline ran**: look for `Calling damage_line_bodyparts`.
- **Wounds/afflictions ran**: look for messages like `bleeds from bruises`.
- **Form/weapon gating issues**: look for `No approproate forms found:`
  `No valid forms found for class ...`.
  - Note: `combat_smoke.sh` treats **player form-selection failures** as a hard
    smoke failure (it checks `combatA`/`combatB` logs specifically).

Additional smoke signals:

```bash
# Proves staff weapon switch succeeded (Scenario 1c)
grep -Rni "walking staff" "$DIR"/mud_client_combatA.log
```

## New player-facing behaviors worth grepping for

- **Targeting UX feedback**: `You aim for ...`
- **Predictability warning**: `Your repeated motions feel predictable.`

## Server crash capture (cores + server.log)

`combat_smoke.sh` launches the server with:
- `ulimit -c unlimited` (enables core dumps for the server process)
- server stdout/stderr captured in the run directory: `server.log`

Core files will be written under `MM32/` using the kernel’s `core_pattern`
(example: `core.tyme3.<pid>.<timestamp>`).

## Manual mode notes (future extension)

The “fully manual turn-based” flow requires scripted coordination of
attacker/defender turns (`It's your turn to move!`) and defense choice (`parry`,
`dodge`, etc.).

The smoke script currently uses **autocombat enabled** for stability; when we
add manual-mode coverage, we’ll do it as a separate scenario that watches logs
and responds to turn prompts.
