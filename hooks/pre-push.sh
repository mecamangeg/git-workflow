#!/bin/bash
# Git Workflow Guardian - Pre-Push Hook
# Prevents pushes to main/master branch

# Read push details from stdin
while read local_ref local_sha remote_ref remote_sha; do
    # Extract branch name from remote ref
    remote_branch=$(echo "$remote_ref" | sed 's|refs/heads/||')

    # Check if pushing to protected branch
    if [ "$remote_branch" = "main" ] || [ "$remote_branch" = "master" ]; then
        python3 "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "push_to_main" \
            --branch "$remote_branch" \
            --repo "$(git rev-parse --show-toplevel)"

        exit $?
    fi
done

exit 0
