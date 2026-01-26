## Ubermap physical-scope policy (source of truth)

This document defines what is considered **physical** for:
- The Ubermap coordinate solve (`locx/locy/locz`)
- The main SVG export
- Data-quality audits (e.g., `ubermap.jpg` terrain vs `sector_type`)

### Definitions

- **Bidirectional exit**: an exit `A --dir--> B` is bidirectional only if `B --rev_dir(dir)--> A` exists and points back to `A`.
- **Physical room**: a room is physical **only if**:
  - It has **≥ 1 exit**, and
  - **All exits are bidirectional**, and
  - It is **not** a teleporter room (`ROOM_TELEPORT` / teleport data).

### Non-negotiables

- **No “Ethereal” heuristics**: names/descriptions (e.g., containing the word “Ethereal”) are *not* used to decide physical scope.
- **Exclude any one-way topology**: rooms with any non-bidirectional exit are excluded from the physical solve and from audits.

### Overland rule (holes are not allowed)

- Overland (ubermap.jpg) tiles are a 10×10 grid per zone using **N/E/S/W** for physical adjacency.
- Overland macro tiles must retain the **standard footprint** (width/height), otherwise the coordinate solver will compute different step sizes and the macro grid can shear (visible as “misaligned columns” and direction-mismatch edges).
- If a tile needs a portal into a farm/city/interior, prefer a **diagonal** exit (**NE/NW/SE/SW**) so **N/E/S/W remain overland movement**.
  - Rationale: keeps the overland grid intact while avoiding unrealistic “UP into a farmhouse” behavior.
  - Exception: If diagonals are not available for a specific area, choose the most physically plausible direction (but never use UP/DOWN just for mapping convenience).

### Audit tooling rule

When comparing `ubermap.jpg` → expected terrain vs world `sector_type`, the comparison must be restricted to **physical rooms only** (as exported by the engine’s coords TSV).

