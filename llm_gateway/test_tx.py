#!/usr/bin/env python3
"""Trace transaction protocol."""

import asyncio


async def trace_transaction():
    print("=" * 70)
    print("TRANSACTION TRACE")
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
    print("=" * 50)
    print("STEP 1: tx_begin ZONES 10")
    print("=" * 50)
    writer.write(b"tx_begin ZONES 10\r\n")
    await writer.drain()

    for i in range(5):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  Response [{i}]: {decoded!r}")
            if not decoded:
                break
        except asyncio.TimeoutError:
            print(f"  Timeout")
            break

    print()
    print("=" * 50)
    print("STEP 2: tx_commit")
    print("=" * 50)
    writer.write(b"tx_commit\r\n")
    await writer.drain()

    for i in range(5):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  Response [{i}]: {decoded!r}")
            if not decoded:
                break
        except asyncio.TimeoutError:
            print(f"  Timeout")
            break

    print()
    print("=" * 50)
    print("STEP 3: Try tx_abort after failed commit")
    print("=" * 50)
    writer.write(b"tx_abort\r\n")
    await writer.drain()

    for i in range(5):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  Response [{i}]: {decoded!r}")
            if not decoded:
                break
        except asyncio.TimeoutError:
            print(f"  Timeout")
            break

    writer.close()
    await writer.wait_closed()
    print()
    print("Disconnected")


if __name__ == "__main__":
    asyncio.run(trace_transaction())
