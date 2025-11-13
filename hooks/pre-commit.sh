#!/bin/bash
# Git Workflow Guardian - Pre-Commit Hook
# Prevents commits to main/master branch

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Define protected branches
PROTECTED_BRANCHES=("main" "master")

# Check if current branch is protected
for branch in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$CURRENT_BRANCH" = "$branch" ]; then
        # Call Python notifier with violation details
        python3 "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "commit_to_main" \
            --branch "$CURRENT_BRANCH" \
            --repo "$(git rev-parse --show-toplevel)"

        # Exit code from notifier determines if commit proceeds
        exit $?
    fi
done

# Allow commit (not on protected branch)
exit 0
