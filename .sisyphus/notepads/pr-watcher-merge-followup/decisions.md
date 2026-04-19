
## 2026-04-19 03:59:22Z — Task 1 freeze boundaries (Sisyphus-Junior)

### Root authority that must remain intact
- `watch-prs-for-comments.sh:156-174` `parse_repo_pr_token` remains the canonical mixed-repo selector/parser. Future tasks must not replace or bypass it with donor single-repo assumptions.
- `watch-prs-for-comments.sh:422-546` `scan_pr_activity` remains the canonical fetch/order/latest-activity pipeline. Future tasks may insert classification/throttle checks inside this flow only; they must not replace the function with donor seen-state logic.
- `watch-prs-for-comments.sh:548-627` `resolve_after_mappings` and `validate_after_cutoffs` remain the canonical repeated per-PR `--after owner/repo#123=<timestamp>` architecture. No donor global cutoff model is allowed.
- `watch-prs-for-comments.sh:656-829` `parse_args`, `resolve_pr_targets`, `prime_latest_activity`, `first_sweep`, and `monitor_loop` remain the canonical control flow. Future tasks must preserve first-sweep full scanning and the current two-pass polling validation/report pattern.

### allowed donor concepts
- Borrow the narrow comment classifier idea from donor `is_codex_no_issues_comment()` (`_agent_work/sisyphus_pr_comment_watcher/watch-prs-for-comments.sh:206-220`), but transplant it as a root-local helper that feeds root precedence rules instead of donor seen-state.
- Borrow the approval-specific outcome concept from donor first-sweep/polling approval exits (`...:610-645` and `...:771-794`), but express it inside root exit semantics so actionable feedback still exits 2 and approval/no-issues exits 0.
- Borrow only the bounded nested-reaction throttling concept from donor `should_scan_comment_reactions()` (`...:237-254`) for long-running polling iterations. Scope is limited to nested issue-comment and review-comment reaction endpoints.

### forbidden donor imports
- Forbidden donor global `AFTER_TIMESTAMP` architecture (`...:18`, `34`, `496-526`): root must keep per-PR `KEY_TO_AFTER` plus `resolve_after_mappings`.
- Forbidden donor seen-state structures `SEEN_COMMENT_IDS` / `SEEN_REACTION_IDS` and mark-seen helpers (`...:103-104`, `256-412`, `483-527`, `686-713`). Root detection must stay baseline/time-based, not restart-persistent ID tracking.
- Forbidden donor init/loop control flow (`...:458-530`, `538-645`, `656-798`). Root initialization, prime pass, first sweep, and monitor loop remain authoritative.
- Forbidden donor `$BASELINE` usage at `...:756`. Future work must not copy any logic that compares against undeclared `$BASELINE`; root already uses explicit per-call baselines.
- Forbidden donor weakening of mixed-repo selectors or repeated per-PR `--after` validation.

### Minimal insertion points for upcoming tasks
- Task 2 insertion point: inside root `scan_pr_activity()` review/comment/reaction processing (`watch-prs-for-comments.sh:450-529`). Add a centralized approval/no-issues classifier/outcome accumulator here so precedence is enforced inside the root scan pipeline: actionable feedback > approval/no-issues > no activity.
- Task 2 output/exit insertion point: root `first_sweep()` / `main()` exit path (`watch-prs-for-comments.sh:742-865`). Add a distinct approval/no-issues success path without altering the existing actionable exit 2 path.
- Task 3 insertion point: root nested reaction gate at `watch-prs-for-comments.sh:531-545` plus polling loop at `794-828`. Apply throttling only when `report_new=false` during repeated monitor iterations; do not throttle first-sweep or `--check-once`.

### Regression risks and avoidance rules
- Latest-activity validation risk: if approval/no-issues events are classified without calling `register_latest_activity`, `validate_after_cutoffs` can incorrectly accept too-late cutoffs. Avoid this by registering approval/no-issues timestamps before any precedence filtering.
- Baseline risk: do not introduce separate donor-style comment/approval baselines that bypass root `KEY_TO_AFTER[$key]:-${KEY_TO_LAST_COMMIT[$key]}` usage unless fixtures prove necessity. Root latest-activity bookkeeping and repeated `--after` validation depend on the existing per-call baseline contract.
- Polling risk: throttling must not suppress top-level PR reactions or initial nested scans, otherwise approval/no-issues signals may be delayed and latest activity snapshots become stale. Restrict throttling to nested reaction endpoints during long-running polling only.
- Scope risk: root `parse_repo_pr_token`, `resolve_after_mappings`, and `validate_after_cutoffs` are frozen boundaries for later tasks and QA.

## 2026-04-19 04:16:40Z — Task 2 implementation decisions (Sisyphus-Junior)

- Implemented Task 2 with one new global outcome flag, `APPROVAL_SIGNAL_FOUND`, instead of donor seen-state or alternate loop control. Root control flow remains `first_sweep()` / `main()` / `monitor_loop()`.
- Kept the classifier narrow and centralized: `is_codex_no_issues_body()` accepts only Codex-authored text matching the donor phrase prefix `Codex Review: Didn't find any major issues.` after whitespace normalization.
- Applied approval/no-issues detection only at the existing root scan sites: issue comments, submitted review bodies, PR reactions, issue-comment reactions, and review-comment reactions. Inline review comments remain actionable; Task 2 did not broaden the taxonomy beyond the frozen scope.
- Enforced precedence exclusively in the root exit path: actionable feedback (`NEW_SIGNAL_FOUND`) exits 2 before approval/no-issues (`APPROVAL_SIGNAL_FOUND`) exits 0, which preserves the required `actionable > approval/no-issues > no activity` ordering.
- Added a minimal `.sisyphus/testbin/gh` fixture because the required harness path was absent in this worktree. The fixture is intentionally limited to the Task 2 scenarios for `example/repo#102` and `example/repo#105` plus the nested reaction endpoints the root watcher still touches during full first-sweep scans.

## 2026-04-19 04:57:18Z — Task 3 stable harness grouping decision (Sisyphus-Junior)

- Chose watcher-exported `GH_FIXTURE_RUN_ID` as the fixture aggregation key instead of `PPID`, because individual `gh api` calls can run under different parent shells and scatter counters across many directories.
- Kept the throttle implementation process-local in `watch-prs-for-comments.sh`: the watcher still owns nested-reaction throttle state through `KEY_TO_NESTED_REACTION_SCAN_EPOCH`, while the fixture harness only records endpoint counts for evidence.
- Preserved first-sweep semantics by continuing to call `scan_pr_activity(..., false)` for `first_sweep()` / `--check-once`; only polling-loop calls pass `true` for nested-reaction throttling.
- Preserved top-level PR reaction behavior by leaving the PR-reaction fetch/scan path outside the nested-reaction throttle gate; the loop evidence relies on those counters continuing to advance even while nested counters stay flat.

## 2026-04-19 12:09:12Z — Task 4 documentation decisions (Sisyphus-Junior)

- Updated `.opencode/skill/pr-monitor.md` only. `rules/803-project-git-workflow.md` already matched the required foreground watcher workflow and already warned against background or tmux-by-default guidance, so Task 4 did not broaden that rule.
- Put the new behavior in three watcher-facing places: the main flow steps, a dedicated outcome-priority section, and the exit-code table. That keeps approval or no-issues visible without changing the established foreground usage guidance.
- Documented throttling as loop-only optimization language, with explicit first-sweep and `--check-once` full-scan wording plus an explicit non-persistence statement, so the docs cannot be read as promising seen-state memory or restart persistence.

## 2026-04-19 12:34:00Z — Task 5 validation decisions (Sisyphus-Junior)

- Extended `.sisyphus/testbin/gh` instead of the watcher so Task 5 remained validation-only. The additions were limited to deterministic fixture coverage for `example/repo#104`, `example/other#201`, and repo-aware `gh pr view --repo ...` URL rendering.
- Used `example/repo#102` + `example/other#201` as the mixed-repo regression pair because they let the matrix prove both canonical owner-qualified selector parsing and repeated explicit `--after owner/repo#pr=<timestamp>` mapping with zero live dependencies.
- Kept the polling proof keyed by `GH_FIXTURE_RUN_ID=task5-throttle` so the final evidence can point at one stable counter directory and show the required throttle invariant directly: top-level poll endpoints continue advancing, nested reaction endpoints do not.

## 2026-04-19 12:46:54Z — F2 reaction surfacing decision (Sisyphus-Junior)

- Added one root-local helper, `record_reaction_approval()`, to keep `register_latest_activity`, approval flagging, and `display_reaction()` coupled for all supported reaction approval paths. This removes the dead-helper regression without broadening watcher control flow.
- Switched Task 5's primary approval fixture for `example/repo#102` from a no-issues comment to a Codex `+1` PR reaction, and added an explicit `reaction_approval_rendering` evidence block plus boolean pattern checks so QA can verify rendered reaction output instead of inferring it from exit code `0`.

## 2026-04-19 14:22:00Z — Polling nested approval fix decision (Sisyphus-Junior)

- Kept `monitor_loop()`'s two-pass structure unchanged and added one root-local per-PR handoff flag, `KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN`, instead of importing donor seen-state or removing throttle globally.
- The validation pass now sets that flag only when a throttled polling scan actually reaches nested reaction endpoints. The immediately following reporting pass may consume that one-loop override, after which the flag is cleared. This fixes the masked-approval regression without broadening nested rescans on ordinary loops.
- Extended `.sisyphus/testbin/gh` with one deterministic polling fixture, `example/repo#106`, whose old issue comment gains a Codex `+1` only after monitoring has started. That fixture is narrowly scoped to prove the live regression and does not alter the older first-sweep, mixed-repo, or throttle fixtures.

## 2026-04-19 15:05:00Z — Corrected polling proof decision (Sisyphus-Junior)

- Left `watch-prs-for-comments.sh` unchanged. After reproducing the hang, the root cause was the proof harness: the old `example/repo#106` command modeled a startup-window case with no elapsed polling interval, so it never exercised the validation-pass-to-reporting-pass handoff that the live bug report described.
- Added one minimal opt-in shim at `.sisyphus/testbin/date` and used it only in the corrected proof command: `PATH="$PWD/.sisyphus/testbin:$PATH" GH_FIXTURE_TIME_SCENARIO="polling-nested-handoff" ./watch-prs-for-comments.sh example/repo#106`. This makes the validation pass cross the interval boundary first, while the immediate reporting pass stays in the same interval and must rely on the existing handoff flag to surface the approval.
- Kept the established throttle evidence on `example/repo#103` under a separate fixed run id with no time shim. That preserves the prior contract proof: `nested_issue_reactions=1`, `nested_review_reactions=1`, and top-level counters at `9`.

## 2026-04-19 15:40:00Z — Restart race fix decisions (Sisyphus-Junior)

- Added three root-local runtime state maps in `watch-prs-for-comments.sh`: `KEY_TO_SURFACED_CURSOR`, `KEY_TO_PENDING_PRECOMMIT_ACTIONABLE`, and `KEY_TO_REPORTED_ACTIONABLE_KEYS`. This keeps the architecture baseline-driven while giving the watcher enough per-PR state to distinguish “printed already” from “durably acknowledged.”
- Kept `KEY_TO_AFTER` durable and operator-owned. Observation-only passes never mutate it; only runtime surfaced state changes in-process, so accidental watcher observation cannot silently advance the restart seed.
- Defined the effective scan baseline as the earlier of latest commit metadata and the runtime cursor seed, where the runtime cursor is the explicit `--after` seed until something actionable is surfaced. Once actionable feedback is printed, the runtime baseline rewinds that surfaced second by one second so same-timestamp follow-up activity is re-fetched safely.
- Treated pre-latest-commit actionable comments and review bodies as visible-but-pending instead of immediate exits, and treated post-latest-commit review activity or approval/no-issues signals as the exit boundary when pending pre-commit actionable feedback exists. That preserves `actionable > approval/no-issues > no activity` while still waiting for the latest review cycle to finish.
- Added one focused fixture, `example/repo#107`, to `.sisyphus/testbin/gh` instead of broadening the harness architecture. It models the settled race directly: earlier actionable comment, later post-commit review boundary, single consolidated actionable exit.
