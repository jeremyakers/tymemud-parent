#!/usr/bin/env python3
"""Test with debug output added to connect."""

import asyncio
import sys

sys.path.insert(0, "/home/jeremy/tymemud/llm_gateway")
import base64
from typing import Optional, List, Dict, Any
from pathlib import Path


class BuilderPortError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"BuilderPort Error {code}: {message}")


class BuilderPortClient:
    def __init__(
        self, host: str = "127.0.0.1", port: int = 9697, token: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.token = token or self._load_token()
        self.reader = None
        self.writer = None
        self.authed = False

    def _load_token(self) -> str:
        possible_roots = [
            Path.cwd(),
            Path(__file__).parent.parent,
            Path(__file__).parent.parent.parent,
            Path.home() / "tymemud",
            Path("/home/jeremy/tymemud"),
        ]
        token_paths = [
            "_agent_work/wld_editor_api_agent/MM32/lib/etc/builderport.token",
            "MM32/lib/etc/builderport.token",
            "lib/etc/builderport.token",
        ]
        for root in possible_roots:
            for subpath in token_paths:
                path = root / subpath
                if path.exists():
                    return path.read_text().strip()
        import os

        if "BUILDERPORT_TOKEN" in os.environ:
            return os.environ["BUILDERPORT_TOKEN"]
        raise RuntimeError("Could not find builderport.token")

    async def connect(self) -> None:
        print("[DEBUG connect] Opening connection...")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print("[DEBUG connect] Connection opened")

        print("[DEBUG connect] Reading greeting lines...")
        for i in range(5):
            greeting = await self._read_line()
            print(f"[DEBUG connect] Greeting line {i}: {greeting!r}")
            if "MikkiMUD" in greeting or "status port" in greeting.lower():
                print("[DEBUG connect] Found banner, breaking")
                break
            if greeting and not (
                "MikkiMUD" in greeting or "status port" in greeting.lower()
            ):
                print("[DEBUG connect] Found non-banner line, breaking")
                break

        print(f"[DEBUG connect] Sending hello with token {self.token}")
        await self._send(f"hello {self.token} 1")

        print("[DEBUG connect] Reading hello response...")
        response = ""
        for i in range(3):
            response = await self._read_line()
            print(f"[DEBUG connect] Hello response line {i}: {response!r}")
            if response:
                break

        if not response.startswith("OK"):
            raise BuilderPortError(401, f"Authentication failed: {response}")

        print("[DEBUG connect] Authentication successful!")
        self.authed = True

    async def _send(self, command: str) -> None:
        if not self.writer:
            raise RuntimeError("Not connected")
        self.writer.write(f"{command}\r\n".encode())
        await self.writer.drain()

    async def _read_line(self) -> str:
        if not self.reader:
            raise RuntimeError("Not connected")
        line = await self.reader.readline()
        return line.decode().strip()

    async def list_zones(self) -> List[Dict[str, Any]]:
        print("[DEBUG list_zones] Sending wld_list...")
        await self._send("wld_list")

        response = ""
        for i in range(3):
            response = await self._read_line()
            print(f"[DEBUG list_zones] Response line {i}: {response!r}")
            if response:
                break

        if not response.startswith("OK"):
            print(f"[DEBUG list_zones] No OK response, returning empty")
            return []

        lines = []
        while True:
            line = await self._read_line()
            if not line or line == "END":
                break
            lines.append(line)

        zones = []
        for line in lines:
            if line.startswith("DATA ZONE"):
                parts = line.split(maxsplit=3)
                if len(parts) >= 4:
                    zones.append(
                        {
                            "vnum": int(parts[2]),
                            "name": base64.b64decode(parts[3]).decode(),
                        }
                    )

        print(f"[DEBUG list_zones] Found {len(zones)} zones")
        return zones

    async def disconnect(self) -> None:
        if self.writer:
            try:
                await self._send("quit")
            except:
                pass
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None
            self.reader = None
            self.authed = False


async def main():
    client = BuilderPortClient()

    print("=" * 60)
    print("Testing with DEBUG output")
    print("=" * 60)
    print()

    await client.connect()
    print()

    zones = await client.list_zones()
    print(f"Got {len(zones)} zones")
    print()

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
