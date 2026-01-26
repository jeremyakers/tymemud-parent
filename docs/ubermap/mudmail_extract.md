## Mudmail: Ubermap-related findings

### How mudmail is stored / queried

From `MM32/src/newmail.c`:

- Headers table: `mail_headers`
  - Fields used: `mail_from`, `mail_to`, `mail_date`, `message_idnum`, `mail_read`, `mail_folder`, `mail_subject`
- Bodies table: `mail_messages`
  - Fields used: `message_idnum`, `message_text`

### Keyword strategy (includes “map/build”)

I used **scoped matching** for broad terms like “map” and “build”, similar to the vboards search:

- Always match if body contains strong Ubermap tokens (“ubermap”, “uber map”, “open world”, “grid”, “wld/zon”, etc.)
- Also match “map/build/road/river/terrain/color…” only when the same message also references a city/zone/grid token.

### Exports (raw)

Generated exports live in `tmp/ubermap_exports/`:

- `mail_header_subject_hits.tsv` (subject-only hits; broad, noisier)
- `mail_body_hits.tsv` (original broad body hits; very large)
- `mail_body_hits_scoped.tsv` (scoped body hits)
- `mail_body_hits_strong.tsv` (explicit “ubermap” / known zone-id hits)

### Quick stats (current run)

- Subject-only hits: **308**
- Broad body hits: **3234**
- Scoped body hits: **1146**
- Strong body hits: **148**

### Notable high-signal example

The strong hits include a mudmail titled **“Ubermap”** discussing **zone scale options** (movement rates, continent size, and rough room count implications).

That suggests the project originally considered at least two macro-scale designs, even if the current implementation focuses on the zone grids listed in the dotproject Ubermap task.

