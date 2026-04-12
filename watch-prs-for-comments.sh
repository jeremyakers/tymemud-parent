#!/bin/bash
# watch-prs-for-comments.sh
# Monitors multiple PRs for NEW comments (posted after last commit)
# Checks both general PR comments AND review comments (line-specific)
# Usage: ./watch-prs-for-comments.sh [--repo owner/repo] [--check-once] [--after <timestamp>] [--codex-login <login>] <pr_number1> [pr_number2] ...

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ARG=""
CHECK_ONCE=false
AFTER_TIMESTAMP=""
CODEX_REVIEWER_LOGIN="${CODEX_REVIEWER_LOGIN:-codex}"
PR_NUMBERS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO_ARG="$2"
            shift 2
            ;;
        --check-once)
            CHECK_ONCE=true
            shift
            ;;
        --after)
            AFTER_TIMESTAMP="$2"
            shift 2
            ;;
        --codex-login)
            CODEX_REVIEWER_LOGIN="$2"
            shift 2
            ;;
        --*)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            exit 1
            ;;
        *)
            PR_NUMBERS+=("$1")
            shift
            ;;
    esac
done

if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ Error: GitHub CLI (gh) is not installed${NC}"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Error: Not authenticated with gh${NC}"
    exit 1
fi

# Get repo info
if [ -n "$REPO_ARG" ]; then
    REPO="$REPO_ARG"
else
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
    if [[ "$REMOTE_URL" == *github.com* ]]; then
        REPO=$(echo "$REMOTE_URL" | sed 's/.*github.com[:/]//; s/.git$//')
    fi
fi

if [ -z "$REPO" ]; then
    echo -e "${RED}❌ Could not determine repository${NC}"
    echo "   Use --repo owner/repo or run from a git repo with GitHub remote"
    exit 1
fi

# Get PR numbers
if [ ${#PR_NUMBERS[@]} -eq 0 ]; then
    CURRENT_PR=$(gh pr view --repo "$REPO" --json number -q '.number' 2>/dev/null || echo "")
    if [ -n "$CURRENT_PR" ]; then
        PR_NUMBERS=($CURRENT_PR)
        echo -e "${BLUE}ℹ️  Using current PR: #$CURRENT_PR${NC}"
    else
        echo -e "${RED}❌ Usage: $0 [--repo owner/repo] [--check-once] [--after <timestamp>] [--codex-login <login>] <pr_number1> [pr_number2] ...${NC}"
        exit 1
    fi
else
    : # no-op
fi

if [ -n "$AFTER_TIMESTAMP" ]; then
    echo -e "${BLUE}🔍 Monitoring PRs: ${PR_NUMBERS[*]}${NC}"
    echo -e "${BLUE}   Repository: $REPO${NC}"
    echo -e "${BLUE}   Showing only comments posted after: ${AFTER_TIMESTAMP}${NC}"
else
    echo -e "${BLUE}🔍 Initializing monitors for PRs: ${PR_NUMBERS[*]}${NC}"
    echo -e "${BLUE}   Repository: $REPO${NC}"
fi
echo ""

declare -A LAST_COMMIT_TIMES
declare -A SEEN_COMMENT_IDS
declare -A SEEN_REACTION_IDS
declare -A PR_TITLES

# Function to get latest commit date for a PR
get_pr_last_commit_date() {
    local pr_num=$1
    local repo=$2
    
    local head_sha=$(gh pr view "$pr_num" --repo "$repo" --json headRefOid --jq '.headRefOid' 2>/dev/null)
    
    if [ -z "$head_sha" ] || [ "$head_sha" = "null" ]; then
        echo ""
        return 1
    fi
    
    local commit_date=$(gh api repos/$repo/commits/$head_sha --jq '.commit.committer.date' 2>/dev/null)
    
    if [ -z "$commit_date" ] || [ "$commit_date" = "null" ]; then
        commit_date=$(gh api repos/$repo/commits/$head_sha --jq '.commit.author.date' 2>/dev/null)
    fi
    
    echo "$commit_date"
}

fetch_general_comment_reactions() {
    local repo=$1
    local comment_id=$2

    gh api "repos/$repo/issues/comments/$comment_id/reactions" -H "Accept: application/vnd.github+json" 2>/dev/null || echo '[]'
}

fetch_general_comments() {
    local pr_num=$1
    local repo=$2

    gh api "repos/$repo/issues/$pr_num/comments" 2>/dev/null || echo '[]'
}

fetch_review_comment_reactions() {
    local repo=$1
    local comment_id=$2

    gh api "repos/$repo/pulls/comments/$comment_id/reactions" -H "Accept: application/vnd.github+json" 2>/dev/null || echo '[]'
}

reaction_key() {
    local source_prefix=$1
    local comment_id=$2
    local reaction_id=$3

    echo "${source_prefix}_${comment_id}_${reaction_id}"
}

mark_codex_reactions_seen_through_baseline() {
    local pr_num=$1
    local source_type=$2
    local comments_json=$3
    local baseline=$4
    local count=0
    local comment_id=""
    local reactions='[]'
    local reaction_count=0
    local reaction_id=""
    local reaction_time=""
    local reaction_content=""
    local reaction_login=""
    local source_prefix=""
    local key=""

    if [ "$source_type" = "general" ]; then
        count=$(echo "$comments_json" | jq 'length')
        source_prefix="genreact"
    else
        count=$(echo "$comments_json" | jq 'length')
        source_prefix="revreact"
    fi

    for ((comment_idx=0; comment_idx<count; comment_idx++)); do
        if [ "$source_type" = "general" ]; then
            comment_id=$(echo "$comments_json" | jq -r ".[$comment_idx].id")
            reactions=$(fetch_general_comment_reactions "$REPO" "$comment_id")
        else
            comment_id=$(echo "$comments_json" | jq -r ".[$comment_idx].id")
            reactions=$(fetch_review_comment_reactions "$REPO" "$comment_id")
        fi

        reaction_count=$(echo "$reactions" | jq 'length')
        for ((reaction_idx=0; reaction_idx<reaction_count; reaction_idx++)); do
            reaction_id=$(echo "$reactions" | jq -r ".[$reaction_idx].id")
            reaction_time=$(echo "$reactions" | jq -r ".[$reaction_idx].created_at // empty")
            reaction_content=$(echo "$reactions" | jq -r ".[$reaction_idx].content // empty")
            reaction_login=$(echo "$reactions" | jq -r ".[$reaction_idx].user.login // empty")
            key=$(reaction_key "$source_prefix" "$comment_id" "$reaction_id")

            if [ "$reaction_content" = "+1" ] && [ "$reaction_login" = "$CODEX_REVIEWER_LOGIN" ] && { [ -z "$reaction_time" ] || [ "$reaction_time" = "$baseline" ] || [[ "$reaction_time" < "$baseline" ]]; }; then
                SEEN_REACTION_IDS[$pr_num]="${SEEN_REACTION_IDS[$pr_num]}${key},"
            fi
        done
    done
}

has_new_codex_approval_reaction() {
    local pr_num=$1
    local source_type=$2
    local comments_json=$3
    local baseline=$4
    local count=0
    local comment_id=""
    local reactions='[]'
    local reaction_count=0
    local reaction_id=""
    local reaction_time=""
    local reaction_content=""
    local reaction_login=""
    local source_prefix=""
    local key=""

    if [ "$source_type" = "general" ]; then
        count=$(echo "$comments_json" | jq 'length')
        source_prefix="genreact"
    else
        count=$(echo "$comments_json" | jq 'length')
        source_prefix="revreact"
    fi

    for ((comment_idx=0; comment_idx<count; comment_idx++)); do
        if [ "$source_type" = "general" ]; then
            comment_id=$(echo "$comments_json" | jq -r ".[$comment_idx].id")
            reactions=$(fetch_general_comment_reactions "$REPO" "$comment_id")
        else
            comment_id=$(echo "$comments_json" | jq -r ".[$comment_idx].id")
            reactions=$(fetch_review_comment_reactions "$REPO" "$comment_id")
        fi

        reaction_count=$(echo "$reactions" | jq 'length')
        for ((reaction_idx=0; reaction_idx<reaction_count; reaction_idx++)); do
            reaction_id=$(echo "$reactions" | jq -r ".[$reaction_idx].id")
            reaction_time=$(echo "$reactions" | jq -r ".[$reaction_idx].created_at // empty")
            reaction_content=$(echo "$reactions" | jq -r ".[$reaction_idx].content // empty")
            reaction_login=$(echo "$reactions" | jq -r ".[$reaction_idx].user.login // empty")
            key=$(reaction_key "$source_prefix" "$comment_id" "$reaction_id")

            [[ "${SEEN_REACTION_IDS[$pr_num]}" == *"${key},"* ]] && continue

            if [ "$reaction_content" = "+1" ] && [ "$reaction_login" = "$CODEX_REVIEWER_LOGIN" ] && [ -n "$reaction_time" ] && [[ "$reaction_time" > "$baseline" ]]; then
                SEEN_REACTION_IDS[$pr_num]="${SEEN_REACTION_IDS[$pr_num]}${key},"
                return 0
            fi
        done
    done

    return 1
}

# Function to display review comment with metadata
display_review_comment() {
    local pr_num=$1
    local reviews_json=$2
    local idx=$3
    local author=$4
    local body=$5
    local created_at=$6
    
    local file=$(echo "$reviews_json" | jq -r ".[$idx].path")
    local line=$(echo "$reviews_json" | jq -r ".[$idx].line // empty")
    local orig_line=$(echo "$reviews_json" | jq -r ".[$idx].original_line // empty")
    local start_line=$(echo "$reviews_json" | jq -r ".[$idx].start_line // empty")
    local end_line=$(echo "$reviews_json" | jq -r ".[$idx].end_line // empty")
    local commit_id=$(echo "$reviews_json" | jq -r ".[$idx].commit_id // empty")
    
    local line_range=""
    if [ -n "$start_line" ] && [ -n "$end_line" ] && [ "$start_line" != "$end_line" ]; then
        line_range="lines $start_line-$end_line"
    elif [ -n "$line" ]; then
        line_range="line $line"
    elif [ -n "$orig_line" ]; then
        line_range="line $orig_line (original)"
    else
        line_range="line unknown"
    fi
    
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}🔔 NEW REVIEW COMMENT on PR #$pr_num: ${PR_TITLES[$pr_num]}${NC}"
    echo -e "${YELLOW}   File: ${file}${NC}"
    echo -e "${YELLOW}   Location: ${line_range}${NC}"
    if [ -n "$commit_id" ]; then
        echo -e "${YELLOW}   Commit: ${commit_id:0:7}${NC}"
    fi
    echo -e "${YELLOW}   Posted: ${created_at}${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
    echo "From: @$author"
    echo ""
    echo "$body"
    echo -e "${YELLOW}───────────────────────────────────────────────────────────────${NC}"
    echo ""
}

# Init each PR
for PR_NUM in "${PR_NUMBERS[@]}"; do
    echo -n "  PR #$PR_NUM: "
    
    PR_DATA=$(gh pr view "$PR_NUM" --repo "$REPO" --json number,title,state 2>/dev/null) || {
        echo -e "${RED}❌ Failed to fetch${NC}"
        continue
    }
    
    STATE=$(echo "$PR_DATA" | jq -r '.state')
    if [ "$STATE" != "OPEN" ]; then
        echo -e "${YELLOW}⚠️  $STATE${NC}"
        continue
    fi
    
    TITLE=$(echo "$PR_DATA" | jq -r '.title')
    
    LAST_COMMIT_TIME=$(get_pr_last_commit_date "$PR_NUM" "$REPO")
    [ -z "$LAST_COMMIT_TIME" ] && LAST_COMMIT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    PR_TITLES[$PR_NUM]="$TITLE"
    LAST_COMMIT_TIMES[$PR_NUM]="$LAST_COMMIT_TIME"
    SEEN_COMMENT_IDS[$PR_NUM]=""
    SEEN_REACTION_IDS[$PR_NUM]=""
    
    # Pre-mark older comments/reviews as seen
    GENERAL=$(fetch_general_comments "$PR_NUM" "$REPO")
    REVIEWS=$(gh api repos/$REPO/pulls/$PR_NUM/comments 2>/dev/null || echo '[]')
    
    COUNT=$(echo "$GENERAL" | jq 'length')
    for ((i=0; i<COUNT; i++)); do
        TIME=$(echo "$GENERAL" | jq -r ".[$i].created_at")
        ID=$(echo "$GENERAL" | jq -r ".[$i].id")
        # If --after is set, mark comments at or before that time as seen
        if [ -n "$AFTER_TIMESTAMP" ]; then
            if [ "$TIME" = "$AFTER_TIMESTAMP" ] || [[ "$TIME" < "$AFTER_TIMESTAMP" ]]; then
                SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}gen_${ID},"
            fi
        elif [ "$TIME" \< "$LAST_COMMIT_TIME" ] 2>/dev/null || [ "$TIME" = "$LAST_COMMIT_TIME" ]; then
            SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}gen_${ID},"
        fi
    done
    
    COUNT=$(echo "$REVIEWS" | jq 'length')
    for ((i=0; i<COUNT; i++)); do
        TIME=$(echo "$REVIEWS" | jq -r ".[$i].created_at")
        ID=$(echo "$REVIEWS" | jq -r ".[$i].id")
        # If --after is set, mark comments at or before that time as seen
        if [ -n "$AFTER_TIMESTAMP" ]; then
            if [ "$TIME" = "$AFTER_TIMESTAMP" ] || [[ "$TIME" < "$AFTER_TIMESTAMP" ]]; then
                SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}rev_${ID},"
            fi
        elif [ "$TIME" \< "$LAST_COMMIT_TIME" ] 2>/dev/null || [ "$TIME" = "$LAST_COMMIT_TIME" ]; then
            SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}rev_${ID},"
        fi
    done

    if [ -n "$AFTER_TIMESTAMP" ]; then
        mark_codex_reactions_seen_through_baseline "$PR_NUM" "general" "$GENERAL" "$AFTER_TIMESTAMP"
        mark_codex_reactions_seen_through_baseline "$PR_NUM" "review" "$REVIEWS" "$AFTER_TIMESTAMP"
    else
        mark_codex_reactions_seen_through_baseline "$PR_NUM" "general" "$GENERAL" "$LAST_COMMIT_TIME"
        mark_codex_reactions_seen_through_baseline "$PR_NUM" "review" "$REVIEWS" "$LAST_COMMIT_TIME"
    fi
    
    echo -e "${GREEN}✓${NC} $TITLE (last commit: ${LAST_COMMIT_TIME:0:16})"
done

echo ""
echo -e "${BLUE}👀 Checking for existing new comments...${NC}"

NEW_FOUND=0

# First sweep: check both general and review comments
for PR_NUM in "${PR_NUMBERS[@]}"; do
    [ -z "${LAST_COMMIT_TIMES[$PR_NUM]}" ] && continue
    
    if [ -n "$AFTER_TIMESTAMP" ]; then
        BASELINE="$AFTER_TIMESTAMP"
    else
        BASELINE="${LAST_COMMIT_TIMES[$PR_NUM]}"
    fi
    
    # Check general comments
    GENERAL=$(fetch_general_comments "$PR_NUM" "$REPO")
    COUNT=$(echo "$GENERAL" | jq 'length')
    for ((i=0; i<COUNT; i++)); do
        ID=$(echo "$GENERAL" | jq -r ".[$i].id")
        TIME=$(echo "$GENERAL" | jq -r ".[$i].created_at")
        AUTHOR=$(echo "$GENERAL" | jq -r ".[$i].user.login")
        BODY=$(echo "$GENERAL" | jq -r ".[$i].body")
        
        [[ "${SEEN_COMMENT_IDS[$PR_NUM]}" == *"gen_${ID},"* ]] && continue
        
        # Use strict > comparison (exclusive)
        if [ "$TIME" \> "$BASELINE" ] 2>/dev/null; then
            NEW_FOUND=1
            
            echo ""
            echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "${YELLOW}🔔 NEW COMMENT on PR #$PR_NUM: ${PR_TITLES[$PR_NUM]}${NC}"
            echo -e "${YELLOW}   Posted: ${TIME}${NC}"
            echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
            echo "From: @$AUTHOR"
            echo ""
            echo "$BODY"
            echo ""
            echo -e "${BLUE}To ignore this comment and future ones, restart with:${NC}"
            echo -e "${BLUE}   --after \"${TIME}\"${NC}"
            echo -e "${YELLOW}───────────────────────────────────────────────────────────────${NC}"
            echo ""
            
            SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}gen_${ID},"
        fi
    done
    
    # Check review comments (line-specific)
    REVIEWS=$(gh api repos/$REPO/pulls/$PR_NUM/comments 2>/dev/null || echo '[]')
    COUNT=$(echo "$REVIEWS" | jq 'length')
    for ((i=0; i<COUNT; i++)); do
        ID=$(echo "$REVIEWS" | jq -r ".[$i].id")
        TIME=$(echo "$REVIEWS" | jq -r ".[$i].created_at")
        
        [[ "${SEEN_COMMENT_IDS[$PR_NUM]}" == *"rev_${ID},"* ]] && continue
        
        # Use strict > comparison (exclusive)
        if [ "$TIME" \> "$BASELINE" ] 2>/dev/null; then
            NEW_FOUND=1
            AUTHOR=$(echo "$REVIEWS" | jq -r ".[$i].user.login")
            BODY=$(echo "$REVIEWS" | jq -r ".[$i].body")
            
            display_review_comment "$PR_NUM" "$REVIEWS" "$i" "$AUTHOR" "$BODY" "$TIME"
            
            # Show the --after hint after the comment display
            echo -e "${BLUE}To ignore this comment and future ones, restart with:${NC}"
            echo -e "${BLUE}   --after \"${TIME}\"${NC}"
            echo ""
            
            SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}rev_${ID},"
        fi
    done
done

if [ $NEW_FOUND -eq 0 ]; then
    for PR_NUM in "${PR_NUMBERS[@]}"; do
        [ -z "${LAST_COMMIT_TIMES[$PR_NUM]}" ] && continue

        if [ -n "$AFTER_TIMESTAMP" ]; then
            BASELINE="$AFTER_TIMESTAMP"
        else
            BASELINE="${LAST_COMMIT_TIMES[$PR_NUM]}"
        fi

        GENERAL=$(fetch_general_comments "$PR_NUM" "$REPO")
        if has_new_codex_approval_reaction "$PR_NUM" "general" "$GENERAL" "$BASELINE"; then
            printf '%s\n' "PR review completed: No new issues found. You may now run final Oracle verification pass on this code"
            exit 0
        fi

        REVIEWS=$(gh api repos/$REPO/pulls/$PR_NUM/comments 2>/dev/null || echo '[]')
        if has_new_codex_approval_reaction "$PR_NUM" "review" "$REVIEWS" "$BASELINE"; then
            printf '%s\n' "PR review completed: No new issues found. You may now run final Oracle verification pass on this code"
            exit 0
        fi
    done
fi

if [ $NEW_FOUND -eq 1 ]; then
    echo ""
    echo -e "${GREEN}📋 Found new comments to address. Exiting so agent can process them.${NC}"
    exit 2
fi

if [ "$CHECK_ONCE" = true ]; then
    echo -e "${GREEN}✓ No pending comments.${NC}"
    exit 0
fi

echo -e "${GREEN}✓ No pending comments. Starting monitor...${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
echo ""

while true; do
    ALL_CLOSED=true
    
    for PR_NUM in "${PR_NUMBERS[@]}"; do
        [ -z "${LAST_COMMIT_TIMES[$PR_NUM]}" ] && continue
        
        STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state' 2>/dev/null || echo "UNKNOWN")
        if [ "$STATE" != "OPEN" ]; then
            echo -e "${GREEN}✅ PR #$PR_NUM $STATE${NC}"
            unset LAST_COMMIT_TIMES[$PR_NUM]
            continue
        fi
        ALL_CLOSED=false
        
        # Check for new commits by comparing commit dates
        CURRENT_COMMIT_TIME=$(get_pr_last_commit_date "$PR_NUM" "$REPO")
        [ -z "$CURRENT_COMMIT_TIME" ] && CURRENT_COMMIT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        
        if [ "$CURRENT_COMMIT_TIME" != "${LAST_COMMIT_TIMES[$PR_NUM]}" ]; then
            echo -e "${BLUE}📝 PR #$PR_NUM: new commit detected${NC}"
            echo -e "${BLUE}   New baseline: last commit at ${CURRENT_COMMIT_TIME:0:16}${NC}"
            
            LAST_COMMIT_TIMES[$PR_NUM]="$CURRENT_COMMIT_TIME"
            SEEN_COMMENT_IDS[$PR_NUM]=""
            SEEN_REACTION_IDS[$PR_NUM]=""
            
            GENERAL=$(fetch_general_comments "$PR_NUM" "$REPO")
            REVIEWS=$(gh api repos/$REPO/pulls/$PR_NUM/comments 2>/dev/null || echo '[]')
            
            COUNT=$(echo "$GENERAL" | jq 'length')
            for ((i=0; i<COUNT; i++)); do
                TIME=$(echo "$GENERAL" | jq -r ".[$i].created_at")
                ID=$(echo "$GENERAL" | jq -r ".[$i].id")
                if [ "$TIME" \< "$CURRENT_COMMIT_TIME" ] 2>/dev/null || [ "$TIME" = "$CURRENT_COMMIT_TIME" ]; then
                    SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}gen_${ID},"
                fi
            done
            
            COUNT=$(echo "$REVIEWS" | jq 'length')
            for ((i=0; i<COUNT; i++)); do
                TIME=$(echo "$REVIEWS" | jq -r ".[$i].created_at")
                ID=$(echo "$REVIEWS" | jq -r ".[$i].id")
                if [ "$TIME" \< "$CURRENT_COMMIT_TIME" ] 2>/dev/null || [ "$TIME" = "$CURRENT_COMMIT_TIME" ]; then
                    SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}rev_${ID},"
                fi
            done

            mark_codex_reactions_seen_through_baseline "$PR_NUM" "general" "$GENERAL" "$CURRENT_COMMIT_TIME"
            mark_codex_reactions_seen_through_baseline "$PR_NUM" "review" "$REVIEWS" "$CURRENT_COMMIT_TIME"
        fi
        
        NEW_FOUND=0
        
        if [ -n "$AFTER_TIMESTAMP" ]; then
            BASELINE="$AFTER_TIMESTAMP"
        else
            BASELINE="${LAST_COMMIT_TIMES[$PR_NUM]}"
        fi
        
        GENERAL=$(fetch_general_comments "$PR_NUM" "$REPO")
        COUNT=$(echo "$GENERAL" | jq 'length')
        for ((i=0; i<COUNT; i++)); do
            ID=$(echo "$GENERAL" | jq -r ".[$i].id")
            TIME=$(echo "$GENERAL" | jq -r ".[$i].created_at")
            [[ "${SEEN_COMMENT_IDS[$PR_NUM]}" == *"gen_${ID},"* ]] && continue

            if [ "$TIME" \> "$BASELINE" ] 2>/dev/null; then
                NEW_FOUND=1
                AUTHOR=$(echo "$GENERAL" | jq -r ".[$i].user.login")
                BODY=$(echo "$GENERAL" | jq -r ".[$i].body")
                
                echo ""
                echo -e "${YELLOW}🔔 NEW COMMENT on PR #$PR_NUM: ${PR_TITLES[$PR_NUM]}${NC}"
                echo "From: @$AUTHOR"
                echo "$BODY"
                echo ""
                
                SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}gen_${ID},"
            fi
        done
        
        REVIEWS=$(gh api repos/$REPO/pulls/$PR_NUM/comments 2>/dev/null || echo '[]')
        COUNT=$(echo "$REVIEWS" | jq 'length')
        for ((i=0; i<COUNT; i++)); do
            ID=$(echo "$REVIEWS" | jq -r ".[$i].id")
            TIME=$(echo "$REVIEWS" | jq -r ".[$i].created_at")
            [[ "${SEEN_COMMENT_IDS[$PR_NUM]}" == *"rev_${ID},"* ]] && continue
            
            if [ "$TIME" \> "$BASELINE" ] 2>/dev/null; then
                NEW_FOUND=1
                AUTHOR=$(echo "$REVIEWS" | jq -r ".[$i].user.login")
                BODY=$(echo "$REVIEWS" | jq -r ".[$i].body")
                
                display_review_comment "$PR_NUM" "$REVIEWS" "$i" "$AUTHOR" "$BODY" "$TIME"
                
                SEEN_COMMENT_IDS[$PR_NUM]="${SEEN_COMMENT_IDS[$PR_NUM]}rev_${ID},"
            fi
        done

        if [ $NEW_FOUND -eq 1 ]; then
            exit 2
        fi

        if has_new_codex_approval_reaction "$PR_NUM" "general" "$GENERAL" "$BASELINE"; then
            printf '%s\n' "PR review completed: No new issues found. You may now run final Oracle verification pass on this code"
            exit 0
        fi

        if has_new_codex_approval_reaction "$PR_NUM" "review" "$REVIEWS" "$BASELINE"; then
            printf '%s\n' "PR review completed: No new issues found. You may now run final Oracle verification pass on this code"
            exit 0
        fi
    done
    
    [ "$ALL_CLOSED" = true ] && echo -e "${GREEN}✅ All PRs closed${NC}" && exit 0
    
    sleep 30
done
