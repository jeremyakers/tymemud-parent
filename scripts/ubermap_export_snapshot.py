#!/usr/bin/env python3
"""
Snapshot Ubermap exports (TSVs + SVG) to timestamped files so humans can reliably open the exact artifacts.

No external dependencies.

Example:
  scripts/ubermap_export_snapshot.py \
    --lib /home/jeremy/cursor/tymemud/_agent_work/ubermap_agent/MM32/lib \
    --out /home/jeremy/cursor/tymemud/tmp \
    --prefix ubermap_468_640_pluslinked
"""

from __future__ import annotations

import argparse
import os
import shutil
import time
from typing import List


def snapshot(lib_dir: str, out_dir: str, prefix: str) -> List[str]:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    os.makedirs(out_dir, exist_ok=True)

    candidates = [
        f"{prefix}_allz.svg",
        f"{prefix}_z0.svg",
        f"ubermap_coords_468_640_pluslinked.tsv",
        f"ubermap_edges_468_640_pluslinked.tsv",
        f"ubermap_direction_mismatch_classified_468_640_pluslinked.tsv",
        f"ubermap_direction_mismatch_edges_468_640_pluslinked_overland.tsv",
        f"ubermap_scope_zones_468_640_pluslinked.tsv",
        f"ubermap_component_summary_468_640_pluslinked.tsv",
        f"ubermap_duplicate_centers_468_640_pluslinked.tsv",
        f"ubermap_city_bypass_report_468_640_pluslinked.tsv",
    ]

    written: List[str] = []
    for name in candidates:
        src = os.path.join(lib_dir, name)
        if not os.path.exists(src):
            continue
        base, ext = os.path.splitext(name)
        dst = os.path.join(out_dir, f"{base}_{stamp}{ext}")
        shutil.copy2(src, dst)
        written.append(dst)

    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="Snapshot Ubermap exports to timestamped copies")
    ap.add_argument("--lib", required=True, help="MM32/lib directory containing ubermap exports")
    ap.add_argument("--out", required=True, help="Output directory for timestamped copies")
    ap.add_argument(
        "--prefix",
        default="ubermap_468_640_pluslinked",
        help="SVG prefix (default: ubermap_468_640_pluslinked)",
    )
    args = ap.parse_args()

    written = snapshot(args.lib, args.out, args.prefix)
    for p in written:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

