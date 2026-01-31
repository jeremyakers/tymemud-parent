# BuilderPort / World-Building API – Design Document (v1)

## Overview
This document describes the proposed design and stabilization of the **BuilderPort protocol** used for world building in a heavily modified CircleMUD engine. The same protocol is intended to support:

- A human-facing web-based world editor
- Automated world generation via a locally hosted LLM (e.g., Ollama)

The guiding principle is:

> **The C engine (BuilderPort) is the canonical authority for world data and .wld generation.**

Higher-level clients (web UI, LLMs) adapt to it rather than introducing parallel schemas or exporters.

---

## Goals

- Keep **.wld generation authoritative and single-sourced** in the engine
- Avoid duplicate schemas or converters between systems
- Allow safe, deterministic automation by LLMs
- Support human builders and automation via the same core API
- Minimize future technical debt while the protocol is still young

---

## Non-Goals

- No requirement for TLS or public internet exposure
- No real-time/live update streaming (e.g., WebSockets)
- No attempt to make the protocol “RESTful” internally

---

## Architectural Summary

```
+------------------+        +------------------+
|  Web Editor UI   |        |   LLM / Agent    |
+------------------+        +------------------+
          |                         |
          | (optional HTTP / MCP)   |
          v                         v
+------------------------------------------------+
|      Thin Gateway / Adapter (Python/Java)      |
|  - JSON / tool interface                       |
|  - Rate limiting / guardrails                  |
|  - Base64 + chunking handled here              |
+------------------------------------------------+
          |
          | (existing line protocol)
          v
+------------------------------------------------+
|          BuilderPort (C, canonical)             |
|  - In-memory world structs                      |
|  - Locking                                     |
|  - Validation                                  |
|  - .wld export                                 |
+------------------------------------------------+
```

The gateway is optional but recommended for LLM use. The web editor may continue to speak the BuilderPort protocol directly.

---

## Canonical Design Decisions

### 1. BuilderPort Remains the Source of Truth

- BuilderPort owns:
  - Room data
  - Exit topology
  - Locks
  - Validation rules
  - .wld serialization

- No sidecar or gateway stores authoritative world state
- No parallel schema exists outside the engine

---

### 2. Line-Oriented RPC Protocol (Not REST-in-C)

- BuilderPort exposes a **line-based RPC protocol** over TCP
- Accessible on a **local-network-only interface** (e.g., 192.168.0.0/24)
- Each connection has its own `DESCRIPTOR_DATA *`

Reasons:
- Already implemented and working
- Natural fit for C
- Easy to debug
- Avoids HTTP/JSON complexity in the engine

---

### 3. Protocol Versioning and Handshake

Add an explicit handshake:

```
HELLO <token> <protocol_version>
```

Server responds:

- `OK <protocol_version>`
- or `ERROR <code> <message_b64>`

This allows:
- Safe evolution of the protocol
- Graceful client/server mismatches

---

## Authentication Model

- Shared secret token supplied at connection time
- Token is **not hardcoded** in the source
- Token generated at startup or loaded from config

This is sufficient given:
- Local network exposure only
- Controlled clients

---

## Transactions and Editing Sessions

BuilderPort already has a transaction-like capture system. This should be formalized.

### Proposed Commands

- `TX_BEGIN ZONES <z1,z2,...>`
- `TX_COMMIT`
- `TX_ABORT`

Rules:
- All write operations occur inside a transaction
- Validation may occur before commit
- Export is only allowed after a successful commit

---

## Room Editing Semantics

### Full Replace vs Patch

#### ROOM_FULL (destructive)

```
ROOM_FULL <vnum> <zone> <sector> <width> <height> <flags> <name_b64> <desc_b64>
```

Behavior:
- Clears exits
- Clears extra descriptions
- Clears specfunc
- Replaces all core fields

Used by:
- Bulk imports
- Canonical rebuilds

#### ROOM_PATCH (non-destructive)

```
ROOM_PATCH <vnum> [FIELD VALUE]...
```

Examples:
- `ROOM_PATCH 46989 NAME <b64>`
- `ROOM_PATCH 46989 DESC <b64>`

Behavior:
- Only updates specified fields
- Preserves exits, extras, and other metadata

This is **required** for safe LLM usage.

---

## Exit Management

### First-Class Linking With Explicit Directionality

Bidirectional exits are the default and should remain the standard, but the protocol must also support **intentional one-way** links.

#### LINK (bidirectional by default)

Introduce a canonical linking command:

```
LINK <from_vnum> <dir> <to_vnum> <flags> <key> <desc_b64> <keyword_b64> [MODE <mode>]
```

- If `MODE` is omitted, the server behaves as **BIDIR** (creates/updates forward + reverse).
- Supported modes:
  - `BIDIR` (default): create/update reverse exit as well
  - `ONEWAY`: create/update only the specified direction

Server behavior:
- Always validates that `dir` is valid and the target exists
- In `BIDIR` mode, automatically creates/updates the reverse exit using `rev_dir[dir]`
- In `ONEWAY` mode, **does not** create/modify the reverse exit

#### UNLINK (removes both ends by default)

```
UNLINK <from_vnum> <dir> [MODE <mode>]
```

- Supported modes:
  - `BIDIR` (default): remove both the forward and reverse exit if present
  - `ONEWAY`: remove only the specified direction

### Validation Rule

- Validator should **warn or error** on missing reverse exits **only when the exit is expected to be bidirectional**.
- For intentional one-way exits, store intent as either:
  - an explicit flag/bit in exit metadata (preferred), or
  - a “known one-way” rule list in the zone build tooling

This preserves safety (accidental one-way is caught) while still allowing legitimate one-way designs.

---

## Text Encoding Rules

- **All free-text fields are base64 encoded**
- No raw text is accepted
- Empty string is valid (no dash sentinel)

Applies to:
- Room names
- Room descriptions
- Exit descriptions
- Exit keywords
- Extra description keywords and text

Benefits:
- Binary safety
- No quoting rules
- Easy chunking

---

## Structured Responses

Standardize responses:

- `OK`
- `OK <data>`
- `ERROR <code> <message_b64>`

Bulk data responses:

```
OK
DATA ROOM ...
DATA EXIT ...
DATA EXTRADESC ...
END
```

This simplifies parsing for both web editors and gateways.

---

## Validation and Export

### Validation

Add a command:

```
VALIDATE ZONES <z1,z2,...>
```

Returns:
- `OK` if clean
- `ERROR <code> <details_b64>` if not

### Export

```
EXPORT ZONES <z1,z2,...>
```

Rules:
- Refuses if validation fails
- BuilderPort writes .wld using existing logic

---

## LLM Integration Strategy

### Do NOT expose raw protocol directly to the LLM

Instead:
- Use a small gateway process
- Gateway exposes a **small, safe toolset**
- Gateway translates tools → BuilderPort commands

Example LLM tools:
- `get_room_context(vnum)`
- `set_room_text(vnum, name, desc, extras)`
- `link_rooms(vnum, dir, to_vnum)`
- `validate_zone(zvnum)`
- `export_zone(zvnum)`

Gateway responsibilities:
- Base64 encoding/decoding
- Chunking
- Lock/unlock
- Transaction management
- Rate limiting

---

## Network Exposure

- BuilderPort listens on a **local network interface only** (e.g., 192.168.0.*)
- Firewall rules restrict access
- No requirement for TLS

---

## Summary

- The existing BuilderPort protocol is fundamentally sound
- REST-in-C is unnecessary and adds risk
- Stabilizing the protocol now avoids long-term debt
- A thin gateway provides modern ergonomics without compromising engine simplicity

**Key immediate improvements:**
1. Protocol versioning + handshake
2. ROOM_PATCH vs ROOM_FULL
3. LINK / UNLINK commands
4. Explicit transactions
5. Structured error codes

With these in place, BuilderPort cleanly supports both human builders and LLM-driven world generation without duplicating schemas or logic.

