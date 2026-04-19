# PR Comment Monitor Skill

Monitor one or more GitHub PRs for actionable post-baseline review activity without losing the current agent session.

## When to Use

- Immediately after opening a PR
- When the same agent should stay responsible for incoming review feedback
- When monitoring multiple PRs in one repo or across multiple repos

## Mandatory Agent Workflow

After opening a PR, agents must do this in order:

1. **Print the PR URL to the user in chat immediately**
2. **Start the watcher immediately after that**
3. **Run it in the foreground**
4. **When using the OpenCode agent command line tool, set the tool timeout to the 2 hour maximum, `7200000` ms**
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

If you are launching the watcher from a plain shell outside the OpenCode tool wrapper, `timeout 2h ./watch-prs-for-comments.sh ...` is still a valid shell example. The real workflow requirement being enforced here is the OpenCode tool timeout, not the shell wrapper by itself.

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
timeout 2h ./watch-prs-for-comments.sh jeremyakers/tymemud-src#104
```

This is the **recommended** form.

### Legacy same-repo form

If all PRs are in the same repo, the watcher still supports `--repo owner/repo` plus bare PR numbers:

```bash
./watch-prs-for-comments.sh --repo jeremyakers/tymemud-src 104
./watch-prs-for-comments.sh --repo jeremyakers/tymemud-src 104 105 106
timeout 2h ./watch-prs-for-comments.sh --repo jeremyakers/tymemud-lib 63
```

## Usage

### Check once instead of blocking

```bash
./watch-prs-for-comments.sh --check-once jeremyakers/tymemud-src#104
./watch-prs-for-comments.sh --repo jeremyakers/tymemud-lib --check-once 63
```

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
- **Codex `+1` reactions on the PR itself**
- **Codex `+1` reactions on PR conversation comments**
- **Codex `+1` reactions on inline review comments**

It does **not** treat every GitHub event as actionable watcher activity.

## Baseline Rules

- Default baseline is the PR head commit timestamp
- `--after` overrides that baseline for the specified PR only
- `--after` is **exclusive**
  - activity at exactly that timestamp is hidden
  - only activity with a later timestamp is shown

## Invalid `--after` Protection

The watcher rejects obviously wrong cutoffs.

If an `--after` value is later than the PR's most recent activity, the script exits with an error and prints:

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
- latest activity validation

## How It Works

1. Resolve the watched PR set
2. Resolve per-PR baselines (`last commit` or `--after`)
3. Compute each PR's latest activity and validate all `--after` values
4. Perform an immediate first sweep
5. Exit with code `2` if actionable activity already exists
6. Exit with code `0` if the first sweep finds only approval or no-issues signals and no actionable feedback
7. If no new activity exists and `--check-once` is not set, poll every 30 seconds until actionable feedback appears, an approval or no-issues outcome appears, or all monitored PRs close

## Outcome Priority

The watcher separates actionable review feedback from approval or no-issues completion signals.

- **Actionable feedback wins** when both kinds of signals appear in the same run.
- **Approval or no-issues is a distinct success outcome** when no actionable feedback is present.
- **No activity** means nothing new happened after the baseline, so the watcher keeps polling unless `--check-once` was used.

Approval or no-issues can come from the supported Codex no-issues body or the supported Codex `+1` reaction paths listed above. Those signals tell the agent it can stop waiting, but they do not override real review comments.

## Polling and Nested Reaction Throttling

The watcher always does a full first sweep.

- The initial pass and `--check-once` still scan nested issue-comment and review-comment reactions in full.
- Throttling applies only inside repeated polling iterations.
- The throttle is only a loop optimization for repeated nested reaction rescans. It is not a seen-state cache and it does not persist across restarts.
- Top-level PR reaction checks stay unthrottled.

## Exit Codes

| Code | Meaning | Agent Action |
|------|---------|--------------|
| 0 | Approval or no-issues detected with no actionable feedback, or no pending activity in `--check-once`, or all monitored PRs closed during foreground monitoring | Move on to the next task |
| 1 | Error (bad args, bad repo, invalid `--after`, auth failure, fetch failure) | Read the error and rerun correctly |
| 2 | New actionable watcher activity detected | Address the feedback now |

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

**"--after ... may not be later than the most recent PR activity"**
- Copy the exact timestamp printed by the watcher
- Re-run with the suggested corrected value

**No, do not background it by default**
- The standard workflow is foreground monitoring, started immediately after printing the PR URL
- In OpenCode, the timeout requirement is the agent tool timeout set to `7200000` ms, which is 2 hours
- `timeout 2h` is only a plain-shell wrapper example when you are not running through the OpenCode tool wrapper
- Background/tmux patterns are not the default recommendation for agents anymore
