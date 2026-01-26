#!/usr/bin/env python3
"""
Small utilities for debugging Ubermap TSV exports (coords/edges/bypass).

Use this instead of pasting long Python into the terminal.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict, deque
from pathlib import Path


def load_edges(edges_tsv: Path, *, undirected: bool) -> dict[int, set[int]]:
    g: dict[int, set[int]] = defaultdict(set)
    with edges_tsv.open() as f:
        r = csv.reader(f, delimiter="\t")
        next(r, None)
        for frm, _dir, to in r:
            a = int(frm)
            b = int(to)
            g[a].add(b)
            if undirected:
                g[b].add(a)
    return g


def bfs_path(g: dict[int, set[int]], src: int, dst: int) -> list[int] | None:
    q: deque[int] = deque([src])
    prev: dict[int, int | None] = {src: None}
    while q:
        v = q.popleft()
        if v == dst:
            break
        for n in g.get(v, ()):
            if n not in prev:
                prev[n] = v
                q.append(n)
    if dst not in prev:
        return None
    path: list[int] = []
    cur: int | None = dst
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def cmd_shortest(args: argparse.Namespace) -> int:
    g = load_edges(args.edges, undirected=args.undirected)
    p = bfs_path(g, args.src, args.dst)
    if not p:
        print("NO PATH")
        return 2
    print("len", len(p) - 1, "path", p)
    return 0


def cmd_missing_range(args: argparse.Namespace) -> int:
    present: set[int] = set()
    with args.coords.open() as f:
        r = csv.reader(f, delimiter="\t")
        next(r, None)
        for row in r:
            present.add(int(row[0]))
    missing = [v for v in range(args.start, args.end + 1) if v not in present]
    print("missing_count", len(missing))
    print("missing", missing[: args.limit])
    return 0


def cmd_coords(args: argparse.Namespace) -> int:
    want = set(args.vnum)
    rows = {}
    with args.coords.open() as f:
        r = csv.reader(f, delimiter="\t")
        hdr = next(r, None)
        if not hdr:
            raise SystemExit("empty coords")
        for row in r:
            v = int(row[0])
            if v in want:
                rows[v] = row
    for v in args.vnum:
        row = rows.get(v)
        if not row:
            print(v, "MISSING")
        else:
            # vnum, x, y, z, zone, sector, width, height, mapx, mapy, mapz, ...
            print(v, "x", row[1], "y", row[2], "z", row[3], "zone", row[4], "sector", row[5], "mapx", row[8], "mapy", row[9])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Ubermap TSV debug helpers")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("shortest", help="Shortest path between two vnums using edges TSV")
    sp.add_argument("--edges", type=Path, required=True)
    sp.add_argument("--src", type=int, required=True)
    sp.add_argument("--dst", type=int, required=True)
    sp.add_argument("--undirected", action="store_true", help="Treat edges as undirected (recommended for connectivity/bypass)")
    sp.set_defaults(func=cmd_shortest)

    sp = sub.add_parser("missing-range", help="Which vnums in [start,end] are missing from coords TSV")
    sp.add_argument("--coords", type=Path, required=True)
    sp.add_argument("--start", type=int, required=True)
    sp.add_argument("--end", type=int, required=True)
    sp.add_argument("--limit", type=int, default=50)
    sp.set_defaults(func=cmd_missing_range)

    sp = sub.add_parser("coords", help="Print key coord fields for vnums from coords TSV")
    sp.add_argument("--coords", type=Path, required=True)
    sp.add_argument("vnum", nargs="+", type=int)
    sp.set_defaults(func=cmd_coords)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

