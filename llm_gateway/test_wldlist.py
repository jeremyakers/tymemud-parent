#!/usr/bin/env python3
"""Trace wld_list specifically."""

import asyncio


async def trace_wld_list():
    print("=" * 70)
    print("WLD_LIST TRACE")
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
        print(f"Hello response line {i}: {decoded!r}")
        if decoded.startswith("OK"):
            print("Authentication successful!")
            break

    print()
    print("Sending wld_list...")
    writer.write(b"wld_list\r\n")
    await writer.drain()

    print("Reading wld_list response:")
    lines = []
    for i in range(50):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            lines.append(decoded)
            print(f"  [{i}] {decoded!r}")
            if decoded == "END" or (decoded.startswith("OK") and i > 0):
                if decoded == "END" or not decoded:
                    break
        except asyncio.TimeoutError:
            print(f"  [{i}] Timeout")
            break

    print()
    print(f"Total lines: {len(lines)}")

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(trace_wld_list())
