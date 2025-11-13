"""
Git Workflow Guardian - Configuration Management
Loads and manages YAML configuration
"""
import yaml
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Manages configuration loading and access"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to config/rules.yaml
            config_path = Path(__file__).parent.parent / "config" / "rules.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            # Return default configuration
            return self._default_config()

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _default_config(self) -> dict:
        """Return default configuration"""
        return {
            "rules": {},
            "notifications": {},
            "overrides": {},
            "monitoring": {
                "poll_interval": 30
            }
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Example:
            config.get("rules.commit_to_main.severity") -> "critical"
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()
