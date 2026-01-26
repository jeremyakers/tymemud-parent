#!/usr/bin/env python3
"""Fill placeholder Ubermap rooms.

Goals (Acceptance criteria B):
- Replace placeholder room names ("The Open World") with consistent, themed names.
- Replace generic placeholder descriptions with unique, polished descriptions.
- Do NOT overwrite already-authored non-placeholder rooms.

This script edits selected `.wld` files in-place.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WLD_DIR = ROOT / 'MM32/lib/world/wld'

# Target the Ubermap MVP zone list (dotproject task 44) plus neighboring zones that
# are part of the same overland grid and have lingering placeholder text.
#
# IMPORTANT: The script only edits rooms that still look like placeholders, so it is
# safe to run repeatedly across a wider set.
TARGET_ZONES = [
    468, 469, 508, 509, 537, 538, 539, 540, 567, 568, 569, 570, 607, 608, 609, 610, 611, 638, 639, 640, 670,
]

PLACEHOLDER_NAME_RE = re.compile(r'^\s*The Open World\s*$', re.IGNORECASE)
# Placeholder desc appears with color codes in many files. We match a robust substring.
PLACEHOLDER_DESC_SUBSTR = 'The vast world stretches out in every direction'

ROOM_HDR_RE = re.compile(r'^#(\d+)\s*$')


@dataclass
class Room:
    vnum: int
    name: str
    desc_lines: list[str]
    tail_lines: list[str]  # everything after desc terminator (~), until next room header


def stable_choice(seed: str, options: list[str]) -> str:
    h = hashlib.sha256(seed.encode('utf-8')).digest()
    idx = int.from_bytes(h[:4], 'big') % len(options)
    return options[idx]


def coord_from_vnum(vnum: int) -> tuple[int, int]:
    cell = vnum % 100
    return cell // 10, cell % 10


def zone_theme(zone: int) -> dict[str, str]:
    # Light touch themes derived from zone titles + existing prose.
    if zone in (468, 469):
        return {
            'region': 'Tar Valon countryside',
            'landmark': 'the White Tower',
            'landmark_dir': stable_choice(str(zone), ['southwest', 'west', 'northwest']),
        }
    if zone in (508, 509):
        return {
            'region': 'south of Tar Valon',
            'landmark': 'Dragonmount',
            'landmark_dir': 'west',
        }
    if zone == 540:
        return {
            'region': 'rolling farmlands',
            'landmark': 'distant farmsteads',
            'landmark_dir': stable_choice(str(zone), ['south', 'east', 'west']),
        }
    if zone == 537:
        return {
            'region': 'Cairhien countryside',
            'landmark': 'Cairhien',
            'landmark_dir': stable_choice(str(zone), ['east', 'southeast', 'south']),
        }
    if zone in (567, 607):
        return {
            'region': 'along the Alguenya',
            'landmark': 'the Alguenya',
            'landmark_dir': stable_choice(str(zone), ['west', 'east', 'north']),
        }
    if zone == 611:
        return {
            'region': 'scattered farmsteads',
            'landmark': 'smoke from low chimneys',
            'landmark_dir': stable_choice(str(zone), ['west', 'east', 'north']),
        }
    if zone == 608:
        return {
            'region': 'north of Aringill',
            'landmark': 'Aringill',
            'landmark_dir': stable_choice(str(zone), ['south', 'southeast', 'southwest']),
        }
    if zone in (638, 639):
        return {
            'region': 'Aringill and Andoran countryside',
            'landmark': 'the Caemlyn Road',
            'landmark_dir': stable_choice(str(zone), ['south', 'west', 'east']),
        }
    if zone == 640:
        return {
            'region': 'Caemlyn countryside',
            'landmark': 'Caemlyn',
            'landmark_dir': stable_choice(str(zone), ['south', 'southeast', 'southwest']),
        }
    if zone == 610:
        return {
            'region': 'the Braem Wood',
            'landmark': 'the dark canopy',
            'landmark_dir': 'above',
        }
    if zone == 670:
        return {
            'region': 'a military encampment',
            'landmark': 'the palisade wall',
            'landmark_dir': stable_choice(str(zone), ['north', 'east', 'west']),
        }
    return {'region': 'the open world', 'landmark': 'the horizon', 'landmark_dir': 'ahead'}


def terrain_from_header_line(header_line: str) -> int | None:
    # After the description terminator, the next line is like: "509 a 2 10 10" or "570 0 4 10 10".
    # We interpret the 3rd token as sector (best-effort).
    parts = header_line.split()
    if len(parts) < 3:
        return None
    try:
        return int(parts[2])
    except ValueError:
        return None


def terrain_label(sector: int | None) -> str:
    # Based on observed files:
    # 2 = plains/fields, 3 = dense forest, 4 = hills/rolling, 6 = river.
    if sector == 6:
        return 'river'
    if sector == 3:
        return 'dense_forest'
    if sector == 4:
        return 'hills'
    return 'plains'


def make_name(zone: int, vnum: int, terrain: str) -> str:
    seed = f'{zone}:{vnum}:name'
    if terrain == 'dense_forest':
        opts = [
            '`2Dense Forest`7',
            '`6Deep in a Dense Forest`7',
            '`2The Shadowed Woods`7',
            '`6Among Tall Trees`7',
        ]
        return stable_choice(seed, opts)
    if terrain == 'river':
        opts = [
            '`^The Alguenya`7',
            '`^Along the Riverbank`7',
            '`^A Broad Riverway`7',
            '`^On the Water\'s Edge`7',
        ]
        return stable_choice(seed, opts)
    if terrain == 'hills':
        opts = [
            '`6The Rolling Hills`7',
            '`3A Rocky Rise`7',
            '`2Wind-swept Hills`7',
            '`3Low, Stony Hills`7',
        ]
        return stable_choice(seed, opts)
    # plains
    opts = [
        '`@Open Plains`7',
        '`#Farmlands`7',
        '`3A Grassy Expanse`7',
        '`@Rolling Grassland`7',
    ]
    return stable_choice(seed, opts)


def make_desc(zone: int, vnum: int, terrain: str, sector_line: str) -> list[str]:
    r, c = coord_from_vnum(vnum)
    theme = zone_theme(zone)
    seed = f'{zone}:{vnum}:desc'

    sky = stable_choice(seed + ':sky', [
        '`7High above, thin clouds drift lazily across the sky.`7',
        '`7A steady breeze moves the air, carrying distant birdsong.`7',
        '`7The air is clear here, and the horizon feels impossibly wide.`7',
        '`7Sunlight filters through the day, brightening the land in soft tones.`7',
    ])

    if terrain == 'dense_forest':
        ground = stable_choice(seed + ':ground', [
            '`2Leaf litter and old pine needles soften each step.`7',
            '`2Fallen branches and mossy roots twist across the forest floor.`7',
            '`2The ground is dark with loam, and the undergrowth crowds close.`7',
        ])
        sound = stable_choice(seed + ':sound', [
            '`2Somewhere deeper within, unseen creatures rustle and then fall silent.`7',
            '`2Insects drone in the shade, and a woodpecker taps at distant bark.`7',
            '`2The woods swallow sound, leaving the area strangely hushed.`7',
        ])
        landmark = f"`2To the {theme['landmark_dir']}, {theme['landmark']} is only a suggestion beyond the trees.`7"
        return [
            f"`2Tall trees rise in tight ranks, their canopy knitting together above you.`7",
            ground,
            sound,
            landmark,
            sky,
        ]

    if terrain == 'river':
        water = stable_choice(seed + ':water', [
            '`^The water slides past with a quiet, persistent murmur.`7',
            '`^Small ripples catch the light, breaking it into bright fragments.`7',
            '`^The current is steady, carrying bits of leaf and reed downstream.`7',
        ])
        bank = stable_choice(seed + ':bank', [
            '`3The banks are threaded with reeds and tough grasses.`7',
            '`3Smooth stones line the edge of the water, worn by time.`7',
            '`3A narrow strip of mud marks where the river has recently receded.`7',
        ])
        return [
            f"`^A broad riverway cuts through the land here, defining the countryside with its flow.`7",
            water,
            bank,
            sky,
        ]

    if terrain == 'hills':
        slope = stable_choice(seed + ':slope', [
            '`3Low hills roll in uneven waves, forcing the eye to climb and dip with the land.`7',
            '`3Stone pushes through the soil in places, forming rough shelves and scattered outcrops.`7',
            '`3The ground rises and falls gently, patterned with scrub and stubborn grass.`7',
        ])
        landmark = stable_choice(seed + ':lm', [
            f"`7From here, {theme['landmark']} lies somewhere to the {theme['landmark_dir']}, beyond the nearest rise.`7",
            f"`7The {theme['region']} continues on, fading into distance in every direction.`7",
        ])
        return [slope, landmark, sky]

    # plains
    field = stable_choice(seed + ':field', [
        '`3Tall grasses ripple in the wind, bending in slow, overlapping waves.`7',
        '`3The land is open and gently sloped, marked only by scattered wildflowers.`7',
        '`3Hard-packed earth shows through where feet and hooves have passed over time.`7',
    ])
    detail = stable_choice(seed + ':detail', [
        '`7A few birds wheel overhead, then vanish into the distance.`7',
        '`7Insects buzz close to the ground, busy in the warm air.`7',
        '`7A faint track suggests travel, though it is not yet a true road.`7',
    ])
    landmark = stable_choice(seed + ':lm', [
        f"`7To the {theme['landmark_dir']}, {theme['landmark']} can be made out when the light is right.`7",
        f"`7The {theme['region']} stretches onward, empty enough to feel immense.`7",
    ])
    return [field, detail, landmark, sky]


def parse_rooms(lines: list[str]) -> list[Room]:
    rooms: list[Room] = []
    i = 0
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        vnum = int(m.group(1))
        if i + 1 >= len(lines):
            break
        name_line = lines[i + 1]
        name = name_line.rstrip('~')

        # Description starts at i+2 and ends at a line that is exactly "~".
        desc: list[str] = []
        j = i + 2
        while j < len(lines):
            if lines[j] == '~':
                break
            desc.append(lines[j])
            j += 1
        if j >= len(lines):
            break
        # tail begins after desc terminator
        tail: list[str] = []
        k = j + 1
        while k < len(lines):
            if ROOM_HDR_RE.match(lines[k]):
                break
            tail.append(lines[k])
            k += 1

        rooms.append(Room(vnum=vnum, name=name, desc_lines=desc, tail_lines=tail))
        i = k
    return rooms


def rebuild_file(rooms: list[Room]) -> str:
    out_lines: list[str] = []
    for r in rooms:
        out_lines.append(f'#{r.vnum}')
        out_lines.append(f'{r.name}~')
        out_lines.extend(r.desc_lines)
        out_lines.append('~')
        out_lines.extend(r.tail_lines)
    # Ensure trailing newline
    return '\n'.join(out_lines) + '\n'


def main() -> None:
    for zone in TARGET_ZONES:
        path = WLD_DIR / f'{zone}.wld'
        text = path.read_text(encoding='latin-1', errors='replace')
        lines = text.splitlines()
        rooms = parse_rooms(lines)
        changed = 0

        for room in rooms:
            is_placeholder_name = bool(PLACEHOLDER_NAME_RE.match(room.name.strip()))
            desc_text = '\n'.join(room.desc_lines)
            is_placeholder_desc = PLACEHOLDER_DESC_SUBSTR in desc_text

            if not (is_placeholder_name or is_placeholder_desc):
                continue

            # Determine sector from the first tail line if possible.
            sector = None
            if room.tail_lines:
                sector = terrain_from_header_line(room.tail_lines[0])
            terr = terrain_label(sector)

            room.name = make_name(zone, room.vnum, terr)
            room.desc_lines = make_desc(zone, room.vnum, terr, room.tail_lines[0] if room.tail_lines else '')
            changed += 1

        if changed:
            path.write_text(rebuild_file(rooms), encoding='latin-1')
        print(f'zone {zone}: updated {changed} rooms')


if __name__ == '__main__':
    main()
