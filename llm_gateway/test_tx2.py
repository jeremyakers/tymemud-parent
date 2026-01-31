#!/usr/bin/env python3
"""Trace tx_begin with more detail."""

import asyncio
import base64


async def trace_tx_begin():
    print("=" * 70)
    print("TX_BEGIN DETAILED TRACE")
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

    # Read hello response
    for i in range(3):
        resp = await asyncio.wait_for(reader.readline(), timeout=2)
        decoded = resp.decode().strip()
        if decoded.startswith("OK"):
            print(f"Hello response: {decoded!r}")
            break

    print()
    print("Testing tx_begin ZONES 10...")
    writer.write(b"tx_begin ZONES 10\r\n")
    await writer.drain()

    # Read multiple lines to see full response
    for i in range(5):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  Line [{i}]: {decoded!r}")
            if decoded.startswith("ERROR"):
                parts = decoded.split(maxsplit=2)
                if len(parts) >= 3:
                    code = parts[1]
                    msg_b64 = parts[2]
                    msg = base64.b64decode(msg_b64).decode()
                    print(f"    -> Error {code}: {msg}")
        except asyncio.TimeoutError:
            print(f"  Line [{i}]: Timeout")
            break

    # Try without ZONES keyword
    print()
    print("Testing tx_begin 10 (without ZONES)...")
    writer.write(b"tx_begin 10\r\n")
    await writer.drain()

    for i in range(5):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  Line [{i}]: {decoded!r}")
            if decoded.startswith("ERROR"):
                parts = decoded.split(maxsplit=2)
                if len(parts) >= 3:
                    code = parts[1]
                    msg_b64 = parts[2]
                    msg = base64.b64decode(msg_b64).decode()
                    print(f"    -> Error {code}: {msg}")
        except asyncio.TimeoutError:
            print(f"  Line [{i}]: Timeout")
            break

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(trace_tx_begin())
