while IFS=' -> ' read -r gitfile gitdir; do
  repo="${gitfile%/.git}"
  echo "=== $repo"
  git -C "$repo" status --porcelain=v1 | sed 's/^/  /' || echo "  (git status failed)"
  echo
done < <(
  find ~/tymemud/_agent_work -type f -name .git -print0 \
  | xargs -0 -r awk 'FNR==1 && $1=="gitdir:" { printf "%s -> %s\n", FILENAME, $2 }'
)
