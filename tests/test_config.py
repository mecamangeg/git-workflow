"""Tests for configuration management"""
import pytest
import yaml
from pathlib import Path
from service.config import ConfigManager


def test_config_manager_loads_yaml(tmp_path):
    """Test that ConfigManager loads YAML correctly"""
    config_file = tmp_path / "test_config.yaml"
    test_config = {
        "rules": {
            "commit_to_main": {
                "severity": "critical",
                "enabled": True
            }
        },
        "monitoring": {
            "poll_interval": 60
        }
    }

    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)

    config = ConfigManager(str(config_file))

    assert config.get("rules.commit_to_main.severity") == "critical"
    assert config.get("rules.commit_to_main.enabled") is True
    assert config.get("monitoring.poll_interval") == 60


def test_config_manager_default_on_missing_file():
    """Test that ConfigManager returns defaults for missing file"""
    config = ConfigManager("/nonexistent/path/config.yaml")

    # Should return default config
    assert config.get("monitoring.poll_interval") == 30
    assert config.get("rules", {}) == {}


def test_config_manager_get_with_default():
    """Test that ConfigManager.get() returns default for missing keys"""
    config = ConfigManager("/nonexistent/path/config.yaml")

    assert config.get("nonexistent.key", "default_value") == "default_value"
    assert config.get("another.missing.key", 42) == 42
    assert config.get("missing.key") is None


def test_config_manager_nested_keys(tmp_path):
    """Test that nested key access works correctly"""
    config_file = tmp_path / "nested_config.yaml"
    test_config = {
        "level1": {
            "level2": {
                "level3": {
                    "value": "deep_value"
                }
            }
        }
    }

    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)

    config = ConfigManager(str(config_file))

    assert config.get("level1.level2.level3.value") == "deep_value"
    assert config.get("level1.level2.level3") == {"value": "deep_value"}
    assert config.get("level1.nonexistent", "default") == "default"
