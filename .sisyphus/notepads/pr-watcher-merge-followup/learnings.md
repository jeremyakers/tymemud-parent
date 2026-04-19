
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

## 2026-04-19 16:05:00Z — Timeout wording follow-up findings (Sisyphus-Junior)

- The reviewer concern was documentation-only: the prior wording made `timeout 2h ./watch-prs-for-comments.sh ...` read like the main enforcement point, but the real enforced limit is the OpenCode agent tool timeout set to `7200000` ms.
- The safest wording keeps the shell command examples simple foreground watcher invocations, then states separately that `timeout 2h` is only a valid plain-shell wrapper example when the watcher is launched outside the OpenCode tool wrapper.
- The workflow contract still needs explicit sequencing language in both docs: print the PR URL first, start the watcher immediately after that, keep it in the foreground, and do not pause for approval between those steps.

## 2026-04-19 16:49:20Z — Forced report nested reaction gate findings (Sisyphus-Junior)

- The confirmed live bug was exactly the final nested-reaction execution gate: `force_report_nested_reaction_scan` could reopen `should_scan_nested_reaction_endpoints`, but the later `needs_nested_reaction_scan` check still suppressed the forced reporting pass after new top-level actionable feedback.
- The smallest safe fix was to let `force_report_nested_reaction_scan` satisfy that same final gate directly, leaving the throttle interval, arming/reset behavior, and two-pass `monitor_loop()` flow unchanged.
- Fresh deterministic evidence in `.sisyphus/evidence/task-force-report-fix.log` now shows `example/repo#106` surfacing the nested Codex `+1` as `Type: issue comment reaction` with `nested_issue_reactions=3`, while `example/repo#103` still pins `nested_issue_reactions=1` and `nested_review_reactions=1` with top-level counters at `9`.
- The preserved regression checks remained green in the same bundle: `example/repo#105` still exits `2` for actionable precedence, and `example/repo#107` still follows the restart-race path with explicit `--after` seeding and exit `2`.

## 2026-04-19 17:05:00Z — Shell-timeout cleanup findings (Sisyphus-Junior)

- The reviewer requirement was stricter than the earlier follow-up wording: even calling `timeout 2h ./watch-prs-for-comments.sh ...` a valid plain-shell example was too permissive and had to be removed entirely from watcher-facing docs.
- The safe cleanup was purely documentation-level in `.opencode/skill/pr-monitor.md` and `rules/803-project-git-workflow.md`, with the 2 hour guidance retained only as the OpenCode tool timeout value, `7200000` ms.
- The strongest QA proof for this pass is one grep-driven artifact, `.sisyphus/evidence/task-timeout-guidance-cleanup.log`, because it shows both absence and preservation in one place: no `timeout 2h` matches remain in the touched docs, and the immediate PR URL, start-now, foreground-monitoring language still exists.

## 2026-04-19 17:13:19Z — Bash-tool timeout wording findings (Sisyphus-Junior)

- The reviewer wanted one more level of precision beyond “OpenCode tool timeout”: the docs now need to name the OpenCode `bash` or `shell` tool invocation directly so agents do not mistake this for a generic timeout on any tool.
- The clearest wording is to pair the scope and the limit in one sentence: use the longest timeout allowed on the `bash` or `shell` tool, currently `7200000` ms, which is 2 hours.
- The safest way to preserve workflow behavior is to leave the watcher command examples as plain foreground `./watch-prs-for-comments.sh ...` invocations and keep the timeout guidance in prose, not in a shell wrapper example.

## 2026-04-19 18:46:22Z — Explicit after cutoff follow-up findings (Sisyphus-Junior)

- The live bug was exactly the helper boundary in `watch-prs-for-comments.sh`: `effective_baseline_for_key()` still treated operator `KEY_TO_AFTER` and runtime surfaced cursors as one clamped path, so a valid post-commit explicit `--after` on `example/repo#102` got forced backward to the `10:00` commit timestamp and re-surfaced the `10:05` approval.
- The smallest safe fix was to make explicit `KEY_TO_AFTER[$key]` authoritative before any runtime cursor math, while leaving the surfaced `KEY_TO_SURFACED_CURSOR` path behind `runtime_baseline_cursor()` unchanged so the restart-race rewind/clamp behavior for `example/repo#107` still holds.
- Fresh fixture evidence in `.sisyphus/evidence/task-explicit-after-fix.log` now shows the intended split: `example/repo#102` with `--after ...10:05:00Z` exits `0` with `✓ No pending activity.` and no approval banner, while `example/repo#105` still exits `2`, `example/repo#107` still exits `2` after the waiting message, and the mixed-repo repeated `--after` pair still exits `0` cleanly.

## 2026-04-19 19:18:40Z — Head-change runtime reset findings (Atlas)

- The live bug was the commit-refresh boundary in `refresh_pr_state()`: the watcher updated `KEY_TO_LAST_COMMIT` for a new head but kept cycle-scoped runtime state alive, so stale pre-commit pending/actionable markers could leak into the next review cycle and manufacture a false actionable exit.
- The smallest safe fix was to introduce `KEY_TO_HEAD_SHA` as the review-cycle identity, reset only runtime cycle maps on SHA change, and leave `KEY_TO_AFTER` untouched so explicit operator restarts still work exactly as before.
- Fresh fixture evidence in `.sisyphus/evidence/task-head-reset-fix.log` now shows `example/repo#108` logging `new commit detected` and exiting `0` on a later no-issues signal instead of exiting `2`, while the preserved explicit-`--after` (`#102`), restart-race (`#107`), and actionable precedence (`#105`) proofs stay green.

## 2026-04-19 20:13:00Z — Multi-PR approval priority findings (Atlas)

- The live bug was in the final approval-success exits: `APPROVAL_SIGNAL_FOUND` is global, but pending actionable state is tracked per PR, so a success on PR B could incorrectly return exit `0` while PR A was still waiting on earlier actionable feedback.
- The smallest safe fix was to add a tiny `any_pending_precommit_actionable()` helper and use it only to guard the two approval-success exit branches. That preserves the existing scan/aggregation flow while enforcing actionable-over-approval across all watched PRs.
- Fresh evidence in `.sisyphus/evidence/task-multi-pr-approval-fix.log` now shows the mixed `example/repo#107 example/repo#102` run timing out with the pending-actionable wait message instead of exiting `0`, while single-PR approval on `#102` still exits `0` and restart-race `#107` still exits `2`.
