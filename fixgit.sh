OLD='/home/jeremy/cursor/tymemud/MM32'
NEW='/home/jeremy/tymemud/_human_work/MM32'   # change if your new root differs

# Fix all worktree pointer files
find . -name .git -type f -print0 | xargs -0 sed -i "s|$OLD|$NEW|g"
