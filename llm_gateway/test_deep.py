#!/usr/bin/env python3
"""Deep trace of what client is doing."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")


class DebugClient:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 9697
        self.token = "c1gtri32"
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

        # Skip greeting
        line = await self._read_line()
        print(f"[connect] Greeting 1: {line!r}")
        for _ in range(5):
            if "MikkiMUD" in line or "status port" in line.lower():
                line = await self._read_line()
                print(f"[connect] Greeting: {line!r}")
            else:
                break

        # Send hello
        await self._send(f"hello {self.token} 1")
        print(f"[connect] Sent: hello {self.token} 1")

        # Read response
        for i in range(3):
            resp = await self._read_line()
            print(f"[connect] Hello response {i}: {resp!r}")
            if resp:
                break

    async def _send(self, cmd):
        self.writer.write(f"{cmd}\r\n".encode())
        await self.writer.drain()

    async def _read_line(self):
        line = await self.reader.readline()
        return line.decode().strip()

    async def list_zones(self):
        await self._send("wld_list")
        print(f"[list_zones] Sent: wld_list")

        # Read OK
        for i in range(3):
            resp = await self._read_line()
            print(f"[list_zones] Response {i}: {resp!r}")
            if resp:
                break

        if not resp.startswith("OK"):
            return []

        # Read data
        zones = []
        for i in range(150):
            try:
                line = await asyncio.wait_for(self._read_line(), timeout=2)
                if not line or line == "END":
                    break
                if line.startswith("DATA ZONE"):
                    parts = line.split(maxsplit=3)
                    if len(parts) >= 4:
                        import base64

                        name = base64.b64decode(parts[3]).decode()
                        zones.append({"vnum": int(parts[2]), "name": name})
            except asyncio.TimeoutError:
                break

        print(f"[list_zones] Found {len(zones)} zones")
        return zones

    async def tx_begin(self, zones):
        zone_str = ",".join(str(z) for z in zones)
        await self._send(f"tx_begin ZONES {zone_str}")
        print(f"[tx_begin] Sent: tx_begin ZONES {zone_str}")

        for i in range(3):
            resp = await self._read_line()
            print(f"[tx_begin] Response {i}: {resp!r}")
            if resp:
                break

        return resp

    async def disconnect(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()


async def main():
    client = DebugClient()

    print("=" * 60)
    print("STEP 1: Connect")
    print("=" * 60)
    await client.connect()

    print("\n" + "=" * 60)
    print("STEP 2: list_zones")
    print("=" * 60)
    zones = await client.list_zones()

    print("\n" + "=" * 60)
    print("STEP 3: tx_begin")
    print("=" * 60)
    resp = await client.tx_begin([0])

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
