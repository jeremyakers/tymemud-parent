#!/usr/bin/env python3
"""Show actual raw protocol responses for each data type."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")

from client import BuilderPortClient


async def show_raw_data():
    client = BuilderPortClient()
    await client.connect()

    print("=" * 80)
    print("ACTUAL RAW PROTOCOL DATA")
    print("=" * 80)
    print()

    # 1. Zone list with ALL data types
    print("1️⃣  wld_list - All data types")
    print("-" * 80)
    await client._send("wld_list")
    await client._read_line()  # Skip OK
    lines = await client._read_bulk_response()

    print(f"Total lines: {len(lines)}")
    print("\nZone entries (first 3):")
    for line in lines[:3]:
        if line.startswith("DATA ZONE"):
            parts = line.split(maxsplit=3)
            vnum = parts[2]
            name_b64 = parts[3] if len(parts) > 3 else ""
            name = client.decode_text(name_b64)
            print(f"  Zone {vnum}: {name[:50]}...")

    print("\nSector types:")
    for line in lines:
        if line.startswith("DATA SECTOR"):
            parts = line.split(maxsplit=3)
            if len(parts) >= 4:
                print(f"  ID {parts[2]}: {client.decode_text(parts[3])}")

    print("\nRoom flags (first 10):")
    for line in lines:
        if line.startswith("DATA ROOMFLAGS"):
            flags = line[15:].split(",")[:10]
            print(f"  {', '.join(flags)}...")
            break

    print("\nSpecial functions (first 10):")
    for line in lines:
        if line.startswith("DATA SPECFUNCS"):
            funcs = line[16:].split(",")[:10]
            print(f"  {', '.join(funcs)}...")
            break
    print()

    # 2. Room with exits
    print("2️⃣  wld_load 12 - Room with exits (room 1204)")
    print("-" * 80)
    await client._send("wld_load 12")
    await client._read_line()  # Skip OK
    lines = await client._read_bulk_response()

    for line in lines:
        if line.startswith("DATA ROOM 1204"):
            print(f"ROOM: {line}")
            parts = line.split(maxsplit=8)
            print(f"  vnum: {parts[2]}")
            print(f"  zone: {parts[3]}")
            print(f"  sector: {parts[4]} (0=Inside, 1=City, 2=Field, etc.)")
            print(f"  width: {parts[5]}")
            print(f"  height: {parts[6]}")
            print(f"  flags: {parts[7]}")
            print(f"  name: {client.decode_text(parts[8])}")
            if len(parts) > 9:
                print(f"  description: {client.decode_text(parts[9])[:100]}...")
        elif line.startswith("DATA EXIT 1204"):
            print(f"\nEXIT: {line[:80]}...")
            parts = line.split(maxsplit=8)
            dir_names = ["N", "E", "S", "W", "U", "D", "NE", "NW", "SE", "SW"]
            print(f"  direction: {parts[3]} ({dir_names[int(parts[3])]})")
            print(f"  to_vnum: {parts[4]}")
            print(f"  flags: {parts[5]} (0=open, 1=closed, etc.)")
            print(f"  key: {parts[6]}")
            print(f"  description: {client.decode_text(parts[7])[:50]}...")
            print(f"  keywords: {client.decode_text(parts[8])}")
    print()

    # 3. Room with special function
    print("3️⃣  wld_load 0 - Looking for SPECFUNC")
    print("-" * 80)
    await client._send("wld_load 0")
    await client._read_line()
    lines = await client._read_bulk_response()

    for line in lines:
        if line.startswith("DATA SPECFUNC"):
            print(f"SPECFUNC: {line}")
            parts = line.split(maxsplit=3)
            print(f"  room: {parts[2]}")
            print(f"  function: {parts[3]}")
    print()

    # 4. Room with extra descriptions
    print("4️⃣  wld_load 15 - Looking for EXTRADESC")
    print("-" * 80)
    await client._send("wld_load 15")
    await client._read_line()
    lines = await client._read_bulk_response()

    extradesc_count = 0
    for line in lines:
        if line.startswith("DATA EXTRADESC"):
            extradesc_count += 1
            if extradesc_count <= 2:  # Show first 2
                print(f"EXTRADESC: {line[:80]}...")
                parts = line.split(maxsplit=4)
                print(f"  room: {parts[2]}")
                print(f"  keywords: {client.decode_text(parts[3])}")
                print(f"  text: {client.decode_text(parts[4])[:100]}...")

    if extradesc_count == 0:
        print("  No extra descriptions in zone 15")
    print()

    await client.disconnect()

    print("=" * 80)
    print("SUMMARY: Complete data structure available")
    print("=" * 80)
    print("""
Each room has:
- Basic: vnum, zone, sector, width, height, flags, name, description
- Exits: list of exits with direction, target, flags, key, desc, keywords
- Extra descriptions: list of keyword+text pairs  
- Special function: optional function name

Zones have:
- Zone list: vnum + name
- Sector types: ID + name (for dropdowns)
- Room flags: list of available flags
- Special functions: list of available functions
""")


if __name__ == "__main__":
    asyncio.run(show_raw_data())
