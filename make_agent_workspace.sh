#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <agent_name> [options]"
  cat <<'EOF'

Creates an agent workspace under ~/tymemud/_agent_work/<agent_name> with optional:
  MM3/src, MM3/lib
  MM32/src, MM32/lib
  public_html

Options:
  --mm3 [branch]           Create MM3/{src,lib}.
                           Default: src=svn/MM_3_Final, lib=main
                           If branch is provided, create that local branch from the defaults.

  --mm32 [branch]          Create MM32/{src,lib}.
                           Default: src=svn/MM_3-2_Start, lib=builder
                           If branch is provided, create that local branch from the defaults.

  --public-html [branch]   Create public_html (tymemud-web) and checkout:
                           Default: base=main
                           If branch is provided, create that local branch from base main.
  --public_html [branch]   Alias for --public-html

  --no-pool-update         Do not fetch --prune in the local pools
  -h, --help               Show this help

Examples:
  ./make_agent_workspace.sh econ_cost_agent --mm32
  ./make_agent_workspace.sh econ_cost_agent --mm32 econ_cost_agent_work
  ./make_agent_workspace.sh legacy_agent --mm3
  ./make_agent_workspace.sh tv_agent --mm3 --mm32 tv_port_work
  ./make_agent_workspace.sh web_agent --public-html
  ./make_agent_workspace.sh web_agent --public-html my_web_branch
EOF
}

if [[ $# -lt 1 ]]; then usage; exit 1; fi
AGENT="$1"; shift

# ---------- Configuration ----------
ROOT="$HOME/tymemud/_agent_work/$AGENT"

# Bare pools (object caches)
SRC_POOL="$HOME/tymemud/_pool/tymemud-src.git"
LIB_POOL="$HOME/tymemud/_pool/tymemud-lib.git"
WEB_POOL="$HOME/tymemud/_pool/tymemud-web.git"

# Remotes (truth)
SRC_REMOTE="git@github.com:jeremyakers/tymemud-src.git"
LIB_REMOTE="git@github.com:jeremyakers/tymemud-lib.git"
WEB_REMOTE="git@github.com:jeremyakers/tymemud-web.git"

PUBLIC_HTML_REMOTE="$WEB_REMOTE"

# Base branches (authoritative defaults)
MM3_SRC_BASE="svn/MM_3_Final"
MM3_LIB_BASE="main"
MM32_SRC_BASE="svn/MM_3-2_Start"
MM32_LIB_BASE="builder"
WEB_BASE="main"   # public_html base branch

# ---------- Option parsing ----------
DO_MM3=0
DO_MM32=0
MM3_CUSTOM_BRANCH=""
MM32_CUSTOM_BRANCH=""

PUBLIC_HTML=0
PUBLIC_HTML_BRANCH=""
POOL_UPDATE=1

# optional-arg parsing must NOT treat another flag as the branch name
is_branch_arg() {
  [[ "${1:-}" != "" && "${1:0:1}" != "-" ]]
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mm3)
      DO_MM3=1
      if is_branch_arg "${2:-}"; then
        MM3_CUSTOM_BRANCH="$2"
        shift 2
      else
        shift 1
      fi
      ;;
    --mm32)
      DO_MM32=1
      if is_branch_arg "${2:-}"; then
        MM32_CUSTOM_BRANCH="$2"
        shift 2
      else
        shift 1
      fi
      ;;
    --public-html|--public_html)
      PUBLIC_HTML=1
      if is_branch_arg "${2:-}"; then
        PUBLIC_HTML_BRANCH="$2"
        shift 2
      else
        shift 1
      fi
      ;;
    --no-pool-update)
      POOL_UPDATE=0
      shift
      ;;
    -h|--help)
      usage; exit 0
      ;;
    *)
      echo "ERROR: unknown arg: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ $DO_MM3 -eq 0 && $DO_MM32 -eq 0 && $PUBLIC_HTML -eq 0 ]]; then
  echo "ERROR: You must specify at least one of --mm3, --mm32, or --public-html"
  usage
  exit 1
fi

# ---------- Helpers ----------
die() { echo "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null || die "missing command: $1"; }

need git
mkdir -p "$ROOT"

[[ -d "$SRC_POOL" ]] || die "src pool not found: $SRC_POOL"
[[ -d "$LIB_POOL" ]] || die "lib pool not found: $LIB_POOL"
if [[ $PUBLIC_HTML -eq 1 ]]; then
  [[ -d "$WEB_POOL" ]] || die "web pool not found: $WEB_POOL (create with: git clone --mirror $WEB_REMOTE $WEB_POOL)"
fi

if [[ $POOL_UPDATE -eq 1 ]]; then
  echo "Refreshing pools..."
  git -C "$SRC_POOL" fetch --prune
  git -C "$LIB_POOL" fetch --prune
  if [[ $PUBLIC_HTML -eq 1 ]]; then
    git -C "$WEB_POOL" fetch --prune
  fi
  echo
fi

clone_if_missing() {
  local pool="$1" remote="$2" dest="$3"

  if [[ -d "$dest/.git" ]]; then
    echo "Exists: $dest"
    return 0
  fi

  echo "Cloning: $dest"
  git clone --reference "$pool" "$remote" "$dest"

  # hardening: prevent background maintenance surprises
  git -C "$dest" config maintenance.auto false
  git -C "$dest" config gc.auto 0
  git -C "$dest" config fetch.prune true
}

# Ensure the base branch exists locally, tracking origin/base
ensure_base_branch() {
  local repo="$1" base="$2"

  git -C "$repo" fetch origin --prune

  if git -C "$repo" show-ref --verify --quiet "refs/heads/$base"; then
    return 0
  fi

  if git -C "$repo" show-ref --verify --quiet "refs/remotes/origin/$base"; then
    git -C "$repo" switch -c "$base" "origin/$base" >/dev/null
    return 0
  fi

  die "Base branch '$base' not found on origin for repo: $repo"
}

# Checkout base (default) OR create local custom branch from base
checkout_based_branch() {
  local repo="$1" base="$2" custom="$3"

  ensure_base_branch "$repo" "$base"

  if [[ -z "$custom" ]]; then
    echo "  -> checkout base $base"
    git -C "$repo" switch "$base" >/dev/null
    git -C "$repo" merge --ff-only "origin/$base" >/dev/null 2>&1 || true
    return 0
  fi

  echo "  -> create/switch $custom (from $base)"

  if git -C "$repo" show-ref --verify --quiet "refs/heads/$custom"; then
    git -C "$repo" switch "$custom" >/dev/null
    return 0
  fi

  git -C "$repo" switch -c "$custom" "$base" >/dev/null
}

make_pair() {
  # $1=label, $2=src_base, $3=lib_base, $4=custom_branch, $5=basepath
  local label="$1" src_base="$2" lib_base="$3" custom="$4" base="$5"

  echo "== $label =="

  clone_if_missing "$SRC_POOL" "$SRC_REMOTE" "$base/src"
  checkout_based_branch "$base/src" "$src_base" "$custom"

  clone_if_missing "$LIB_POOL" "$LIB_REMOTE" "$base/lib"
  checkout_based_branch "$base/lib" "$lib_base" "$custom"

  echo
}

# ---------- Create requested workspaces ----------
if [[ $DO_MM3 -eq 1 ]]; then
  make_pair "MM3" "$MM3_SRC_BASE" "$MM3_LIB_BASE" "$MM3_CUSTOM_BRANCH" "$ROOT/MM3"
fi

if [[ $DO_MM32 -eq 1 ]]; then
  make_pair "MM32" "$MM32_SRC_BASE" "$MM32_LIB_BASE" "$MM32_CUSTOM_BRANCH" "$ROOT/MM32"
fi

if [[ $PUBLIC_HTML -eq 1 ]]; then
  echo "== public_html =="

  if [[ -d "$ROOT/public_html/.git" ]]; then
    echo "Exists: $ROOT/public_html"
  else
    echo "Cloning: $ROOT/public_html"
    git clone --reference "$WEB_POOL" "$PUBLIC_HTML_REMOTE" "$ROOT/public_html"
    git -C "$ROOT/public_html" config maintenance.auto false
    git -C "$ROOT/public_html" config gc.auto 0
    git -C "$ROOT/public_html" config fetch.prune true
  fi

  # Based checkout: base=main, optional custom branch created from base
  checkout_based_branch "$ROOT/public_html" "$WEB_BASE" "${PUBLIC_HTML_BRANCH:-}"

  # sanity assert: ensure correct origin
  want="$WEB_REMOTE"
  got="$(git -C "$ROOT/public_html" remote get-url origin)"
  [[ "$got" == "$want" ]] || die "public_html origin is '$got' (expected '$want')"

  echo
fi

# ---------- grepai workspace registration ----------
GREPAI_WS="tymemud"
if command -v grepai >/dev/null; then
  if ! grepai workspace add "$GREPAI_WS" "$ROOT" >/dev/null 2>&1; then
    echo "WARN: grepai workspace add failed (maybe already exists): $ROOT" >&2
  fi
fi

echo "Done."
echo "Workspace: $ROOT"
