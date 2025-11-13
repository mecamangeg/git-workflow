"""Pytest fixtures for Git Workflow Guardian tests"""
import os
import tempfile
import pytest
from pathlib import Path
import subprocess


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing"""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )

    # Create initial commit on main
    (repo_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True
    )

    return repo_path


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "rules": {
            "commit_to_main": {
                "severity": "critical",
                "enabled": True,
                "blocking": True,
                "message": "You're about to commit to main branch",
                "action": "Create a feature branch first",
                "why": "Main should only receive reviewed code via PRs."
            },
            "push_to_main": {
                "severity": "critical",
                "enabled": True,
                "blocking": True
            },
            "branch_naming": {
                "severity": "warning",
                "enabled": True,
                "blocking": False,
                "pattern": "^claude/[a-z0-9-]+-[A-Za-z0-9]{24}$"
            }
        },
        "monitoring": {
            "poll_interval": 1  # Fast polling for tests
        },
        "notifications": {
            "critical": {
                "type": "popup",
                "blocking": True
            },
            "suggestion": {
                "type": "toast",
                "blocking": False,
                "timeout": 10
            }
        }
    }


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary SQLite database"""
    db_path = tmp_path / "test.db"
    # Initialize schema
    from service.state import StateManager
    StateManager(str(db_path)).initialize()
    return db_path


@pytest.fixture
def mock_config_manager(mock_config, tmp_path):
    """Create a mock ConfigManager with test configuration"""
    import yaml
    from service.config import ConfigManager

    # Create temporary config file
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(mock_config, f)

    return ConfigManager(str(config_file))
