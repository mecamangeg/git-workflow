#!/bin/bash
# Git Workflow Guardian - Post-Merge Hook
# Suggests deleting merged branches

# Detect Python command (python3 or python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    # Silently exit if Python not found (post-merge is non-critical)
    exit 0
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Get merged branches (excluding main/master)
MERGED_BRANCHES=$(git branch --merged | grep -v -E "^\*|main|master" | sed 's/^[ \t]*//')

# Suggest deletion for each merged branch
if [ -n "$MERGED_BRANCHES" ]; then
    for branch in $MERGED_BRANCHES; do
        $PYTHON_CMD "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "delete_merged_branch" \
            --branch "$branch" \
            --repo "$(git rev-parse --show-toplevel)" \
            --non-blocking &
    done
fi

exit 0
