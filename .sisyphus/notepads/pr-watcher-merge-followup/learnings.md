
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

## 2026-04-19 20:31:30Z — Full-scan validation and closed-PR cleanup findings (Atlas)

- The `validate_after_cutoffs` failure was not just placement; the throttled validation pass could skip nested reactions and leave `KEY_TO_LATEST_ACTIVITY_TIME` regressed to top-level activity. Moving validation after the full reporting pass and arming a forced nested scan when the validation pass skips nested endpoints fixes the reproduced `#109` restart case.
- Closed PRs must be treated as no longer participating in pending-actionable aggregation. Resetting review-cycle runtime state and clearing latest-activity fields before returning on a non-`OPEN` state prevents stale `KEY_TO_PENDING_PRECOMMIT_ACTIONABLE` from blocking approval success on other still-open PRs.
- Fresh evidence in `.sisyphus/evidence/task-latest-fixes.log` now shows `example/repo#109` timing out cleanly instead of failing `--after`, `example/repo#110 + #102` exiting `0` with the approval banner after `#110` closes, and explicit `#102` behavior staying green.

## 2026-04-19 21:24:10Z — All-PR approval requirement findings (Atlas)

- The previous success rule was still too loose: it allowed a single PR approval/no-issues signal to satisfy the global success condition as long as no actionable feedback was pending. That meant a second still-open PR with no approval yet could be silently skipped.
- The corrected rule is per-open-PR: success only happens when every still-open watched PR has produced its own approval/no-issues signal, while actionable feedback still wins immediately.
- Fresh evidence in `.sisyphus/evidence/task-all-pr-approval-fix.log` now shows `#102 + #104` exiting `0`, `#102 + #201` continuing to wait without a success banner, and `#107 + #102` still exiting `2` because actionable feedback outranks approval.

## 2026-04-19 22:31:10Z — Explicit codex-login override findings (Atlas)

- The live bug was in `is_codex_actor()`: even when `--codex-login` supplied a specific reviewer, the helper still accepted the hardcoded fallback aliases `codex` and `chatgpt-codex-connector`, so an approval from the wrong bot could still satisfy the watcher.
- The smallest safe fix was to introduce a `DEFAULT_CODEX_REVIEWER_LOGIN` constant and treat fallback aliases as valid only when the configured reviewer is still the default. Once the caller overrides `--codex-login`, matching becomes exact.
- Fresh evidence in `.sisyphus/evidence/task-codex-login-override-fix.log` now shows the default reviewer still approving `#102`, while `--codex-login custom-review-bot` blocks the fallback approval and keeps monitoring instead of exiting success.

## 2026-04-19 22:40:40Z — Initial-report nested reaction findings (Atlas)

- The live gap was specific to unthrottled reporting passes (`first_sweep()` / `--check-once`): once any newer top-level comment or review set `needs_nested_reaction_scan=false`, the final nested-reaction gate skipped issue/review comment reactions entirely because there was no preceding validation pass to arm the force flag.
- The smallest safe fix was to treat unthrottled scans as always eligible for nested reaction endpoints, while leaving the throttled polling path on the existing `needs_nested_reaction_scan` / force-flag rules.
- Fresh evidence in `.sisyphus/evidence/task-initial-report-fix.log` now shows `example/repo#111` scanning `initial_report_nested_issue_reactions.count=1` during `--check-once`, and the established forced-report polling proof for `#106` remains green.

## 2026-04-19 22:52:05Z — Throttle-preserving handoff findings (Atlas)

- The regression came from arming `KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN` even when a throttled validation pass skipped nested reactions. That made the immediate reporting pass re-enable nested endpoints every loop and defeated `REACTION_POLL_INTERVAL_SECONDS`.
- The correct fix was simply to stop arming the force flag on the skip path. The force handoff still works when the validation pass actually performs a nested scan, and the initial-report fix still covers unthrottled `--check-once` / `first_sweep` scans.
- Fresh evidence in `.sisyphus/evidence/task-throttle-preserving-fix.log` now shows `#103` back to `nested_issue_reactions.count=1` / `nested_review_reactions.count=1`, while the existing forced-report `#106` and initial-report `#111` proofs remain green.

## 2026-04-19 23:07:20Z — Approval reaction deduplication findings (Atlas)

- The live bug was noise, not correctness: once an approval reaction was above the baseline, the watcher would redisplay the same `NEW CODEX 👍` banner on every polling loop because reactions were never marked as reported.
- The smallest safe fix was to add a per-PR approval-report token set and use it only to suppress repeat banners. The approval state itself still counts toward final success, so deduplication does not block eventual approval exits.
- Fresh evidence in `.sisyphus/evidence/task-approval-dedupe-fix.log` now shows the mixed pending case printing the `#102` approval banner only once while continuing to wait, and the single-PR approval path still exits `0` with one approval banner.

## 2026-04-19 23:18:35Z — Check-once false-success findings (Atlas)

- Oracle was right: `--check-once` could print actionable old-cycle feedback and then still end with `✓ No pending activity.` because that branch never checked `any_pending_precommit_actionable()`.
- The smallest safe fix was to reuse the waiting semantics in the `CHECK_ONCE` path: if earlier actionable feedback is visible, print the waiting warning and return exit `2` instead of a false success.
- Fresh evidence in `.sisyphus/evidence/task-check-once-false-success-fix.log` now shows `#110` and mixed `#110 + #102` returning `2` with the waiting message, while the clean explicit-`--after` `#102` case still exits `0` with `✓ No pending activity.`

## 2026-04-20 01:39:10Z — Nested reaction failure messaging findings (Atlas)

- The live failure mode was exactly what Codex called out: nested issue/review reaction helpers were invoked directly under `set -e`, so one bad nested endpoint aborted the whole watcher with a raw exit `1` and no watcher-specific error context.
- The smallest safe fix was to wrap the nested helper calls at their loop sites with explicit `|| fail ...` messages. That preserves the current hard-fail behavior for bad nested endpoints, but makes the failure clear and operator-readable instead of looking like a random mid-scan crash.
- Fresh evidence in `.sisyphus/evidence/task-nested-reaction-failure-fix.log` now shows `example/repo#111` preserving already-surfaced output and then failing with `Failed to fetch nested review-comment reactions for example/repo#111 comment 1112.`, while clean `#102` behavior remains intact.

## 2026-04-20 02:12:40Z — Oracle follow-up UX fixes findings (Atlas)

- Oracle’s remaining UX concerns were all real and all small-scope: restart hints were incomplete for multi-PR runs, closed selectors could still confuse startup behavior, and `--codex-login` only changed actor matching without letting a clean alternate reviewer body count as approval.
- The restart hint is now a complete restart command for the same watch set, including the updated `--after` for the triggering PR plus any existing `--after` values for the other watched PRs.
- Closed selectors now no longer block startup monitoring of still-open PRs, and an explicit alternate reviewer with a clean “Didn’t find any major issues.” body now counts as approval. Fresh proof for all three fixes is in `.sisyphus/evidence/task-oracle-followup-fixes.log`.

## 2026-04-20 02:22:15Z — Restart hint codex-login preservation findings (Atlas)

- Oracle’s follow-up FAIL was a real last-mile UX gap: even after the restart-hint rewrite, a non-default `--codex-login` was still omitted from the generated command, so operators could silently fall back to the default reviewer identity on restart.
- The safe fix was tiny: when `CODEX_REVIEWER_LOGIN` differs from `DEFAULT_CODEX_REVIEWER_LOGIN`, prepend `--codex-login <value>` to the generated restart command.
- Fresh evidence in `.sisyphus/evidence/task-oracle-codex-login-restart-fix.log` now shows the custom reviewer override preserved in the restart hint, while the default case still omits the flag.

## 2026-04-20 02:31:50Z — Final Oracle follow-up findings (Atlas)

- Oracle’s second follow-up FAIL was also real: the restart hint still dropped `--check-once`, and the one-shot path still treated “review pending” and “review complete” as the same green success unless an old actionable comment had already been seen.
- The fixes were both surgical: preserve `--check-once` in generated restart commands when the current run used it, and make the `CHECK_ONCE` branch return a waiting exit/message whenever no approval/no-issues signal has been observed yet for the still-open PR set.
- Fresh evidence in `.sisyphus/evidence/task-oracle-final-followup-fixes.log` now shows the custom restart command preserving both `--check-once` and `--codex-login`, a pending-review snapshot returning exit `2` with an explicit waiting message, and the acknowledged-clean / alternate-reviewer approval paths still succeeding.

## 2026-04-20 02:43:30Z — Actual-head Oracle follow-up findings (Atlas)

- The prior Oracle review was stale against the live root-branch head, so I reran the UX checks directly on the current branch and fixed the same two operator-facing gaps in the actual file: restart hints now preserve both `--check-once` and non-default reviewer overrides, and one-shot runs now return a distinct pending-review status instead of a false-green success.
- Fresh evidence in `.sisyphus/evidence/task-oracle-actual-head-followup.log` shows those behaviors working on the real branch head. Nested reaction failures still fail clearly at the specific comment endpoint; when the underlying `gh` error text is available, the helper now preserves it for fail messages.

## 2026-04-20 03:02:20Z — Clarified Oracle blocker reconciliation (Atlas)

- Oracle later flagged stale pre-commit actionable state surviving a later approval/no-issues signal, but under the user’s clarified intent that is not a bug: earlier actionable feedback should still trigger an agent-handling exit once the later review-cycle boundary arrives, so the agent can process both together.
- The genuinely valid UX fixes from that pass were narrower: fully closed startup should not exit green, and closed-PR status should not use success-style wording. Those fixes remain the only code changes I’m carrying forward from that review pass.
