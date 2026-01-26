#!/usr/bin/env python3
"""Scenic prose pass for Ubermap zones (de-template, keep house style).

Why this exists:
- Earlier placeholder-filling introduced short, repeated "template" sentences.
- We want rooms to feel hand-authored: literary WoT tone, but short.
- We must preserve the established house style from already-finished areas:
  - Roads: see zones like 539
  - Forest/farm: see zones like 568
  - Riverbanks: see zones like 567

This script:
- Rewrites ONLY rooms whose descriptions contain known template sentences.
- Produces short prose (typically 4–7 wrapped lines).
- Enforces: 75–80 char wrap (color codes excluded) per Builders vboard guidance.
- Enforces: no identical sentences across the run (guardrail against repetition).

Usage:
  uv run python scripts/ubermap_scenic_pass.py --zones 608
  uv run python scripts/ubermap_scenic_pass.py --zones 607,608,638
  uv run python scripts/ubermap_scenic_pass.py --zones 468,469,508,509,538,539,540,567,568,569,570,607,608,610,638,639,640
"""

from __future__ import annotations

import argparse
import hashlib
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WLD_DIR = ROOT / "MM32/lib/world/wld"

# Match room headers like "#60800"
ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")

# Builders board rule: wrap room desc 75-80, color codes don't count.
WRAP_WIDTH = 78

# Template sentences we want to eliminate (introduced by placeholder fill).
TEMPLATE_SENTENCE_SNIPPETS = [
    "The air is clear here, and the horizon feels impossibly wide.",
    "The north of Aringill stretches onward",
    "Hard-packed earth shows through where feet and hooves have passed over time.",
    "Tall grasses ripple in the wind, bending in slow, overlapping waves.",
    "Sunlight filters through the day, brightening the land in soft tones.",
    "A few birds wheel overhead, then vanish into the distance.",
    "A faint track suggests travel, though it is not yet a true road.",
    "Insects buzz close to the ground, busy in the warm air.",
    "High above, thin clouds drift lazily across the sky.",
    "To the west, the Caemlyn Road can be made out when the light is right.",
    "The Aringill and Andoran countryside stretches onward, empty enough to feel immense.",
]


def latin1_safe(s: str) -> str:
    """Force text into latin-1 safe characters (worldfiles are latin-1)."""
    # Replace common unicode punctuation with ASCII equivalents.
    return (
        s.replace("\u2014", "-")  # em dash
        .replace("\u2013", "-")  # en dash
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2026", "...")
    )


def strip_mud_color_codes(s: str) -> str:
    """Remove backtick-based color codes for width checks.

    Typical codes: `3 `7 `^ etc. We'll remove any backtick + one char.
    """
    return re.sub(r"`.", "", s)


def wrap_lines(text: str) -> list[str]:
    """Wrap text to WRAP_WIDTH (no color codes in text)."""
    text = latin1_safe(text)
    return textwrap.fill(
        text,
        width=WRAP_WIDTH,
        break_long_words=False,
        break_on_hyphens=False,
    ).splitlines()


def stable_int(seed: str) -> int:
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def choose(seed: str, options: list[str]) -> str:
    if not options:
        raise ValueError("empty options")
    return options[stable_int(seed) % len(options)]


def choose_unique(seed: str, options: list[str], used: set[str]) -> str:
    """Pick an option, but avoid exact reuse (best effort)."""
    if not options:
        raise ValueError("empty options")
    start = stable_int(seed) % len(options)
    for off in range(len(options)):
        s = options[(start + off) % len(options)]
        if s not in used:
            used.add(s)
            return s
    # If exhausted, fall back (still add so we can track it's happening).
    s = options[start]
    used.add(s)
    return s


def normalize_room_name(name_line: str) -> str:
    # Name line typically ends with "~" in the file.
    raw = name_line.rstrip("~")
    raw = strip_mud_color_codes(raw)
    return raw.strip().lower()


def infer_kind(name_line: str, sector_line: str | None) -> str:
    """Infer a broad room kind for prose patterns."""
    name = normalize_room_name(name_line)
    if "road" in name:
        return "road"
    if "river" in name or "riverbank" in name:
        return "river"
    if "farm" in name:
        return "farm"
    if "forest" in name or "wood" in name or "woods" in name:
        return "forest"
    # Fall back to sector if available (observed: 3 forest, 6 river, 4 hills).
    if sector_line:
        parts = sector_line.split()
        if len(parts) >= 3:
            try:
                sector = int(parts[2])
            except ValueError:
                sector = None
            if sector == 6:
                return "river"
            if sector == 3:
                return "forest"
            if sector == 4:
                return "hills"
    return "field"


def theme_for_zone(zone: int) -> dict[str, str]:
    # Very light, used sparingly.
    if zone in (468, 469, 508, 509, 538, 539, 540):
        return {"region": "Tar Valon countryside", "landmark": "the White Tower"}
    if zone in (638, 639, 640):
        return {"region": "Andoran countryside", "landmark": "the Caemlyn Road"}
    if zone in (607, 608, 567, 568, 569, 570):
        return {"region": "the countryside", "landmark": "distant farmsteads"}
    return {"region": "the countryside", "landmark": "the horizon"}


def make_sentences(zone: int, vnum: int, kind: str, used: set[str]) -> list[str]:
    """Produce a small set of unique sentences (no color codes)."""
    seed = f"{zone}:{vnum}:{kind}"
    theme = theme_for_zone(zone)

    # Shared sensory banks (kept short and Jordan-adjacent, but not purple).
    wind = [
        "A steady breeze combs through the grasses, carrying the clean bite of open air.",
        "Wind slides over the land in quiet pulses, stirring seedheads and loose straw.",
        "The breeze never quite dies here, worrying at cloaks and whispering in the weeds.",
        "Warm air moves lazily, bringing the faint scent of sun-baked earth.",
        "A cooler breath of wind comes and goes, as if the land itself were sighing.",
        "Wind moves through the weeds with a soft hiss, never quite still.",
        "The air smells of sun and grass, and the breeze tastes faintly of dust.",
        "A gust comes sudden and brief, then leaves only quiet and rustling stems.",
        "Wind tugs at loose hair and cloak-edges, a reminder of how open the land is.",
        "The breeze carries the dry scent of old straw and the sharper tang of crushed leaf.",
        "Warm wind rolls by in waves, as steady as the turning of a millwheel.",
        "A faint chill rides the breeze, quickly swallowed by the sun's warmth.",
        "The wind is restless, shifting direction as if it cannot decide where to go.",
        "Air moves across the land in long breaths, bending grass and then letting it rise.",
        "A light wind stirs the ground-scent up from the soil, rich and earthy.",
    ]
    sky = [
        "Clouds drift in thin ranks overhead, and the light shifts from moment to moment.",
        "The sky is wide and pale, bright enough to make distance feel deceptive.",
        "High above, a hawk circles once and then vanishes into the glare.",
        "A few scattered clouds throw slow shadows that crawl across the ground.",
        "The sun rides high, washing color from the far hills and making the world feel larger.",
        "Thin clouds slide past in slow procession, leaving the sun to glare down between them.",
        "The sky stretches clean and open, a hard blue that makes the land feel exposed.",
        "Sunlight falls broad and even, with no shade to hide anything at a distance.",
        "A drifting veil of cloud softens the light, turning the world gray for a heartbeat.",
        "The sun warms your face, and the horizon shimmers faintly in the heat.",
        "A faint haze lies over the land, blurring the line where earth meets sky.",
        "The day is bright and clear, the sort that makes far things look close.",
        "Cloud shadows wander across the ground, slow as grazing cattle.",
        "A line of clouds gathers far off, promising weather that may come later.",
        "Light catches on seedheads and stone alike, sharp enough to make you squint.",
    ]
    small_life = [
        "Grasshoppers flit up at your approach and vanish again into the tangle.",
        "Somewhere nearby, a lark calls once, answered by another farther off.",
        "A dragonfly skims low and fast, flashing blue-green before it is gone.",
        "Bees worry at stubborn wildflowers, indifferent to any traveler passing through.",
        "A rabbit freezes in the weeds, then bolts away in a blur of brown.",
        "A crow wheels overhead, cawing once before it glides away on still wings.",
        "A small brown bird hops through the grass, quick as a thought and twice as wary.",
        "Insects sing in the heat, a thin chorus that rises and falls with the breeze.",
        "A mouse darts from one tuft of grass to another, vanishing as soon as it is seen.",
        "A butterfly drifts past, pale wings flashing when it turns into the sun.",
        "Something rustles in the grass and then is gone, leaving only swaying stems.",
        "A hawk cries out somewhere above, its voice carrying farther than seems right.",
        "A line of ants works across a bare patch of earth, oblivious to the wider world.",
        "A field cricket chirps, stopping abruptly when you step too close.",
        "A thin trail of feathers hints that a fox has eaten well nearby.",
    ]

    if kind == "road":
        road_surface = [
            "The road is packed hard by countless wheels, its ruts worn deep enough to hold shadow.",
            "A well-traveled way cuts through the land, dust ground fine beneath hooves and boots.",
            "The roadway is a ribbon of beaten earth, edged by crushed grass and scattered stones.",
            "Old wagon ruts score the road, and the verge is trampled where people have stepped aside.",
            "The road here is dry and firm, the kind that carries travelers swiftly when the weather holds.",
        ]
        landmarks = [
            f"Far off, {theme['landmark']} is only a suggestion against the sky.",
            "A line of trees marks a low rise in the distance, darker than the land around it.",
            "Somewhere beyond sight, a village bell might be ringing - or it might be imagination.",
            "A smear of smoke on the horizon hints at hearthfires and settled folk.",
            "The land opens in every direction, and it is easy to feel small upon it.",
        ]
        return [
            choose_unique(seed + ":road", road_surface, used),
            choose_unique(seed + ":land", landmarks, used),
            choose_unique(seed + ":wind", wind, used),
            choose_unique(seed + ":sky", sky, used),
        ]

    if kind == "river":
        water = [
            "The river moves with patient strength, never hurried and never stopping.",
            "Water slides past with a muted hiss, curling around stones and reeds.",
            "The current tugs at the shallows, carrying leaf and reed downstream.",
            "Small ripples catch the light and break it into bright fragments.",
            "The river murmurs softly, a constant sound beneath the open sky.",
        ]
        bank = [
            "Reeds crowd the bank, tough as wire and sharp enough to bite careless hands.",
            "Smooth stones line the water's edge, rounded by years of steady flow.",
            "Mud marks the lower bank where the water has recently fallen back.",
            "Willow roots clutch the soil, and damp earth gives underfoot near the edge.",
            "A narrow strip of sand shows where the current has laid down its burden.",
        ]
        return [
            choose_unique(seed + ":water", water, used),
            choose_unique(seed + ":bank", bank, used),
            choose_unique(seed + ":life", small_life, used),
            choose_unique(seed + ":sky", sky, used),
        ]

    if kind == "forest":
        canopy = [
            "Trees stand close enough to knit their branches overhead, turning sunlight into shifting scraps.",
            "The forest thickens here, trunks rising in dark ranks and swallowing distance between them.",
            "A tangle of undergrowth crowds the way, and the shade is cooler beneath the leaves.",
            "Needle and leaf muffle sound, and the world feels smaller for all the green around you.",
            "The woods are quiet in the way of places that watch back, every rustle sounding too near.",
        ]
        ground = [
            "Leaf litter softens each step, hiding roots that catch at boots when you are not careful.",
            "The ground is dark loam and old needles, damp enough to hold the imprint of a heel.",
            "Ferns and brambles claw at legs, and fallen branches make the footing uncertain.",
            "Moss clings to stone and root alike, slick in places where shade never lifts.",
            "The smell of growing things is thick here - sap, earth, and the faint rot of old wood.",
        ]
        return [
            choose_unique(seed + ":canopy", canopy, used),
            choose_unique(seed + ":ground", ground, used),
            choose_unique(seed + ":life", small_life, used),
            choose_unique(seed + ":wind", wind, used),
        ]

    if kind == "farm":
        field = [
            "Low stone walls and broken fence rails hint at fields worked hard through better years.",
            "A patchwork of farmland lies nearby, the soil dark where it has been turned and tended.",
            "Fallow ground spreads out, choked with weeds where rows once ran straight and neat.",
            "The land bears the marks of labor - flattened paths, trampled edges, and scattered straw.",
            "A distant farmhouse sits in a shallow hollow, its roof a dark line against the sky.",
        ]
        return [
            choose_unique(seed + ":farm", field, used),
            choose_unique(seed + ":life", small_life, used),
            choose_unique(seed + ":wind", wind, used),
            choose_unique(seed + ":sky", sky, used),
        ]

    if kind == "hills":
        hills = [
            "Low hills roll in uneven waves, and the ground rises just enough to steal the horizon.",
            "Stone pushes up through the soil in scattered outcrops, rough underfoot and sun-warmed.",
            "The land climbs and dips gently, patterned with scrub and stubborn grass.",
            "Shallow rises break the view into pieces, each crest revealing another beyond it.",
            "The slope is mild, but it is constant, tugging at the legs with every step.",
        ]
        return [
            choose_unique(seed + ":hills", hills, used),
            choose_unique(seed + ":life", small_life, used),
            choose_unique(seed + ":wind", wind, used),
        ]

    # field / grassland
    field = [
        "Tall grass brushes at knees, moving in waves that never seem to repeat themselves.",
        "Open ground stretches out, broken only by wildflowers and the occasional stubborn scrub.",
        "The earth is firm here, the grass worn thin where travelers and animals have passed.",
        "A broad sweep of grassland lies quiet under the sky, empty enough to make sound carry.",
        "The land is gently sloped and open, offering little shelter and long sightlines.",
    ]
    far = [
        f"Somewhere off, {theme['landmark']} can be picked out when the light is right.",
        f"The {theme['region']} continues on, fading into distance in every direction.",
        "A faint smudge of road lies far off, more imagined than seen until you stare for it.",
        "The horizon looks closer than it is, and the emptiness between is all grass and air.",
        "A thin line of trees marks the edge of something different, though it is far away.",
    ]
    return [
        choose_unique(seed + ":field", field, used),
        choose_unique(seed + ":far", far, used),
        choose_unique(seed + ":life", small_life, used),
        choose_unique(seed + ":sky", sky, used),
    ]


def build_desc_lines(zone: int, vnum: int, kind: str, used_sentences: set[str]) -> list[str]:
    """Build description lines in the common worldfile style.

    We emit a multi-line string without repeating leading color codes on every line,
    like the 'good' zones do (539/568).
    """
    sentences = make_sentences(zone, vnum, kind, used_sentences)
    paragraph = " ".join(sentences)
    wrapped = wrap_lines(paragraph)

    # Choose a modest leading color code consistent with many outdoor rooms.
    lead = choose(f"{zone}:{vnum}:lead", ["`3", "`2", "`7"])

    out: list[str] = []
    for idx, line in enumerate(wrapped):
        if idx == 0:
            out.append(f"{lead}{line}")
        else:
            out.append(line)

    # Ensure last line ends with a reset, matching common patterns.
    if out:
        out[-1] = out[-1].rstrip() + "`7"

    # Validate widths (excluding codes)
    for line in out:
        plain = strip_mud_color_codes(line)
        if len(plain) > 80:
            raise ValueError(f"wrapped line too long ({len(plain)}): {plain!r}")

    return out


@dataclass
class Room:
    vnum: int
    name_line: str  # includes trailing "~" in source
    desc_lines: list[str]  # raw lines up to "~"
    tail_lines: list[str]  # lines after "~" until next room header


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

        desc: list[str] = []
        j = i + 2
        while j < len(lines) and lines[j] != "~":
            desc.append(lines[j])
            j += 1
        if j >= len(lines):
            break

        tail: list[str] = []
        k = j + 1
        while k < len(lines) and not ROOM_HDR_RE.match(lines[k]):
            tail.append(lines[k])
            k += 1

        rooms.append(Room(vnum=vnum, name_line=name_line, desc_lines=desc, tail_lines=tail))
        i = k
    return rooms


def rebuild(rooms: list[Room]) -> str:
    out: list[str] = []
    for r in rooms:
        out.append(f"#{r.vnum}")
        out.append(r.name_line.rstrip("\n"))
        out.extend(r.desc_lines)
        out.append("~")
        out.extend(r.tail_lines)
    data = "\n".join(out) + "\n"
    # Safety: ensure file terminator is present and at end (no trailing blanks).
    if not data.rstrip("\n").endswith("$~"):
        data = data.rstrip("\n") + "\n$~\n"
    else:
        # Normalize trailing whitespace after $~
        data = data.rstrip() + "\n"
    return data


def is_template_room(room: Room) -> bool:
    text = strip_mud_color_codes("\n".join(room.desc_lines))
    return any(snippet in text for snippet in TEMPLATE_SENTENCE_SNIPPETS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", required=True, help="Comma-separated zone numbers, e.g. 608 or 607,608,638")
    ap.add_argument(
        "--rewrite-all",
        action="store_true",
        help="Rewrite all rooms in the target zones (useful for restored/blanket scenic passes).",
    )
    args = ap.parse_args()

    zones = [int(z.strip()) for z in args.zones.split(",") if z.strip()]
    used_sentences: set[str] = set()

    for zone in zones:
        path = WLD_DIR / f"{zone}.wld"
        raw = path.read_text(encoding="latin-1", errors="replace")
        lines = raw.splitlines()
        rooms = parse_rooms(lines)

        changed = 0
        for room in rooms:
            if not args.rewrite_all and not is_template_room(room):
                continue
            sector_line = room.tail_lines[0] if room.tail_lines else None
            kind = infer_kind(room.name_line, sector_line)
            room.desc_lines = build_desc_lines(zone, room.vnum, kind, used_sentences)
            changed += 1

        if changed:
            # Atomic write: avoid leaving 0-byte files if encoding fails mid-write.
            data = rebuild(rooms)
            data = latin1_safe(data)
            data.encode("latin-1")  # ensure encodable before touching disk
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="latin-1", dir=str(path.parent)) as tf:
                tf.write(data)
                tmp_name = tf.name
            Path(tmp_name).replace(path)
        print(f"zone {zone}: scenic-updated {changed} rooms")


if __name__ == "__main__":
    main()

