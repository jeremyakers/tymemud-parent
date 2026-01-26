#!/usr/bin/env python3
"""
Find exits that point to zone numbers with no corresponding .wld file.

This answers: "are missing zone numbers actionable?" (i.e., does any exit dest
reference them), without being fooled by <key_vnum> fields inside exit triples.

Output TSV:
  src_zone  src_vnum  dir  dest_vnum  dest_zone  dest_wld_exists  src_wld
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WLD_DIR = ROOT / "MM32/lib/world/wld"

ROOM_HDR_RE = re.compile(r"^#(\d+)\s*$")
EXIT_HDR_RE = re.compile(r"^D([0-5])\s*$")


def consume_tilde_string(lines: list[str], start: int) -> int:
    """Consume 1+ lines until a line ends with '~' (inclusive). Return next index."""
    i = start
    while i < len(lines):
        if lines[i].endswith("~"):
            return i + 1
        i += 1
    return i


def iter_exit_dests(wld_path: Path) -> list[tuple[int, int, int, int]]:
    """
    Return list of (src_vnum, dir, dest_vnum, dest_zone) for exits in a .wld.
    """
    b = wld_path.read_bytes()
    raw = b.decode("latin-1", errors="replace")
    lines = raw.splitlines()

    out: list[tuple[int, int, int, int]] = []
    cur_vnum: int | None = None
    i = 0
    while i < len(lines):
        m = ROOM_HDR_RE.match(lines[i])
        if m:
            cur_vnum = int(m.group(1))
            i += 1
            continue

        em = EXIT_HDR_RE.match(lines[i])
        if em and cur_vnum is not None:
            d = int(em.group(1))
            j = consume_tilde_string(lines, i + 1)  # desc
            j = consume_tilde_string(lines, j)  # keywords
            if j < len(lines):
                parts = lines[j].split()
                # triple: "<flags> <key> <dest>"
                if len(parts) >= 3 and parts[-1].lstrip("-").isdigit():
                    dest = int(parts[-1])
                    # dest -1 means "no destination" (unlinked exit); not a missing zone file.
                    if dest >= 0:
                        out.append((cur_vnum, d, dest, dest // 100))
            i = j + 1
            continue

        i += 1

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, default=DEFAULT_WLD_DIR)
    ap.add_argument("--max-zone", type=int, default=999)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dest-zone", type=int, default=None, help="Only report rows where dest_zone equals this value.")
    ap.add_argument("--src-zone", type=int, default=None, help="Only scan a single src zone (file).")
    ap.add_argument(
        "--include-existing",
        action="store_true",
        help="Include destinations whose zone file exists (default: only report missing-zone destinations).",
    )
    args = ap.parse_args()

    wld_dir = args.wld_dir.resolve()
    existing = {int(p.stem) for p in wld_dir.glob("*.wld") if p.stem.isdigit()}

    rows: list[str] = ["src_zone\tsrc_vnum\tdir\tdest_vnum\tdest_zone\tdest_wld_exists\tsrc_wld"]
    missing_count = 0

    for p in sorted(wld_dir.glob("*.wld")):
        if not p.stem.isdigit():
            continue
        src_zone = int(p.stem)
        if src_zone > args.max_zone:
            continue
        if args.src_zone is not None and src_zone != args.src_zone:
            continue
        for src_vnum, d, dest, dest_zone in iter_exit_dests(p):
            if args.dest_zone is not None and dest_zone != args.dest_zone:
                continue
            exists = dest_zone in existing
            if not exists:
                missing_count += 1
            if args.include_existing or (not exists):
                rows.append(
                    f"{src_zone}\t{src_vnum}\tD{d}\t{dest}\t{dest_zone}\t{'yes' if exists else 'NO'}\t{p.name}"
                )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {args.out} rows={len(rows)-1} missing_zone_dests={missing_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

