## Zone 536 due diligence

- **File**: `MM32/lib/world/wld/536.wld`
- **10x10 overland shape**: yes (rooms=100)
- **Cross-zone exits**: 0

### Room-name terrain tags (heuristic)

| tag | count |
|---|---:|
| plains | 100 |

### Sector numbers (best-effort parse of header line)

| sector | count |
|---:|---:|
| 2 | 100 |

### Seam hypothesis: 536 is east of Cairhien (zone 537)

| row | west(vnum,name,tags) | east(vnum,name,tags) |
|---:|---|---|
| 0 | 53709 ``2Light Forest`7~` (forest) | 53600 ``3A Grassy Expanse`7~` (plains) |
| 1 | 53719 ``*The Gaelin`7~` (river) | 53610 ``@Rolling Grassland`7~` (plains) |
| 2 | 53729 ``3Forgotten Farmland`7~` (plains) | 53620 ``@Rolling Grassland`7~` (plains) |
| 3 | 53739 ``3The Jangai Road Travels `7East`3 and `7West`7~` (road) | 53630 ``#Farmlands`7~` (plains) |
| 4 | 53749 ``3Low Rolling Hills`7~` (hills) | 53640 ``@Rolling Grassland`7~` (plains) |
| 5 | 53759 ``3Struggling Farmland`7~` (plains) | 53650 ``3A Grassy Expanse`7~` (plains) |
| 6 | 53769 ``2Light Forest`7~` (forest) | 53660 ``@Open Plains`7~` (plains) |
| 7 | 53779 ``2Light Forest`7~` (forest) | 53670 ``#Farmlands`7~` (plains) |
| 8 | 53789 ``2Light Forest`7~` (forest) | 53680 ``@Open Plains`7~` (plains) |
| 9 | 53799 ``2Light Forest`7~` (forest) | 53690 ``@Rolling Grassland`7~` (plains) |

Notes:
- This seam comparison is only about *terrain label plausibility* (road/river/forest/hills/plains) based on room names.
- If we decide to link 537↔536, we’ll also enforce reciprocal exits and (if needed) road/river directionality prose on the seam tiles.

