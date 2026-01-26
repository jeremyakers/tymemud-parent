#!/usr/bin/env python3
"""
Apply remaining sector-only fixes after payload restoration.

Reads a mismatch TSV produced by scripts/ubermap_expected_vs_world_sector.py and
sets the sector number on those vnums to match expected_sector.

This is intentionally minimal:
- sector-only (no title/desc changes)
- preserves exits
- skips expected features that represent city inserts/towns unless explicitly enabled
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from collections import defaultdict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply sector-only fixes from mismatch TSV")
    ap.add_argument("--mismatch-tsv", type=Path, required=True)
    ap.add_argument("--wld-dir", type=Path, required=True)
    ap.add_argument("--include-inserts", action="store_true", help="Also apply expected_sector for town/insert rows")
    ap.add_argument("--apply", action="store_true", help="Write changes (otherwise dry-run summary only)")
    args = ap.parse_args()

    # zone -> sector -> set[vnum]
    work: dict[int, dict[int, set[int]]] = defaultdict(lambda: defaultdict(set))
    with args.mismatch_tsv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            feat = row.get("feature") or ""
            if (feat in ("town", "insert")) and not args.include_inserts:
                continue
            vnum = int(row["vnum"])
            z = int(row["zone"])
            exp_sector = int(row["expected_sector"])
            work[z][exp_sector].add(vnum)

    total = sum(len(vs) for z in work.values() for vs in z.values())
    print(f"pending_sector_fixes={total} zones={len(work)}")
    for z in sorted(work):
        parts = []
        for sect in sorted(work[z]):
            parts.append(f"{sect}:{len(work[z][sect])}")
        print(f"  zone {z}: " + ", ".join(parts))

    if not args.apply:
        return 0

    wld_ops = Path(__file__).resolve().parent / "wld_room_ops.py"
    for z in sorted(work):
        wld_file = args.wld_dir / f"{z}.wld"
        for sect, vnums in sorted(work[z].items()):
            spec = ",".join(str(v) for v in sorted(vnums))
            subprocess.run(
                [
                    "python",
                    str(wld_ops),
                    "set-sector",
                    "--wld-file",
                    str(wld_file),
                    "--vnums",
                    spec,
                    "--sector",
                    str(sect),
                    "--inplace",
                ],
                check=True,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

