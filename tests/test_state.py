"""Tests for state management"""
import pytest
from pathlib import Path
from service.state import StateManager


def test_state_manager_initialization(temp_db):
    """Test StateManager initializes database correctly"""
    state = StateManager(str(temp_db))

    # Check that tables exist
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    assert "repositories" in tables
    assert "violations" in tables
    assert "overrides" in tables

    conn.close()


def test_log_violation(temp_db):
    """Test logging violations"""
    state = StateManager(str(temp_db))

    repo_path = Path("/tmp/test-repo")
    state.log_violation(
        repo_path=repo_path,
        rule_name="commit_to_main",
        severity="critical",
        branch_name="main"
    )

    # Verify violation was logged
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM violations")
    count = cursor.fetchone()[0]

    assert count == 1

    conn.close()


def test_override_checking(temp_db):
    """Test override checking"""
    state = StateManager(str(temp_db))

    # Initially not overridden
    assert not state.is_overridden("commit_to_main", "test-branch")

    # Add override
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    # Create repo first
    cursor.execute("INSERT INTO repositories (path, name) VALUES (?, ?)", ("/tmp/test", "test"))
    repo_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO overrides (repo_id, rule_name, session_id, expires_at)
        VALUES (?, ?, ?, NULL)
    """, (repo_id, "commit_to_main", "test-branch"))

    conn.commit()
    conn.close()

    # Should be overridden now
    assert state.is_overridden("commit_to_main", "test-branch")


def test_get_compliance_stats(temp_db):
    """Test compliance statistics"""
    state = StateManager(str(temp_db))

    repo_path = Path("/tmp/test-repo")

    # Log some violations
    state.log_violation(repo_path, "commit_to_main", "critical", "main")
    state.log_violation(repo_path, "test_locally", "suggestion", "feature")
    state.log_violation(repo_path, "commit_to_main", "critical", "main", overridden=True)

    stats = state.get_compliance_stats(repo_path)

    assert stats["total_violations"] == 3
    assert stats["overridden_count"] == 1
    assert "critical" in stats["by_severity"]
    assert "suggestion" in stats["by_severity"]
