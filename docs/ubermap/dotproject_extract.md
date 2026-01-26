## Dotproject: Ubermap-related findings

### Source

- Original exports: `dotproject_files/*.ods`
- Converted CSV: `tmp/dotproject_csv/*.csv`

### Key task: `Ubermap` (task_id = 44)

Pulled from `tmp/dotproject_csv/tasks.csv`:

- **task_name**: Ubermap
- **task_id**: 44
- **task_percent_complete**: 65
- **task_description (high-signal excerpt)**:
  - Mentions the design map: `http://tymemud.com/ubermap.jpg` (local copy: `Building_Design_Notes/ubermap.jpg`)
  - Notes that “several hundred rooms need descriptions” and that **Tar Valon area + Braem wood** had work done.
  - Provides a progress breakdown by zone:
    - **Zones Not Completed**: `469 468 509 508 538 540 539 570 (Ayasha) 569 567 608 607 638`
    - **Needs Editing**: `640 (Needs to be color-coded)`, `639 (Needs to be color-coded)`
    - **Ready to be Ported**: `610`

### Notes

- I also searched dotproject exports with **broader keywords** (e.g. `map`, `build`, `builder`, `road`, `river`, plus city/zone terms) but the single most relevant, explicit artifact is still **task 44**.
- If you want, I can generate a “related tasks” list grouped by mentions of:
  - **cities**: Tar Valon, Caemlyn, Cairhien, Aringill
  - **zones**: 468/469/508/509/…/640
  - **map/building** terms

