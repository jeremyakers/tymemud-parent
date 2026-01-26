# MM32 Combat Guide (Players)

This explains **how to use combat commands**, how **targeting** works, and how
the new **readiness** and **predictability** mechanics reward tactical play
(longer, more deliberate fights).

## Quick start

### Common commands

These commands all route through the same turn-based combat engine:

- `unarmed <target> [aim]`
- `slash <target> [aim]`
- `thrust <target> [aim]`
- `parry <target> [aim]` (defense)
- `dodge <target> [aim]` (defense)
- `pass` (advance your turn; can be used even while you are defending)
- `flee` (attempt to escape a fight; only allowed on your turn; in autocombat it can be queued)
- `subdue` (toggle: lethal blows against NPCs convert to capture/subdue instead of death)
- `followthru <practice|normal|extreme>` (changes follow-through behavior)

### Minimal fight loop

1. Attack using your weapon’s command (example: `slash bandit`)
2. If you get attacked, defend (`parry bandit` or `dodge bandit`)
3. If you need to **build readiness**, use `pass` at the right time
4. If the game warns you that you are predictable, **change your command
   class** (see “Predictability”)

## Targeting (region vs. bodypart)

You can optionally add an **aim token** to your command. The engine accepts an
aim token in either order:

- `<command> <target> <aim>`
- `<command> <aim> <target>`

Examples:

- `unarmed bandit head`
- `unarmed head bandit`
- `slash bandit chest`

### What counts as an aim token?

An aim token can be:

- a **specific bodypart name** (example: `head`)
- a **body region name** (example: `head`, `arms`, `torso`, `legs`, `feet`,
  `hands`) *(depends on the bodypart region table)*

If your aim token resolves to a valid bodypart (directly or by choosing a
bodypart within the region), you’ll see:

> `You aim for <victim>'s <bodypart>.`

If the token is not valid for the current form/target, the command fails
cleanly (no attack is executed).

## Readiness (tempo and preparation)

Readiness is a per-character value from **0 to 100** (baseline **50**) that
represents how prepared you are to execute your next move.

### How readiness affects you

Readiness applies as a **small modifier to your effective form skill**:

- Higher readiness → slightly better effective skill
- Lower readiness → slightly worse effective skill

This is intentionally a modest effect (it’s meant to reward tactics without
overpowering gear/skill).

### How readiness changes during combat

At a high level:

- **Passing** increases readiness
  - `pass` gives a meaningful bump (bigger bump when you truly pass)
- **Attacking** reduces readiness
- **Defending** can increase readiness if you avoid damage, and reduce it if
  you get hit

Practical takeaways:

- If you’re behind on tempo, use `pass` (or choose defense wisely) to regain
  readiness.
- If you’re already “ahead,” pressing attacks repeatedly will slowly drain
  readiness.

### Bruises and readiness (pain)

Bruises primarily represent **pain and impairment**, not “blood loss.”

- **Bruises can reduce readiness** (your reactions slow down).
- Bruise effects are **aggregated** so you don’t get spammed with repeated
  “bleeding” lines for every bruise record.

## Predictability (anti-spam / “don’t be a metronome”)

Predictability discourages repeating the same **combat command class** over and
over (for example spamming `unarmed` repeatedly).

### What triggers predictability?

If you repeat the same **command class** multiple times in a row, your
**predictability streak** increases.

Once the streak is high enough, the game warns you:

> `Your repeated motions feel predictable.`

### What predictability does

Predictability applies a mild penalty to your **effective form skill** while
you keep repeating the same command class.

### How to break predictability

The simplest way:

- switch to a **different command class** (example: `unarmed` → `slash`, or
  `slash` → `thrust`)

Later, as more forms are added per weapon family, you’ll have more “within-kit”
options to vary your plan.

## Forms (what they are vs. what they are not)

In this codebase, “forms” are the **Wheel of Time** fighting forms (named
stances/movements). They are **not** “equipment mods.”

Practically:

- The *command* you type (`slash`, `unarmed`, etc.) picks an *appropriate form*
  your character knows for that class.
- Your **form skill value** (what `setform` adjusts for testing/immortals) and
  your current state (wounds/exhaustion/readiness/predictability) determine how
  well you execute it.

## Troubleshooting (player-visible symptoms)

### “No appropriate forms found: No valid forms found for class X”

This means the engine could not find an enabled, usable form for that command
class. Common causes:

- You don’t know any forms for that class yet (newbie kit not applied /
  character not trained)
- Your equipment doesn’t match the form requirements (weapon mismatch)
- The form exists but is disabled/exotic (not intended for auto-selection)

### “You try to strike, but you have no weapon!”

You selected an attack that requires a weapon, but you’re not wielding one.

## Notes for balance (what to expect)

- The system is tuned toward **tactical, longer fights** where defense and
  readiness matter.
- If you want to “win on autopilot,” you’ll run into predictability penalties
  and readiness drain.
