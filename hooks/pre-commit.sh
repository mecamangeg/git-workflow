#!/bin/bash
# Git Workflow Guardian - Pre-Commit Hook
# Prevents commits to main/master branch

# Detect Python command (python3 or python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.8+"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Define protected branches
PROTECTED_BRANCHES=("main" "master")

# Check if current branch is protected
for branch in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$CURRENT_BRANCH" = "$branch" ]; then
        # Call Python notifier with violation details
        $PYTHON_CMD "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "commit_to_main" \
            --branch "$CURRENT_BRANCH" \
            --repo "$(git rev-parse --show-toplevel)"

        # Exit code from notifier determines if commit proceeds
        exit $?
    fi
done

# Allow commit (not on protected branch)
exit 0
