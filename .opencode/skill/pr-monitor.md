# PR Comment Monitor Skill

Monitor one or more GitHub PRs for actionable post-baseline review activity without losing the current agent session.

The watcher is **merge-only for success**. It does **not** treat Codex `+1` reactions or no-issues review bodies as completion signals.

## When to Use

- Immediately after opening a PR
- When the same agent should stay responsible for incoming review feedback
- When monitoring multiple PRs in one repo or across multiple repos

## Mandatory Agent Workflow

Before opening a PR, and again before pushing any new commits to an already-open PR branch, agents must get a fresh Oracle signoff on the exact code they are about to publish.

After opening a PR, agents must do this in order:

1. **Print the PR URL to the user in chat immediately**
2. **Start the watcher immediately after that**
3. **Run it in the foreground**
4. **When using the OpenCode `bash` or `shell` tool invocation, set that tool timeout to the longest allowed value, currently `7200000` ms, which is 2 hours**
5. **Do not pause to ask the user whether to start monitoring** unless the watcher cannot be started

Canonical post-PR flow:

```bash
# 1. Create the PR
gh pr create --title "fix: ..." --body "..."

# 2. Print the returned PR URL to the user in chat
# Example: https://github.com/owner/repo/pull/123

# 3. Immediately start foreground monitoring
./watch-prs-for-comments.sh owner/repo#123
```

The workflow timeout requirement here applies only to the OpenCode `bash` or `shell` tool invocation that starts the watcher. Use the longest timeout allowed on that tool, currently `7200000` ms, which is 2 hours.

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- `jq` installed
- `watch-prs-for-comments.sh` available in the project root or your PATH

## Canonical CLI Forms

### Mixed-repo / explicit form

Use `owner/repo#123` when you want zero ambiguity:

```bash
./watch-prs-for-comments.sh jeremyakers/tymemud-src#104
./watch-prs-for-comments.sh jeremyakers/tymemud-src#104 jeremyakers/tymemud-lib#63
```

This is the **recommended** form.

### Legacy same-repo form

If all PRs are in the same repo, the watcher still supports `--repo owner/repo` plus bare PR numbers:

```bash
./watch-prs-for-comments.sh --repo jeremyakers/tymemud-src 104
./watch-prs-for-comments.sh --repo jeremyakers/tymemud-src 104 105 106
```

## Usage

### Check once instead of blocking

```bash
./watch-prs-for-comments.sh --check-once jeremyakers/tymemud-src#104
./watch-prs-for-comments.sh --repo jeremyakers/tymemud-lib --check-once 63
```

When `--check-once` finds no actionable activity but the PR is still open, it exits with a distinct pending status so callers can distinguish "still waiting" from "feedback to address now."

### Resume after a specific activity

The canonical form is one optional `--after <selector>=<timestamp>` per PR:

```bash
./watch-prs-for-comments.sh \
  --after jeremyakers/tymemud-src#104=2026-04-18T13:52:32Z \
  --after jeremyakers/tymemud-lib#63=2026-04-17T22:08:40Z \
  jeremyakers/tymemud-src#104 \
  jeremyakers/tymemud-lib#63
```

If you are watching exactly one PR, a bare timestamp is still accepted for compatibility:

```bash
./watch-prs-for-comments.sh --repo jeremyakers/tymemud-lib --after "2026-04-17T22:08:40Z" 63
```

### Same-repo selector shortcuts with `--repo`

When `--repo owner/repo` is active, you can use either bare PR numbers or full selectors inside `--after`:

```bash
./watch-prs-for-comments.sh \
  --repo jeremyakers/tymemud-src \
  --after 104=2026-04-18T13:52:32Z \
  104 105

./watch-prs-for-comments.sh \
  --repo jeremyakers/tymemud-src \
  --after jeremyakers/tymemud-src#104=2026-04-18T13:52:32Z \
  104
```

## What Counts as Watcher Activity

The watcher surfaces only these supported signal types:

- **PR conversation comments**
- **Inline review comments** with file/line metadata
- **Submitted reviews with a non-empty body**

It does **not** treat every GitHub event as actionable watcher activity.
It also does **not** treat approval emojis, thumbs-up reactions, or "no issues found" bodies as success.

## Baseline Rules

- Default baseline is the PR head commit timestamp
- `--after` overrides that baseline for the specified PR only
- `--after` is **exclusive**
  - activity at exactly that timestamp is hidden
  - only activity with a later timestamp is shown

## Invalid `--after` Protection

The watcher rejects obviously wrong cutoffs.

If an `--after` value is later than the PR's most recent watcher baseline or supported activity, the script exits with an error and prints:

- the PR selector
- the latest activity type
- the exact latest activity timestamp
- the exact `--after` value to use instead

Example:

```bash
./watch-prs-for-comments.sh \
  --after jeremyakers/tymemud-lib#63=2099-01-01T00:00:00Z \
  jeremyakers/tymemud-lib#63
```

Output will explain that the cutoff is too late and show the correct timestamp to rerun with.

## Mixed-repo Monitoring

Yes, one invocation can watch PRs in different repos now.

Use the repo-qualified selector form:

```bash
./watch-prs-for-comments.sh \
  jeremyakers/tymemud-src#104 \
  jeremyakers/tymemud-lib#63
```

The watcher tracks each PR independently, including:

- repo selection
- commit baseline
- optional `--after` cutoff
- latest watcher baseline or supported activity validation

## How It Works

1. Resolve the watched PR set
2. Resolve per-PR baselines (`last commit` or `--after`)
3. Compute each PR's latest watcher baseline or supported activity and validate all `--after` values
4. Perform an immediate first sweep
5. Exit with code `2` if actionable activity already exists
6. Exit with code `0` only when all watched PRs are merged
7. If no new activity exists and `--check-once` is not set, poll every 30 seconds until actionable feedback appears, the watched PRs merge, or a watched PR closes without merge

## Outcome Priority

The watcher separates actionable review feedback from merge state.

- **Actionable feedback wins** when new review activity appears.
- **Merge is the only success outcome.**
- **No activity on an open PR** means nothing new happened after the baseline, so the watcher keeps polling unless `--check-once` was used.
- **Closed without merge** is a terminal non-success outcome.

Oracle remains a required process gate before publishing code, but that requirement is enforced by workflow, not by watcher heuristics.

## Polling Behavior

The watcher always does a full first sweep.

- The initial pass and `--check-once` scan comments and reviews in full.
- The script keeps the restart/baseline safety rules, but it no longer polls reaction endpoints looking for approval signals.

## Exit Codes

| Code | Meaning | Agent Action |
|------|---------|--------------|
| 0 | All monitored PRs merged | Move on to the next task |
| 1 | Error, invalid invocation, auth/fetch failure, or a watched PR closed without merge | Read the error and rerun correctly |
| 2 | New actionable watcher activity detected | Address the feedback now |
| 3 | `--check-once` found no actionable activity, but review is still pending on open PRs | Keep waiting; do not treat this as actionable feedback |

## Recommended Agent Examples

### Single PR after creation

```bash
# PR URL already printed to the user in chat
./watch-prs-for-comments.sh jeremyakers/tymemud-src#104
```

### Two PRs in different repos

```bash
# Print both PR URLs to the user first
./watch-prs-for-comments.sh \
  jeremyakers/tymemud-src#104 \
  jeremyakers/tymemud-lib#63
```

### Ignoring already-seen bot activity on one PR only

```bash
./watch-prs-for-comments.sh \
  --after jeremyakers/tymemud-lib#63=2026-04-17T22:08:40Z \
  jeremyakers/tymemud-src#104 \
  jeremyakers/tymemud-lib#63
```

## Troubleshooting

**"Could not determine repository"**
- Use `owner/repo#123`, or
- pass `--repo owner/repo`, or
- run from a git checkout with a GitHub remote

**"Failed to fetch PR ... in owner/repo"**
- Verify the repo is correct
- The PR may belong to a different repo than the current checkout
- Use `owner/repo#123` to remove ambiguity

**"--after ... may not be later than the most recent watcher baseline or supported activity"**
- Copy the exact timestamp printed by the watcher
- Re-run with the suggested corrected value

**Using a non-default Codex reviewer identity**
- Pass `--codex-login <login>` when your Codex reviewer bot uses a different GitHub login.
- Restart hints preserve that override automatically.

**No, do not background it by default**
- The standard workflow is foreground monitoring, started immediately after printing the PR URL
- In OpenCode, the timeout requirement is the `bash` or `shell` tool timeout set to the longest allowed value, currently `7200000` ms, which is 2 hours
- Background/tmux patterns are not the default recommendation for agents anymore

## Required Oracle Review Flow

- **Before opening a PR:** get a fresh Oracle signoff on the exact code you plan to publish.
- **Before pushing any new commit to an open PR branch:** get a fresh Oracle signoff on the exact updated code you plan to push.
- **After printing the PR URL:** start the watcher immediately; do not wait for more user confirmation.
- **Do not treat watcher success as Oracle success.** Merge-only watcher success means GitHub state reached merge, not that Oracle can be skipped.
