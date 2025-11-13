"""
Sync Daemon - Main orchestration service for Claude branch synchronization.

Coordinates:
- Claude branch detection (via ClaudeBranchDetector)
- Branch syncing (via BranchSyncManager)
- Notifications (via NotificationQueue)
- Polling loop for continuous monitoring
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from .claude_branch_detector import ClaudeBranchDetector
from .branch_sync_manager import BranchSyncManager
from .notification_queue import NotificationQueue, NotificationBuilder
from .notification_storage import NotificationStorage

logger = logging.getLogger(__name__)


class SyncDaemon:
    """
    Background daemon for Claude Code branch synchronization.

    Features:
    - Polling-based detection (webhook support future)
    - Multi-repository monitoring
    - Automatic sync on detection
    - Notification integration
    - Graceful shutdown
    """

    def __init__(self, config_path: Path, db_path: Path):
        """
        Initialize sync daemon.

        Args:
            config_path: Path to sync.yaml configuration
            db_path: Path to SQLite database
        """
        self.config_path = config_path
        self.db_path = db_path
        self.running = False
        self.tasks: List[asyncio.Task] = []

        # Load configuration
        self.config = self._load_config()

        # Initialize components
        self.storage = NotificationStorage(db_path)
        self.notification_queue = NotificationQueue(self.storage)
        self.branch_detector = ClaudeBranchDetector(self.config)
        self.branch_sync_manager = BranchSyncManager(self.config)

        # Repository managers (one per repository)
        self.repo_managers: Dict[str, BranchSyncManager] = {}

        logger.info("Sync daemon initialized")

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Return minimal default config
            return {
                'sync': {
                    'mode': 'polling',
                    'polling': {'interval': 30},
                    'repositories': []
                }
            }

    async def start(self):
        """Start sync daemon"""
        if self.running:
            logger.warning("Daemon already running")
            return

        self.running = True
        logger.info("Starting sync daemon")

        mode = self.config.get('sync', {}).get('mode', 'polling')
        logger.info(f"Sync mode: {mode}")

        # Start polling loop
        if mode in ['polling', 'hybrid']:
            polling_task = asyncio.create_task(self._polling_loop())
            self.tasks.append(polling_task)

        # TODO: Start webhook receiver if mode is 'webhook' or 'hybrid'
        # This will be implemented in Phase 5

        logger.info("Sync daemon started successfully")

        # Keep running until stopped
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Sync daemon tasks cancelled")

    async def stop(self):
        """Stop sync daemon gracefully"""
        if not self.running:
            return

        logger.info("Stopping sync daemon")
        self.running = False

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        logger.info("Sync daemon stopped")

    async def _polling_loop(self):
        """Main polling loop for detecting Claude branches"""
        interval = self.config.get('sync', {}).get('polling', {}).get('interval', 30)
        active_branch_interval = self.config.get('sync', {}).get('polling', {}).get('active_branch_interval', 10)

        logger.info(f"Starting polling loop (interval: {interval}s, active check: {active_branch_interval}s)")

        last_active_check = datetime.now()

        while self.running:
            try:
                # Get repositories to monitor
                repos = self.config.get('sync', {}).get('repositories', [])

                if not repos:
                    logger.warning("No repositories configured for monitoring")
                    await asyncio.sleep(interval)
                    continue

                # Check each repository
                for repo_config in repos:
                    if not self.running:
                        break

                    await self._check_repository(repo_config)

                # Check active branches more frequently
                elapsed = (datetime.now() - last_active_check).total_seconds()
                if elapsed >= active_branch_interval:
                    await self._check_active_branches(repos)
                    last_active_check = datetime.now()

                # Sleep until next check
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Polling loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                # Continue running despite errors
                await asyncio.sleep(interval)

    async def _check_repository(self, repo_config: dict):
        """
        Check single repository for Claude branch changes.

        Args:
            repo_config: Repository configuration dict
        """
        repo_path = Path(repo_config['path']).expanduser()

        if not repo_path.exists():
            logger.warning(f"Repository path does not exist: {repo_path}")
            return

        if not (repo_path / '.git').exists():
            logger.warning(f"Not a git repository: {repo_path}")
            return

        # Check for active teleport/CLI session before syncing
        if await self._is_cli_or_teleport_active(repo_path):
            logger.info(f"Skipping {repo_path.name} - CLI/teleport session detected")
            return

        logger.debug(f"Checking repository: {repo_path}")

        try:
            # Detect new branches
            new_branches = await self.branch_detector.detect_new_branches(repo_path)

            if new_branches:
                logger.info(f"Found {len(new_branches)} new Claude branch(es) in {repo_path}")

                # Sync the latest branch (or all if configured)
                sync_latest_only = self.config.get('sync', {}).get('claude_branches', {}).get('sync_latest_only', True)

                if sync_latest_only:
                    latest = new_branches[0]  # Already sorted by detector
                    await self._sync_branch(repo_path, latest, is_new=True)
                else:
                    # Sync all new branches
                    for branch in new_branches:
                        await self._sync_branch(repo_path, branch, is_new=True)

        except Exception as e:
            logger.error(f"Error checking repository {repo_path}: {e}", exc_info=True)

    async def _check_active_branches(self, repos: List[dict]):
        """Check active branches for updates"""
        for repo_config in repos:
            repo_path = Path(repo_config['path']).expanduser()

            # Get manager for this repo
            manager = self.repo_managers.get(str(repo_path))
            if not manager:
                continue

            active_branch = manager.get_active_branch()
            if not active_branch:
                continue

            logger.debug(f"Checking active branch '{active_branch}' for updates")

            try:
                has_updates = await self.branch_detector.detect_branch_updates(
                    active_branch,
                    repo_path
                )

                if has_updates:
                    logger.info(f"Active branch '{active_branch}' has updates")
                    await self._sync_branch(repo_path, active_branch, is_new=False)

            except Exception as e:
                logger.error(f"Error checking active branch: {e}")

    async def _sync_branch(self, repo_path: Path, branch_name: str, is_new: bool):
        """
        Sync a Claude branch.

        Args:
            repo_path: Path to repository
            branch_name: Branch to sync
            is_new: True if newly detected, False if update
        """
        logger.info(f"Syncing branch: {branch_name} (new={is_new})")

        # Get or create manager for this repo
        repo_key = str(repo_path)
        if repo_key not in self.repo_managers:
            self.repo_managers[repo_key] = BranchSyncManager(self.config)

        manager = self.repo_managers[repo_key]

        try:
            # Perform sync
            if is_new:
                result = await manager.sync_new_branch(repo_path, branch_name)
            else:
                result = await manager.sync_branch_update(repo_path, branch_name)

            # Handle result
            if result.success:
                logger.info(f"Successfully synced: {result.message}")

                # Send notification
                notif_data = NotificationBuilder.branch_sync_success(
                    branch_name=branch_name,
                    repo_path=str(repo_path),
                    commit_count=result.commit_count
                )

                await self.notification_queue.add_notification(**notif_data)

                # TODO: Run tests if configured (Phase 3)
                # TODO: Start dev server if configured (Phase 4)

            else:
                logger.error(f"Sync failed: {result.error}")

                # Send error notification
                notif_data = NotificationBuilder.sync_error(
                    branch_name=branch_name,
                    repo_path=str(repo_path),
                    error_message=result.error or "Unknown error"
                )

                await self.notification_queue.add_notification(**notif_data)

        except Exception as e:
            logger.error(f"Unexpected error syncing branch: {e}", exc_info=True)

            # Send error notification
            notif_data = NotificationBuilder.sync_error(
                branch_name=branch_name,
                repo_path=str(repo_path),
                error_message=str(e)
            )

            await self.notification_queue.add_notification(**notif_data)

    async def _is_cli_or_teleport_active(self, repo_path: Path) -> bool:
        """
        Check if user is working in CLI or has an active teleport session.

        Claude Teleport: When user runs 'claude --teleport session_XXX', the entire
        conversation from Claude Code web is teleported to the local terminal.
        Claude continues working in the same branch locally.

        Detects:
        - Active 'claude' CLI process in this directory (teleport session)
        - Session ID in branch name + claude process anywhere
        - Uncommitted changes (user or Claude editing locally)
        - Git lock file (git command running)

        Returns:
            True if CLI/teleport active, False if safe to sync
        """
        import subprocess
        import time
        import os

        try:
            # Method 1: Check for 'claude' CLI process in this directory
            if self._has_claude_process(repo_path):
                logger.info(f"Claude CLI process detected in {repo_path.name} - teleport session active")
                return True

            # Method 2: Check for git lock file (git command in progress)
            if (repo_path / '.git/index.lock').exists():
                logger.debug(f"Git lock file found in {repo_path.name}")
                return True

            # Method 3: Check current branch for session ID
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            current_branch = result.stdout.strip()

            # If branch contains session ID, check for activity
            if current_branch and 'session_' in current_branch:
                # Check for uncommitted changes (Claude or user working)
                status_result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if status_result.stdout.strip():
                    # Has uncommitted changes on a session branch
                    logger.info(f"Teleport branch with uncommitted changes: {current_branch}")
                    return True

                # Check for recent git activity (file modifications)
                index_file = repo_path / '.git/index'
                if index_file.exists():
                    mtime = index_file.stat().st_mtime
                    age = time.time() - mtime
                    if age < 300:  # 5 minutes
                        logger.info(f"Recent activity on teleport branch {current_branch} ({age:.0f}s ago)")
                        return True

            # Method 4: Check for any uncommitted changes (non-session branch)
            elif current_branch:
                status_result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if status_result.stdout.strip():
                    # Has uncommitted changes, check if recent
                    index_file = repo_path / '.git/index'
                    if index_file.exists():
                        mtime = index_file.stat().st_mtime
                        age = time.time() - mtime
                        if age < 300:  # 5 minutes
                            logger.debug(f"Recent uncommitted changes in {repo_path.name} ({age:.0f}s old)")
                            return True

            return False

        except subprocess.TimeoutError:
            logger.warning(f"Git command timeout checking {repo_path.name}")
            # Assume active to be safe
            return True
        except Exception as e:
            logger.error(f"Error checking CLI/teleport status: {e}")
            # Assume active to be safe
            return True

    def _has_claude_process(self, repo_path: Path) -> bool:
        """
        Check if there's an active 'claude' CLI process in this directory.

        Detects: claude --teleport, claude chat, or any claude CLI command
        running in this repository directory.
        """
        import subprocess
        import platform

        try:
            repo_path_str = str(repo_path)

            # Different commands for different OS
            if platform.system() == 'Windows':
                # Windows: Use tasklist and wmic to find processes with working directory
                # Check for claude.exe or claude processes
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq claude.exe', '/FO', 'CSV'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )

                if 'claude.exe' in result.stdout.lower():
                    # Claude process exists, now check if it's in this directory
                    # This is a simplification - on Windows it's harder to get CWD
                    # We'll check for the process and trust session ID detection
                    logger.debug(f"Claude.exe process found (Windows)")
                    return False  # Let session ID detection handle it

            else:
                # Linux/macOS: Use ps to find processes
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )

                # Look for 'claude' command with this directory in the command line
                for line in result.stdout.split('\n'):
                    if 'claude' in line.lower():
                        # Check if this directory is mentioned
                        if repo_path_str in line or repo_path.name in line:
                            logger.debug(f"Claude process found for {repo_path.name}")
                            return True

                        # Check for 'claude --teleport' anywhere (might affect this repo)
                        if '--teleport' in line or 'teleport' in line:
                            logger.debug("Claude teleport process found")
                            # Let session ID detection verify if it's this repo
                            return False

            return False

        except subprocess.TimeoutError:
            logger.warning("Process check timeout")
            return False
        except Exception as e:
            logger.debug(f"Error checking for claude process: {e}")
            return False

    def get_status(self) -> dict:
        """Get daemon status"""
        return {
            'running': self.running,
            'mode': self.config.get('sync', {}).get('mode', 'polling'),
            'repositories': len(self.config.get('sync', {}).get('repositories', [])),
            'active_branches': {
                repo: manager.get_active_branch()
                for repo, manager in self.repo_managers.items()
            },
            'queue_size': self.notification_queue.get_queue_size(),
            'unread_notifications': self.notification_queue.get_unread_count()
        }


async def main():
    """Main entry point for sync daemon"""
    import argparse

    parser = argparse.ArgumentParser(description='Git Workflow Guardian - Sync Daemon')
    parser.add_argument(
        '--config',
        type=Path,
        default=Path.home() / '.git-workflow-guardian' / 'sync.yaml',
        help='Path to sync.yaml configuration'
    )
    parser.add_argument(
        '--db',
        type=Path,
        default=Path.home() / '.git-workflow-guardian' / 'state.db',
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create daemon
    daemon = SyncDaemon(args.config, args.db)

    # Handle shutdown signals
    import signal

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(daemon.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start daemon
    try:
        await daemon.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await daemon.stop()


if __name__ == '__main__':
    asyncio.run(main())
