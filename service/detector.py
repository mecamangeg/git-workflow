"""
Git Workflow Guardian - Violation Detection
Logic for detecting workflow violations
"""
import subprocess
import re
import requests
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class ViolationDetector:
    """Detects git workflow violations"""

    def __init__(self, config):
        self.config = config

    def get_current_branch(self, repo_path: Path) -> Optional[str]:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Could not get current branch for {repo_path}: {e}")
            return None

    def is_behind_remote(self, repo_path: Path, branch: str) -> bool:
        """Check if local branch is behind remote"""
        try:
            # Fetch quietly
            subprocess.run(
                ["git", "fetch", "origin", branch, "--quiet"],
                cwd=repo_path,
                capture_output=True,
                check=True,
                timeout=10
            )

            # Compare local and remote
            local = subprocess.run(
                ["git", "rev-parse", branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            ).stdout.strip()

            remote = subprocess.run(
                ["git", "rev-parse", f"origin/{branch}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            ).stdout.strip()

            return local != remote

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Could not check remote status for {repo_path}: {e}")
            return False

    def get_merged_branches(self, repo_path: Path) -> List[str]:
        """Get list of merged branches (except main/master)"""
        try:
            result = subprocess.run(
                ["git", "branch", "--merged"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            branches = [
                b.strip().replace("* ", "")
                for b in result.stdout.split("\n")
                if b.strip() and not b.strip().startswith("*")
            ]

            # Filter out main/master
            return [b for b in branches if b not in ["main", "master"]]

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Could not get merged branches for {repo_path}: {e}")
            return []

    def has_uncommitted_changes(self, repo_path: Path) -> bool:
        """Check if there are uncommitted changes"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            return bool(result.stdout.strip())

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.debug(f"Could not check git status for {repo_path}: {e}")
            return False

    def check_local_server(self) -> bool:
        """Check if local dev server is running"""
        url = self.config.get("rules.test_locally.check_url", "http://localhost:3011")

        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def is_branch_name_valid(self, branch_name: str) -> bool:
        """Validate branch name against pattern"""
        pattern = self.config.get("rules.branch_naming.pattern")

        if not pattern:
            return True  # No validation if pattern not set

        # Skip validation for protected branches
        if branch_name in ["main", "master"]:
            return True

        return bool(re.match(pattern, branch_name))
