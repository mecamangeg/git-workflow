"""
Branch Sync Manager - Manages synchronization of Claude branches to local environment.

Handles:
- Safe git checkout with stash management
- Pulling latest changes
- Tracking active branch state
- Conflict detection and handling
"""

import asyncio
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    branch_name: str
    message: str
    commit_count: int = 0
    had_stash: bool = False
    error: Optional[str] = None


class BranchSyncManager:
    """
    Manages syncing of Claude branches to local environment.

    Features:
    - Safe checkout with automatic stash
    - Pull with conflict detection
    - Track active branch
    - Comprehensive error handling
    """

    def __init__(self, config: dict):
        """
        Initialize sync manager.

        Args:
            config: Configuration dict
        """
        self.config = config
        self.active_branch: Optional[str] = None
        self.stash_before_checkout = config.get('sync', {}).get('branch_sync', {}).get('stash_before_checkout', True)
        self.auto_pop_stash = config.get('sync', {}).get('branch_sync', {}).get('auto_pop_stash', False)

    async def sync_new_branch(self, repo_path: Path, branch_name: str) -> SyncResult:
        """
        Sync newly created Claude branch.

        Steps:
        1. Stash uncommitted changes (if configured)
        2. Fetch branch from remote
        3. Checkout branch (create tracking if needed)
        4. Update active_branch
        5. Optionally pop stash

        Args:
            repo_path: Path to repository
            branch_name: Name of branch to sync

        Returns:
            SyncResult with operation details
        """
        logger.info(f"Syncing new branch: {branch_name} in {repo_path}")

        try:
            # Check for uncommitted changes
            had_stash = False
            if self.stash_before_checkout and await self._has_uncommitted_changes(repo_path):
                logger.info("Stashing uncommitted changes before checkout")
                await self._stash_changes(repo_path, f"Auto-stash before syncing {branch_name}")
                had_stash = True

            # Fetch branch
            logger.info(f"Fetching origin/{branch_name}")
            await self._run_git(repo_path, ['fetch', 'origin', branch_name])

            # Check if branch exists locally
            local_branches = await self._get_local_branches(repo_path)

            if branch_name in local_branches:
                # Branch exists, just checkout and pull
                logger.info(f"Branch exists locally, checking out")
                await self._run_git(repo_path, ['checkout', branch_name])
                await self._run_git(repo_path, ['pull', 'origin', branch_name])
            else:
                # Create new tracking branch
                logger.info(f"Creating new tracking branch")
                await self._run_git(
                    repo_path,
                    ['checkout', '-b', branch_name, f'origin/{branch_name}']
                )

            # Update active branch
            self.active_branch = branch_name

            # Get commit count info
            commit_count = await self._get_commit_count(repo_path, branch_name)

            # Pop stash if configured
            if had_stash and self.auto_pop_stash:
                logger.info("Popping stashed changes")
                try:
                    await self._run_git(repo_path, ['stash', 'pop'])
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Could not pop stash automatically: {e}")
                    # Don't fail the sync for stash pop issues

            logger.info(f"Successfully synced branch: {branch_name}")
            return SyncResult(
                success=True,
                branch_name=branch_name,
                message=f"Successfully synced '{branch_name}'",
                commit_count=commit_count,
                had_stash=had_stash
            )

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Failed to sync branch: {error_msg}")
            return SyncResult(
                success=False,
                branch_name=branch_name,
                message="Sync failed",
                error=error_msg
            )
        except Exception as e:
            logger.error(f"Unexpected error syncing branch: {e}")
            return SyncResult(
                success=False,
                branch_name=branch_name,
                message="Unexpected error",
                error=str(e)
            )

    async def sync_branch_update(self, repo_path: Path, branch_name: str) -> SyncResult:
        """
        Sync updates to existing Claude branch.

        Steps:
        1. Ensure on correct branch
        2. Pull latest changes
        3. Handle conflicts

        Args:
            repo_path: Path to repository
            branch_name: Name of branch

        Returns:
            SyncResult with operation details
        """
        logger.info(f"Syncing branch update: {branch_name}")

        try:
            # Ensure we're on the correct branch
            current_branch = await self._get_current_branch(repo_path)
            if current_branch != branch_name:
                logger.info(f"Switching from {current_branch} to {branch_name}")
                await self._run_git(repo_path, ['checkout', branch_name])

            # Pull latest changes
            result = await self._run_git(repo_path, ['pull', 'origin', branch_name])

            # Check if there were updates
            if 'Already up to date' in result.stdout:
                logger.info("Branch already up to date")
                commit_count = 0
            else:
                commit_count = await self._get_commit_count(repo_path, branch_name)
                logger.info(f"Pulled {commit_count} new commit(s)")

            return SyncResult(
                success=True,
                branch_name=branch_name,
                message=f"Updated '{branch_name}'",
                commit_count=commit_count
            )

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"Failed to update branch: {error_msg}")

            # Check if it's a merge conflict
            if 'CONFLICT' in error_msg or 'conflict' in error_msg.lower():
                logger.warning("Merge conflict detected")
                return SyncResult(
                    success=False,
                    branch_name=branch_name,
                    message="Merge conflict detected",
                    error="conflict"
                )

            return SyncResult(
                success=False,
                branch_name=branch_name,
                message="Update failed",
                error=error_msg
            )
        except Exception as e:
            logger.error(f"Unexpected error updating branch: {e}")
            return SyncResult(
                success=False,
                branch_name=branch_name,
                message="Unexpected error",
                error=str(e)
            )

    async def switch_active_branch(self, repo_path: Path, branch_name: str) -> SyncResult:
        """
        Manually switch to a different Claude branch.

        Args:
            repo_path: Path to repository
            branch_name: Branch to switch to

        Returns:
            SyncResult
        """
        logger.info(f"Switching active branch to: {branch_name}")

        if not branch_name.startswith('claude/'):
            logger.warning(f"Branch '{branch_name}' does not match Claude pattern")
            return SyncResult(
                success=False,
                branch_name=branch_name,
                message="Only Claude branches can be set as active",
                error="invalid_branch"
            )

        # Use sync_new_branch logic
        return await self.sync_new_branch(repo_path, branch_name)

    def get_active_branch(self) -> Optional[str]:
        """Get currently active Claude branch"""
        return self.active_branch

    async def _has_uncommitted_changes(self, repo_path: Path) -> bool:
        """Check if there are uncommitted changes"""
        try:
            result = await self._run_git(repo_path, ['status', '--porcelain'])
            has_changes = bool(result.stdout.strip())
            if has_changes:
                logger.debug(f"Uncommitted changes detected:\n{result.stdout}")
            return has_changes
        except Exception as e:
            logger.error(f"Error checking for uncommitted changes: {e}")
            return False

    async def _stash_changes(self, repo_path: Path, message: str):
        """Stash uncommitted changes"""
        await self._run_git(repo_path, ['stash', 'push', '-m', message])
        logger.info(f"Stashed changes: {message}")

    async def _get_local_branches(self, repo_path: Path) -> List[str]:
        """Get list of local branch names"""
        result = await self._run_git(
            repo_path,
            ['branch', '--format=%(refname:short)']
        )

        branches = [
            line.strip()
            for line in result.stdout.split('\n')
            if line.strip()
        ]

        return branches

    async def _get_current_branch(self, repo_path: Path) -> Optional[str]:
        """Get name of currently checked out branch"""
        try:
            result = await self._run_git(repo_path, ['branch', '--show-current'])
            return result.stdout.strip() or None
        except Exception as e:
            logger.error(f"Error getting current branch: {e}")
            return None

    async def _get_commit_count(self, repo_path: Path, branch_name: str) -> int:
        """Get number of commits in branch"""
        try:
            result = await self._run_git(
                repo_path,
                ['rev-list', '--count', branch_name]
            )
            return int(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not get commit count: {e}")
            return 0

    async def _run_git(self, repo_path: Path, args: List[str], timeout: int = 30):
        """
        Run git command asynchronously.

        Args:
            repo_path: Repository path
            args: Git command arguments
            timeout: Command timeout in seconds

        Returns:
            Result object with stdout/stderr

        Raises:
            subprocess.CalledProcessError: If command fails
            asyncio.TimeoutError: If command times out
        """
        cmd = ['git'] + args
        logger.debug(f"Running: {' '.join(cmd)} in {repo_path}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Git command failed: {error_msg}")
                raise subprocess.CalledProcessError(
                    process.returncode,
                    cmd,
                    stdout,
                    stderr
                )

            # Create result object
            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout.decode().strip()
                    self.stderr = stderr.decode().strip()

            return Result(process.returncode, stdout, stderr)

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.error(f"Git command timed out after {timeout}s")
            raise

    async def get_branch_info(self, repo_path: Path, branch_name: str) -> dict:
        """
        Get detailed information about a branch.

        Returns:
            Dict with branch info
        """
        try:
            # Get commit hash
            hash_result = await self._run_git(
                repo_path,
                ['rev-parse', branch_name]
            )

            # Get commit message
            msg_result = await self._run_git(
                repo_path,
                ['log', '-1', '--format=%s', branch_name]
            )

            # Get commit date
            date_result = await self._run_git(
                repo_path,
                ['log', '-1', '--format=%cI', branch_name]
            )

            # Get commit count
            count = await self._get_commit_count(repo_path, branch_name)

            return {
                'name': branch_name,
                'hash': hash_result.stdout.strip(),
                'message': msg_result.stdout.strip(),
                'date': date_result.stdout.strip(),
                'commit_count': count,
                'is_active': branch_name == self.active_branch
            }

        except Exception as e:
            logger.error(f"Error getting branch info: {e}")
            return {
                'name': branch_name,
                'error': str(e)
            }
