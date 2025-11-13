#!/bin/bash
# Git Workflow Guardian - Pre-Push Hook
# Prevents pushes to main/master branch

# Detect Python command (python3 or python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.8+"
    exit 1
fi

# Read push details from stdin
while read local_ref local_sha remote_ref remote_sha; do
    # Extract branch name from remote ref
    remote_branch=$(echo "$remote_ref" | sed 's|refs/heads/||')

    # Check if pushing to protected branch
    if [ "$remote_branch" = "main" ] || [ "$remote_branch" = "master" ]; then
        $PYTHON_CMD "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "push_to_main" \
            --branch "$remote_branch" \
            --repo "$(git rev-parse --show-toplevel)"

        exit $?
    fi
done

exit 0
