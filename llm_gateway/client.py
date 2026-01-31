"""BuilderPort Protocol Client - Handles raw TCP communication with MUD engine."""

import asyncio
import base64
from typing import Optional, List, Dict, Any, Union
from pathlib import Path


class BuilderPortError(Exception):
    """Raised when BuilderPort returns an error."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"BuilderPort Error {code}: {message}")


class BuilderPortClient:
    """Async client for BuilderPort protocol v1."""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 9697, token: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.token = token or self._load_token()
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.authed = False

    def _load_token(self) -> str:
        """Load token from lib/etc/builderport.token."""
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

        raise RuntimeError(
            "Could not find builderport.token. "
            "Searched in various locations relative to working directory. "
            "Set BUILDERPORT_TOKEN env var as fallback."
        )

    async def connect(self) -> None:
        """Connect and perform HELLO handshake."""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

        # Read and skip initial greeting lines
        for _ in range(5):
            greeting = await self._read_line()
            if "MikkiMUD" in greeting or "status port" in greeting.lower():
                break
            if greeting and not (
                "MikkiMUD" in greeting or "status port" in greeting.lower()
            ):
                break

        # Send HELLO
        await self._send(f"hello {self.token} 1")

        # Read response (skip empty lines)
        response = ""
        for _ in range(3):
            response = await self._read_line()
            if response:
                break

        if not response.startswith("OK"):
            raise BuilderPortError(401, f"Authentication failed: {response}")

        self.authed = True

    async def disconnect(self) -> None:
        """Send quit and close connection."""
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

    async def _send(self, command: str) -> None:
        """Send a command line."""
        if not self.writer:
            raise RuntimeError("Not connected")
        self.writer.write(f"{command}\r\n".encode())
        await self.writer.drain()

    async def _read_line(self) -> str:
        """Read a single line response."""
        if not self.reader:
            raise RuntimeError("Not connected")
        line = await self.reader.readline()
        return line.decode().strip()

    async def _read_bulk_response(self) -> List[str]:
        """Read a bulk response until END marker."""
        lines = []
        while True:
            line = await self._read_line()
            if line == "END" or not line:
                break
            lines.append(line)
        return lines

    @staticmethod
    def encode_text(text: str) -> str:
        """Encode text to base64 (no dash sentinel)."""
        if not text:
            return ""
        return base64.b64encode(text.encode()).decode()

    @staticmethod
    def decode_text(b64: str) -> str:
        """Decode base64 to text."""
        if not b64 or b64 == "-":
            return ""
        try:
            return base64.b64decode(b64).decode()
        except:
            return ""

    async def get_room(self, vnum: int) -> Optional[Dict[str, Any]]:
        """Read complete room data including exits and extra descriptions."""
        zone = vnum // 100
        await self._send(f"wld_load {zone}")

        # Read OK
        response = await self._read_line()
        if not response.startswith("OK"):
            return None

        # Read all data lines
        lines = await self._read_bulk_response()

        # Parse room data
        room_data = None
        exits = []
        extra_descs = []
        specfunc = None

        for line in lines:
            if line.startswith("DATA ROOM "):
                parts = line.split(maxsplit=8)
                if len(parts) >= 9 and int(parts[2]) == vnum:
                    room_data = {
                        "vnum": int(parts[2]),
                        "zone": int(parts[3]),
                        "sector": int(parts[4]),
                        "width": int(parts[5]),
                        "height": int(parts[6]),
                        "flags": int(parts[7]),
                        "name": self.decode_text(parts[8]),
                        "description": self.decode_text(parts[9])
                        if len(parts) > 9
                        else "",
                        "exits": [],
                        "extra_descriptions": [],
                        "special_function": None,
                    }
            elif line.startswith("DATA EXIT ") and room_data:
                parts = line.split(maxsplit=8)
                if len(parts) >= 9 and int(parts[2]) == vnum:
                    dir_names = [
                        "North",
                        "East",
                        "South",
                        "West",
                        "Up",
                        "Down",
                        "Northeast",
                        "Northwest",
                        "Southeast",
                        "Southwest",
                    ]
                    dir_code = int(parts[3])
                    exits.append(
                        {
                            "direction_code": dir_code,
                            "direction_name": dir_names[dir_code]
                            if dir_code < len(dir_names)
                            else f"Dir_{dir_code}",
                            "to_vnum": int(parts[4]),
                            "flags": int(parts[5]),
                            "key": int(parts[6]),
                            "description": self.decode_text(parts[7]),
                            "keywords": self.decode_text(parts[8]),
                        }
                    )
            elif line.startswith("DATA EXTRADESC ") and room_data:
                parts = line.split(maxsplit=4)
                if len(parts) >= 5 and int(parts[2]) == vnum:
                    extra_descs.append(
                        {
                            "keywords": self.decode_text(parts[3]),
                            "description": self.decode_text(parts[4]),
                        }
                    )
            elif line.startswith("DATA SPECFUNC ") and room_data:
                parts = line.split(maxsplit=3)
                if len(parts) >= 4 and int(parts[2]) == vnum:
                    specfunc = parts[3]

        if room_data:
            room_data["exits"] = exits
            room_data["extra_descriptions"] = extra_descs
            room_data["special_function"] = specfunc

        return room_data

    async def list_zones(self) -> Dict[str, Any]:
        """List all zones with comprehensive metadata including sectors, flags, and special functions."""
        await self._send("wld_list")

        # Read OK
        response = ""
        for _ in range(3):
            response = await self._read_line()
            if response:
                break

        if not response.startswith("OK"):
            return {
                "zones": [],
                "sector_types": [],
                "room_flags": [],
                "special_functions": [],
                "count": 0,
            }

        # Read bulk data
        lines = await self._read_bulk_response()

        zones = []
        sectors = []
        room_flags = []
        spec_funcs = []

        for line in lines:
            if line.startswith("DATA ZONE "):
                parts = line.split(maxsplit=3)
                if len(parts) >= 4:
                    zones.append(
                        {
                            "vnum": int(parts[2]),
                            "name": self.decode_text(parts[3]),
                        }
                    )
            elif line.startswith("DATA SECTOR "):
                parts = line.split(maxsplit=3)
                if len(parts) >= 4:
                    sectors.append(
                        {
                            "id": int(parts[2]),
                            "name": self.decode_text(parts[3]),
                        }
                    )
            elif line.startswith("DATA ROOMFLAGS "):
                flags_str = line[15:]
                room_flags = [f.strip() for f in flags_str.split(",") if f.strip()]
            elif line.startswith("DATA SPECFUNCS "):
                funcs_str = line[16:]
                spec_funcs = [f.strip() for f in funcs_str.split(",") if f.strip()]

        return {
            "zones": zones,
            "sector_types": sectors,
            "room_flags": room_flags,
            "special_functions": spec_funcs,
            "count": len(zones),
        }

    def _parse_error(self, response: str) -> tuple:
        """Parse ERROR code message_b64 format."""
        parts = response.split(maxsplit=2)
        if len(parts) >= 3:
            return int(parts[1]), parts[2]
        return 500, "Unknown error"

    def transaction(self, zones: List[int]):
        """Context manager for transactions."""
        return TransactionContext(self, zones)


class TransactionContext:
    """Async context manager for BuilderPort transactions."""

    def __init__(self, client: BuilderPortClient, zones: List[int]):
        self.client = client
        self.zones = zones
        self.active = False

    async def __aenter__(self):
        """Begin transaction."""
        zone_str = ",".join(str(z) for z in self.zones)
        await self.client._send(f"tx_begin ZONES {zone_str}")

        response = ""
        for _ in range(3):
            response = await self.client._read_line()
            if response:
                break

        if not response.startswith("OK"):
            code, msg = self.client._parse_error(response)
            raise BuilderPortError(code, self.client.decode_text(msg))

        self.active = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or abort based on success/failure."""
        if not self.active:
            return

        if exc_val is None:
            await self.client._send("tx_commit")
        else:
            await self.client._send("tx_abort")

        response = ""
        for _ in range(3):
            response = await self.client._read_line()
            if response:
                break

        if not response.startswith("OK"):
            code, msg = self.client._parse_error(response)
            raise BuilderPortError(code, self.client.decode_text(msg))

    async def room_patch(self, vnum: int, **fields) -> None:
        """Update specific room fields."""
        field_map = {
            "name": "NAME",
            "desc": "DESC",
            "sector": "SECTOR",
            "flags": "FLAGS",
            "width": "WIDTH",
            "height": "HEIGHT",
            "spec_func": "SPECFUNC",
        }

        cmd_parts = [f"room_patch {vnum}"]
        for key, value in fields.items():
            if key in field_map:
                if key in ["name", "desc"]:
                    value = self.client.encode_text(value)
                cmd_parts.append(f"{field_map[key]} {value}")

        await self.client._send(" ".join(cmd_parts))
        response = await self.client._read_line()
        if not response.startswith("OK"):
            code, msg = self.client._parse_error(response)
            raise BuilderPortError(code, self.client.decode_text(msg))

    async def room_full(
        self,
        vnum: int,
        zone: int,
        sector: int,
        width: int,
        height: int,
        flags: int,
        name: str,
        desc: str,
    ) -> None:
        """Full room replacement (destructive)."""
        name_b64 = self.client.encode_text(name)
        desc_b64 = self.client.encode_text(desc)

        cmd = f"room_full {vnum} {zone} {sector} {width} {height} {flags} {name_b64} {desc_b64}"
        await self.client._send(cmd)

        response = await self.client._read_line()
        if not response.startswith("OK"):
            code, msg = self.client._parse_error(response)
            raise BuilderPortError(code, self.client.decode_text(msg))

    async def link_rooms(
        self,
        from_vnum: int,
        direction: int,
        to_vnum: int,
        flags: int = 0,
        key: int = -1,
        desc: str = "",
        keywords: str = "",
        mode: str = "BIDIR",
    ) -> None:
        """Create or update an exit link."""
        desc_b64 = self.client.encode_text(desc)
        keywords_b64 = self.client.encode_text(keywords)

        cmd = f"link {from_vnum} {direction} {to_vnum} {flags} {key} {desc_b64} {keywords_b64} {mode}"
        await self.client._send(cmd)

        response = await self.client._read_line()
        if not response.startswith("OK"):
            code, msg = self.client._parse_error(response)
            raise BuilderPortError(code, self.client.decode_text(msg))

    async def validate(self, zones: List[int]) -> None:
        """Validate zones within transaction."""
        zone_str = ",".join(str(z) for z in zones)
        await self.client._send(f"validate ZONES {zone_str}")

        response = await self.client._read_line()
        if not response.startswith("OK"):
            code, msg = self.client._parse_error(response)
            raise BuilderPortError(code, self.client.decode_text(msg))

    async def export(self, zones: List[int]) -> None:
        """Export zones to disk within transaction."""
        zone_str = ",".join(str(z) for z in zones)
        await self.client._send(f"export ZONES {zone_str}")

        response = await self.client._read_line()
        if not response.startswith("OK"):
            code, msg = self.client._parse_error(response)
            raise BuilderPortError(code, self.client.decode_text(msg))
