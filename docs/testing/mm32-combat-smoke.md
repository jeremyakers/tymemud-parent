# MM32 Combat Smoke Testing (manual-first)

## Goal
Use `mud_client.py` + `mud_client_helper.sh` to smoke test the **turn-based combat engine** in-game, without immediately writing brittle end-to-end scripts for the **character creation** UI.

## Roles (important)
- **`testimp` (imm)**: admin/setup only
  - `transfer`, `load mob`, `setform`, `advance`, etc.
- **Dedicated mortal combat chars** (create once, reuse forever):
  - `combatA`, `combatB` (or similar)
  - These are the characters that actually issue: `unarmed`, `slash`, `parry`, `dodge`, `combat ...`, etc.

## Start the server
From the MM32 root (`MM32/`):

```bash
./src/bin/tyme3 6969
```

## Start client sessions
From `MM32/src/tests`:

```bash
./mud_client_helper.sh testimp start
./mud_client_helper.sh combatA start
./mud_client_helper.sh combatB start
```

Tail output:

```bash
./mud_client_helper.sh testimp tail
./mud_client_helper.sh combatA tail
./mud_client_helper.sh combatB tail
```

## Manual login / create characters (do this once)
### Login
Send username/password:

```bash
./mud_client_helper.sh combatA send "combatA"
./mud_client_helper.sh combatA send "combatA1"
./mud_client_helper.sh combatA send ""   # press RETURN if you see a "PRESS RETURN"/pager prompt
```

### First-time creation (one-time cost)
If the log shows `Create <Name>? [y/n] :`, create the character manually and finish creation:
- Answer prompts as needed (yes/name/password, etc.)
- When you see the creation prompt `Enter selection ...`, type:

```bash
./mud_client_helper.sh combatA send "done"
```

Repeat for `combatB`.

## Admin setup (testimp)
Bring combat chars into the same room:

```bash
./mud_client_helper.sh testimp send "transfer combatA testimp"
./mud_client_helper.sh testimp send "transfer combatB testimp"
```

Grant baseline forms (current DB has these names):
- Unarmed attack: `Ram`
- Dodge: `Withdraw`
- Parry: `Parry To Left` / `Parry To Right`

```bash
./mud_client_helper.sh testimp send "setform combatA 'Ram' 499"
./mud_client_helper.sh testimp send "setform combatA 'Withdraw' 499"
./mud_client_helper.sh testimp send "setform combatA 'Parry To Left' 499"

./mud_client_helper.sh testimp send "setform combatB 'Ram' 499"
./mud_client_helper.sh testimp send "setform combatB 'Withdraw' 499"
./mud_client_helper.sh testimp send "setform combatB 'Parry To Right' 499"
```

## Scenario A: manual turn-based (mortal vs mortal)
For manual driving, **turn autocombat OFF** on both chars:

```bash
./mud_client_helper.sh combatA send "autocombat"
./mud_client_helper.sh combatB send "autocombat"
```

Set turn speed higher so you have time:

```bash
./mud_client_helper.sh combatA send "combat speed 20"
./mud_client_helper.sh combatB send "combat speed 20"
```

Then drive combat explicitly:

```bash
./mud_client_helper.sh combatA send "unarmed combatB"
./mud_client_helper.sh combatB send "dodge combatA"
./mud_client_helper.sh combatB send "unarmed combatA"
./mud_client_helper.sh combatA send "parry combatB"
```

## Scenario B: mortal vs mob (wounds/afflictions)
Spawn a mob via `testimp` (vnum 2 = “fierce bandit”):

```bash
./mud_client_helper.sh testimp send "load mob 2"
```

Attack via the mortal:

```bash
./mud_client_helper.sh combatA send "unarmed bandit"
./mud_client_helper.sh combatA send "unarmed bandit"
```

## Optional: scripted smoke (after manual setup)
Once `combatA/combatB` exist and are fully created, you can run:

```bash
cd MM32/src/tests
./combat_smoke.sh
```

This script assumes characters exist and focuses on combat + log capture, not full creation UI scripting.

