#!/bin/bash
# Git Workflow Guardian - Post-Checkout Hook
# Reminds to pull main after switching branches

# Arguments: previous_head new_head branch_checkout_flag
PREV_HEAD=$1
NEW_HEAD=$2
BRANCH_CHECKOUT=$3

# Only trigger on branch checkout (flag=1)
if [ "$BRANCH_CHECKOUT" != "1" ]; then
    exit 0
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Get main branch name
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$MAIN_BRANCH" ]; then
    MAIN_BRANCH="main"
fi

# Check if main is out of sync
if [ "$CURRENT_BRANCH" = "$MAIN_BRANCH" ]; then
    git fetch origin "$MAIN_BRANCH" --quiet 2>/dev/null

    LOCAL=$(git rev-parse "$MAIN_BRANCH" 2>/dev/null)
    REMOTE=$(git rev-parse "origin/$MAIN_BRANCH" 2>/dev/null)

    if [ -n "$LOCAL" ] && [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
        # Main is out of sync - suggest pull
        python3 "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "pull_before_work" \
            --branch "$MAIN_BRANCH" \
            --repo "$(git rev-parse --show-toplevel)" \
            --non-blocking
    fi
fi

exit 0
