"""
Claude Branch Detector - Detect and track Claude Code branches.

Monitors remote repository for branches created by Claude Code on the web.
Uses flexible pattern matching since exact naming convention not in official docs.
"""

import re
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BranchInfo:
    """Information about a detected Claude branch"""
    name: str
    commit_hash: str
    commit_date: datetime
    is_new: bool = False  # True if newly detected this check


class ClaudeBranchDetector:
    """
    Detects Claude Code branches on remote repository.

    Features:
    - Flexible pattern matching (claude/*, ai/*, etc.)
    - Tracks known branches to identify new ones
    - Detects updates to existing branches
    - Sorts by creation date to find latest
    """

    def __init__(self, config: dict):
        """
        Initialize detector with configuration.

        Args:
            config: Configuration dict with 'sync.claude_branches.patterns'
        """
        self.config = config
        self.patterns = config.get('sync', {}).get('claude_branches', {}).get('patterns', [
            r'^claude/.*'
        ])
        self.known_branches: Set[str] = set()
        logger.info(f"Initialized with patterns: {self.patterns}")

    async def detect_new_branches(self, repo_path: Path) -> List[str]:
        """
        Detect newly created Claude branches.

        Args:
            repo_path: Path to git repository

        Returns:
            List of new branch names

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        try:
            # Fetch all remote branches
            await self._run_git(repo_path, ['fetch', '--all', '--prune'])

            # Get all remote branches
            remote_branches = await self._get_remote_branches(repo_path)

            # Filter for Claude branches
            claude_branches = [
                branch for branch in remote_branches
                if self._matches_claude_pattern(branch)
            ]

            # Find new branches
            new_branches = [
                branch for branch in claude_branches
                if branch not in self.known_branches
            ]

            # Update known branches
            self.known_branches.update(claude_branches)

            if new_branches:
                logger.info(f"Detected {len(new_branches)} new Claude branch(es): {new_branches}")
            else:
                logger.debug("No new Claude branches detected")

            return new_branches

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error detecting branches: {e}")
            return []

    async def detect_branch_updates(self, branch_name: str, repo_path: Path) -> bool:
        """
        Check if a Claude branch has new commits.

        Args:
            branch_name: Name of branch to check
            repo_path: Path to git repository

        Returns:
            True if remote has new commits, False otherwise
        """
        try:
            # Fetch specific branch
            await self._run_git(repo_path, ['fetch', 'origin', branch_name])

            # Get local and remote commit hashes
            local_hash = await self._get_commit_hash(repo_path, branch_name)
            remote_hash = await self._get_commit_hash(repo_path, f'origin/{branch_name}')

            has_updates = local_hash != remote_hash

            if has_updates:
                logger.info(f"Branch '{branch_name}' has updates")
                logger.debug(f"Local: {local_hash}, Remote: {remote_hash}")

            return has_updates

        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking branch updates: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking updates: {e}")
            return False

    def get_latest_claude_branch(self, repo_path: Path) -> Optional[str]:
        """
        Get the most recently created Claude branch.

        Uses commit date to determine latest.

        Args:
            repo_path: Path to git repository

        Returns:
            Branch name or None if no Claude branches exist
        """
        try:
            claude_branches = self._get_claude_branches_sync(repo_path)
            if not claude_branches:
                return None

            # Get commit dates for all branches
            branches_with_dates = []
            for branch in claude_branches:
                try:
                    commit_date = self._get_branch_commit_date_sync(repo_path, branch)
                    branches_with_dates.append((branch, commit_date))
                except Exception as e:
                    logger.warning(f"Could not get date for branch {branch}: {e}")
                    continue

            if not branches_with_dates:
                return None

            # Sort by date (most recent first)
            branches_with_dates.sort(key=lambda x: x[1], reverse=True)
            latest = branches_with_dates[0][0]

            logger.info(f"Latest Claude branch: {latest}")
            return latest

        except Exception as e:
            logger.error(f"Error finding latest branch: {e}")
            return None

    def _matches_claude_pattern(self, branch_name: str) -> bool:
        """
        Check if branch name matches any Claude pattern.

        Args:
            branch_name: Branch name to check

        Returns:
            True if matches any pattern, False otherwise
        """
        # Remove 'origin/' prefix if present
        clean_name = branch_name.replace('origin/', '')

        return any(
            re.match(pattern, clean_name)
            for pattern in self.patterns
        )

    def extract_session_id(self, branch_name: str) -> Optional[str]:
        """
        Extract session ID from Claude branch name.

        Example: 'claude/add-feature-xyz123' → 'xyz123'

        Args:
            branch_name: Branch name

        Returns:
            Session ID or None if not found
        """
        # Pattern: claude/{feature-name}-{sessionId}
        # Session ID is typically alphanumeric after last hyphen
        match = re.match(r'claude/.*-([A-Za-z0-9]+)$', branch_name)
        return match.group(1) if match else None

    async def _get_remote_branches(self, repo_path: Path) -> List[str]:
        """Get list of remote branch names"""
        result = await self._run_git(
            repo_path,
            ['branch', '-r', '--format=%(refname:short)']
        )

        branches = [
            line.strip().replace('origin/', '')
            for line in result.stdout.split('\n')
            if line.strip() and 'origin/HEAD' not in line
        ]

        return branches

    def _get_claude_branches_sync(self, repo_path: Path) -> List[str]:
        """Get list of Claude branches (synchronous)"""
        try:
            result = subprocess.run(
                ['git', 'branch', '-r', '--format=%(refname:short)'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

            branches = [
                line.strip().replace('origin/', '')
                for line in result.stdout.split('\n')
                if line.strip() and 'origin/HEAD' not in line
            ]

            return [b for b in branches if self._matches_claude_pattern(b)]

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            return []

    async def _get_commit_hash(self, repo_path: Path, ref: str) -> Optional[str]:
        """Get commit hash for a ref"""
        try:
            result = await self._run_git(
                repo_path,
                ['rev-parse', ref]
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _get_branch_commit_date_sync(self, repo_path: Path, branch: str) -> datetime:
        """Get commit date for branch (synchronous)"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cI', f'origin/{branch}'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            date_str = result.stdout.strip()
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting commit date: {e}")
            # Return epoch if error
            return datetime.fromtimestamp(0)

    async def _run_git(self, repo_path: Path, args: List[str], timeout: int = 10):
        """
        Run git command asynchronously.

        Args:
            repo_path: Repository path
            args: Git command arguments
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess result

        Raises:
            subprocess.CalledProcessError: If command fails
            asyncio.TimeoutError: If command times out
        """
        import asyncio

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

            # Create result object similar to subprocess.run
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

    def get_all_known_branches(self) -> List[str]:
        """Get list of all known Claude branches"""
        return list(self.known_branches)

    def reset_known_branches(self):
        """Reset known branches (useful for testing)"""
        self.known_branches.clear()
        logger.info("Reset known branches")
