# Learnings — pr-comment-watcher-fixes

- The current watcher is single-repo and single-global-`--after`; mixed-repo and per-PR cutoff support must be introduced in the parser and carried through all state tables.
- The current implementation only watches PR conversation comments (`gh pr view --json comments`) and review comments (`gh api repos/$REPO/pulls/$PR_NUM/comments`); it does not yet watch review bodies or any reaction surfaces.
- `SEEN_REACTION_IDS` and `--codex-login` are dead scaffolding in the current script and can be repurposed or replaced during the reaction implementation.
- The existing false-success path comes from initialization `continue` on failed PR fetch plus `ALL_CLOSED=true` loop logic; bad repo selection must become an error state, not an implicit "all closed" result.
- The existing skill doc still recommends background/tmux usage and documents only a global `--after`; the doc rewrite must explicitly flip that to foreground `timeout 2h` and per-PR `--after <selector>=<timestamp>` guidance.
- Replacing the script file dropped its executable bit, so verification must include a direct `./watch-prs-for-comments.sh ...` invocation and the implementation must restore execute permissions.
- With Bash arrays, `${ARRAY[@]:-}` is unsafe here because it yields a synthetic empty element when the array is empty; the watcher parser must iterate over `${ARRAY[@]}` directly or it will invent a blank `--after` value.
- To keep `--after` mistake-proof, repeated cutoffs for the same PR should be rejected explicitly rather than silently letting the last one win.
- Beyond the dedicated watcher skill doc, `rules/803-project-git-workflow.md` is the main broader workflow doc that needs to tell agents to print the PR URL and immediately start foreground monitoring with `timeout 2h`.
- ShellCheck is useful here not just for syntax: it immediately caught an unused reaction-loop local after the large rewrite, so the watcher should be shellchecked before any live PR validation is treated as trustworthy.
- On busy PRs, nested per-comment reaction fetches are the expensive path. The watcher should scan direct comments/reviews/PR reactions first and only crawl nested comment-reaction endpoints when those are still needed to detect or validate activity.
- Final plan completion is now blocked only by the plan's explicit requirement that the user reply with approval before F1-F4 can be checked off.
- Git operations in this workspace can leave a stale `.git/index.lock`; verify no live git process owns it before removing the lock and retrying the command.
