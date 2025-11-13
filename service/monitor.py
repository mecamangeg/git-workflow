"""
Git Workflow Guardian - Background Monitoring Service
Proactive workflow compliance monitoring
"""
import time
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta

from .detector import ViolationDetector
from .notifier import ToastNotifier
from .state import StateManager
from .config import ConfigManager

logger = logging.getLogger(__name__)


class MonitorService:
    """Background service for monitoring git workflow compliance"""

    def __init__(self, config_path: str = None):
        self.config = ConfigManager(config_path)
        self.detector = ViolationDetector(self.config)
        self.notifier = ToastNotifier(self.config)
        self.state = StateManager()

        self.is_running = False
        self.poll_interval = self.config.get("monitoring.poll_interval", 30)

    def discover_repositories(self) -> List[Path]:
        """Discover git repositories to monitor"""
        repos = []

        # Auto-discovery
        if self.config.get("monitoring.repos.auto_discover"):
            search_paths = self.config.get("monitoring.repos.search_paths", [])
            for search_path in search_paths:
                # Expand user home directory
                expanded_path = Path(search_path.replace("{username}", Path.home().name))
                if expanded_path.exists():
                    repos.extend(self._scan_for_repos(expanded_path))

        # Manual repos
        manual_repos = self.config.get("monitoring.repos.manual_repos", [])
        repos.extend([Path(r) for r in manual_repos if Path(r).exists()])

        # Deduplicate
        repos = list(set(repos))

        logger.info(f"Discovered {len(repos)} repositories")
        return repos

    def _scan_for_repos(self, search_path: Path, max_depth: int = 3) -> List[Path]:
        """Recursively scan for .git directories"""
        repos = []

        if not search_path.exists():
            return repos

        try:
            for item in search_path.rglob(".git"):
                if item.is_dir():
                    repo_path = item.parent
                    repos.append(repo_path)
                    logger.debug(f"Found repository: {repo_path}")
        except (PermissionError, OSError) as e:
            logger.debug(f"Skipping {search_path}: {e}")

        return repos

    def check_repository(self, repo_path: Path) -> List[Dict]:
        """Check single repository for violations"""
        violations = []

        try:
            # Get current state
            current_branch = self.detector.get_current_branch(repo_path)
            if not current_branch:
                return violations

            # Check various rules
            # 1. Main sync status
            if current_branch in ["main", "master"]:
                if self.detector.is_behind_remote(repo_path, current_branch):
                    violations.append({
                        "rule": "pull_before_work",
                        "severity": "suggestion",
                        "repo": repo_path,
                        "branch": current_branch,
                        "message": f"{current_branch} is behind remote"
                    })

            # 2. Stale merged branches
            merged_branches = self.detector.get_merged_branches(repo_path)
            for branch in merged_branches:
                if branch not in ["main", "master"] and not branch.startswith("*"):
                    violations.append({
                        "rule": "delete_merged_branch",
                        "severity": "suggestion",
                        "repo": repo_path,
                        "branch": branch,
                        "message": f"Branch {branch} has been merged"
                    })

            # 3. Local dev server check (before commits)
            if self.detector.has_uncommitted_changes(repo_path):
                if self.config.get("rules.test_locally.enabled"):
                    if not self.detector.check_local_server():
                        violations.append({
                            "rule": "test_locally",
                            "severity": "suggestion",
                            "repo": repo_path,
                            "branch": current_branch,
                            "message": "Local dev server not detected"
                        })

            # 4. Branch naming compliance
            if self.config.get("rules.branch_naming.enabled"):
                if not self.detector.is_branch_name_valid(current_branch):
                    violations.append({
                        "rule": "branch_naming",
                        "severity": "warning",
                        "repo": repo_path,
                        "branch": current_branch,
                        "message": f"Branch name doesn't follow convention: {current_branch}"
                    })

        except Exception as e:
            logger.error(f"Error checking repository {repo_path}: {e}")

        return violations

    def process_violations(self, violations: List[Dict]):
        """Process violations and send notifications"""

        for violation in violations:
            # Check if already notified recently
            if self._was_notified_recently(violation):
                continue

            # Check if overridden
            if self.state.is_overridden(violation["rule"], violation.get("branch")):
                continue

            # Send notification
            self.notifier.show_toast(
                rule_name=violation["rule"],
                severity=violation["severity"],
                message=violation["message"],
                repo_path=violation["repo"],
                branch=violation.get("branch")
            )

            # Log violation
            self.state.log_violation(
                repo_path=violation["repo"],
                rule_name=violation["rule"],
                severity=violation["severity"],
                branch_name=violation.get("branch")
            )

    def _was_notified_recently(self, violation: Dict) -> bool:
        """Check if same violation was notified within cooldown period"""
        last_notification = self.state.get_last_notification(
            rule_name=violation["rule"],
            repo_path=violation["repo"]
        )

        if not last_notification:
            return False

        cooldown = timedelta(minutes=5)  # 5-minute cooldown
        return (datetime.now() - last_notification) < cooldown

    def run(self):
        """Main monitoring loop"""
        self.is_running = True

        logger.info("Git Workflow Guardian monitoring service started")
        logger.info(f"Poll interval: {self.poll_interval}s")

        # Discover repositories
        repos = self.discover_repositories()

        if not repos:
            logger.warning("No repositories found to monitor")

        while self.is_running:
            try:
                # Check each repository
                all_violations = []
                for repo in repos:
                    violations = self.check_repository(repo)
                    all_violations.extend(violations)

                # Process violations
                if all_violations:
                    logger.info(f"Found {len(all_violations)} violations")
                    self.process_violations(all_violations)

                # Sleep until next check
                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.is_running = False
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)

        logger.info("Git Workflow Guardian monitoring service stopped")

    def stop(self):
        """Stop monitoring service"""
        self.is_running = False


def main():
    """Entry point for background service"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    service = MonitorService()
    service.run()


if __name__ == "__main__":
    main()
