## Vboards: Ubermap-related findings

### How vboards are stored / queried

From `MM32/src/vboards.c` and `public_html/displaymessage.php`:

- Messages table: `vboard_messages`
- Key fields used in code:
  - `vboard` (board type)
  - `guild` (0 for global project board; otherwise a subguild ID for guild boards)
  - `id` (post id)
  - `comment` (threading: topic has `comment=id`; replies have `comment=<topic_id>`)
  - `date`, `last_edit`, `author`, `author_id`, `title`, `message`

Board type constants (from `MM32/src/boards.h`):

- `VBOARD_PROJECTS = 0`
- `VBOARD_GUILD = 4` (guild-specific boards)

### Which boards I searched

- **Project board**: `vboard=0 AND guild=0`
- **Builders guild board**: `vboard=4 AND guild=20` (from `Player_Subguilds`: tag `BD`, name `Builders Dept`)
- **Coders guild board**: `vboard=4 AND guild=24` (from `Player_Subguilds`: tag `CD`, name `Coder`)

### Keyword strategy (includes your request for “map/build”)

Because terms like **“map”** and **“build”** are extremely common, I used **scoped matching**:

- Always match if the post contains strong Ubermap tokens (e.g. “ubermap”, “open world”, zone/grid/file tokens, city names).
- Also match “map/build/road/river/terrain/color…” **only when** the same post also contains at least one strong Ubermap token (city/zone/grid/etc).

### Exports (raw)

Generated exports live in `tmp/ubermap_exports/`:

- `vboard_project_matches.tsv` (all scoped matches)
- `vboard_builders_coders_matches.tsv` (all scoped matches)
- `vboard_project_strong.tsv` (strong hits)
- `vboard_builders_coders_strong.tsv` (strong hits)

### Quick stats (current run)

- Project board scoped matches: **26**
- Builders/Coders scoped matches: **52**
- Project board strong hits: **24**
- Builders/Coders strong hits: **44**

### Notable high-signal example (Builders board)

The Builders board includes operational info about building workflow, including a reminder about saving zones via:

- `redit save zone#`
- `zedit save zone #`
- `oedit save zone #`

This is useful context for finishing the Ubermap work in a way that doesn’t lose progress.

