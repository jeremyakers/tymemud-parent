---
name: run-mud-server
description: Start the Tyme MUD game server on a specified port. Handles proper directory navigation, port registration, and server startup. Use this when you need to boot the game server for testing the builder port protocol or web editor API.
license: MIT
compatibility: opencode
metadata:
  purpose: server-startup
  project: tymemud
  agent: any
---

# Run MUD Server

## Purpose

Start the Tyme MUD game server (builder port) correctly on a specified port with proper worktree setup.

## When to use me

Use this skill when you need to:
- Start the game server for BuilderPort protocol testing
- Boot the server for web editor API testing  
- Run smoke tests against the status port
- Validate world building operations

## Critical Setup Requirements

### 1. Worktree Location
**MUST run from MM32 directory, NOT src directory**

```bash
# CORRECT - Run from MM32 root
cd _agent_work/<agent_name>/MM32
src/bin/tyme3 <port>

# WRONG - Don't run from src
cd _agent_work/<agent_name>/MM32/src
./bin/tyme3 <port>  # This will fail!
```

### 2. Port Registration
Before starting the server, register your port in `tmp/agent_ports.tsv`:

```bash
echo -e "<agent_name>\t<port>\t<purpose>\t$(date -u +%Y-%m-%dT%H:%M:%S%Z)\t$(pwd)" >> ../../tmp/agent_ports.tsv
```

### 3. Verify Prerequisites
Ensure these files exist in your worktree:
- `lib/mysql-interface.conf` - MySQL connection config
- `lib/commands.dat` - Command definitions
- `lib/etc/builderport.token` - BuilderPort auth token (for v1 protocol)

## Startup Command

```bash
cd _agent_work/<agent_name>/MM32
src/bin/tyme3 <port> > server_<port>.log 2>&1 &
```

## Verify Server is Running

```bash
# Check process
ps aux | grep "tyme3.*<port>" | grep -v grep

# Check status port responds
echo -e "who\nquit" | nc -w 2 127.0.0.1 <status_port>
# Status port = game port + 1 (e.g., 9696 -> 9697)
```

## Troubleshooting

**Issue**: Server starts then immediately exits
- **Cause**: Missing lib/text/commands file or mysql-interface.conf
- **Fix**: Ensure lib/ directory is properly copied from original MM32/lib

**Issue**: "Unable to open command input file"
- **Cause**: Running from wrong directory
- **Fix**: cd to MM32 root, not MM32/src

**Issue**: Port already in use
- **Cause**: Another agent's server running on same port
- **Fix**: Check `tmp/agent_ports.tsv` and use an available port

## Example Usage

```bash
# Register port
echo -e "my_agent\t9696\tbuilderport_test\t$(date -u +%Y-%m-%dT%H:%M:%S%Z)\t$(pwd)" >> ../../tmp/agent_ports.tsv

# Start server
cd _agent_work/my_agent/MM32
src/bin/tyme3 9696 > server_9696.log 2>&1 &

# Verify
ps aux | grep "tyme3.*9696"
echo -e "who\nquit" | nc -w 2 127.0.0.1 9697
```

## Safety Notes

- Never use `pkill` or pattern killing - only stop your own PID
- Always register ports to avoid conflicts with other agents
- Server logs go to `server_<port>.log` in the MM32 directory
- Status port is always game port + 1
