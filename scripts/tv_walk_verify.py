#!/usr/bin/env python3
"""
Non-interactive Tar Valon area verification walk.

Connects via telnet, logs in, then runs a scripted sequence of commands
to verify that villages/bridges/river/road rooms "read correctly" after
overland realignment work.

Output: a plain transcript file (raw server output) + a command log.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import telnetlib
import time
from pathlib import Path


PAGER_MARKERS = ("-- More --", "Press RETURN", "Press Return", "press return", "Hit return", "hit return")


def _read_available(tn: telnetlib.Telnet) -> str:
    try:
        data = tn.read_very_eager()
    except EOFError:
        return ""
    if not data:
        return ""
    return data.decode("utf-8", errors="ignore")


def _wait_for(tn: telnetlib.Telnet, needle: str, timeout_s: float) -> str:
    buf = ""
    start = time.time()
    while time.time() - start < timeout_s:
        buf += _read_available(tn)
        if needle in buf:
            return buf
        if any(m in buf for m in PAGER_MARKERS):
            tn.write(b"\n")
        time.sleep(0.05)
    return buf


def _send(tn: telnetlib.Telnet, cmd: str) -> None:
    tn.write(cmd.encode("ascii", errors="ignore") + b"\n")


def _send_and_collect(tn: telnetlib.Telnet, cmd: str, wait_s: float = 0.35) -> str:
    _send(tn, cmd)
    time.sleep(wait_s)
    out = _read_available(tn)
    for _ in range(12):
        if any(m in out for m in PAGER_MARKERS):
            tn.write(b"\n")
        time.sleep(0.08)
        out += _read_available(tn)
    return out


def _section(title: str) -> str:
    return f"\n\n===== {title} =====\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Walk/verify Tar Valon bridge/village/road/river rooms.")
    ap.add_argument("--host", default=os.environ.get("TYME_SIT_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("TYME_SIT_PORT", "6969")))
    ap.add_argument("--user", default=os.environ.get("TYME_SIT_USER", "testimp"))
    ap.add_argument("--password", default=os.environ.get("TYME_SIT_PASS", "testing123"))
    ap.add_argument("--out", type=Path, required=True, help="Transcript output path")
    ap.add_argument("--cmdlog", type=Path, required=True, help="Command log output path")
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.cmdlog.parent.mkdir(parents=True, exist_ok=True)

    tn = telnetlib.Telnet(args.host, args.port, timeout=10)
    time.sleep(0.5)

    # Login
    _wait_for(tn, "known?", timeout_s=12.0)
    _send(tn, args.user)
    _wait_for(tn, "Password", timeout_s=12.0)
    _send(tn, args.password)
    time.sleep(1.0)
    _send(tn, "")  # press RETURN through motd/pager if present
    time.sleep(0.5)

    transcript = ""
    cmdlog: list[str] = []

    def run(title: str, cmd: str) -> None:
        nonlocal transcript
        cmdlog.append(cmd)
        transcript += _section(f"{title}: {cmd}")
        transcript += _send_and_collect(tn, cmd)

    # Reduce paging/noise (best-effort)
    run("setup", "compact")
    run("setup", "brief")

    # Villages + bridge traversals (walk by direction, not just goto)
    run("goto", "goto 46998")  # Darein
    run("look", "look")
    run("exits", "exits")
    run("walk", "ne")  # onto bridge
    run("look", "look")
    run("walk", "ne")
    run("look", "look")
    run("walk", "ne")
    run("look", "look")

    run("goto", "goto 46977")  # Jualdhe
    run("look", "look")
    run("exits", "exits")
    run("walk", "e")
    run("look", "look")
    run("walk", "e")
    run("look", "look")
    run("walk", "e")
    run("look", "look")

    run("goto", "goto 46959")  # Luagde
    run("look", "look")
    run("exits", "exits")
    run("walk", "s")
    run("look", "look")
    run("walk", "s")
    run("look", "look")
    run("walk", "s")
    run("look", "look")

    run("goto", "goto 46861")  # Daghain
    run("look", "look")
    run("exits", "exits")
    run("walk", "sw")
    run("look", "look")
    run("walk", "sw")
    run("look", "look")
    run("walk", "sw")
    run("look", "look")

    run("goto", "goto 46882")  # Osenrein
    run("look", "look")
    run("exits", "exits")
    run("walk", "w")
    run("look", "look")
    run("walk", "w")
    run("look", "look")
    run("walk", "w")
    run("look", "look")

    # Key road split tiles near Luagde
    for v in (46949, 46939, 46820, 46928, 46830):
        run("goto", f"goto {v}")
        run("look", "look")
        run("exits", "exits")

    # River ring tiles sanity
    for v in (46870, 46881, 46890, 46968, 46969, 46978, 46988, 46999):
        run("goto", f"goto {v}")
        run("look", "look")
        run("exits", "exits")

    # Camp
    run("goto", "goto 50946")
    run("look", "look")
    run("exits", "exits")

    run("quit", "quit")
    try:
        tn.close()
    except Exception:
        pass

    args.out.write_text(transcript, encoding="utf-8", errors="ignore")
    args.cmdlog.write_text("\n".join(cmdlog) + "\n", encoding="utf-8")
    print(f"Wrote transcript: {args.out}")
    print(f"Wrote cmdlog: {args.cmdlog}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

