find ~/tymemud/_agent_work -type f -name .git -print0 \
| xargs -0 -r awk '
  FNR==1 && $1=="gitdir:" {
    repo=FILENAME
    sub(/\/\.git$/, "", repo)
    cmd = "git -C \"" repo "\" status --porcelain=v1 2>/dev/null"
    cmd | getline line
    close(cmd)
    if (line != "")
      printf "%s  (%s)\n", repo, substr(line,1,2)
  }
'
