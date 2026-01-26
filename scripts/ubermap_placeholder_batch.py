#!/usr/bin/env python3
"""
Fill Ubermap placeholder rooms in one or more zone .wld files.

This replaces giant inline heredoc Python blocks in terminal commands.

Design constraints:
- Latin-1 safe output (MM3/MM32 world files).
- Atomic writes (temp file + rename).
- Preserve non-placeholder rooms untouched.
- Keep output small; use --quiet for minimal logs.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import hashlib
import os
from pathlib import Path
import re
import tempfile


PLACEHOLDER_NAME_RE = re.compile(r"^\s*The Open World\s*$", re.IGNORECASE)
PLACEHOLDER_DESC_SUBSTR = "The vast world stretches out in every direction"
ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HDR_RE = re.compile(r"^D([0-3])\s*$")


@dataclass(frozen=True)
class ZoneResult:
    zone: int
    rooms_rewritten: int
    west_mislinks_fixed: int


def stable_choice(seed: str, options: list[str]) -> str:
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    idx = int.from_bytes(h[:4], "big") % len(options)
    return options[idx]


def terrain_from_header_line(header_line: str) -> int | None:
    parts = header_line.split()
    if len(parts) < 3:
        return None
    try:
        return int(parts[2])
    except ValueError:
        return None


def terrain_label(sector: int | None) -> str:
    if sector == 6:
        return "river"
    if sector == 3:
        return "dense_forest"
    if sector == 4:
        return "hills"
    return "plains"


def make_name(zone: int, vnum: int, terrain: str) -> str:
    seed = f"{zone}:{vnum}:name"
    if terrain == "dense_forest":
        return stable_choice(seed, ["`2Dense Forest`7", "`6Among Tall Trees`7", "`2The Shadowed Woods`7"])
    if terrain == "river":
        return stable_choice(seed, ["`^Along the Riverbank`7", "`^A Broad Riverway`7", "`^On the Water's Edge`7"])
    if terrain == "hills":
        return stable_choice(seed, ["`6The Rolling Hills`7", "`3A Rocky Rise`7", "`2Wind-swept Hills`7"])
    return stable_choice(seed, ["`@Open Plains`7", "`#Farmlands`7", "`3A Grassy Expanse`7", "`@Rolling Grassland`7"])


def zone_theme(zone: int) -> dict[str, str]:
    return {
        "landmark": stable_choice(str(zone), ["distant hills", "a thin tree-line", "a wavering road", "smoke on the horizon"]),
        "landmark_dir": stable_choice(str(zone), ["north", "east", "south", "west"]),
    }


def make_desc(zone: int, vnum: int, terrain: str) -> list[str]:
    theme = zone_theme(zone)
    seed = f"{zone}:{vnum}:desc"
    sky = stable_choice(
        seed + ":sky",
        [
            "`7High above, thin clouds drift lazily across the sky.`7",
            "`7A steady breeze moves the air, carrying distant birdsong.`7",
            "`7The air is clear here, and the horizon feels impossibly wide.`7",
            "`7Sunlight filters through the day, brightening the land in soft tones.`7",
        ],
    )

    if terrain == "dense_forest":
        return [
            "`2Tall trees rise in tight ranks, their canopy knitting together above you.`7",
            stable_choice(
                seed + ":ground",
                ["`2Leaf litter and old pine needles soften each step.`7", "`2The undergrowth crowds close, thorny and thick.`7"],
            ),
            stable_choice(
                seed + ":sound",
                [
                    "`2Insects drone in the shade, and a woodpecker taps at distant bark.`7",
                    "`2The woods swallow sound, leaving the area strangely hushed.`7",
                ],
            ),
            f"`7To the {theme['landmark_dir']}, {theme['landmark']} is only a suggestion beyond the trees.`7",
            sky,
        ]

    # Keep water/hills as plains-like for now; these placeholder ranges have largely been plains.
    return [
        stable_choice(
            seed + ":field",
            [
                "`3Tall grasses ripple in the wind, bending in slow, overlapping waves.`7",
                "`3Hard-packed earth shows through where feet and hooves have passed over time.`7",
                "`3The land is open and gently sloped, marked only by scattered wildflowers.`7",
            ],
        ),
        stable_choice(
            seed + ":detail",
            [
                "`7A few birds wheel overhead, then vanish into the distance.`7",
                "`7Insects buzz close to the ground, busy in the warm air.`7",
                "`7A faint track suggests travel, though it is not yet a true road.`7",
            ],
        ),
        f"`7To the {theme['landmark_dir']}, {theme['landmark']} can be made out when the light is right.`7",
        sky,
    ]


def atomic_write(path: Path, text: str) -> None:
    if not text.endswith("$~\n"):
        raise ValueError(f"{path.name}: missing $~ terminator")
    with tempfile.NamedTemporaryFile("w", encoding="latin-1", delete=False, dir=str(path.parent)) as tf:
        tf.write(text)
        tmp = tf.name
    os.replace(tmp, path)


def parse_rooms(lines: list[str]):
    rooms: list[tuple[int, str, list[str], list[str]]] = []
    i = 0
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if not m:
            i += 1
            continue

        vnum = int(m.group(1))
        if i + 1 >= len(lines):
            break

        name = lines[i + 1].rstrip("~")
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

        rooms.append((vnum, name, desc, tail))
        i = k
    return rooms


def rebuild(rooms) -> str:
    out: list[str] = []
    for vnum, name, desc, tail in rooms:
        out.append(f"#{vnum}")
        out.append(f"{name}~")
        out.extend(desc)
        out.append("~")
        out.extend(tail)
    return "\n".join(out) + "\n"


def consume_tilde_string(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines):
        if lines[i].endswith("~"):
            return i + 1
        i += 1
    return i


def fix_west_mislinks(path: Path) -> int:
    """Fix systematic D3 mislinks where dest is in-zone but not vnum-1."""
    lines = path.read_text(encoding="latin-1", errors="replace").splitlines()
    changed = 0

    i = 0
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if not m:
            i += 1
            continue

        vnum = int(m.group(1))
        zone = vnum // 100

        # Skip name+desc to reach after '~' line.
        j = i + 2
        while j < len(lines) and lines[j] != "~":
            j += 1
        if j >= len(lines):
            break
        j += 2

        k = j
        while k < len(lines) and not ROOM_HDR_RE.match(lines[k]):
            if lines[k] == "$~":
                break
            em = EXIT_HDR_RE.match(lines[k])
            if not em:
                k += 1
                continue

            d = int(em.group(1))
            nxt = consume_tilde_string(lines, k + 1)
            nxt2 = consume_tilde_string(lines, nxt)
            if nxt2 >= len(lines):
                break

            triple_idx = nxt2
            parts = lines[triple_idx].split()
            if len(parts) == 3 and parts[2].lstrip("-").isdigit():
                dest = int(parts[2])
                if d == 3 and dest // 100 == zone:
                    expected = vnum - 1
                    if expected // 100 == zone and dest != expected:
                        parts[2] = str(expected)
                        lines[triple_idx] = " ".join(parts)
                        changed += 1

            k = triple_idx + 1

        i = k

    if changed:
        atomic_write(path, "\n".join(lines) + "\n")

    return changed


def process_zone(wld_dir: Path, zone: int) -> ZoneResult:
    path = wld_dir / f"{zone}.wld"
    text = path.read_text(encoding="latin-1", errors="replace")
    rooms = parse_rooms(text.splitlines())

    changed = 0
    new_rooms = []
    for vnum, name, desc, tail in rooms:
        is_placeholder = bool(PLACEHOLDER_NAME_RE.match(name.strip())) or (PLACEHOLDER_DESC_SUBSTR in "\n".join(desc))
        if not is_placeholder:
            new_rooms.append((vnum, name, desc, tail))
            continue

        sector = terrain_from_header_line(tail[0]) if tail else None
        terr = terrain_label(sector)
        new_rooms.append((vnum, make_name(zone, vnum, terr), make_desc(zone, vnum, terr), tail))
        changed += 1

    out = rebuild(new_rooms)
    atomic_write(path, out)
    west_fixed = fix_west_mislinks(path)
    return ZoneResult(zone=zone, rooms_rewritten=changed, west_mislinks_fixed=west_fixed)


def parse_zones_arg(zones: str) -> list[int]:
    # Accept: "900-909", "900,901,902", mixed, whitespace ok.
    out: set[int] = set()
    for part in re.split(r"[,\s]+", zones.strip()):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def resolve_default_wld_dir(script_path: Path) -> Path:
    """
    Pick a sensible default `world/wld` location regardless of current working directory.

    Common cases:
    - cwd is repo root: MM32/lib/world/wld
    - cwd is MM32/lib: world/wld
    """
    repo_root = script_path.resolve().parents[1]
    candidates = [
        Path("MM32/lib/world/wld"),
        Path("world/wld"),
        repo_root / "MM32/lib/world/wld",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError(
        "Could not locate world/wld directory. Tried: "
        + ", ".join(str(c) for c in candidates)
        + ". Pass --wld-dir explicitly."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wld-dir", type=Path, default=None)
    parser.add_argument("--zones", required=True, help='Comma list or ranges, e.g. "900-909" or "900,901,905-907"')
    parser.add_argument("--quiet", action="store_true", help="Only print one summary line per zone.")
    args = parser.parse_args()

    wld_dir: Path = args.wld_dir or resolve_default_wld_dir(Path(__file__))
    zones = parse_zones_arg(args.zones)

    results: list[ZoneResult] = []
    for z in zones:
        res = process_zone(wld_dir, z)
        results.append(res)
        if args.quiet:
            print(f"{res.zone}: rooms={res.rooms_rewritten} west_fix={res.west_mislinks_fixed}")
        else:
            print(f"[zone {res.zone}] rewrote {res.rooms_rewritten} rooms; fixed west mislinks={res.west_mislinks_fixed}")

    total_rooms = sum(r.rooms_rewritten for r in results)
    total_west = sum(r.west_mislinks_fixed for r in results)
    print(f"TOTAL: zones={len(results)} rooms={total_rooms} west_fix={total_west}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

