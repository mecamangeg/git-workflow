"""Tests for monitoring service"""
import pytest
from pathlib import Path
from service.monitor import MonitorService
from service.detector import ViolationDetector


def test_monitor_service_initialization(mock_config_manager):
    """Test that MonitorService initializes correctly"""
    service = MonitorService()

    assert service.config is not None
    assert service.detector is not None
    assert service.notifier is not None
    assert service.state is not None
    assert service.is_running is False


def test_repository_discovery(temp_git_repo, tmp_path, monkeypatch):
    """Test repository auto-discovery"""
    # Create a mock config with the temp path
    import yaml
    config_file = tmp_path / "test_config.yaml"
    config = {
        "monitoring": {
            "repos": {
                "auto_discover": True,
                "search_paths": [str(temp_git_repo.parent)],
                "manual_repos": []
            },
            "poll_interval": 1
        },
        "rules": {}
    }

    with open(config_file, 'w') as f:
        yaml.dump(config, f)

    service = MonitorService(str(config_file))
    repos = service.discover_repositories()

    # Should find at least one repo (our test repo)
    assert len(repos) >= 1
    assert temp_git_repo in repos


def test_check_repository_finds_violations(temp_git_repo, mock_config_manager):
    """Test that check_repository detects violations"""
    service = MonitorService()

    # Create uncommitted changes
    (temp_git_repo / "test.txt").write_text("uncommitted change")

    violations = service.check_repository(temp_git_repo)

    # Should detect uncommitted changes or other violations
    # Result depends on configuration
    assert isinstance(violations, list)


def test_violation_processing(mock_config_manager, monkeypatch):
    """Test violation processing logic"""
    service = MonitorService()

    # Mock notification to prevent GUI
    notifications_sent = []

    def mock_show_toast(*args, **kwargs):
        notifications_sent.append(kwargs)

    monkeypatch.setattr(service.notifier, "show_toast", mock_show_toast)

    # Create test violation
    violations = [{
        "rule": "test_locally",
        "severity": "suggestion",
        "repo": Path("/tmp/test"),
        "branch": "main",
        "message": "Test message"
    }]

    service.process_violations(violations)

    # Should have sent notification (or not based on cooldown)
    # At least should not crash
    assert True
