# MM32 Combat NPC Kits (Builder Standard)

This is a **builder-facing** standard for assigning combat forms to NPCs so
mobs are fun and interactive even before deep per-mob curation is complete.

## Design goals

- Every mob can **attack** and **defend**.
- Default kits should be **small** and **consistent** so builders can apply them
  quickly.
- Kits should be weapon-appropriate *when possible*, but the engine also has a
  **fail-safe** that assigns a minimal kit if a mob has no forms.

## Engine fail-safe (backstop)

At mob load time, if a mob has **no** `Forms:` line (or it resolves to none),
the engine auto-assigns a minimal kit:

- `Ram` (90)
- `Withdraw` (89)
- `Parry To Left` (93)
- `Parry To Right` (94)

This is a backstop only; builders should still set real kits.

## Recommended baseline kits

All form IDs below exist in the current MM32 DB and are safe starter defaults.

### Unarmed humanoid (bandit / thug)

- **Attack**: `Ram` (90)
- **Attack**: `a kick` (6101)
- **Defense**: `a block` (6094)
- **Defense**: `a dodge` (6096)
- **Tempo**: `a counter` (6095)

### Armed humanoid (generic)

Use these when you want a “works with most weapons” baseline:

- **Attack**: `a hit` (6093)
- **Attack**: `a thrust` (6018)
- **Defense**: `a block` (6094)
- **Defense**: `a dodge` (6096)
- **Tempo**: `a counter` (6095)

### Mace / flail users

Prefer a crush-style attack form under the `slash` command class:

- **Attack**: `Kingsfisher Takes a Silverback` (6028)
- **Attack**: `a hit` (6093)
- **Defense**: `a block` (6094)
- **Defense**: `a dodge` (6096)
- **Tempo**: `a counter` (6095)

## How to apply to mobs (world files)

In a mob prototype, set a `Forms:` line with form IDs:

```text
Forms: 90 89 93 94
```

Use higher-value form IDs (6000+) for MM2-imported nostalgia forms where
appropriate.

