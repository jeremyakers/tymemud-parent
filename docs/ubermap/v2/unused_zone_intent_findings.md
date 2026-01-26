## Findings: “built but unused” zones (e.g., 536) — intent signals

### Summary

- The **database search did not find strong evidence** that zone `536` (or the nearby isolated band `520–545`) was discussed as a special-purpose zone by number.
- The **mail/vboard content does include explicit discussion** of *template zones* and copying *10×10 room blocks* into multiple zone numbers and then connecting them.
- Our file-level analysis supports that: the “isolated” zones look like **template-generated variants**, not bespoke hand-built content.

### Evidence

#### 1) Zone 536 is currently isolated

See `docs/ubermap/v2/zone_536_due_diligence.md`:
- 10×10 overland grid (100 rooms)
- `0` cross-zone exits (no inbound or outbound links)
- Plains-only (sector `2` in all rooms; names are plains-like)
- Seam plausibility vs `537` is poor for “east of Cairhien” (Cairhien edge has river/road/forest/hills; 536 is plains-only)

#### 2) Mudmail: explicit “template zone / 10×10 copy” language

Extract: `docs/ubermap/v2/extracts/mudmail_template_zone_mentions.tsv`

This includes multiple lines like:
- “We could make a template zone of 10x10 rooms, and just copy it into different zone numbers, then connect them”
- “a template zone that we'll just copy over and over again”

#### 3) Vboards: smaller signal, but still mentions “template zone”

Extract: `docs/ubermap/v2/extracts/vboards_template_zone_mentions.tsv`

#### 4) Copy/near-copy analysis (isolated zones near v1)

Extract: `docs/ubermap/v2/extracts/isolated_near_v1_normalized_hashes.tsv`

For the sampled isolated set near v1 numbering (`520–525`, `530–536`, `541–545`):
- **No exact normalized duplicates** were found.
- This indicates *not literal file copies*, but consistent with **template-based generation** (same structure, different sentence/name choices).

### Interpretation (tentative)

Zone `536` most likely represents one of:
- a staging/template-generated overland block that was never stitched in, or
- a partially-planned v2 expansion seed that was created early but not aligned to the Cairhien seam.

Given the seam mismatch vs `537`, we should treat `536` as **reusable template material**, not as finished “east of Cairhien” content to preserve as-is.

