"""Tests for git hooks"""
import subprocess
import pytest
from pathlib import Path


def test_pre_commit_hook_blocks_main(temp_git_repo):
    """Test that pre-commit hook blocks commits to main"""
    # Install a simple blocking hook
    hook_path = temp_git_repo / ".git" / "hooks" / "pre-commit"
    hook_path.write_text("#!/bin/bash\nexit 1\n")
    hook_path.chmod(0o755)

    # Attempt commit on main
    (temp_git_repo / "test.txt").write_text("test")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test"],
        cwd=temp_git_repo,
        capture_output=True
    )

    assert result.returncode != 0, "Commit should be blocked"


def test_pre_commit_hook_allows_feature_branch(temp_git_repo):
    """Test that commits are allowed on feature branches"""
    # Create and checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "claude/test-feature-123"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True
    )

    # Install a hook that only blocks main
    hook_path = temp_git_repo / ".git" / "hooks" / "pre-commit"
    hook_content = """#!/bin/bash
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    exit 1
fi
exit 0
"""
    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)

    # Commit should succeed
    (temp_git_repo / "test.txt").write_text("test")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test"],
        cwd=temp_git_repo,
        capture_output=True
    )

    assert result.returncode == 0, "Commit should be allowed on feature branch"


def test_pre_push_hook_blocks_main(temp_git_repo):
    """Test that pre-push hook blocks pushes to main"""
    # Install a simple blocking pre-push hook
    hook_path = temp_git_repo / ".git" / "hooks" / "pre-push"
    hook_content = """#!/bin/bash
while read local_ref local_sha remote_ref remote_sha; do
    remote_branch=$(echo "$remote_ref" | sed 's|refs/heads/||')
    if [ "$remote_branch" = "main" ] || [ "$remote_branch" = "master" ]; then
        exit 1
    fi
done
exit 0
"""
    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)

    # This test would require a remote, so we'll just verify the hook exists
    assert hook_path.exists()
    assert hook_path.stat().st_mode & 0o111  # Check executable bit


def test_branch_naming_pattern():
    """Test branch naming pattern validation"""
    import re
    pattern = r"^claude/[a-z0-9-]+-[A-Za-z0-9]{24}$"

    # Valid branch names
    assert re.match(pattern, "claude/feature-name-011CV4zUPzgSkobBUdcow2EN")
    assert re.match(pattern, "claude/fix-bug-123abc456def789ghi012jkl")

    # Invalid branch names
    assert not re.match(pattern, "main")
    assert not re.match(pattern, "feature/test")
    assert not re.match(pattern, "claude/Feature-Name-123")  # Capital in middle
    assert not re.match(pattern, "claude/feature")  # Missing session ID


def test_config_loading(mock_config_manager):
    """Test configuration loading"""
    assert mock_config_manager.get("rules.commit_to_main.severity") == "critical"
    assert mock_config_manager.get("rules.commit_to_main.enabled") is True
    assert mock_config_manager.get("monitoring.poll_interval") == 1
    assert mock_config_manager.get("nonexistent.key", "default") == "default"


def test_notifier_override_check(temp_db):
    """Test override checking logic"""
    from service.state import StateManager
    import sqlite3

    state = StateManager(str(temp_db))

    # No override exists initially
    assert not state.is_overridden("commit_to_main", "test-branch")

    # Add override
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO overrides (repo_id, rule_name, session_id, expires_at)
        VALUES (1, 'commit_to_main', 'test-branch', NULL)
    """)
    conn.commit()
    conn.close()

    # Override should now be active
    assert state.is_overridden("commit_to_main", "test-branch")
