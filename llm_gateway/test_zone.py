#!/usr/bin/env python3
"""Test zone 10 specifically."""

import asyncio


async def test_zone_10():
    reader, writer = await asyncio.open_connection("127.0.0.1", 9697)

    # Skip greeting
    await reader.readline()
    await reader.readline()

    # Send hello
    writer.write(b"hello c1gtri32 1\r\n")
    await writer.drain()

    for i in range(3):
        resp = await asyncio.wait_for(reader.readline(), timeout=2)
        decoded = resp.decode().strip()
        if decoded.startswith("OK"):
            break

    # Get list of zones
    writer.write(b"wld_list\r\n")
    await writer.drain()

    zones = []
    for i in range(150):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            if decoded.startswith("DATA ZONE"):
                parts = decoded.split()
                if len(parts) >= 3:
                    zones.append(int(parts[2]))
            if decoded == "END" or not decoded:
                break
        except asyncio.TimeoutError:
            break

    print(f"Available zones: {sorted(zones)[:20]}...")
    print(f"Zone 10 in list: {10 in zones}")

    # Try zone 0 which should exist
    print("\nTrying tx_begin ZONES 0...")
    writer.write(b"tx_begin ZONES 0\r\n")
    await writer.drain()

    for i in range(3):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=2)
            decoded = line.decode().strip()
            print(f"  [{i}] {decoded!r}")
        except asyncio.TimeoutError:
            print(f"  [{i}] Timeout")
            break

    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    asyncio.run(test_zone_10())
