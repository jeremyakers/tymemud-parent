#!/usr/bin/env python3
"""
Sanity-audit world .wld files for common boot-breaking / acceptance issues.

Checks (per file):
- Contains 'undefined~'
- Contains 'The Open World~'
- Contains nonprintable control bytes (excluding \\n, \\r, \\t)
- Ends with '$~\\n' (required: newline after terminator)

Outputs a TSV report:
  zone  issue  detail

Exit code:
- 0 if no issues
- 1 if any issues
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WLD_DIR = ROOT / "MM32/lib/world/wld"


def has_nonprintables(data: bytes) -> list[int]:
    bad: list[int] = []
    for b in data:
        if b in (9, 10, 13):  # tab, lf, cr
            continue
        if b < 32:
            bad.append(b)
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wld-dir", type=Path, default=DEFAULT_WLD_DIR)
    ap.add_argument("--zones-csv", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    zones = [int(x) for x in args.zones_csv.read_text().strip().split(",") if x]

    rows: list[str] = ["zone\tissue\tdetail"]
    for z in zones:
        wld = args.wld_dir / f"{z}.wld"
        if not wld.exists():
            rows.append(f"{z}\tmissing-file\t{wld}")
            continue
        data = wld.read_bytes()
        text = data.decode("latin-1", errors="replace")

        if "undefined~" in text:
            rows.append(f"{z}\tundefined~\tcontains undefined~")
        if "The Open World~" in text:
            rows.append(f"{z}\topen-world-placeholder\tcontains The Open World~")

        bad = has_nonprintables(data)
        if bad:
            uniq = sorted(set(bad))
            rows.append(f"{z}\tnonprintable\tbytes={','.join(str(b) for b in uniq)}")

        if not data.endswith(b"$~\n"):
            # Be explicit: many past failures were missing final newline after $~
            tail = data[-40:].decode("latin-1", errors="replace").replace("\n", "\\n")
            rows.append(f"{z}\tbad-terminator\tendswith={tail}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(rows) + "\n", encoding="utf-8")

    issues = len(rows) - 1
    print(f"wrote {args.out} issues={issues}")
    return 0 if issues == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

