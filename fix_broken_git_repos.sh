set -Eeuo pipefail

AGENT_ROOT="$HOME/tymemud/_agent_work"
STAMP="$(date +%s)"

# Bare pools (object caches)
SRC_POOL="$HOME/tymemud/_pool/tymemud-src.git"
LIB_POOL="$HOME/tymemud/_pool/tymemud-lib.git"

# Clone sources (truth)
SRC_REMOTE="git@github.com:jeremyakers/tymemud-src.git"
LIB_REMOTE="git@github.com:jeremyakers/tymemud-lib.git"

# Where to store salvage artifacts
SALVAGE_BASE="/tmp/agent_salvage_${STAMP}"
mkdir -p "$SALVAGE_BASE"

# If you want maximum independence after clone, set to 1
DISSOCIATE=0

log() { printf '%s\n' "$*" >&2; }

classify_repo() {
  case "$1" in
    # lib layouts
    *"/lib"|*"/MM32/lib"|*"/MM3/lib"|*"/MM32/lib/"*|*"/MM3/lib/"*|*"/MM32_lib_"*|*"/MM3_lib_"*) echo lib ;;
    # src layouts
    *"/src"|*"/MM32/src"|*"/MM3/src"|*"/MM32/src/"*|*"/MM3/src/"*|*"/MM32_src_"*|*"/MM3_src_"*) echo src ;;
    *) echo skip ;;
  esac
}

is_dirty() {
  # returns 0 if dirty, 1 if clean or unreadable
  git -C "$1" status --porcelain=v1 2>/dev/null | head -n 1 | grep -q .
}

salvage_repo() {
  # $1 = repo path, $2 = salvage prefix
  local R="$1" P="$2"

  git -C "$R" rev-parse --abbrev-ref HEAD > "${P}.branch" 2>/dev/null || echo master > "${P}.branch"

  # patches (may be empty)
  git -C "$R" diff --staged > "${P}.staged.patch" 2>/dev/null || true
  git -C "$R" diff         > "${P}.unstaged.patch" 2>/dev/null || true

  # untracked
  git -C "$R" ls-files -o --exclude-standard > "${P}.untracked.list" 2>/dev/null || true
  if [ -s "${P}.untracked.list" ]; then
    tar -C "$R" -czf "${P}.untracked.tgz" -T "${P}.untracked.list"
  else
    : > "${P}.untracked.tgz"
  fi
}

restore_repo() {
  # $1 = repo path, $2 = salvage prefix
  local R="$1" P="$2"
  local BR
  BR="$(cat "${P}.branch" 2>/dev/null || echo master)"

  # checkout branch (track origin if possible)
  if git -C "$R" show-ref --verify --quiet "refs/heads/$BR"; then
    git -C "$R" checkout "$BR" >/dev/null
  else
    if git -C "$R" show-ref --verify --quiet "refs/remotes/origin/$BR"; then
      git -C "$R" checkout -b "$BR" "origin/$BR" >/dev/null
    else
      git -C "$R" checkout -b "$BR" >/dev/null
    fi
  fi

  # restore changes (best-effort)
  git -C "$R" apply "${P}.unstaged.patch" 2>/dev/null || true
  git -C "$R" apply --index "${P}.staged.patch" 2>/dev/null || true
  if [ -s "${P}.untracked.tgz" ]; then
    tar -C "$R" -xzf "${P}.untracked.tgz" 2>/dev/null || true
  fi

  # harden (prevents agents doing repo-maintenance surprise)
  git -C "$R" config maintenance.auto false
  git -C "$R" config gc.auto 0
  git -C "$R" config fetch.prune true
}

clone_with_pool() {
  # $1 = kind(src|lib), $2 = destination path
  local kind="$1" dst="$2"
  local pool remote diss=""
  if [ "$DISSOCIATE" -eq 1 ]; then diss="--dissociate"; fi

  if [ "$kind" = "src" ]; then
    pool="$SRC_POOL"; remote="$SRC_REMOTE"
  else
    pool="$LIB_POOL"; remote="$LIB_REMOTE"
  fi

  git clone --reference "$pool" $diss "$remote" "$dst" >/dev/null
}

# Collect broken repos (worktree copies) by reading .git files that begin with "gitdir:"
mapfile -d '' GITFILES < <(find "$AGENT_ROOT" -type f -name .git -print0)

broken_repos=()
for gf in "${GITFILES[@]}"; do
  if head -n1 "$gf" 2>/dev/null | grep -q '^gitdir: '; then
    broken_repos+=( "${gf%/.git}" )
  fi
done

log "Found ${#broken_repos[@]} linked-worktree copies under $AGENT_ROOT"
log "Salvage dir: $SALVAGE_BASE"
log

fixed=0
skipped=0
dirty_count=0
failed=0

for R in "${broken_repos[@]}"; do
  kind="$(classify_repo "$R")"
  if [ "$kind" = "skip" ]; then
    log "SKIP (unknown type): $R"
    skipped=$((skipped+1))
    continue
  fi

  if [ ! -d "$R" ]; then
    log "SKIP (missing dir): $R"
    skipped=$((skipped+1))
    continue
  fi

  tag="$(echo "$R" | sed 's#^/##; s#[^A-Za-z0-9._-]#_#g')"
  P="$SALVAGE_BASE/$tag"

  log "==== $R  [$kind]"

  dirty=0
  if is_dirty "$R"; then
    dirty=1
    dirty_count=$((dirty_count+1))
    log "  dirty: yes (salvaging)"
    salvage_repo "$R" "$P"
  else
    log "  dirty: no"
    # still record branch so we can checkout same branch after rebuild
    git -C "$R" rev-parse --abbrev-ref HEAD > "${P}.branch" 2>/dev/null || echo master > "${P}.branch"
    : > "${P}.staged.patch"
    : > "${P}.unstaged.patch"
    : > "${P}.untracked.tgz"
  fi

  # Move aside and rebuild
  BROKEN="${R}.BROKEN.${STAMP}"
  mv "$R" "$BROKEN"

  if clone_with_pool "$kind" "$R"; then
    restore_repo "$R" "$P"
    log "  rebuilt: ok"
    git -C "$R" status --porcelain=v1 | sed 's/^/    /' || true
    fixed=$((fixed+1))
  else
    log "  ERROR: clone failed; original preserved at $BROKEN"
    failed=$((failed+1))
  fi

  log
done

log "Done."
log "Fixed:  $fixed"
log "Dirty:  $dirty_count (salvaged/restored)"
log "Skipped:$skipped"
log "Failed: $failed"
log "Salvage artifacts: $SALVAGE_BASE"
log "Originals moved to: <repo>.BROKEN.${STAMP}"
