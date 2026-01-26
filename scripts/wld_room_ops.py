#!/usr/bin/env python3
"""
Utility ops for CircleMUD-style `.wld` files (targeted room edits).

Design goals:
- Repeatable, scriptable edits for overland/ubermap work (no giant one-liners).
- Make surgical changes: operate on specific vnums, preserve everything else.
- Supports:
  - disconnecting rooms ("hole" vnums): remove all exits from those rooms and remove inbound exits
  - setting sector type / name / description for specific vnums
  - copying *text fields* (name + description) from one vnum to another while preserving the
    destination's exits (so we don't break the overland grid)
  - restoring a room block from a git ref (used to revert old placeholder vnums back to builder)

Notes:
- This is a text-level editor. It does not attempt to validate full world consistency.
- Encoding: MUD world files are typically latin-1.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOM_HEADER_RE = re.compile(r"^#(\d+)\s*$")


@dataclass(frozen=True)
class RoomSpan:
    vnum: int
    start: int  # inclusive line index
    end: int  # exclusive line index (points at line after trailing 'S')


def _parse_int_set(spec: str) -> set[int]:
    out: set[int] = set()
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            lo = int(a.strip())
            hi = int(b.strip())
            if hi < lo:
                lo, hi = hi, lo
            out.update(range(lo, hi + 1))
        else:
            out.add(int(part))
    return out


def _read_text(p: Path) -> list[str]:
    return p.read_text(encoding="latin-1", errors="replace").splitlines()


def _write_text(p: Path, lines: list[str]) -> None:
    p.write_text("\n".join(lines) + "\n", encoding="latin-1")


def _index_rooms(lines: list[str]) -> dict[int, RoomSpan]:
    spans: dict[int, RoomSpan] = {}
    i = 0
    while i < len(lines):
        m = ROOM_HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue
        v = int(m.group(1))
        start = i
        # room ends at the next line that is exactly "S"
        j = i + 1
        while j < len(lines) and lines[j].strip() != "S":
            j += 1
        if j >= len(lines):
            raise SystemExit(f"Malformed .wld: room #{v} missing terminal 'S'")
        end = j + 1
        spans[v] = RoomSpan(vnum=v, start=start, end=end)
        i = end
    return spans


def _split_room(lines: list[str], span: RoomSpan) -> list[str]:
    return lines[span.start : span.end]


def _find_zone_line_idx(room_lines: list[str]) -> int:
    # Format typically:
    # #vnum
    # <name>~
    # <desc...>
    # ~
    # <zone> <flags> <sector> [<x> <y>]
    for i, ln in enumerate(room_lines):
        # Support both 3-field and 5-field zone lines.
        if re.match(r"^\d+\s+\S+\s+\d+(\s+\d+\s+\d+)?\s*$", ln.strip()):
            return i
    raise SystemExit("Could not find room 'zone flags sector [x y]' line")


def _room_name_idx(room_lines: list[str]) -> int:
    # Immediately after #vnum
    if len(room_lines) < 2 or not ROOM_HEADER_RE.match(room_lines[0]):
        raise SystemExit("Malformed room block (missing #vnum header)")
    return 1


def _room_desc_span(room_lines: list[str]) -> tuple[int, int]:
    # Description begins after name line and continues until a line that is exactly "~"
    i = _room_name_idx(room_lines) + 1
    start = i
    while i < len(room_lines):
        if room_lines[i].strip() == "~":
            return start, i + 1  # include terminator
        i += 1
    raise SystemExit("Malformed room block (missing desc terminator ~)")


def _remove_exit_blocks_from_room(room_lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(room_lines):
        ln = room_lines[i]
        if re.match(r"^D\d+\s*$", ln):
            # Exit block format:
            # Dn
            # <desc...>~ or ~
            # <keywords...>~ or ~
            # <doorflags key to_room>
            # We remove entire block.
            i += 1
            # skip desc block (~-terminated)
            while i < len(room_lines):
                if room_lines[i].strip() == "~" or room_lines[i].endswith("~"):
                    i += 1
                    break
                i += 1
            # skip keywords block (~-terminated)
            while i < len(room_lines):
                if room_lines[i].strip() == "~" or room_lines[i].endswith("~"):
                    i += 1
                    break
                i += 1
            # skip info line
            if i < len(room_lines):
                i += 1
            continue
        out.append(ln)
        i += 1
    return out


def _remove_inbound_exits(lines: list[str], target_vnums: set[int]) -> tuple[list[str], int]:
    """Remove any exit blocks that lead to any vnum in target_vnums. Returns (new_lines, removed_count)."""
    spans = _index_rooms(lines)
    removed = 0
    out = list(lines)
    # We'll rebuild each room independently and then stitch back into the file in-place.
    # Simpler: operate per-room and rewrite its slice.
    for v, sp in sorted(spans.items(), key=lambda kv: kv[1].start, reverse=True):
        room = _split_room(out, sp)
        new_room: list[str] = []
        i = 0
        while i < len(room):
            if re.match(r"^D\d+\s*$", room[i]):
                d_header = room[i]
                j = i + 1
                # skip desc (~-terminated)
                while j < len(room) and not (room[j].strip() == "~" or room[j].endswith("~")):
                    j += 1
                if j < len(room):
                    j += 1
                # skip keywords (~-terminated)
                while j < len(room) and not (room[j].strip() == "~" or room[j].endswith("~")):
                    j += 1
                if j < len(room):
                    j += 1
                if j >= len(room):
                    # malformed; keep as-is
                    new_room.append(d_header)
                    i += 1
                    continue
                info = room[j]
                parts = info.split()
                to_room = None
                if len(parts) >= 3:
                    try:
                        to_room = int(parts[2])
                    except ValueError:
                        to_room = None
                if to_room is not None and to_room in target_vnums:
                    # drop whole block
                    removed += 1
                    i = j + 1
                    continue
                # keep block
                new_room.extend(room[i : j + 1])
                i = j + 1
                continue
            new_room.append(room[i])
            i += 1
        out[sp.start : sp.end] = new_room
    return out, removed


def _split_room_exits(room_lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    """
    Split a room block into (prefix, exits, suffix).
    - prefix: up through the zone line (inclusive), and any non-exit lines before first D*
    - exits: all D* blocks
    - suffix: everything after exits (R/G blocks, etc.)
    """
    prefix: list[str] = []
    exits: list[str] = []
    suffix: list[str] = []

    in_exit = False
    i = 0
    while i < len(room_lines):
        ln = room_lines[i]
        if re.match(r"^D\d+\s*$", ln):
            in_exit = True
            # capture the whole exit block
            j = i + 1
            # desc block
            while j < len(room_lines):
                if room_lines[j].strip() == "~" or room_lines[j].endswith("~"):
                    j += 1
                    break
                j += 1
            # keywords block
            while j < len(room_lines):
                if room_lines[j].strip() == "~" or room_lines[j].endswith("~"):
                    j += 1
                    break
                j += 1
            # info line
            if j < len(room_lines):
                j += 1
            exits.extend(room_lines[i:j])
            i = j
            continue
        if in_exit:
            suffix = room_lines[i:]
            break
        prefix.append(ln)
        i += 1

    return prefix, exits, suffix


def _set_room_name_desc_sector(
    room: list[str],
    *,
    name_line: str | None,
    desc_lines: list[str] | None,
    sector: int | None,
) -> list[str]:
    out = list(room)
    if name_line is not None:
        out[_room_name_idx(out)] = name_line
    if desc_lines is not None:
        ds, de = _room_desc_span(out)
        out[ds:de] = desc_lines
    if sector is not None:
        zi = _find_zone_line_idx(out)
        parts = out[zi].split()
        if len(parts) < 5:
            raise SystemExit("Malformed zone line (expected 5 fields)")
        parts[2] = str(int(sector))
        out[zi] = " ".join(parts)
    return out


def _git_show_file(repo_dir: Path, ref: str, rel_path: str) -> list[str]:
    cmd = ["git", "show", f"{ref}:{rel_path}"]
    p = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="latin-1",
        errors="replace",
    )
    if p.returncode != 0:
        raise SystemExit(f"git show failed: {p.stderr.strip()}")
    return p.stdout.splitlines()


def cmd_disconnect(args: argparse.Namespace) -> int:
    wld = Path(args.wld_file)
    targets = _parse_int_set(args.vnums)
    lines = _read_text(wld)
    spans = _index_rooms(lines)

    missing = sorted(v for v in targets if v not in spans)
    if missing:
        raise SystemExit(f"Missing vnums in {wld}: {missing}")

    # Remove inbound exits to target vnums.
    lines, removed = _remove_inbound_exits(lines, targets)
    spans = _index_rooms(lines)

    # For each target room: remove all exits + mark unused.
    for v in sorted(targets, reverse=True):
        sp = spans[v]
        room = _split_room(lines, sp)
        room = _remove_exit_blocks_from_room(room)
        # Set name/desc to unused marker.
        name = f"!unused (reserved hole)~"
        desc = [
            "!unused (reserved hole)",
            "This room is intentionally disconnected to reserve overland space for a city insert.",
            "~",
        ]
        # Ensure desc terminator on its own line as per parser.
        desc = [ln if ln != "~" else "~" for ln in desc]
        room = _set_room_name_desc_sector(room, name_line=name, desc_lines=desc, sector=None)
        lines[sp.start : sp.end] = room

    if args.inplace:
        _write_text(wld, lines)
    print(f"{wld}: disconnected_vnums={len(targets)} inbound_exit_blocks_removed={removed}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_remove_exits_to(args: argparse.Namespace) -> int:
    wld = Path(args.wld_file)
    targets = _parse_int_set(args.vnums)
    lines = _read_text(wld)

    lines, removed = _remove_inbound_exits(lines, targets)

    if args.inplace:
        _write_text(wld, lines)
    print(f"{wld}: removed_exit_blocks_to={len(targets)} removed={removed}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_copy_text(args: argparse.Namespace) -> int:
    wld = Path(args.wld_file)
    src_wld = Path(args.src_wld_file) if args.src_wld_file else wld
    src_v = int(args.src_vnum)
    dst_v = int(args.dst_vnum)
    dst_lines = _read_text(wld)
    dst_spans = _index_rooms(dst_lines)
    if dst_v not in dst_spans:
        raise SystemExit(f"Missing dst vnum in {wld}: dst={dst_v}")

    src_lines = _read_text(src_wld)
    src_spans = _index_rooms(src_lines)
    if src_v not in src_spans:
        raise SystemExit(f"Missing src vnum in {src_wld}: src={src_v}")

    src_room = _split_room(src_lines, src_spans[src_v])
    dst_room = _split_room(dst_lines, dst_spans[dst_v])

    name = src_room[_room_name_idx(src_room)]
    ds, de = _room_desc_span(src_room)
    desc = src_room[ds:de]

    dst_room2 = _set_room_name_desc_sector(dst_room, name_line=name, desc_lines=desc, sector=None)
    dst_lines[dst_spans[dst_v].start : dst_spans[dst_v].end] = dst_room2

    if args.inplace:
        _write_text(wld, dst_lines)
    print(f"{wld}: copied_text src={src_v} ({src_wld}) -> dst={dst_v}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_copy_room(args: argparse.Namespace) -> int:
    wld = Path(args.wld_file)
    src_wld = Path(args.src_wld_file) if args.src_wld_file else wld
    src_v = int(args.src_vnum)
    dst_v = int(args.dst_vnum)

    dst_lines = _read_text(wld)
    dst_spans = _index_rooms(dst_lines)
    if dst_v not in dst_spans:
        raise SystemExit(f"Missing dst vnum in {wld}: dst={dst_v}")

    src_lines = _read_text(src_wld)
    src_spans = _index_rooms(src_lines)
    if src_v not in src_spans:
        raise SystemExit(f"Missing src vnum in {src_wld}: src={src_v}")

    src_room = _split_room(src_lines, src_spans[src_v])
    # Replace vnum header to keep destination vnum stable.
    if not ROOM_HEADER_RE.match(src_room[0]):
        raise SystemExit(f"Malformed source room block for {src_v} in {src_wld}")
    src_room = [f"#{dst_v}"] + src_room[1:]

    dst_lines[dst_spans[dst_v].start : dst_spans[dst_v].end] = src_room

    if args.inplace:
        _write_text(wld, dst_lines)
    print(f"{wld}: copied_room src={src_v} ({src_wld}) -> dst={dst_v}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_copy_payload(args: argparse.Namespace) -> int:
    """
    Copy non-exit payload from src vnum to dst vnum, preserving dst exits.

    “Payload” here means everything except exit blocks:
    - name line
    - description
    - zone/flags/sector line
    - extra desc blocks / other suffix content

    This is intentionally the inverse of restore-exits-from-git, and is the
    surgical primitive we want for overland terrain restoration.
    """
    wld = Path(args.wld_file)
    src_wld = Path(args.src_wld_file) if args.src_wld_file else wld
    src_v = int(args.src_vnum)
    dst_v = int(args.dst_vnum)

    dst_lines = _read_text(wld)
    dst_spans = _index_rooms(dst_lines)
    if dst_v not in dst_spans:
        raise SystemExit(f"Missing dst vnum in {wld}: dst={dst_v}")

    src_lines = _read_text(src_wld)
    src_spans = _index_rooms(src_lines)
    if src_v not in src_spans:
        raise SystemExit(f"Missing src vnum in {src_wld}: src={src_v}")

    src_room = _split_room(src_lines, src_spans[src_v])
    dst_room = _split_room(dst_lines, dst_spans[dst_v])

    pre_src, _exits_src, suf_src = _split_room_exits(src_room)
    pre_dst, exits_dst, _suf_dst = _split_room_exits(dst_room)

    if not (pre_src and pre_dst and ROOM_HEADER_RE.match(pre_src[0]) and ROOM_HEADER_RE.match(pre_dst[0])):
        raise SystemExit("Malformed room blocks (missing #vnum header)")

    new_room = [pre_dst[0]] + pre_src[1:] + exits_dst + suf_src

    # Ensure zone id matches destination zone when copying across zone files.
    zi = _find_zone_line_idx(new_room)
    parts = new_room[zi].split()
    if parts:
        parts[0] = str(int(dst_v // 100))
        new_room[zi] = " ".join(parts)

    dst_lines[dst_spans[dst_v].start : dst_spans[dst_v].end] = new_room

    if args.inplace:
        _write_text(wld, dst_lines)
    print(f"{wld}: copied_payload src={src_v} ({src_wld}) -> dst={dst_v} (preserved exits)")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_swap_payload(args: argparse.Namespace) -> int:
    """
    Swap non-exit payload (name/desc/zone-line/extra blocks) between two vnums, preserving each room's exits.
    Useful for relocating a feature without breaking the overland grid connectivity.
    """
    wld_dir = Path(args.wld_dir)
    a = int(args.a_vnum)
    b = int(args.b_vnum)

    wld_a = wld_dir / f"{a // 100}.wld"
    wld_b = wld_dir / f"{b // 100}.wld"

    lines_a = _read_text(wld_a)
    spans_a = _index_rooms(lines_a)
    if a not in spans_a:
        raise SystemExit(f"Missing vnum in {wld_a}: {a}")

    if wld_b == wld_a:
        lines_b = lines_a
        spans_b = spans_a
    else:
        lines_b = _read_text(wld_b)
        spans_b = _index_rooms(lines_b)
    if b not in spans_b:
        raise SystemExit(f"Missing vnum in {wld_b}: {b}")

    room_a = _split_room(lines_a, spans_a[a])
    room_b = _split_room(lines_b, spans_b[b])

    pre_a, exits_a, suf_a = _split_room_exits(room_a)
    pre_b, exits_b, suf_b = _split_room_exits(room_b)

    if not (pre_a and pre_b and ROOM_HEADER_RE.match(pre_a[0]) and ROOM_HEADER_RE.match(pre_b[0])):
        raise SystemExit("Malformed room blocks (missing #vnum header in prefix)")

    # Swap everything except exits and the vnum header line.
    new_a = [pre_a[0]] + pre_b[1:] + exits_a + suf_b
    new_b = [pre_b[0]] + pre_a[1:] + exits_b + suf_a

    # Ensure the zone-id field in the "<zone> <flags> <sector> <x> <y>" line
    # matches the file/vnum zone, even when swapping across zone files.
    def _fix_zone_id(room_lines: list[str], zone_id: int) -> list[str]:
        out = list(room_lines)
        zi = _find_zone_line_idx(out)
        parts = out[zi].split()
        if not parts:
            return out
        parts[0] = str(int(zone_id))
        out[zi] = " ".join(parts)
        return out

    new_a = _fix_zone_id(new_a, a // 100)
    new_b = _fix_zone_id(new_b, b // 100)

    if wld_a == wld_b:
        # Replace in reverse order by start index to keep spans valid.
        sp_a = spans_a[a]
        sp_b = spans_b[b]
        if sp_a.start < sp_b.start:
            first_v, first_sp, first_room = b, sp_b, new_b
            second_v, second_sp, second_room = a, sp_a, new_a
        else:
            first_v, first_sp, first_room = a, sp_a, new_a
            second_v, second_sp, second_room = b, sp_b, new_b
        lines_a[first_sp.start : first_sp.end] = first_room
        spans_a2 = _index_rooms(lines_a)
        lines_a[spans_a2[second_v].start : spans_a2[second_v].end] = second_room
        if args.inplace:
            _write_text(wld_a, lines_a)
    else:
        lines_a[spans_a[a].start : spans_a[a].end] = new_a
        lines_b[spans_b[b].start : spans_b[b].end] = new_b
        if args.inplace:
            _write_text(wld_a, lines_a)
            _write_text(wld_b, lines_b)

    print(f"swap_payload: a={a} ({wld_a}) <-> b={b} ({wld_b}) exits preserved")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_swap_zone_payload(args: argparse.Namespace) -> int:
    """
    Bulk swap of non-exit payloads between two zones (e.g., 539 <-> 540) for a set of cells,
    preserving exits in place.
    """
    wld_dir = Path(args.wld_dir)
    zone_a = int(args.zone_a)
    zone_b = int(args.zone_b)

    # Cells are 0..99 by default (vnum%100)
    cells = sorted(_parse_int_set(args.cells) if args.cells else set(range(0, 100)))
    if not cells:
        raise SystemExit("--cells resulted in an empty set")

    wld_a = wld_dir / f"{zone_a}.wld"
    wld_b = wld_dir / f"{zone_b}.wld"
    if not wld_a.exists():
        raise SystemExit(f"Missing zone file: {wld_a}")
    if not wld_b.exists():
        raise SystemExit(f"Missing zone file: {wld_b}")

    lines_a = _read_text(wld_a)
    lines_b = _read_text(wld_b)
    spans_a = _index_rooms(lines_a)
    spans_b = _index_rooms(lines_b)

    missing_a = [zone_a * 100 + c for c in cells if (zone_a * 100 + c) not in spans_a]
    missing_b = [zone_b * 100 + c for c in cells if (zone_b * 100 + c) not in spans_b]
    if missing_a:
        raise SystemExit(f"Missing vnums in {wld_a}: {missing_a[:10]}{'...' if len(missing_a) > 10 else ''}")
    if missing_b:
        raise SystemExit(f"Missing vnums in {wld_b}: {missing_b[:10]}{'...' if len(missing_b) > 10 else ''}")

    def _fix_zone_id(room_lines: list[str], zone_id: int) -> list[str]:
        out = list(room_lines)
        zi = _find_zone_line_idx(out)
        parts = out[zi].split()
        if parts:
            parts[0] = str(int(zone_id))
            out[zi] = " ".join(parts)
        return out

    new_rooms_a: dict[int, list[str]] = {}
    new_rooms_b: dict[int, list[str]] = {}

    for c in cells:
        a = zone_a * 100 + c
        b = zone_b * 100 + c
        room_a = _split_room(lines_a, spans_a[a])
        room_b = _split_room(lines_b, spans_b[b])

        pre_a, exits_a, suf_a = _split_room_exits(room_a)
        pre_b, exits_b, suf_b = _split_room_exits(room_b)

        if not (pre_a and pre_b and ROOM_HEADER_RE.match(pre_a[0]) and ROOM_HEADER_RE.match(pre_b[0])):
            raise SystemExit(f"Malformed room blocks while swapping a={a} b={b}")

        swapped_a = [pre_a[0]] + pre_b[1:] + exits_a + suf_b
        swapped_b = [pre_b[0]] + pre_a[1:] + exits_b + suf_a
        swapped_a = _fix_zone_id(swapped_a, zone_a)
        swapped_b = _fix_zone_id(swapped_b, zone_b)

        new_rooms_a[a] = swapped_a
        new_rooms_b[b] = swapped_b

    # Apply replacements in reverse order so offsets remain valid.
    for v, sp in sorted(spans_a.items(), key=lambda kv: kv[1].start, reverse=True):
        if v in new_rooms_a:
            lines_a[sp.start : sp.end] = new_rooms_a[v]
    for v, sp in sorted(spans_b.items(), key=lambda kv: kv[1].start, reverse=True):
        if v in new_rooms_b:
            lines_b[sp.start : sp.end] = new_rooms_b[v]

    print(f"swap_zone_payload: zone_a={zone_a} <-> zone_b={zone_b} cells={len(cells)} exits preserved")
    if args.inplace:
        _write_text(wld_a, lines_a)
        _write_text(wld_b, lines_b)
    else:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_set_sector(args: argparse.Namespace) -> int:
    wld = Path(args.wld_file)
    vnums = _parse_int_set(args.vnums)
    sector = int(args.sector)
    lines = _read_text(wld)
    spans = _index_rooms(lines)
    missing = sorted(v for v in vnums if v not in spans)
    if missing:
        raise SystemExit(f"Missing vnums in {wld}: {missing}")
    for v in sorted(vnums, reverse=True):
        sp = spans[v]
        room = _split_room(lines, sp)
        room2 = _set_room_name_desc_sector(room, name_line=None, desc_lines=None, sector=sector)
        lines[sp.start : sp.end] = room2
    if args.inplace:
        _write_text(wld, lines)
    print(f"{wld}: set_sector vnums={len(vnums)} sector={sector}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_restore_from_git(args: argparse.Namespace) -> int:
    repo = Path(args.repo_dir)
    wld = Path(args.wld_file)
    ref = args.ref
    vnums = _parse_int_set(args.vnums)

    # Relative path inside repo for git show
    try:
        rel = str(wld.relative_to(repo))
    except ValueError:
        raise SystemExit(f"--wld-file must be under --repo-dir (got {wld} not under {repo})")

    cur_lines = _read_text(wld)
    cur_spans = _index_rooms(cur_lines)
    missing = sorted(v for v in vnums if v not in cur_spans)
    if missing:
        raise SystemExit(f"Missing vnums in current file {wld}: {missing}")

    ref_lines = _git_show_file(repo, ref, rel)
    ref_spans = _index_rooms(ref_lines)
    missing_ref = sorted(v for v in vnums if v not in ref_spans)
    if missing_ref:
        raise SystemExit(f"Missing vnums in {ref}:{rel}: {missing_ref}")

    # Replace room blocks.
    for v in sorted(vnums, reverse=True):
        cur_sp = cur_spans[v]
        ref_room = _split_room(ref_lines, ref_spans[v])
        cur_lines[cur_sp.start : cur_sp.end] = ref_room
        # reindex as offsets change
        cur_spans = _index_rooms(cur_lines)

    if args.inplace:
        _write_text(wld, cur_lines)
    print(f"{wld}: restored_from_git ref={ref} vnums={len(vnums)}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_restore_exits_from_git(args: argparse.Namespace) -> int:
    repo = Path(args.repo_dir)
    wld = Path(args.wld_file)
    ref = args.ref
    vnums = _parse_int_set(args.vnums)

    try:
        rel = str(wld.relative_to(repo))
    except ValueError:
        raise SystemExit(f"--wld-file must be under --repo-dir (got {wld} not under {repo})")

    cur_lines = _read_text(wld)
    cur_spans = _index_rooms(cur_lines)
    missing = sorted(v for v in vnums if v not in cur_spans)
    if missing:
        raise SystemExit(f"Missing vnums in current file {wld}: {missing}")

    ref_lines = _git_show_file(repo, ref, rel)
    ref_spans = _index_rooms(ref_lines)
    missing_ref = sorted(v for v in vnums if v not in ref_spans)
    if missing_ref:
        raise SystemExit(f"Missing vnums in {ref}:{rel}: {missing_ref}")

    for v in sorted(vnums, reverse=True):
        cur_sp = cur_spans[v]
        cur_room = _split_room(cur_lines, cur_sp)
        ref_room = _split_room(ref_lines, ref_spans[v])

        cur_prefix, _, cur_suffix = _split_room_exits(cur_room)
        _, ref_exits, _ = _split_room_exits(ref_room)

        new_room = cur_prefix + ref_exits + cur_suffix
        cur_lines[cur_sp.start : cur_sp.end] = new_room
        cur_spans = _index_rooms(cur_lines)

    if args.inplace:
        _write_text(wld, cur_lines)
    print(f"{wld}: restored_exits_from_git ref={ref} vnums={len(vnums)}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def cmd_restore_payload_from_git(args: argparse.Namespace) -> int:
    """
    Restore only non-exit payload (name/desc/zone-line/suffix) from a git ref for specified vnums,
    preserving the current file's exits.
    """
    repo = Path(args.repo_dir)
    wld = Path(args.wld_file)
    ref = str(args.ref)
    vnums = _parse_int_set(args.vnums)

    # Derive repo-relative path for git show.
    try:
        rel = wld.relative_to(repo)
    except Exception:
        rel = Path(str(wld).lstrip("/"))

    cur_lines = _read_text(wld)
    cur_spans = _index_rooms(cur_lines)
    missing = sorted(v for v in vnums if v not in cur_spans)
    if missing:
        raise SystemExit(f"Missing vnums in current file {wld}: {missing}")

    ref_lines = _git_show_file(repo, ref, str(rel))
    ref_spans = _index_rooms(ref_lines)
    missing_ref = sorted(v for v in vnums if v not in ref_spans)
    if missing_ref:
        raise SystemExit(f"Missing vnums in {ref}:{rel}: {missing_ref}")

    for v in sorted(vnums, reverse=True):
        cur_sp = cur_spans[v]
        cur_room = _split_room(cur_lines, cur_sp)
        ref_room = _split_room(ref_lines, ref_spans[v])

        cur_prefix, cur_exits, _cur_suffix = _split_room_exits(cur_room)
        ref_prefix, _ref_exits, ref_suffix = _split_room_exits(ref_room)

        # Preserve vnum header + current exits, but take everything else from ref.
        new_room = [cur_prefix[0]] + ref_prefix[1:] + cur_exits + ref_suffix

        # Ensure zone id matches file/vnum zone.
        zi = _find_zone_line_idx(new_room)
        parts = new_room[zi].split()
        if parts:
            parts[0] = str(int(v // 100))
            new_room[zi] = " ".join(parts)

        cur_lines[cur_sp.start : cur_sp.end] = new_room
        cur_spans = _index_rooms(cur_lines)

    if args.inplace:
        _write_text(wld, cur_lines)
    print(f"{wld}: restored_payload_from_git ref={ref} vnums={len(vnums)}")
    if not args.inplace:
        print("NOTE: dry-run only (no files written). Pass --inplace to write changes.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Room-level operations for CircleMUD .wld files.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("disconnect", help="Disconnect vnums: remove inbound exits and clear exits on the room(s).")
    sp.add_argument("--wld-file", required=True)
    sp.add_argument("--vnums", required=True, help="Comma/range list (e.g. '46979,46989,46880' or '46979-46989')")
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_disconnect)

    sp = sub.add_parser("remove-exits-to", help="Remove exits pointing to specified vnums (does not modify target rooms).")
    sp.add_argument("--wld-file", required=True)
    sp.add_argument("--vnums", required=True, help="Comma/range list")
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_remove_exits_to)

    sp = sub.add_parser("copy-text", help="Copy room name+description from src vnum to dst vnum (preserve dst exits).")
    sp.add_argument("--wld-file", required=True)
    sp.add_argument("--src-wld-file", default=None, help="Optional: source .wld file (defaults to --wld-file).")
    sp.add_argument("--src-vnum", required=True)
    sp.add_argument("--dst-vnum", required=True)
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_copy_text)

    sp = sub.add_parser("copy-room", help="Copy full room block from src vnum to dst vnum (preserve dst vnum).")
    sp.add_argument("--wld-file", required=True)
    sp.add_argument("--src-wld-file", default=None, help="Optional: source .wld file (defaults to --wld-file).")
    sp.add_argument("--src-vnum", required=True)
    sp.add_argument("--dst-vnum", required=True)
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_copy_room)

    sp = sub.add_parser("copy-payload", help="Copy non-exit payload from src vnum to dst vnum (preserve dst exits).")
    sp.add_argument("--wld-file", required=True)
    sp.add_argument("--src-wld-file", default=None, help="Optional: source .wld file (defaults to --wld-file).")
    sp.add_argument("--src-vnum", required=True)
    sp.add_argument("--dst-vnum", required=True)
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_copy_payload)

    sp = sub.add_parser("swap-payload", help="Swap payload (name/desc/sector/tail) between two vnums; preserve exits.")
    sp.add_argument("--wld-dir", required=True, help="Directory containing <zone>.wld files")
    sp.add_argument("--a-vnum", required=True)
    sp.add_argument("--b-vnum", required=True)
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_swap_payload)

    sp = sub.add_parser(
        "swap-zone-payload",
        help="Swap payloads between two zones for a set of cells (preserve exits).",
    )
    sp.add_argument("--wld-dir", required=True, help="Directory containing <zone>.wld files")
    sp.add_argument("--zone-a", required=True, dest="zone_a")
    sp.add_argument("--zone-b", required=True, dest="zone_b")
    sp.add_argument("--cells", default="", help="Cells to swap (e.g. 0-99 or 0,1,2). Default: 0-99.")
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_swap_zone_payload)

    sp = sub.add_parser("set-sector", help="Set sector type number on specified vnums (does not change text).")
    sp.add_argument("--wld-file", required=True)
    sp.add_argument("--vnums", required=True)
    sp.add_argument("--sector", required=True, help="Sector type integer from MUD (e.g. 6 for water).")
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_set_sector)

    sp = sub.add_parser("restore-from-git", help="Restore specified vnums from a git ref for this file.")
    sp.add_argument("--repo-dir", required=True, help="Repo root containing .git (e.g. .../MM32/lib)")
    sp.add_argument("--wld-file", required=True, help="Absolute or repo-relative path to <zone>.wld")
    sp.add_argument("--ref", required=True, help="Git ref (e.g. 'builder')")
    sp.add_argument("--vnums", required=True, help="Comma/range list")
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_restore_from_git)

    sp = sub.add_parser("restore-exits-from-git", help="Restore only exit blocks from a git ref for specified vnums.")
    sp.add_argument("--repo-dir", required=True, help="Repo root containing .git (e.g. .../MM32/lib)")
    sp.add_argument("--wld-file", required=True, help="Absolute or repo-relative path to <zone>.wld")
    sp.add_argument("--ref", required=True, help="Git ref (e.g. 'builder')")
    sp.add_argument("--vnums", required=True, help="Comma/range list")
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_restore_exits_from_git)

    sp = sub.add_parser(
        "restore-payload-from-git",
        help="Restore only non-exit payload from a git ref for specified vnums (preserve current exits).",
    )
    sp.add_argument("--repo-dir", required=True, help="Repo root containing .git (e.g. .../MM32/lib)")
    sp.add_argument("--wld-file", required=True, help="Absolute or repo-relative path to <zone>.wld")
    sp.add_argument("--ref", required=True, help="Git ref (e.g. 'builder')")
    sp.add_argument("--vnums", required=True, help="Comma/range list")
    sp.add_argument("--inplace", action="store_true")
    sp.set_defaults(func=cmd_restore_payload_from_git)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

