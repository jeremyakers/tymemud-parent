#!/usr/bin/env bash
# watch-prs-for-comments.sh
# Monitor GitHub PRs for actionable post-baseline review activity.

set -euo pipefail
IFS=$'\n\t'

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DEFAULT_CODEX_REVIEWER_LOGIN='chatgpt-codex-connector[bot]'
REPO_ARG=""
CHECK_ONCE=false
CODEX_REVIEWER_LOGIN="${CODEX_REVIEWER_LOGIN:-$DEFAULT_CODEX_REVIEWER_LOGIN}"
REACTION_POLL_INTERVAL_SECONDS="${REACTION_POLL_INTERVAL_SECONDS:-300}"
LAST_FETCH_ERROR=""

declare -a RAW_PR_ARGS=()
declare -a RAW_AFTER_ARGS=()
declare -a PR_KEYS=()
declare -A KEY_TO_REPO=()
declare -A KEY_TO_PR=()
declare -A KEY_TO_TITLE=()
declare -A KEY_TO_URL=()
declare -A KEY_TO_HEAD_SHA=()
declare -A KEY_TO_IS_OPEN=()
declare -A KEY_TO_LAST_COMMIT=()
declare -A KEY_TO_AFTER=()
declare -A KEY_TO_SURFACED_CURSOR=()
declare -A KEY_TO_PENDING_PRECOMMIT_ACTIONABLE=()
declare -A KEY_TO_REPORTED_ACTIONABLE_KEYS=()
declare -A KEY_TO_REPORTED_APPROVAL_KEYS=()
declare -A KEY_TO_APPROVAL_SIGNAL_FOUND=()
declare -A KEY_TO_LATEST_ACTIVITY_TIME=()
declare -A KEY_TO_LATEST_ACTIVITY_TYPE=()
declare -A KEY_TO_NESTED_REACTION_SCAN_EPOCH=()
declare -A KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN=()
APPROVAL_SIGNAL_FOUND=0
POSTCOMMIT_BOUNDARY_FOUND=0

usage() {
    cat <<'EOF'
Usage:
  ./watch-prs-for-comments.sh [--repo owner/repo] [--check-once] [--after <selector>=<timestamp>] [--codex-login <login>] <pr...>

PR selectors:
  owner/repo#123        Monitor PR #123 in owner/repo
  123                   Monitor PR #123 in --repo owner/repo (or the inferred current repo)

Examples:
  ./watch-prs-for-comments.sh --repo jeremyakers/tymemud-src 104
  ./watch-prs-for-comments.sh jeremyakers/tymemud-src#104 jeremyakers/tymemud-lib#63
  ./watch-prs-for-comments.sh --repo jeremyakers/tymemud-lib --after 63=2026-04-17T22:08:40Z 63
  ./watch-prs-for-comments.sh --after jeremyakers/tymemud-lib#63=2026-04-17T22:08:40Z jeremyakers/tymemud-lib#63

Notes:
  - Repeated --after flags are supported: one optional cutoff per watched PR
  - For a single watched PR, a bare timestamp is still accepted for compatibility
EOF
}

fail() {
    local message="$1"
    echo -e "${RED}❌ ${message}${NC}" >&2
    exit 1
}

note() {
    local message="$1"
    echo -e "${BLUE}${message}${NC}"
}

warn() {
    local message="$1"
    echo -e "${YELLOW}${message}${NC}"
}

pass() {
    local message="$1"
    echo -e "${GREEN}${message}${NC}"
}

normalize_login() {
    local login="${1,,}"
    login="${login%\[bot\]}"
    printf '%s\n' "$login"
}

is_codex_actor() {
    local login
    login="$(normalize_login "$1")"
    local custom
    custom="$(normalize_login "$CODEX_REVIEWER_LOGIN")"
    local default_login
    default_login="$(normalize_login "$DEFAULT_CODEX_REVIEWER_LOGIN")"

    [[ "$login" == "$custom" ]] && return 0

    if [[ "$custom" != "$default_login" ]]; then
        return 1
    fi

    [[ "$login" == "codex" ]] && return 0
    [[ "$login" == "chatgpt-codex-connector" ]] && return 0
    return 1
}

normalize_timestamp() {
    local raw="$1"
    local normalized

    if ! normalized=$(date -u -d "$raw" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null); then
        fail "Invalid timestamp: $raw"
    fi

    printf '%s\n' "$normalized"
}

compare_iso_gt() {
    local left="$1"
    local right="$2"

    [[ -n "$left" ]] || return 1
    [[ -n "$right" ]] || return 0
    [[ "$left" > "$right" ]]
}

compare_iso_gte() {
    local left="$1"
    local right="$2"

    [[ "$left" == "$right" ]] && return 0
    compare_iso_gt "$left" "$right"
}

compare_iso_lte() {
    local left="$1"
    local right="$2"

    [[ "$left" == "$right" ]] && return 0
    [[ "$left" < "$right" ]]
}

trimmed_nonempty() {
    local value="$1"
    [[ -n "${value//[[:space:]]/}" ]]
}

normalize_message_whitespace() {
    local value="$1"

    value="${value//$'\r'/ }"
    value="${value//$'\n'/ }"
    value="$(sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//' <<<"$value")"

    printf '%s\n' "$value"
}

fetch_error_suffix() {
    local normalized=""

    [[ -n "$LAST_FETCH_ERROR" ]] || return 0
    normalized="$(normalize_message_whitespace "$LAST_FETCH_ERROR")"
    [[ -n "$normalized" ]] || return 0
    printf ' Details: %s' "$normalized"
}

shell_quote() {
    printf '%q' "$1"
}

is_codex_no_issues_body() {
    local actor="$1"
    local body="$2"
    local normalized_body=""

    is_codex_actor "$actor" || return 1

    normalized_body="$(normalize_message_whitespace "$body")"

    case "$normalized_body" in
        "Codex Review: Didn't find any major issues."*) return 0 ;;
        "Didn't find any major issues."*) return 0 ;;
        "No new issues found."*) return 0 ;;
    esac

    return 1
}

is_approval_activity_type() {
    local activity_type="$1"

    case "$activity_type" in
        "pr reaction"|"issue comment reaction"|"review comment reaction"|"review approval") return 0 ;;
    esac

    return 1
}

fetch_paginated_array() {
    local endpoint="$1"
    local stderr_file=""
    local raw_output
    local output

    LAST_FETCH_ERROR=""
    stderr_file=$(mktemp)

    if ! raw_output=$(gh api --paginate -H "Accept: application/vnd.github+json" "$endpoint" 2>"$stderr_file"); then
        LAST_FETCH_ERROR="$(<"$stderr_file")"
        rm -f "$stderr_file"
        return 1
    fi

    if [[ -s "$stderr_file" ]]; then
        LAST_FETCH_ERROR="$(<"$stderr_file")"
    fi
    rm -f "$stderr_file"

    if ! output=$(jq -sc 'add' <<<"$raw_output" 2>&1); then
        LAST_FETCH_ERROR="$output"
        return 1
    fi

    if [[ -z "$output" || "$output" == "null" ]]; then
        output='[]'
    fi

    LAST_FETCH_ERROR=""
    printf '%s\n' "$output"
}

detect_repo_from_git() {
    local remote_url=""
    remote_url=$(git remote get-url origin 2>/dev/null || true)

    if [[ "$remote_url" == *github.com* ]]; then
        printf '%s\n' "$remote_url" | sed 's#.*github.com[:/]##; s#\.git$##'
        return 0
    fi

    return 1
}

make_pr_key() {
    local repo="$1"
    local pr="$2"
    printf '%s#%s\n' "$repo" "$pr"
}

parse_repo_pr_token() {
    local token="$1"
    local default_repo="$2"
    local repo=""
    local pr=""

    if [[ "$token" == *'#'* ]]; then
        repo="${token%#*}"
        pr="${token##*#}"
    else
        repo="$default_repo"
        pr="$token"
    fi

    [[ -n "$repo" ]] || fail "Could not determine repository for selector '$token'. Use --repo owner/repo or owner/repo#123."
    [[ "$pr" =~ ^[0-9]+$ ]] || fail "Invalid PR selector '$token'. Expected owner/repo#123 or numeric PR number."

    printf '%s\n%s\n' "$repo" "$pr"
}

add_pr_key() {
    local key="$1"
    local existing

    for existing in "${PR_KEYS[@]}"; do
        if [[ "$existing" == "$key" ]]; then
            return 0
        fi
    done

    PR_KEYS+=("$key")
}

get_pr_last_commit_date() {
    local repo="$1"
    local pr="$2"
    local head_sha=""
    local commit_date=""

    head_sha=$(gh pr view "$pr" --repo "$repo" --json headRefOid --jq '.headRefOid' 2>/dev/null || true)
    [[ -n "$head_sha" && "$head_sha" != "null" ]] || return 1

    commit_date=$(gh api "repos/$repo/commits/$head_sha" --jq '.commit.committer.date // .commit.author.date' 2>/dev/null || true)
    [[ -n "$commit_date" && "$commit_date" != "null" ]] || return 1

    printf '%s\n' "$commit_date"
}

get_pr_head_sha() {
    local repo="$1"
    local pr="$2"
    local head_sha=""

    head_sha=$(gh pr view "$pr" --repo "$repo" --json headRefOid --jq '.headRefOid' 2>/dev/null || true)
    [[ -n "$head_sha" && "$head_sha" != "null" ]] || return 1

    printf '%s\n' "$head_sha"
}

reset_review_cycle_runtime_state() {
    local key="$1"

    KEY_TO_SURFACED_CURSOR["$key"]=""
    KEY_TO_PENDING_PRECOMMIT_ACTIONABLE["$key"]=false
    KEY_TO_REPORTED_ACTIONABLE_KEYS["$key"]=$'\n'
    KEY_TO_REPORTED_APPROVAL_KEYS["$key"]=$'\n'
    KEY_TO_APPROVAL_SIGNAL_FOUND["$key"]=false
    KEY_TO_NESTED_REACTION_SCAN_EPOCH["$key"]=0
    KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN["$key"]=false
}

any_pending_precommit_actionable() {
    local key

    for key in "${PR_KEYS[@]}"; do
        if [[ "${KEY_TO_PENDING_PRECOMMIT_ACTIONABLE[$key]:-false}" == "true" ]]; then
            return 0
        fi
    done

    return 1
}

all_open_prs_have_approval_signal() {
    local key
    local saw_open=false

    for key in "${PR_KEYS[@]}"; do
        if [[ "${KEY_TO_IS_OPEN[$key]:-true}" != "true" ]]; then
            continue
        fi

        saw_open=true
        if [[ "${KEY_TO_APPROVAL_SIGNAL_FOUND[$key]:-false}" != "true" ]]; then
            return 1
        fi
    done

    [[ "$saw_open" == true ]]
}

all_open_prs_acknowledged_or_approved() {
    local key
    local saw_open=false
    local explicit_after
    local latest_time
    local latest_type

    for key in "${PR_KEYS[@]}"; do
        if [[ "${KEY_TO_IS_OPEN[$key]:-true}" != "true" ]]; then
            continue
        fi

        saw_open=true

        if [[ "${KEY_TO_APPROVAL_SIGNAL_FOUND[$key]:-false}" == "true" ]]; then
            continue
        fi

        explicit_after="${KEY_TO_AFTER[$key]:-}"
        latest_time="${KEY_TO_LATEST_ACTIVITY_TIME[$key]:-}"
        latest_type="${KEY_TO_LATEST_ACTIVITY_TYPE[$key]:-}"

        if [[ -n "$explicit_after" && -n "$latest_time" ]] && compare_iso_lte "$latest_time" "$explicit_after" && is_approval_activity_type "$latest_type"; then
            continue
        fi

        return 1
    done

    [[ "$saw_open" == true ]]
}

load_pr_metadata() {
    local key="$1"
    local repo="$2"
    local pr="$3"
    local pr_data
    local state
    local title
    local url
    local head_sha
    local last_commit

    if ! pr_data=$(gh pr view "$pr" --repo "$repo" --json number,title,state,url 2>/dev/null); then
        fail "Failed to fetch PR #$pr in $repo.$(fetch_error_suffix) If this PR belongs to a different repo, use --repo owner/repo $pr or owner/repo#$pr."
    fi

    state=$(jq -r '.state' <<<"$pr_data")
    title=$(jq -r '.title' <<<"$pr_data")
    url=$(jq -r '.url' <<<"$pr_data")

    KEY_TO_REPO["$key"]="$repo"
    KEY_TO_PR["$key"]="$pr"
    KEY_TO_TITLE["$key"]="$title"
    KEY_TO_URL["$key"]="$url"

    if [[ "$state" != "OPEN" ]]; then
        KEY_TO_IS_OPEN["$key"]=false
        KEY_TO_HEAD_SHA["$key"]=""
        KEY_TO_LAST_COMMIT["$key"]=""
        return 1
    fi

    if ! head_sha=$(get_pr_head_sha "$repo" "$pr"); then
        fail "Could not determine the latest head SHA for $repo#$pr."
    fi

    if ! last_commit=$(get_pr_last_commit_date "$repo" "$pr"); then
        fail "Could not determine the latest commit timestamp for $repo#$pr."
    fi

    KEY_TO_IS_OPEN["$key"]=true
    KEY_TO_HEAD_SHA["$key"]="$head_sha"
    KEY_TO_LAST_COMMIT["$key"]="$last_commit"
}

register_latest_activity() {
    local key="$1"
    local timestamp="$2"
    local activity_type="$3"
    local current_time="${KEY_TO_LATEST_ACTIVITY_TIME[$key]:-}"
    local current_type="${KEY_TO_LATEST_ACTIVITY_TYPE[$key]:-}"

    if compare_iso_gt "$timestamp" "$current_time"; then
        KEY_TO_LATEST_ACTIVITY_TIME["$key"]="$timestamp"
        KEY_TO_LATEST_ACTIVITY_TYPE["$key"]="$activity_type"
        return 0
    fi

    if [[ "$timestamp" == "$current_time" ]] && is_approval_activity_type "$activity_type" && ! is_approval_activity_type "$current_type"; then
        KEY_TO_LATEST_ACTIVITY_TYPE["$key"]="$activity_type"
    fi
}

get_runtime_cursor() {
    local key="$1"

    if [[ -n "${KEY_TO_SURFACED_CURSOR[$key]:-}" ]]; then
        printf '%s\n' "${KEY_TO_SURFACED_CURSOR[$key]}"
        return 0
    fi

    printf '%s\n' "${KEY_TO_AFTER[$key]:-}"
}

runtime_baseline_cursor() {
    local key="$1"
    local surfaced="${KEY_TO_SURFACED_CURSOR[$key]:-}"

    if [[ -n "$surfaced" ]]; then
        date -u -d "$surfaced -1 second" +"%Y-%m-%dT%H:%M:%SZ"
        return 0
    fi

    printf '%s\n' "${KEY_TO_AFTER[$key]:-}"
}

effective_baseline_for_key() {
    local key="$1"
    local cursor=""
    local explicit_after="${KEY_TO_AFTER[$key]:-}"
    local latest_commit="${KEY_TO_LAST_COMMIT[$key]}"

    if [[ -n "$explicit_after" ]]; then
        printf '%s\n' "$explicit_after"
        return 0
    fi

    cursor="$(runtime_baseline_cursor "$key")"
    if [[ -z "$cursor" ]]; then
        printf '%s\n' "$latest_commit"
        return 0
    fi

    if compare_iso_gt "$cursor" "$latest_commit"; then
        printf '%s\n' "$latest_commit"
        return 0
    fi

    printf '%s\n' "$cursor"
}

is_post_commit_activity() {
    local key="$1"
    local timestamp="$2"

    compare_iso_gt "$timestamp" "${KEY_TO_LAST_COMMIT[$key]}"
}

is_already_reported_actionable() {
    local key="$1"
    local token="$2"
    local reported="${KEY_TO_REPORTED_ACTIONABLE_KEYS[$key]:-}"

    [[ "$reported" == *$'\n'"$token"$'\n'* ]]
}

mark_actionable_reported() {
    local key="$1"
    local token="$2"

    KEY_TO_REPORTED_ACTIONABLE_KEYS["$key"]+="$token"$'\n'
}

is_already_reported_approval() {
    local key="$1"
    local token="$2"
    local reported="${KEY_TO_REPORTED_APPROVAL_KEYS[$key]:-}"

    [[ "$reported" == *$'\n'"$token"$'\n'* ]]
}

mark_approval_reported() {
    local key="$1"
    local token="$2"

    KEY_TO_REPORTED_APPROVAL_KEYS["$key"]+="$token"$'\n'
}

record_actionable_visibility() {
    local key="$1"
    local timestamp="$2"
    local token="$3"

    if compare_iso_gt "$timestamp" "${KEY_TO_SURFACED_CURSOR[$key]:-}"; then
        KEY_TO_SURFACED_CURSOR["$key"]="$timestamp"
    fi

    mark_actionable_reported "$key" "$token"
}

flag_postcommit_boundary_if_needed() {
    local key="$1"
    local timestamp="$2"
    local report_new="$3"
    local baseline="$4"

    [[ "$report_new" == "true" ]] || return 0
    compare_iso_gt "$timestamp" "$baseline" || return 0
    is_post_commit_activity "$key" "$timestamp" || return 0

    POSTCOMMIT_BOUNDARY_FOUND=1
}

record_actionable_event() {
    local key="$1"
    local timestamp="$2"
    local token="$3"
    local display_callback="$4"
    shift 4

    if is_post_commit_activity "$key" "$timestamp"; then
        NEW_SIGNAL_FOUND=1
    else
        KEY_TO_PENDING_PRECOMMIT_ACTIONABLE["$key"]=true
    fi

    if ! is_already_reported_actionable "$key" "$token"; then
        "$display_callback" "$@"
        record_actionable_visibility "$key" "$timestamp" "$token"
    fi
}

display_restart_hint() {
    local key="$1"
    local timestamp="$2"
    local current_key
    local current_after
    local command="./watch-prs-for-comments.sh"

    if [[ "$CHECK_ONCE" == true ]]; then
        command+=" --check-once"
    fi

    if [[ "$CODEX_REVIEWER_LOGIN" != "$DEFAULT_CODEX_REVIEWER_LOGIN" ]]; then
        command+=" --codex-login $(shell_quote "$CODEX_REVIEWER_LOGIN")"
    fi

    for current_key in "${PR_KEYS[@]}"; do
        if [[ "$current_key" == "$key" ]]; then
            current_after="$timestamp"
        else
            current_after="${KEY_TO_AFTER[$current_key]:-}"
        fi

        if [[ -n "$current_after" ]]; then
            command+=" --after $(shell_quote "${current_key}=${current_after}")"
        fi
    done

    for current_key in "${PR_KEYS[@]}"; do
        command+=" $(shell_quote "$current_key")"
    done

    echo -e "${BLUE}To ignore this activity and future ones on this PR, restart with the same watch set:${NC}"
    echo -e "${BLUE}   ${command}${NC}"
    echo ""
}

display_issue_comment() {
    local key="$1"
    local author="$2"
    local body="$3"
    local timestamp="$4"

    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}🔔 NEW PR COMMENT on ${key}: ${KEY_TO_TITLE[$key]}${NC}"
    echo -e "${YELLOW}   Posted: ${timestamp}${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo "From: @$author"
    echo ""
    echo "$body"
    echo -e "${YELLOW}───────────────────────────────────────────────────────────────${NC}"
    display_restart_hint "$key" "$timestamp"
}

display_review_comment() {
    local key="$1"
    local file="$2"
    local line="$3"
    local original_line="$4"
    local start_line="$5"
    local end_line="$6"
    local commit_id="$7"
    local author="$8"
    local body="$9"
    local timestamp="${10}"
    local line_range="line unknown"

    if [[ -n "$start_line" && -n "$end_line" && "$start_line" != "$end_line" ]]; then
        line_range="lines $start_line-$end_line"
    elif [[ -n "$line" ]]; then
        line_range="line $line"
    elif [[ -n "$original_line" ]]; then
        line_range="line $original_line (original)"
    fi

    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}🔔 NEW REVIEW COMMENT on ${key}: ${KEY_TO_TITLE[$key]}${NC}"
    echo -e "${YELLOW}   File: ${file}${NC}"
    echo -e "${YELLOW}   Location: ${line_range}${NC}"
    if [[ -n "$commit_id" ]]; then
        echo -e "${YELLOW}   Commit: ${commit_id:0:7}${NC}"
    fi
    echo -e "${YELLOW}   Posted: ${timestamp}${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo "From: @$author"
    echo ""
    echo "$body"
    echo -e "${YELLOW}───────────────────────────────────────────────────────────────${NC}"
    display_restart_hint "$key" "$timestamp"
}

display_review_body() {
    local key="$1"
    local state="$2"
    local author="$3"
    local body="$4"
    local timestamp="$5"

    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}🔔 NEW REVIEW on ${key}: ${KEY_TO_TITLE[$key]}${NC}"
    echo -e "${YELLOW}   State: ${state}${NC}"
    echo -e "${YELLOW}   Submitted: ${timestamp}${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo "From: @$author"
    echo ""
    echo "$body"
    echo -e "${YELLOW}───────────────────────────────────────────────────────────────${NC}"
    display_restart_hint "$key" "$timestamp"
}

display_reaction() {
    local key="$1"
    local reaction_type="$2"
    local actor="$3"
    local timestamp="$4"
    local context_line="$5"

    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}🔔 NEW CODEX 👍 on ${key}: ${KEY_TO_TITLE[$key]}${NC}"
    echo -e "${YELLOW}   Type: ${reaction_type}${NC}"
    if [[ -n "$context_line" ]]; then
        echo -e "${YELLOW}   Context: ${context_line}${NC}"
    fi
    echo -e "${YELLOW}   Posted: ${timestamp}${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo "From: @$actor"
    echo -e "${YELLOW}───────────────────────────────────────────────────────────────${NC}"
    display_restart_hint "$key" "$timestamp"
}

record_reaction_approval() {
    local key="$1"
    local reaction_type="$2"
    local actor="$3"
    local timestamp="$4"
    local context_line="$5"
    local baseline="$6"
    local report_new="$7"
    local token=""

    register_latest_activity "$key" "$timestamp" "$reaction_type"

    if [[ "$report_new" == "true" ]] && compare_iso_gt "$timestamp" "$baseline" && is_post_commit_activity "$key" "$timestamp"; then
        APPROVAL_SIGNAL_FOUND=1
        KEY_TO_APPROVAL_SIGNAL_FOUND["$key"]=true
        POSTCOMMIT_BOUNDARY_FOUND=1
        token="approval:${reaction_type}:${actor}:${timestamp}:${context_line}"
        if ! is_already_reported_approval "$key" "$token"; then
            display_reaction "$key" "$reaction_type" "$actor" "$timestamp" "$context_line"
            mark_approval_reported "$key" "$token"
        fi
    fi
}

process_reactions_for_issue_comment() {
    local repo="$1"
    local comment_id="$2"
    local key="$3"
    local baseline="$4"
    local report_new="$5"
    local reactions
    local count=0
    local i
    local actor
    local content
    local timestamp

    reactions=$(fetch_paginated_array "repos/$repo/issues/comments/$comment_id/reactions?per_page=100") || return 1
    count=$(jq 'length' <<<"$reactions")

    for ((i=0; i<count; i++)); do
        actor=$(jq -r ".[$i].user.login" <<<"$reactions")
        content=$(jq -r ".[$i].content" <<<"$reactions")
        timestamp=$(jq -r ".[$i].created_at" <<<"$reactions")

        [[ "$content" == "+1" ]] || continue
        is_codex_actor "$actor" || continue

        record_reaction_approval "$key" "issue comment reaction" "$actor" "$timestamp" "pull request conversation comment approval signal" "$baseline" "$report_new"
    done
}

process_reactions_for_review_comment() {
    local repo="$1"
    local comment_id="$2"
    local key="$3"
    local baseline="$4"
    local file="$5"
    local report_new="$6"
    local reactions
    local count=0
    local i
    local actor
    local content
    local timestamp

    reactions=$(fetch_paginated_array "repos/$repo/pulls/comments/$comment_id/reactions?per_page=100") || return 1
    count=$(jq 'length' <<<"$reactions")

    for ((i=0; i<count; i++)); do
        actor=$(jq -r ".[$i].user.login" <<<"$reactions")
        content=$(jq -r ".[$i].content" <<<"$reactions")
        timestamp=$(jq -r ".[$i].created_at" <<<"$reactions")

        [[ "$content" == "+1" ]] || continue
        is_codex_actor "$actor" || continue

        record_reaction_approval "$key" "review comment reaction" "$actor" "$timestamp" "inline review comment on ${file}" "$baseline" "$report_new"
    done
}

should_scan_nested_reactions() {
    local key="$1"
    local throttle_during_polling="$2"
    local now_epoch=0
    local last_scan=0

    if [[ "$throttle_during_polling" != "true" ]]; then
        return 0
    fi

    now_epoch=$(date +%s)
    last_scan="${KEY_TO_NESTED_REACTION_SCAN_EPOCH[$key]:-0}"

    (( last_scan == 0 || now_epoch - last_scan >= REACTION_POLL_INTERVAL_SECONDS ))
}

mark_nested_reaction_scan() {
    local key="$1"

    KEY_TO_NESTED_REACTION_SCAN_EPOCH["$key"]="$(date +%s)"
}

scan_pr_activity() {
    local key="$1"
    local baseline="$2"
    local report_new="$3"
    local throttle_nested_reactions="${4:-false}"
    local repo="${KEY_TO_REPO[$key]}"
    local pr="${KEY_TO_PR[$key]}"
    local issue_comments
    local review_comments
    local reviews
    local pr_reactions
    local count=0
    local i
    local timestamp
    local actor
    local body
    local file
    local line
    local original_line
    local start_line
    local end_line
    local commit_id
    local state
    local content
    local comment_id
    local review_id
    local needs_nested_reaction_scan=true
    local should_scan_nested_reaction_endpoints=true
    local force_report_nested_reaction_scan="${KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN[$key]:-false}"

    register_latest_activity "$key" "${KEY_TO_LAST_COMMIT[$key]}" "head commit"

    issue_comments=$(fetch_paginated_array "repos/$repo/issues/$pr/comments?per_page=100") || fail "Failed to fetch issue comments for $key.$(fetch_error_suffix)"
    review_comments=$(fetch_paginated_array "repos/$repo/pulls/$pr/comments?per_page=100") || fail "Failed to fetch review comments for $key.$(fetch_error_suffix)"
    reviews=$(fetch_paginated_array "repos/$repo/pulls/$pr/reviews?per_page=100") || fail "Failed to fetch reviews for $key.$(fetch_error_suffix)"
    pr_reactions=$(fetch_paginated_array "repos/$repo/issues/$pr/reactions?per_page=100") || fail "Failed to fetch PR reactions for $key.$(fetch_error_suffix)"

    count=$(jq 'length' <<<"$issue_comments")
    for ((i=0; i<count; i++)); do
        comment_id=$(jq -r ".[$i].id" <<<"$issue_comments")
        timestamp=$(jq -r ".[$i].created_at" <<<"$issue_comments")
        actor=$(jq -r ".[$i].user.login" <<<"$issue_comments")
        body=$(jq -r ".[$i].body // \"\"" <<<"$issue_comments")

        register_latest_activity "$key" "$timestamp" "issue comment"

        if [[ "$report_new" == "true" ]] && is_codex_no_issues_body "$actor" "$body"; then
            register_latest_activity "$key" "$timestamp" "review approval"
            if compare_iso_gt "$timestamp" "$baseline"; then
                flag_postcommit_boundary_if_needed "$key" "$timestamp" "$report_new" "$baseline"
                if is_post_commit_activity "$key" "$timestamp"; then
                    APPROVAL_SIGNAL_FOUND=1
                    KEY_TO_APPROVAL_SIGNAL_FOUND["$key"]=true
                fi
            fi
            continue
        fi

        if [[ "$report_new" == "true" ]] && compare_iso_gt "$timestamp" "$baseline"; then
            needs_nested_reaction_scan=false
            record_actionable_event "$key" "$timestamp" "issue-comment:${comment_id}" display_issue_comment "$key" "$actor" "$body" "$timestamp"
        fi
    done

    count=$(jq 'length' <<<"$review_comments")
    for ((i=0; i<count; i++)); do
        comment_id=$(jq -r ".[$i].id" <<<"$review_comments")
        timestamp=$(jq -r ".[$i].created_at" <<<"$review_comments")
        actor=$(jq -r ".[$i].user.login" <<<"$review_comments")
        body=$(jq -r ".[$i].body // \"\"" <<<"$review_comments")
        file=$(jq -r ".[$i].path // \"unknown\"" <<<"$review_comments")
        line=$(jq -r ".[$i].line // \"\"" <<<"$review_comments")
        original_line=$(jq -r ".[$i].original_line // \"\"" <<<"$review_comments")
        start_line=$(jq -r ".[$i].start_line // \"\"" <<<"$review_comments")
        end_line=$(jq -r ".[$i].end_line // \"\"" <<<"$review_comments")
        commit_id=$(jq -r ".[$i].commit_id // \"\"" <<<"$review_comments")

        register_latest_activity "$key" "$timestamp" "review comment"

        if [[ "$report_new" == "true" ]] && compare_iso_gt "$timestamp" "$baseline"; then
            needs_nested_reaction_scan=false
            record_actionable_event "$key" "$timestamp" "review-comment:${comment_id}" display_review_comment "$key" "$file" "$line" "$original_line" "$start_line" "$end_line" "$commit_id" "$actor" "$body" "$timestamp"
        fi
    done

    count=$(jq 'length' <<<"$reviews")
    for ((i=0; i<count; i++)); do
        review_id=$(jq -r ".[$i].id // \"review-$i\"" <<<"$reviews")
        timestamp=$(jq -r ".[$i].submitted_at // \"\"" <<<"$reviews")
        [[ -n "$timestamp" ]] || continue

        body=$(jq -r ".[$i].body // \"\"" <<<"$reviews")
        actor=$(jq -r ".[$i].user.login" <<<"$reviews")
        state=$(jq -r ".[$i].state" <<<"$reviews")

        register_latest_activity "$key" "$timestamp" "review body"

        if [[ "$report_new" == "true" ]] && compare_iso_gt "$timestamp" "$baseline" && ! trimmed_nonempty "$body"; then
            if [[ "${KEY_TO_PENDING_PRECOMMIT_ACTIONABLE[$key]:-false}" == "true" ]]; then
                flag_postcommit_boundary_if_needed "$key" "$timestamp" "$report_new" "$baseline"
            fi
            continue
        fi

        trimmed_nonempty "$body" || continue

        if [[ "$report_new" == "true" ]] && is_codex_no_issues_body "$actor" "$body"; then
            register_latest_activity "$key" "$timestamp" "review approval"
            if compare_iso_gt "$timestamp" "$baseline"; then
                flag_postcommit_boundary_if_needed "$key" "$timestamp" "$report_new" "$baseline"
                if is_post_commit_activity "$key" "$timestamp"; then
                    APPROVAL_SIGNAL_FOUND=1
                    KEY_TO_APPROVAL_SIGNAL_FOUND["$key"]=true
                fi
            fi
            continue
        fi

        if [[ "$report_new" == "true" ]] && compare_iso_gt "$timestamp" "$baseline"; then
            needs_nested_reaction_scan=false
            record_actionable_event "$key" "$timestamp" "review:${review_id}" display_review_body "$key" "$state" "$actor" "$body" "$timestamp"
        fi
    done

    count=$(jq 'length' <<<"$pr_reactions")
    for ((i=0; i<count; i++)); do
        actor=$(jq -r ".[$i].user.login" <<<"$pr_reactions")
        content=$(jq -r ".[$i].content" <<<"$pr_reactions")
        timestamp=$(jq -r ".[$i].created_at" <<<"$pr_reactions")

        [[ "$content" == "+1" ]] || continue
        is_codex_actor "$actor" || continue

        record_reaction_approval "$key" "pr reaction" "$actor" "$timestamp" "pull request approval signal" "$baseline" "$report_new"
    done

    if ! should_scan_nested_reactions "$key" "$throttle_nested_reactions"; then
        should_scan_nested_reaction_endpoints=false
    fi

    if [[ "$report_new" == "true" && "$force_report_nested_reaction_scan" == "true" ]]; then
        should_scan_nested_reaction_endpoints=true
    fi

    if [[ "$should_scan_nested_reaction_endpoints" == true && ( "$throttle_nested_reactions" != "true" || "$report_new" == "false" || "$needs_nested_reaction_scan" == true || "$force_report_nested_reaction_scan" == "true" ) ]]; then
        if [[ "$report_new" == "false" && "$throttle_nested_reactions" == "true" ]]; then
            KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN["$key"]=true
        else
            KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN["$key"]=false
        fi

        mark_nested_reaction_scan "$key"
        count=$(jq 'length' <<<"$issue_comments")
        for ((i=0; i<count; i++)); do
            comment_id=$(jq -r ".[$i].id" <<<"$issue_comments")
            actor=$(jq -r ".[$i].user.login" <<<"$issue_comments")
            process_reactions_for_issue_comment "$repo" "$comment_id" "$key" "$baseline" "$report_new" || fail "Failed to fetch nested issue-comment reactions for ${key} comment ${comment_id}.$(fetch_error_suffix)"
        done

        count=$(jq 'length' <<<"$review_comments")
        for ((i=0; i<count; i++)); do
            comment_id=$(jq -r ".[$i].id" <<<"$review_comments")
            file=$(jq -r ".[$i].path // \"unknown\"" <<<"$review_comments")
            process_reactions_for_review_comment "$repo" "$comment_id" "$key" "$baseline" "$file" "$report_new" || fail "Failed to fetch nested review-comment reactions for ${key} comment ${comment_id}.$(fetch_error_suffix)"
        done
    else
        KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN["$key"]=false
    fi

    if [[ "${KEY_TO_PENDING_PRECOMMIT_ACTIONABLE[$key]:-false}" == "true" && "$POSTCOMMIT_BOUNDARY_FOUND" -eq 1 ]]; then
        NEW_SIGNAL_FOUND=1
    fi
}

resolve_after_mappings() {
    local current_repo="$1"
    local raw
    local selector
    local timestamp
    local normalized_selector
    local parsed_repo
    local parsed_pr
    local key
    local matched=false
    local accepted=""
    local pr_key

    for pr_key in "${PR_KEYS[@]}"; do
        KEY_TO_AFTER["$pr_key"]=""
        reset_review_cycle_runtime_state "$pr_key"
    done

    for raw in "${RAW_AFTER_ARGS[@]}"; do
        if [[ "$raw" == *'='* ]]; then
            selector="${raw%%=*}"
            timestamp="${raw#*=}"

            mapfile -t parsed < <(parse_repo_pr_token "$selector" "$current_repo")
            parsed_repo="${parsed[0]}"
            parsed_pr="${parsed[1]}"
            normalized_selector="$(make_pr_key "$parsed_repo" "$parsed_pr")"
            timestamp="$(normalize_timestamp "$timestamp")"

            matched=false
            accepted=""
            for pr_key in "${PR_KEYS[@]}"; do
                accepted+="${pr_key} "
                if [[ "$pr_key" == "$normalized_selector" ]]; then
                    matched=true
                    if [[ -n "${KEY_TO_AFTER[$pr_key]:-}" ]]; then
                        fail "Duplicate --after provided for ${pr_key}. Pass at most one cutoff per PR."
                    fi
                    KEY_TO_AFTER["$pr_key"]="$timestamp"
                fi
            done

            if [[ "$matched" != "true" ]]; then
                fail "The --after selector '$selector' does not match a watched PR. Accepted selectors: ${accepted% }"
            fi
        else
            if [[ ${#PR_KEYS[@]} -ne 1 ]]; then
                fail "Ambiguous --after value '$raw'. When monitoring multiple PRs, use --after owner/repo#123=<timestamp> once per PR."
            fi

            if [[ -n "${KEY_TO_AFTER[${PR_KEYS[0]}]:-}" ]]; then
                fail "Duplicate --after provided for ${PR_KEYS[0]}. Pass at most one cutoff per PR."
            fi

            KEY_TO_AFTER["${PR_KEYS[0]}"]="$(normalize_timestamp "$raw")"
        fi
    done
}

validate_after_cutoffs() {
    local key
    local cutoff
    local latest_time
    local latest_type

    for key in "${PR_KEYS[@]}"; do
        cutoff="${KEY_TO_AFTER[$key]:-}"
        [[ -n "$cutoff" ]] || continue

        latest_time="${KEY_TO_LATEST_ACTIVITY_TIME[$key]:-}"
        latest_type="${KEY_TO_LATEST_ACTIVITY_TYPE[$key]:-unknown activity}"

        [[ -n "$latest_time" ]] || continue

        if compare_iso_gt "$cutoff" "$latest_time"; then
            echo -e "${RED}❌ --after ${key}=${cutoff} may not be later than the most recent PR activity.${NC}" >&2
            echo -e "${RED}   Latest activity: ${latest_type}${NC}" >&2
            echo -e "${RED}   Latest timestamp: ${latest_time}${NC}" >&2
            echo -e "${RED}   Retry with: --after \"${key}=${latest_time}\"${NC}" >&2
            exit 1
        fi
    done
}

print_targets() {
    local key

    note "🔍 Initializing monitors for:"
    for key in "${PR_KEYS[@]}"; do
        echo -e "${BLUE}   - ${key}${NC}"
    done
    echo ""
}

print_pr_status() {
    local key
    local title
    local last_commit

    for key in "${PR_KEYS[@]}"; do
        title="${KEY_TO_TITLE[$key]}"
        last_commit="${KEY_TO_LAST_COMMIT[$key]}"
        if [[ "${KEY_TO_IS_OPEN[$key]:-true}" == "true" ]]; then
            echo -e "  ${GREEN}✓${NC} ${key}: ${title} (last commit: ${last_commit:0:16})"
        else
            echo -e "  ${YELLOW}✓${NC} ${key}: ${title} (closed)"
        fi
        echo -e "${BLUE}     ${KEY_TO_URL[$key]}${NC}"
        if [[ -n "${KEY_TO_AFTER[$key]:-}" ]]; then
            echo -e "${BLUE}     After: ${KEY_TO_AFTER[$key]}${NC}"
        fi
    done
    echo ""
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --repo)
                [[ $# -ge 2 ]] || fail "--repo requires owner/repo"
                REPO_ARG="$2"
                shift 2
                ;;
            --check-once)
                CHECK_ONCE=true
                shift
                ;;
            --after)
                [[ $# -ge 2 ]] || fail "--after requires a timestamp or selector=timestamp"
                RAW_AFTER_ARGS+=("$2")
                shift 2
                ;;
            --codex-login)
                [[ $# -ge 2 ]] || fail "--codex-login requires a login"
                CODEX_REVIEWER_LOGIN="$2"
                shift 2
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            --*)
                fail "Unknown option: $1"
                ;;
            *)
                RAW_PR_ARGS+=("$1")
                shift
                ;;
        esac
    done
}

resolve_pr_targets() {
    local current_repo="${REPO_ARG:-}"
    local token
    local repo
    local pr
    local key

    if [[ -z "$current_repo" ]]; then
        current_repo="$(detect_repo_from_git || true)"
    fi

    if [[ ${#RAW_PR_ARGS[@]} -eq 0 ]]; then
        [[ -n "$current_repo" ]] || fail "Could not determine repository. Use --repo owner/repo or run from a git repo with a GitHub remote."
        local current_pr
        current_pr=$(gh pr view --repo "$current_repo" --json number --jq '.number' 2>/dev/null || true)
        [[ -n "$current_pr" ]] || fail "Usage: $0 [--repo owner/repo] [--check-once] [--after <selector>=<timestamp>] [--codex-login <login>] <pr selector...>"
        RAW_PR_ARGS=("$current_pr")
        note "ℹ️  Using current PR: ${current_repo}#${current_pr}"
    fi

    for token in "${RAW_PR_ARGS[@]}"; do
        mapfile -t parsed < <(parse_repo_pr_token "$token" "$current_repo")
        repo="${parsed[0]}"
        pr="${parsed[1]}"
        key="$(make_pr_key "$repo" "$pr")"
        add_pr_key "$key"
    done

    resolve_after_mappings "$current_repo"
}

load_all_pr_metadata() {
    local key
    local any_open=false
    for key in "${PR_KEYS[@]}"; do
        if load_pr_metadata "$key" "${KEY_TO_REPO[$key]:-${key%#*}}" "${KEY_TO_PR[$key]:-${key##*#}}"; then
            any_open=true
        fi
    done

    if [[ "$any_open" != true ]]; then
        fail "All monitored PRs are already closed. Start the watcher on an open PR instead."
    fi
}

prime_latest_activity() {
    local key
    for key in "${PR_KEYS[@]}"; do
        [[ "${KEY_TO_IS_OPEN[$key]:-true}" == "true" ]] || continue
        [[ -n "${KEY_TO_AFTER[$key]:-}" ]] || continue
        KEY_TO_LATEST_ACTIVITY_TIME["$key"]=""
        KEY_TO_LATEST_ACTIVITY_TYPE["$key"]=""
        NEW_SIGNAL_FOUND=0
        scan_pr_activity "$key" "9999-12-31T23:59:59Z" false false
    done
}

first_sweep() {
    local key
    local baseline

    NEW_SIGNAL_FOUND=0
    APPROVAL_SIGNAL_FOUND=0
    POSTCOMMIT_BOUNDARY_FOUND=0
    note "👀 Checking for existing new activity..."

    for key in "${PR_KEYS[@]}"; do
        [[ "${KEY_TO_IS_OPEN[$key]:-true}" == "true" ]] || continue
        POSTCOMMIT_BOUNDARY_FOUND=0
        baseline="$(effective_baseline_for_key "$key")"
        scan_pr_activity "$key" "$baseline" true false
    done
}

refresh_pr_state() {
    local key="$1"
    local repo="${KEY_TO_REPO[$key]}"
    local pr="${KEY_TO_PR[$key]}"
    local pr_data
    local state
    local title
    local url
    local current_head_sha
    local current_commit

    if ! pr_data=$(gh pr view "$pr" --repo "$repo" --json title,state,url 2>/dev/null); then
        fail "Failed to refresh ${key}. Check gh auth and verify the PR still exists."
    fi

    state=$(jq -r '.state' <<<"$pr_data")
    title=$(jq -r '.title' <<<"$pr_data")
    url=$(jq -r '.url' <<<"$pr_data")

    KEY_TO_TITLE["$key"]="$title"
    KEY_TO_URL["$key"]="$url"
    KEY_TO_IS_OPEN["$key"]=true

    if [[ "$state" != "OPEN" ]]; then
        KEY_TO_IS_OPEN["$key"]=false
        reset_review_cycle_runtime_state "$key"
        KEY_TO_LATEST_ACTIVITY_TIME["$key"]=""
        KEY_TO_LATEST_ACTIVITY_TYPE["$key"]=""
        warn "ℹ️ ${key} ${state}"
        return 1
    fi

    if ! current_head_sha=$(get_pr_head_sha "$repo" "$pr"); then
        fail "Could not refresh the latest head SHA for ${key}."
    fi

    if ! current_commit=$(get_pr_last_commit_date "$repo" "$pr"); then
        fail "Could not refresh the latest commit timestamp for ${key}."
    fi

    if [[ "$current_head_sha" != "${KEY_TO_HEAD_SHA[$key]:-}" ]]; then
        note "📝 ${key}: new commit detected"
        note "   New baseline: ${current_commit:0:16}"
        reset_review_cycle_runtime_state "$key"
        KEY_TO_HEAD_SHA["$key"]="$current_head_sha"
        KEY_TO_LAST_COMMIT["$key"]="$current_commit"
    elif [[ "$current_commit" != "${KEY_TO_LAST_COMMIT[$key]}" ]]; then
        KEY_TO_LAST_COMMIT["$key"]="$current_commit"
    fi

    return 0
}

monitor_loop() {
    local any_open=false
    local key
    local baseline

    while true; do
        any_open=false
        NEW_SIGNAL_FOUND=0
        APPROVAL_SIGNAL_FOUND=0

        for key in "${PR_KEYS[@]}"; do
            if ! refresh_pr_state "$key"; then
                continue
            fi

            any_open=true

            KEY_TO_LATEST_ACTIVITY_TIME["$key"]=""
            KEY_TO_LATEST_ACTIVITY_TYPE["$key"]=""
            KEY_TO_FORCE_REPORT_NESTED_REACTION_SCAN["$key"]=false
            POSTCOMMIT_BOUNDARY_FOUND=0

            scan_pr_activity "$key" "$(effective_baseline_for_key "$key")" false true

            baseline="$(effective_baseline_for_key "$key")"
            POSTCOMMIT_BOUNDARY_FOUND=0
            scan_pr_activity "$key" "$baseline" true true
            validate_after_cutoffs
        done

        if [[ "$NEW_SIGNAL_FOUND" -eq 1 ]]; then
            echo ""
            pass "📋 Found new activity to address. Exiting so the agent can process it."
            exit 2
        fi

        if [[ "$APPROVAL_SIGNAL_FOUND" -eq 1 ]] && ! any_pending_precommit_actionable && all_open_prs_have_approval_signal; then
            echo ""
            pass "✅ Codex approval/no-issues signal found. No new actionable feedback."
            printf '%s\n' "Codex PR review completed: No new issues found. If you haven't already: You may now run final Oracle verification pass on this code. Once both Codex reviewer and Oracle have signed off, alert the user that all reviews are complete and the code is ready to merge"
            exit 0
        fi

        if [[ "$any_open" != true ]]; then
            pass "✅ All monitored PRs closed"
            exit 0
        fi

        sleep 30
    done
}

main() {
    parse_args "$@"

    export GH_FIXTURE_RUN_ID="${GH_FIXTURE_RUN_ID:-watcher-$$}"

    command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is not installed"
    command -v jq >/dev/null 2>&1 || fail "jq is required for JSON parsing"

    if ! gh auth status >/dev/null 2>&1; then
        fail "Not authenticated with gh"
    fi

    resolve_pr_targets
    load_all_pr_metadata
    print_targets
    print_pr_status

    prime_latest_activity
    validate_after_cutoffs

    first_sweep

    if [[ "$NEW_SIGNAL_FOUND" -eq 1 ]]; then
        echo ""
        pass "📋 Found new activity to address. Exiting so the agent can process it."
        exit 2
    fi

    if [[ "$APPROVAL_SIGNAL_FOUND" -eq 1 ]] && ! any_pending_precommit_actionable && all_open_prs_have_approval_signal; then
        echo ""
        pass "✅ Codex approval/no-issues signal found. No new actionable feedback."
        printf '%s\n' "Codex PR review completed: No new issues found. If you haven't already: You may now run final Oracle verification pass on this code. Once both Codex reviewer and Oracle have signed off, alert the user that all reviews are complete and the code is ready to merge"
        exit 0
    fi

    if [[ "$CHECK_ONCE" == true ]]; then
        if any_pending_precommit_actionable; then
            warn "⏳ Earlier actionable feedback is visible, but the latest review cycle is still in progress. A normal watch run would keep waiting for a post-commit review signal."
            exit 2
        fi
        if ! all_open_prs_acknowledged_or_approved; then
            warn "⏳ No actionable feedback is currently visible, but review is still pending. A normal watch run would keep waiting for approval or new feedback."
            exit 2
        fi
        pass "✓ No pending activity."
        exit 0
    fi

    if printf '%s\n' "${KEY_TO_PENDING_PRECOMMIT_ACTIONABLE[@]:-}" | grep -qx 'true'; then
        warn "⏳ Earlier actionable feedback is visible, but the latest review cycle is still in progress. Waiting for a post-commit review signal before exiting."
    else
        pass "✓ No pending activity. Starting monitor..."
    fi

    warn "   Press Ctrl+C to stop"
    echo ""
    monitor_loop
}

main "$@"
