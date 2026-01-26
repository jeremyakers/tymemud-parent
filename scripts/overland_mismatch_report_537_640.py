#!/usr/bin/env python3
"""
Generate mismatch reports for overland zones 537–640.

Inputs:
- expected terrain TSV from scripts/ubermap_jpg_extract_cells.py --mode terrain
- world snapshots from scripts/overland_audit_537_640.py (worktree + reference)

Outputs:
- per-zone mismatch TSVs in an output directory
- summary TSV

This tool is READ-ONLY with respect to .wld files.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


FEATURE_TO_EXPECTED_SECTOR: dict[str, int | None] = {
    "plains": 2,  # SECT_FIELD
    "forest_light": 3,  # SECT_FOREST
    "forest_dense": 3,  # SECT_FOREST
    "hills": 4,  # SECT_HILLS
    "dragonmount": 5,  # SECT_MOUNTAIN
    "mountain": 5,  # SECT_MOUNTAIN
    # Initial pass: treat riverway as SECT_WATER_SWIM; we can refine 6 vs 7 later by local convention.
    "river": 6,
    "road": 11,  # SECT_MAIN_ROAD
    "town": 1,  # SECT_CITY
    "insert": 1,  # SECT_CITY
    "nothing": None,
    "unknown": None,
}


def _load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Mismatch report generator for zones 537–640")
    ap.add_argument("--expected-terrain-tsv", type=Path, required=True)
    ap.add_argument("--snapshot-worktree", type=Path, required=True)
    ap.add_argument("--snapshot-reference", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    expected_rows = _load_tsv(args.expected_terrain_tsv)
    cur_rows = _load_tsv(args.snapshot_worktree)
    ref_rows = _load_tsv(args.snapshot_reference)

    cur = {int(r["vnum"]): r for r in cur_rows}
    ref = {int(r["vnum"]): r for r in ref_rows}

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    by_zone: dict[int, list[list[str]]] = {}

    summary: list[list[str]] = []
    summary.append(["zone", "mismatches", "sector_mismatches", "style_mismatches", "special_tiles"])

    for er in expected_rows:
        z = int(er["zone"])
        if not (537 <= z <= 640):
            continue
        cell = int(er["cell"])
        feat = er["feature"]
        vnum = z * 100 + cell
        exp_sector = FEATURE_TO_EXPECTED_SECTOR.get(feat)
        if exp_sector is None:
            continue

        c = cur.get(vnum)
        if not c:
            continue
        r = ref.get(vnum)

        cur_sector = int(c["sector"]) if (c.get("sector") or "").strip() else None
        ref_sector = int(r["sector"]) if r and (r.get("sector") or "").strip() else None

        sector_mismatch = cur_sector is not None and cur_sector != exp_sector

        # Lightweight style mismatch checks (expanded later during candidate selection):
        t = (c.get("title_stripped") or "").lower()
        style_mismatch = False
        if feat == "river" and ("river" not in t and "erinin" not in t):
            style_mismatch = True
        if feat == "road" and ("road" not in t and "jangai" not in t and "caemlyn" not in t):
            style_mismatch = True
        if feat in ("forest_light", "forest_dense") and any(k in t for k in ("plains", "grass", "expanse", "open")):
            style_mismatch = True

        # Special tile heuristic: any non-overland exit suggests portals/bridges/city inserts.
        special = int(c.get("exit_non_overland_count") or "0") > 0

        if not (sector_mismatch or style_mismatch):
            continue

        if z not in by_zone:
            by_zone[z] = [[
                "vnum",
                "cell",
                "expected_feature",
                "expected_sector",
                "cur_sector",
                "ref_sector",
                "cur_exit_non_overland_count",
                "special_tile",
                "cur_title_raw",
                "cur_title_stripped",
                "ref_title_raw",
                "ref_title_stripped",
                "sector_mismatch",
                "style_mismatch",
            ]]

        by_zone[z].append([
            str(vnum),
            f"{cell:02d}",
            feat,
            str(exp_sector),
            "" if cur_sector is None else str(cur_sector),
            "" if ref_sector is None else str(ref_sector),
            str(c.get("exit_non_overland_count") or ""),
            "1" if special else "0",
            (c.get("title_raw") or "").replace("\t", " "),
            (c.get("title_stripped") or "").replace("\t", " "),
            (r.get("title_raw") or "").replace("\t", " ") if r else "",
            (r.get("title_stripped") or "").replace("\t", " ") if r else "",
            "1" if sector_mismatch else "0",
            "1" if style_mismatch else "0",
        ])

    # Write per-zone.
    for z, rows in sorted(by_zone.items()):
        out = out_dir / f"mismatches_{z}.tsv"
        out.write_text("\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8")

        mismatches = len(rows) - 1
        sector_m = sum(1 for r in rows[1:] if r[-2] == "1")
        style_m = sum(1 for r in rows[1:] if r[-1] == "1")
        special_n = sum(1 for r in rows[1:] if r[7] == "1")
        summary.append([str(z), str(mismatches), str(sector_m), str(style_m), str(special_n)])

    (out_dir / "mismatch_summary.tsv").write_text(
        "\n".join("\t".join(r) for r in summary) + "\n", encoding="utf-8"
    )
    print(f"wrote {out_dir} zones={len(by_zone)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

