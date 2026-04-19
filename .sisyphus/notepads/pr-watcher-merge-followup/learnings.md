
## 2026-04-19 03:59:22Z — Task 1 findings (Sisyphus-Junior)

- The root watcher already has the right architecture for multi-PR/mixed-repo monitoring: `parse_repo_pr_token`, `resolve_after_mappings`, and `validate_after_cutoffs` together enforce selector normalization and per-PR cutoff safety.
- The donor watcher contributes only three reusable ideas: an explicit no-issues phrase classifier, a distinct approval completion path, and an interval gate for nested reaction rescans. Everything else in the donor is structurally incompatible with the root script.
- In the root watcher, `scan_pr_activity()` is the safe merge seam because it already centralizes fetch order, `register_latest_activity`, and new-signal display behavior.
- The donor's seen-state architecture would regress the root watcher because it swaps root time/baseline reasoning for mutable ID memory and a single global-after model.
- The donor `$BASELINE` comparison near line 756 is a concrete do-not-copy marker; later tasks should continue using explicit local baselines threaded through root calls instead.
- First-sweep semantics are part of the frozen contract: full scan on startup/check-once, throttle only inside repeated polling.

## 2026-04-19 04:16:40Z — Task 2 findings (Sisyphus-Junior)

- The narrow no-issues classifier works cleanly as a root-local helper when it is limited to Codex-authored bodies beginning with `Codex Review: Didn't find any major issues.` and reused from both issue-comment and submitted-review-body scan paths.
- Treating Codex `+1` reactions as approval/no-issues instead of actionable feedback preserves the root scan order while making precedence explicit: comments/reviews still set `NEW_SIGNAL_FOUND`, approval/no-issues sets `APPROVAL_SIGNAL_FOUND`, and the exit path resolves `NEW` before `APPROVAL`.
- Latest-activity bookkeeping stayed correct because the script still calls `register_latest_activity` before any approval/actionable filtering; the `--after example/repo#102=2026-04-18T10:06:00Z` sanity check failed with the approval comment timestamp `2026-04-18T10:05:00Z` as intended.
- This tree did not contain the expected `.sisyphus/testbin` harness, so Task 2 needed a minimal fake `gh` fixture at `.sisyphus/testbin/gh` to make the required `example/repo#102` and `#105` scenarios deterministic.

## 2026-04-19 04:57:18Z — Task 3 harness/throttle findings (Sisyphus-Junior)

- The reliable fixture grouping point is the watcher process itself, not `PPID`: exporting `GH_FIXTURE_RUN_ID=watcher-$$` from `watch-prs-for-comments.sh` lets every fake `gh api` call in one watcher invocation accumulate into a single `.sisyphus/evidence/gh-fixture-watcher-<pid>/` directory.
- The `example/repo#103` check-once fixture now proves first-sweep behavior cleanly with one coherent run summary: `nested_issue_reactions=1` and `nested_review_reactions=1` alongside one call each to the top-level issue-comment, review-comment, review, and PR-reaction endpoints.
- The 3-second polling fixture now proves throttle behavior deterministically: top-level endpoints advanced to `9` calls in the run summary while both nested reaction counters stayed at `1`, confirming that repeated loop iterations kept scanning top-level activity but did not re-hit nested reaction endpoints inside the throttle window.
- Keeping the accelerated `.sisyphus/testbin/sleep` shim in PATH remains the fastest deterministic way to exercise multiple polling iterations without changing the production watcher sleep cadence.

## 2026-04-19 12:09:12Z — Task 4 documentation findings (Sisyphus-Junior)

- The watcher-facing skill needed an explicit outcome split because the prior wording documented only actionable activity and generic no-activity success, which hid the new approval or no-issues success path added in Task 2.
- The clearest way to document precedence was to state it directly in watcher terms: actionable feedback wins, approval or no-issues succeeds only when no actionable signal is present, and no activity remains the keep-waiting state outside `--check-once`.
- The throttling note needed to say two things at once to stay true to Task 3: first sweep and `--check-once` still do full nested scans, and throttling is only a repeated-polling optimization for nested reaction rescans, not persistent state.

## 2026-04-19 12:34:00Z — Task 5 validation findings (Sisyphus-Junior)

- The existing fake-`gh` harness already covered the approval, actionable-precedence, and polling-throttle scenarios; Task 5 only needed minimal fixture expansion for `example/repo#104` and `example/other#201` to prove invalid-future `--after` correction and real mixed-repo selector handling without live GitHub state.
- The merged watcher matrix now has one deterministic proof bundle in `.sisyphus/evidence/task-5-validation.log`: shellcheck passes, actionable precedence exits `2`, approval/no-issues exits `0` with the distinct success message, mixed-repo owner-qualified selectors initialize correctly, repeated per-PR `--after` suppresses only the intended PRs, and invalid future `--after` fails with the latest activity type/timestamp.
- The polling-loop throttle evidence is strongest when read from the stable fixture directory rather than stdout alone: `.sisyphus/evidence/gh-fixture-task5-throttle/` shows top-level endpoints advancing to `9` calls while `nested_issue_reactions` and `nested_review_reactions` stay pinned at `1`, proving loop-only throttling without suppressing first-sweep scans.

## 2026-04-19 12:46:54Z — F2 reaction contract findings (Sisyphus-Junior)

- The root watcher already preserved the approval outcome split; the regression was only in reaction presentation. Restoring banner output at the reaction branches fixed the missing event/timestamp/restart-hint contract without touching precedence, baselines, or polling flow.
- A deterministic top-level PR reaction fixture on `example/repo#102` is the smallest stable proof because it exercises `display_reaction()` directly while leaving the invalid-`--after`, mixed-repo, and loop-throttle evidence intact.

## 2026-04-19 13:49:00Z — PR handoff findings (Sisyphus-Junior)

- The live GitHub repo for this checkout is `jeremyakers/tymemud-parent`, not `jeremyakers/tymemud-src`, so the release handoff PR and watcher selector must target `jeremyakers/tymemud-parent#6`.
- Branch `sisyphus/pr-comment-watcher-fixes` already had a closed PR (`#4`), but after pushing fresh commits GitHub accepted a new PR (`#6`) from the same branch without requiring a branch rename.
- The foreground watcher startup for the fresh PR reported `No pending activity. Starting monitor...` on its first sweep, which is the expected clean handoff state immediately after PR creation.

## 2026-04-19 14:22:00Z — Polling nested approval regression findings (Sisyphus-Junior)

- The live regression was not in classification or latest-activity bookkeeping; it was the immediate monitor-loop handoff between the throttled validation pass and the throttled reporting pass. When the validation pass hit nested reaction endpoints first, it consumed the per-PR throttle window before the reporting pass could surface the same approval.
- A blanket unthrottle on every reporting pass was too broad: it fixed `example/repo#106`, but it also regressed the established throttle invariant for `example/repo#103` by re-hitting nested reaction endpoints on every polling iteration.
- The stable proof pair is now complementary: `.sisyphus/evidence/task-5-validation.log` shows `example/repo#106` rendering a polling-time `issue comment reaction` approval with `nested_issue_reactions=3`, while the same bundle keeps `example/repo#103` at `nested_issue_reactions=1` and `nested_review_reactions=1` with top-level counters at `9`.

## 2026-04-19 15:05:00Z — Corrected polling proof findings (Sisyphus-Junior)

- The previous `example/repo#106` proof was invalid because it never modeled elapsed nested-reaction time between first sweep and the first polling validation pass. With plain `PATH="$PWD/.sisyphus/testbin:$PATH" ./watch-prs-for-comments.sh example/repo#106`, the watcher correctly stayed idle and timed out because `should_scan_nested_reactions()` never reopened the interval.
- The existing watcher handoff fix is sufficient for the real Codex bug once the interval is modeled correctly. The real deterministic proof needs three nested issue-reaction fetches in one run: first sweep sees nothing, the throttled validation pass reaches the nested endpoint and sees the new `+1`, and the immediate reporting pass re-fetches and renders it.
- The minimal reproducible way to model that interval is an opt-in `date` shim, not another watcher change. `.sisyphus/testbin/date` only activates when `GH_FIXTURE_TIME_SCENARIO=polling-nested-handoff` is set, so the normal throttle fixture for `example/repo#103` still stays at one nested issue-reaction scan and one nested review-reaction scan.

## 2026-04-19 15:40:00Z — Restart race fix findings (Sisyphus-Junior)

- The unsafe part of the old watcher was not commit refresh by itself; it was using `KEY_TO_LAST_COMMIT` as both metadata and implicit acknowledgement state. Splitting “latest commit timestamp” from a runtime surfaced cursor fixed the restart race without importing donor seen-state.
- A surfaced timestamp alone is still too weak when multiple events share the same second. The stable minimal fix was to rewind only the runtime surfaced cursor by one second when computing the next baseline, then suppress duplicates with per-event tokens scoped to the current watcher process.
- The deterministic `example/repo#107` fixture proves the exact operator-visible behavior the user wanted: first sweep prints the pre-commit actionable comment at `2026-04-18T09:55:00Z`, the watcher keeps waiting with an explicit latest-cycle warning, and a later post-commit no-issues review boundary at `2026-04-18T10:06:00Z` causes one consolidated exit `2`.
- The preserved contract evidence stayed intact in the same proof bundle: `example/repo#105` still exits `2` for actionable-over-approval precedence, mixed-repo selectors still initialize `example/repo#102` and `example/other#201` together, repeated per-PR `--after` still works, and the throttle fixture still shows top-level counters at `9` while nested reaction counters remain `1`.
