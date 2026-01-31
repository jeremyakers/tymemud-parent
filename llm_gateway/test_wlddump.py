#!/usr/bin/env python3
"""Trace wld_dump specifically."""

import asyncio


async def trace_wld_dump():
    print("=" * 70)
    print("WLD_DUMP TRACE")
    print("=" * 70)
    print()

    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)
    print("Connected")

    # Skip greeting
    await reader.readline()  # empty
    await reader.readline()  # banner

    # Send hello
    writer.write(b"hello c1gtri32 1\r\n")
    await writer.drain()

    # Read hello response with retry
    for i in range(3):
        resp = await asyncio.wait_for(reader.readline(), timeout=2)
        decoded = resp.decode().strip()
        if decoded.startswith("OK"):
            print(f"Hello response: {decoded!r}")
            break

    print()
    print("Sending wld_dump 1000...")
    writer.write(b"wld_dump 1000\r\n")
    await writer.drain()

    print("Reading wld_dump response:")
    for i in range(10):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  [{i}] {decoded!r}")
            if not decoded:
                break
        except asyncio.TimeoutError:
            print(f"  [{i}] Timeout")
            break

    print()

    # Also test non-existent room
    print("Sending wld_dump 999999...")
    writer.write(b"wld_dump 999999\r\n")
    await writer.drain()

    print("Reading wld_dump response:")
    for i in range(10):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  [{i}] {decoded!r}")
            if not decoded:
                break
        except asyncio.TimeoutError:
            print(f"  [{i}] Timeout")
            break

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(trace_wld_dump())
