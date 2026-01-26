# MM32 Player-Ready Combat Surface Matrix

This is a checklist of **player-facing** and **fight-adjacent** surfaces that must
behave correctly under the MM32 **turn-based combat engine**.

## Command families (manual turn combat)

- **Attack**: `unarmed`, `slash`, `thrust`, `flourish`
- **Defense**: `parry`, `dodge`
- **Turn control**: `pass`, `wait`
- **Combat meta**: `combat ...` (speed, debug, test hooks on builder ports)
- **Follow-through preference**: `followthru` / `fthru` aliases

## Fight-adjacent commands and features

| Surface | Player command(s) | Expected behavior | Status | Notes / tests |
|---|---|---|---|---|
| Enter combat | `unarmed/slash/thrust/flourish <target> [aim]` | Enters turn combat, picks valid form, supports aim token parsing | ✅ | Covered by smoke + SIT targeting/predictability |
| Defend | `parry/dodge <target> [aim]` | Sets defense move; resolves on attacker’s action | ✅ | Covered by smoke + SIT |
| Pass | `pass` | Only on your turn; advances turn order; increases readiness | ✅ | Covered by smoke |
| Wait | `wait` | Only on your turn; advances turn order (non-pass) | ✅ | Covered by smoke |
| Follow-through | `followthru <practice|normal|extreme>` | Changes follow-through setting and affects resolution + messaging | ⚠️ audit | Add deterministic smoke assertion during follow-through pass |
| Flee (escape) | `flee` | **Turn-gated**: only on your turn; attempts escape; if success exits combat and moves | ✅ (new) | Add smoke scenario + help text |
| Movement during combat | `north/east/...` | Blocked; must use `flee` to exit a fight | ✅ | `perform_move()` already blocks fighting moves |
| Recall during combat | `recall` | Blocked during fights | ✅ | `do_recall_new` blocks `isFighting()` |
| Subdue | `subdue` (toggle) | Nonlethal intent; must integrate with turn-combat hit/death rules | ⚠️ audit | Add deterministic smoke scenario |
| Retainers: orders | `retainer order <name> <cmd>` | Orders allowed commands; should behave during combat (including `flee`) | ⚠️ audit | Add retainer assist + flee coverage |
| Retainers: AI assist | (auto) | Retainers acquire targets and participate without breaking turn order | ⚠️ audit | Add deterministic scenario |
| Autocombat toggle | `autocombat` | Must behave correctly with turn combat (manual vs auto defense/attack) | ✅ | Covered by smoke harness usage |
| Help accuracy | `help <topic>` | Help topics match actual commands/behavior | ⚠️ audit | Help is DB-backed (`Online_Help`) |

## Notes

- MM32 help is served from the DB via `Online_Help` / `Online_Policy` (not `lib/text/*`).
- This matrix is intended to be kept current as combat systems are migrated/refined.

