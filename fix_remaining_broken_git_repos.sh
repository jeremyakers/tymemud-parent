set -euo pipefail
STAMP=$(date +%s)
SALV="/tmp/agent_salvage_extra_${STAMP}"
mkdir -p "$SALV"

SRC_POOL="$HOME/tymemud/_pool/tymemud-src.git"
SRC_REMOTE="git@github.com:jeremyakers/tymemud-src.git"

fix_one() {
  R="$1"
  tag=$(echo "$R" | sed 's#^/##; s#[^A-Za-z0-9._-]#_#g')
  P="$SALV/$tag"

  echo "==== $R"

  BR=$(git -C "$R" rev-parse --abbrev-ref HEAD 2>/dev/null || echo master)
  echo "$BR" > "${P}.branch"

  git -C "$R" diff --staged > "${P}.staged.patch" 2>/dev/null || true
  git -C "$R" diff         > "${P}.unstaged.patch" 2>/dev/null || true

  git -C "$R" ls-files -o --exclude-standard > "${P}.untracked.list" 2>/dev/null || true
  if [ -s "${P}.untracked.list" ]; then
    tar -C "$R" -czf "${P}.untracked.tgz" -T "${P}.untracked.list"
  else
    : > "${P}.untracked.tgz"
  fi

  mv "$R" "${R}.BROKEN.${STAMP}"
  git clone --reference "$SRC_POOL" "$SRC_REMOTE" "$R" >/dev/null

  # checkout/track branch
  if git -C "$R" show-ref --verify --quiet "refs/remotes/origin/$BR"; then
    git -C "$R" checkout -b "$BR" "origin/$BR" >/dev/null
  else
    git -C "$R" checkout -b "$BR" >/dev/null
  fi

  git -C "$R" apply "${P}.unstaged.patch" 2>/dev/null || true
  git -C "$R" apply --index "${P}.staged.patch" 2>/dev/null || true
  if [ -s "${P}.untracked.tgz" ]; then
    tar -C "$R" -xzf "${P}.untracked.tgz" 2>/dev/null || true
  fi

  git -C "$R" config maintenance.auto false
  git -C "$R" config gc.auto 0
  git -C "$R" config fetch.prune true

  git -C "$R" status --porcelain=v1 | sed 's/^/  /'
  echo
}

fix_one /home/jeremy/tymemud/_agent_work/gpt52_agent/MM32_src_defensefix
fix_one /home/jeremy/tymemud/_agent_work/gpt52_agent/MM32_src_loginprompt

echo "Salvage artifacts: $SALV"
