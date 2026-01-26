#!/usr/bin/env python3
"""
Harvest candidate room payloads for mismatched overland vnums (zones 537–640).

This is a READ/REPORT tool:
- does not modify any files
- reads:
  - expected terrain TSV (ubermap.jpg derived)
  - mismatch TSV for a single zone (from overland_mismatch_report_537_640.py)
  - worktree + reference .wld files
  - git history for the zone file (optional; defaults to last N commits touching that file)

Outputs:
- a TSV of candidates per vnum per source (worktree/ref/git:<sha>)

This tool is vnum-keyed (no keyword searching), so color codes cannot hide rooms.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Payload:
    vnum: int
    title_raw: str
    sector_line: str
    sector: int | None


def _parse_sector(sector_line: str) -> int | None:
    parts = sector_line.split()
    if len(parts) < 3:
        return None
    try:
        return int(parts[2])
    except Exception:
        return None


def parse_wld_payloads(txt: str, wanted: set[int]) -> dict[int, Payload]:
    out: dict[int, Payload] = {}
    lines = txt.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not (line.startswith("#") and line[1:].isdigit()):
            i += 1
            continue
        vnum = int(line[1:])
        if vnum not in wanted:
            i += 1
            continue
        if i + 1 >= len(lines):
            break
        title = lines[i + 1]

        # Skip description to terminator '~'
        j = i + 2
        while j < len(lines):
            l = lines[j]
            if l.strip() == "~":
                j += 1
                break
            if l.endswith("~"):
                j += 1
                break
            j += 1
        if j >= len(lines):
            break
        sector_line = lines[j].strip()
        out[vnum] = Payload(vnum=vnum, title_raw=title, sector_line=sector_line, sector=_parse_sector(sector_line))
        i = j + 1
    return out


def git_show(repo: Path, ref: str, relpath: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{relpath}"],
        check=False,
        capture_output=True,
        text=True,
        encoding="latin-1",
        errors="replace",
    )
    if cp.returncode != 0:
        return ""
    return cp.stdout


def git_recent_commits(repo: Path, relpath: str, n: int) -> list[str]:
    cp = subprocess.run(
        ["git", "-C", str(repo), "log", "--format=%H", f"-n{n}", "--", relpath],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]


def _load_expected(expected_tsv: Path) -> dict[int, tuple[str, int]]:
    # vnum -> (expected_feature, expected_sector)
    feat2sect = {
        "plains": 2,
        "forest_light": 3,
        "forest_dense": 3,
        "hills": 4,
        "dragonmount": 5,
        "mountain": 5,
        # Initial pass; refined later if needed.
        "river": 6,
        "road": 11,
        "town": 1,
        "insert": 1,
    }
    out: dict[int, tuple[str, int]] = {}
    with expected_tsv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            z = int(row["zone"])
            cell = int(row["cell"])
            feat = row["feature"]
            if feat not in feat2sect:
                continue
            vnum = z * 100 + cell
            out[vnum] = (feat, feat2sect[feat])
    return out


def _load_mismatch_vnums(mismatch_zone_tsv: Path) -> list[int]:
    vnums: list[int] = []
    with mismatch_zone_tsv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            vnums.append(int(row["vnum"]))
    return vnums


def _read_file(path: Path) -> str:
    return path.read_text(encoding="latin-1", errors="replace")


def iter_sources(
    repo: Path,
    zone: int,
    worktree_wld_dir: Path,
    ref_wld_dir: Path,
    git_refs: Iterable[str],
) -> Iterable[tuple[str, str]]:
    relpath = f"world/wld/{zone}.wld"
    # Worktree and reference are read from filesystem paths.
    yield ("worktree", _read_file(worktree_wld_dir / f"{zone}.wld"))
    yield ("reference", _read_file(ref_wld_dir / f"{zone}.wld"))
    for ref in git_refs:
        txt = git_show(repo, ref, relpath)
        if txt:
            yield (f"git:{ref}", txt)


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvest candidate payloads for a mismatch zone")
    ap.add_argument("--repo-dir", type=Path, required=True, help="git repo root (MM32/lib)")
    ap.add_argument("--zone", type=int, required=True)
    ap.add_argument("--expected-terrain-tsv", type=Path, required=True)
    ap.add_argument("--mismatch-zone-tsv", type=Path, required=True)
    ap.add_argument("--worktree-wld-dir", type=Path, required=True)
    ap.add_argument("--ref-wld-dir", type=Path, required=True)
    ap.add_argument("--git-ref", action="append", default=None, help="extra git ref to include (repeatable)")
    ap.add_argument("--git-recent", type=int, default=8, help="include N most recent commits touching this zone file")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    expected = _load_expected(args.expected_terrain_tsv)
    vnums = _load_mismatch_vnums(args.mismatch_zone_tsv)
    wanted = set(vnums)

    relpath = f"world/wld/{args.zone}.wld"
    refs: list[str] = []
    # Recent commits for this file.
    refs.extend(git_recent_commits(args.repo_dir, relpath, args.git_recent))
    # Extra explicit refs.
    if args.git_ref:
        for r in args.git_ref:
            refs.append(r)
    # Deduplicate while preserving order.
    seen: set[str] = set()
    uniq_refs: list[str] = []
    for r in refs:
        if r in seen:
            continue
        seen.add(r)
        uniq_refs.append(r)

    rows: list[list[str]] = []
    rows.append(
        [
            "vnum",
            "cell",
            "expected_feature",
            "expected_sector",
            "source",
            "sector",
            "sector_line",
            "title_raw",
            "matches_expected_sector",
        ]
    )

    for source, txt in iter_sources(
        repo=args.repo_dir,
        zone=args.zone,
        worktree_wld_dir=args.worktree_wld_dir,
        ref_wld_dir=args.ref_wld_dir,
        git_refs=uniq_refs,
    ):
        payloads = parse_wld_payloads(txt, wanted)
        for vnum in vnums:
            exp = expected.get(vnum)
            if not exp:
                continue
            feat, exp_sector = exp
            p = payloads.get(vnum)
            if not p:
                continue
            matches = p.sector is not None and p.sector == exp_sector
            rows.append(
                [
                    str(vnum),
                    f"{vnum % 100:02d}",
                    feat,
                    str(exp_sector),
                    source,
                    "" if p.sector is None else str(p.sector),
                    p.sector_line.replace("\t", " "),
                    p.title_raw.replace("\t", " "),
                    "1" if matches else "0",
                ]
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8")
    print(f"wrote {args.out} rows={len(rows)-1} refs={len(uniq_refs)} vnums={len(vnums)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

