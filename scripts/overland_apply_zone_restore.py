#!/usr/bin/env python3
"""
Apply surgical payload restorations for a single overland zone file.

Uses:
- candidates_<zone>.tsv from scripts/overland_candidate_harvest.py
- mismatch_<zone>.tsv from scripts/overland_mismatch_report_537_640.py

Strategy (deterministic, vnum-keyed):
- Prefer reference payloads that match expected sector, unless the title looks like a placeholder/unused marker.
- Otherwise prefer the first (most recent) git payload that matches expected sector.
- Preserve current exits always by using:
  - scripts/wld_room_ops.py copy-payload (for reference file sources)
  - scripts/wld_room_ops.py restore-payload-from-git (for git sources)

Writes a decision log TSV and then applies changes.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from collections import defaultdict
from pathlib import Path


BAD_TITLE_PREFIXES = (
    "unused",
    "!unused",
    "disconnect me",
)


def _looks_bad_title(title_raw: str) -> bool:
    s = title_raw.strip().lower()
    return any(s.startswith(p) for p in BAD_TITLE_PREFIXES)


def _load_candidates(path: Path) -> dict[int, list[dict[str, str]]]:
    by_v: dict[int, list[dict[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            by_v[int(row["vnum"])].append(row)
    return by_v


def _load_mismatches(path: Path) -> list[int]:
    vnums: list[int] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            vnums.append(int(row["vnum"]))
    return vnums


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply per-zone payload restore using harvested candidates")
    ap.add_argument("--zone", type=int, required=True)
    ap.add_argument("--candidates-tsv", type=Path, required=True)
    ap.add_argument("--mismatch-tsv", type=Path, required=True)
    ap.add_argument("--repo-dir", type=Path, required=True, help="MM32/lib git repo root (worktree)")
    ap.add_argument("--worktree-wld-file", type=Path, required=True)
    ap.add_argument("--ref-wld-file", type=Path, required=True)
    ap.add_argument("--decision-log", type=Path, required=True)
    ap.add_argument("--apply", action="store_true", help="Actually write changes (otherwise dry-run decisions only)")
    args = ap.parse_args()

    by_v = _load_candidates(args.candidates_tsv)
    vnums = _load_mismatches(args.mismatch_tsv)

    decisions: list[list[str]] = []
    decisions.append(["vnum", "expected_feature", "expected_sector", "chosen_source", "chosen_sector", "chosen_title_raw"])

    # Group by chosen git ref for batch application.
    git_batches: dict[str, list[int]] = defaultdict(list)
    ref_vnums: list[int] = []

    for v in vnums:
        cand = by_v.get(v, [])
        if not cand:
            continue

        exp_feat = cand[0]["expected_feature"]
        exp_sector = cand[0]["expected_sector"]

        # Find reference candidate if it matches sector and isn't obviously placeholder.
        ref_rows = [r for r in cand if r["source"] == "reference" and r["matches_expected_sector"] == "1"]
        if ref_rows and not _looks_bad_title(ref_rows[0]["title_raw"]):
            chosen = ref_rows[0]
            ref_vnums.append(v)
            decisions.append([str(v), exp_feat, exp_sector, "reference", chosen.get("sector", ""), chosen.get("title_raw", "")])
            continue

        # Otherwise choose the first matching git candidate (harvester orders git refs most-recent-first).
        git_rows = [r for r in cand if r["source"].startswith("git:") and r["matches_expected_sector"] == "1"]
        git_rows = [r for r in git_rows if not _looks_bad_title(r.get("title_raw", ""))]
        if git_rows:
            chosen = git_rows[0]
            git_ref = chosen["source"][4:]
            git_batches[git_ref].append(v)
            decisions.append([str(v), exp_feat, exp_sector, chosen["source"], chosen.get("sector", ""), chosen.get("title_raw", "")])
            continue

        # Fallback: reference even if placeholder (still better sector), else do nothing.
        if ref_rows:
            chosen = ref_rows[0]
            ref_vnums.append(v)
            decisions.append([str(v), exp_feat, exp_sector, "reference(placeholder_ok)", chosen.get("sector", ""), chosen.get("title_raw", "")])
            continue

        decisions.append([str(v), exp_feat, exp_sector, "SKIP", "", ""])

    args.decision_log.parent.mkdir(parents=True, exist_ok=True)
    args.decision_log.write_text("\n".join("\t".join(r) for r in decisions) + "\n", encoding="utf-8")
    print(f"wrote {args.decision_log} decisions={len(decisions)-1} ref={len(ref_vnums)} git_batches={len(git_batches)}")

    if not args.apply:
        return 0

    # Apply reference payload restores (one-by-one; copy-payload is file-based).
    for v in ref_vnums:
        subprocess.run(
            [
                "python",
                str(Path(__file__).resolve().parent / "wld_room_ops.py"),
                "copy-payload",
                "--wld-file",
                str(args.worktree_wld_file),
                "--src-wld-file",
                str(args.ref_wld_file),
                "--src-vnum",
                str(v),
                "--dst-vnum",
                str(v),
                "--inplace",
            ],
            check=True,
        )

    # Apply git payload restores in batches per ref (more efficient).
    for ref, vs in git_batches.items():
        spec = ",".join(str(v) for v in sorted(vs))
        subprocess.run(
            [
                "python",
                str(Path(__file__).resolve().parent / "wld_room_ops.py"),
                "restore-payload-from-git",
                "--repo-dir",
                str(args.repo_dir),
                "--wld-file",
                str(args.worktree_wld_file),
                "--ref",
                ref,
                "--vnums",
                spec,
                "--inplace",
            ],
            check=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

