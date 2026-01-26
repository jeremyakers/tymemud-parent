# Parallel-Safe Agent Workflow (Multi-Agent Host)

This repository is often worked on by **multiple agents in parallel on the same host**. Follow this doc to avoid stepping on each other.

## Non-Negotiables

- **Never edit the shared trees while another agent is working**
  - Treat these as shared and potentially “dirty” at any moment:
    - `MM3/`
    - `MM32/`
  - **Do all work in your own isolated workspace** under `_agent_work/<your_agent>/...`

- **Never use `pkill` / pattern killing**
  - **Forbidden:** `pkill`, `killall`, `kill -9 $(pgrep ...)`, “kill anything named tyme3”, etc.
  - These can kill other agents’ servers and destroy their runs.

- **Only stop processes you started**
  - If you started a server, you should have the **PID**. Stop *that PID only*.
  - If you do not own the PID, do not kill it.

## 1) Create your isolated workspace tree (recommended)

Create one worktree per agent and keep your changes confined to that directory.

Example layout:

- `_agent_work/<agent_name>/MM32/` (your isolated MM32 tree)
- `_agent_work/<agent_name>/MM3/` (your isolated MM3 tree, if needed)

If you’re unsure how the repo expects worktrees to be created, search `AGENTS.md` / `README.md` and mirror the existing `_agent_work/*_agent/` patterns.

### Pre-flight: “am I in my worktree?”

Before editing anything, run:

```bash
pwd
git status --porcelain
```

You should see a path like `_agent_work/<agent_name>/...` and **only** the files you intend to change.

### Worktree layout (mirror the repo structure)

Recommended layout (mirrors the top-level `MM3/` and `MM32/` folders):

- `_agent_work/<agent_name>/MM3/{src,lib}`
- `_agent_work/<agent_name>/MM32/{src,lib}`

### MM32 worktree setup (dev branch; `svn/MM_3-2_Start`)

Create an isolated git worktree for `MM32/src/` and copy `lib/` so you can safely create your own DB config without touching shared trees.

```bash
# From repo root:
mkdir -p _agent_work/<agent_name>/MM32

# Create an isolated git worktree for MM32/src (THIS is where you do git commits)
cd MM32/src
git fetch origin --prune
git worktree add -b feature/<short_desc> ../../_agent_work/<agent_name>/MM32/src origin/svn/MM_3-2_Start

# Copy lib so you can safely create your own mysql-interface.conf without touching shared trees
cp -a ../lib ../../_agent_work/<agent_name>/MM32/

# Create your private MySQL config (never commit secrets)
cp ../../_agent_work/<agent_name>/MM32/lib/mysql-interface.conf.example \
   ../../_agent_work/<agent_name>/MM32/lib/mysql-interface.conf
```

### MM3 worktree setup (stable branch; `svn/MM_3_Final`)

Only do this if you need to change stable (remember: **Fix in Stable, Merge to Dev**).

```bash
# From repo root:
mkdir -p _agent_work/<agent_name>/MM3

# Create an isolated git worktree for MM3/src (THIS is where you do git commits)
cd MM3/src
git fetch origin --prune
git worktree add -b fix/<short_desc> ../../_agent_work/<agent_name>/MM3/src origin/svn/MM_3_Final

# Copy lib (includes DB config); do not edit shared MM3/lib
cp -a ../lib ../../_agent_work/<agent_name>/MM3/
```

## 2) Ports: pick a unique port and register it

Agents frequently run servers locally for SIT testing. Port conflicts waste time and can break other runs.

### Canonical port registry

Use: `tmp/agent_ports.tsv`

- One line per agent run
- Record:
  - agent name
  - port
  - purpose (e.g., `sit_mm32_sickbay_room98_smoke`)
  - timestamp
  - worktree path

### Safe port selection checklist

1. **Check the registry** for recent ports.
2. **Verify the port is free** before starting your server:

```bash
python3 - <<'PY'
import socket
port = 9850  # change me
s = socket.socket()
try:
    s.bind(('127.0.0.1', port))
    print(f"OK: port {port} is free")
finally:
    s.close()
PY
```

3. **Append your allocation** to `tmp/agent_ports.tsv` before starting the server.

## 3) Testing hygiene (SIT / servers)

- **Run tests in the foreground** so you can see failures and logs as they happen.
- **Do not run “global cleanup”** steps that might kill other agents’ work.
- Prefer the test harness to manage the server it launched, and if manual cleanup is needed:
  - stop by PID
  - or fix the harness to store/stop the exact PID it created

## 4) PR-only workflow (required)

- **Never push directly** to:
  - `origin/svn/MM_3_Final`
  - `origin/svn/MM_3-2_Start`
- Always work on a feature/fix branch in your worktree and submit a PR:
  - MM3 PRs target `svn/MM_3_Final`
  - MM32 PRs target `svn/MM_3-2_Start`

## 5) PR hygiene: never “update” merged/closed PRs (required)

Before pushing commits to a branch that already has (or had) a PR, check the PR state:

```bash
# Show PRs for a branch (OPEN/CLOSED/MERGED):
gh pr list --repo jeremyakers/tymemud-src --head <branch> --state all

# Inspect a PR state explicitly:
gh pr view <PR_NUMBER> --repo jeremyakers/tymemud-src --json state,mergedAt
```

Rules:

- If the PR is **MERGED** or **CLOSED**:
  - Do **not** push more commits expecting to “update that PR”.
  - Create a **new branch** from the target branch tip and open a **new PR**.
- You may edit the description of a merged PR for clarity, but **new code always requires a new PR**.

## 6) “Things not to do” (real failure modes)

- **Don’t touch `MM32/` or `MM3/` at the repo root** when you’re supposed to be isolated.
- **Don’t use `pkill`**, even if it “seems convenient”.
- **Don’t assume ports are free** (check + register).
- **Don’t start long-running servers on default/common ports** without coordination.
- **Don’t “work around” engine state bugs with output-only hacks** (see `AGENTS.md`: “Fix the Cause; Don’t Work Around It”).

