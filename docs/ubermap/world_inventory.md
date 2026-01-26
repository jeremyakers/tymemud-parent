## Ubermap world inventory (expanded: JPG + world scan)

### Core zones
Seeded from `Building_Design_Notes/ubermap.jpg` and expanded to include any **grid-like (100-room) zones** in the 400–799 range connected via exits.

- **JPG seed zones**: [468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 638, 639, 640]
- **Core zone set**: [400, 468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 611, 638, 639, 640, 670]

| zone | title | rooms | placeholder_name | placeholder_desc | undefined~ | nonprintable_bytes | terminator_ok | trailing_newline | cross_zone_exits |
|---|---|---|---|---|---|---|---|---|---|
| 400 | Player Houses~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 1 |
| 468 | `^W`6est `^TV C`6ountryside`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 34 |
| 469 | `^E`6ast `^TV C`6ountryside`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 23 |
| 508 | `^S`6outh of `^T`6ar `^V`6alon`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 30 |
| 509 | `^S`6outhwest of `^T`6ar `^V`6alon`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 29 |
| 537 | Cairhien Countryside~ | 100 | 7 | 0 | 173 | 0 | yes | yes | 25 |
| 538 | `#F`3armlands`7/`#P`3lains`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 40 |
| 539 | `^E`6rinin/`^A`6lindrelle `^F`6ork`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 40 |
| 540 | `#F`3armlands`7/`#P`3lains`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 20 |
| 567 | `#A`3lguenya `#R`3oad`7/`^R`6iver`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 30 |
| 568 | `^S`6outhwest of `^C`6airhien`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 40 |
| 569 | `^A`6lindrelle`7/`#F`3arms`7/`@F`2orest`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 40 |
| 570 | `#F`3arms`7/`!C`1a`&e`7m`&l`1y`!n`& Road`7/`@F`2orest`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 32 |
| 607 | `#A`3lguenya `#R`3oad`7/`#F`3arms`7/`@F`2orest`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 20 |
| 608 | `@F`2orest`7/`&N`7orth of `&A`7ringill`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 40 |
| 609 | `@D`2eep `@B`2raem `@W`2oods`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 40 |
| 610 | `2The Braem Wood`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 32 |
| 611 | `#F`3armhouses`7/`#M`3isc. `#B`3uildings`7~ | 100 | 87 | 0 | 0 | 0 | yes | yes | 1 |
| 638 | `@A`2ringill `@C`2ountryside`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 26 |
| 639 | `@A`2ndoran `@C`2ountryside`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 31 |
| 640 | `@C`2aemlyn `@C`2ountryside`7~ | 100 | 0 | 0 | 0 | 0 | yes | yes | 27 |
| 670 | `1Builder Testings`7~ | 100 | 18 | 0 | 142 | 0 | yes | yes | 1 |

### Other connected zones (non-core)
These zones are connected via exits from the core set but are not treated as overland grid build targets (often city/house/test/utility zones).

| zone | title | rooms | undefined~ | nonprintable_bytes | terminator_ok | trailing_newline |
|---|---|---:|---:|---|---|---|
| 0 | `&I`7mm `&R`7ooms~ | 100 | 24 | 0 | yes | yes |
| 1 | `2Immortal Hideaway`7~ | 46 | 8 | 0 | yes | yes |
| 3 | `^N`6ewbie `^Z`6one`7~ | 56 | 97 | 0 | yes | yes |
| 15 | `7Alindaer (Mikki)`7~ | 100 | 33 | 0 | yes | yes |
| 16 | Alindaer, continued~ | 100 | 20 | 0 | yes | yes |
| 24 | Wolfkin Guild Area (Dugoth)~ | 47 | 88 | 0 | yes | yes |
| 45 | `2Tinker Camp (Kendric)`7~ | 87 | 174 | 0 | yes | yes |
| 47 | `2Tinker Guild Area`7~ | 32 | 60 | 0 | yes | yes |
| 51 | `7Aiel Camp (Marek/Rhuarc)`7~ | 100 | 6 | 0 | yes | yes |
| 56 | Illuminator Area~ | 100 | 4 | 0 | yes | yes |
| 90 | `^T`6ar `^V`6alon`7~ | 100 | 200 | 0 | yes | yes |
| 91 | `^T`6ar `^V`6alon`7~ | 100 | 200 | 0 | yes | yes |
| 92 | `^T`6ar `^V`6alon`7~ | 50 | 42 | 0 | yes | yes |
| 94 | `6(`^WT`6) `3Lower Floors`0~ | 100 | 201 | 0 | yes | yes |
| 95 | `6(`^WT`6) `3Ajah Wing`0~ | 100 | 203 | 0 | yes | yes |
| 96 | `6(`^WT`6) `3Grounds`0~ | 100 | 200 | 0 | yes | yes |
| 97 | `6(`^WT`6) `3Upper/Base.`0~ | 78 | 151 | 0 | yes | yes |
| 98 | `6(`^WT`6) `3Maze/Palace`7~ | 100 | 200 | 0 | yes | yes |
| 130 | `^C`6airhien `^- `6Inns, Etc`0~ | 52 | 34 | 0 | yes | yes |
| 132 | `2Cairhien - City (Katt)`7~ | 100 | 38 | 0 | yes | yes |
| 133 | `2Cairhien - City (cont)`7~ | 100 | 12 | 0 | yes | yes |
| 134 | `6Cairhien Palace`7 (Helena)~ | 41 | 16 | 0 | yes | yes |
| 135 | `2Cairhien Gardens and Shops`7~ | 74 | 14 | 0 | yes | yes |
| 140 | The Andoran Palace~ | 65 | 44 | 0 | yes | yes |
| 160 | `6Caemlyn - Streets`7~ | 100 | 85 | 0 | yes | yes |
| 161 | `6Caemlyn - Inns and things`7~ | 100 | 72 | 0 | yes | yes |
| 162 | `6Caemlyn - Extras`7~ | 3 | 6 | 0 | yes | yes |
| 165 | `2Aringill`7~ | 90 | 10 | 0 | yes | yes |
| 171 | `6Asha'man GA - mostly empty`7~ | 9 | 0 | 0 | yes | yes |
| 191 | Player Houses~ | 97 | 48 | 0 | yes | yes |
| 193 | `#Player's Houses`7~ | 51 | 98 | 0 | yes | yes |
| 195 | `1Player Houses`7~ | 60 | 8 | 0 | yes | yes |
| 486 | `6Tar Valon Peripherals`7~ | 19 | 38 | 0 | yes | yes |
| 526 | `6CH Peripherals`7~ | 10 | 20 | 0 | yes | yes |
| 626 | `6CM/Aringill Peripherals`7~ | 9 | 18 | 0 | yes | yes |
