"""
PR Creator - GitHub Pull Request creation utility.

Uses GitHub CLI (gh) to create pull requests from command line.
Provides interactive and automated PR creation workflows.
"""

import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PRResult:
    """Result of PR creation"""
    success: bool
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    error: Optional[str] = None
    message: str = ""


class PRCreator:
    """
    GitHub Pull Request creator using gh CLI.

    Requires gh CLI to be installed and authenticated.
    Falls back to opening browser for manual PR creation.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize PR creator.

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.has_gh_cli = self._check_gh_cli()

    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is installed and authenticated"""
        if not shutil.which('gh'):
            logger.warning("GitHub CLI (gh) not found in PATH")
            return False

        try:
            # Check if authenticated
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("GitHub CLI is installed and authenticated")
                return True
            else:
                logger.warning("GitHub CLI not authenticated")
                return False
        except Exception as e:
            logger.warning(f"Error checking gh CLI: {e}")
            return False

    def create_pr(
        self,
        repo_path: Path,
        branch_name: str,
        base_branch: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        draft: bool = False,
        interactive: bool = False
    ) -> PRResult:
        """
        Create pull request for branch.

        Args:
            repo_path: Path to repository
            branch_name: Source branch name
            base_branch: Target branch (default: main/master)
            title: PR title (auto-generated if None)
            body: PR body/description
            draft: Create as draft PR
            interactive: Use interactive mode (open editor)

        Returns:
            PRResult with PR URL and metadata
        """
        if not self.has_gh_cli:
            return self._fallback_browser_pr(repo_path, branch_name)

        logger.info(f"Creating PR for {branch_name} in {repo_path}")

        try:
            # Build gh pr create command
            cmd = ['gh', 'pr', 'create']

            if interactive:
                # Interactive mode - opens editor
                cmd.append('--web')
            else:
                # Automated mode
                if base_branch:
                    cmd.extend(['--base', base_branch])

                if title:
                    cmd.extend(['--title', title])
                else:
                    # Auto-generate title from branch name
                    auto_title = self._generate_title(branch_name)
                    cmd.extend(['--title', auto_title])

                if body:
                    cmd.extend(['--body', body])
                else:
                    # Auto-generate body
                    auto_body = self._generate_body(repo_path, branch_name)
                    cmd.extend(['--body', auto_body])

                if draft:
                    cmd.append('--draft')

            # Execute command
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Extract PR URL from output
                pr_url = result.stdout.strip().split('\n')[-1]

                # Extract PR number
                pr_number = None
                if '/pull/' in pr_url:
                    try:
                        pr_number = int(pr_url.split('/pull/')[-1])
                    except ValueError:
                        pass

                logger.info(f"PR created successfully: {pr_url}")

                return PRResult(
                    success=True,
                    pr_url=pr_url,
                    pr_number=pr_number,
                    message=f"Pull request created: {pr_url}"
                )
            else:
                error = result.stderr.strip()
                logger.error(f"Failed to create PR: {error}")

                # Check if PR already exists
                if 'already exists' in error.lower():
                    # Try to get existing PR URL
                    existing_pr = self._get_existing_pr(repo_path, branch_name)
                    if existing_pr:
                        return PRResult(
                            success=True,
                            pr_url=existing_pr,
                            message=f"Pull request already exists: {existing_pr}"
                        )

                return PRResult(
                    success=False,
                    error=error,
                    message=f"Failed to create PR: {error}"
                )

        except subprocess.TimeoutExpired:
            logger.error("PR creation timed out")
            return PRResult(
                success=False,
                error="Timeout",
                message="PR creation timed out"
            )
        except Exception as e:
            logger.error(f"Error creating PR: {e}", exc_info=True)
            return PRResult(
                success=False,
                error=str(e),
                message=f"Error creating PR: {e}"
            )

    def _fallback_browser_pr(self, repo_path: Path, branch_name: str) -> PRResult:
        """Fallback to opening browser for manual PR creation"""
        logger.info("Falling back to browser for PR creation")

        try:
            # Get remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                remote_url = result.stdout.strip()

                # Convert to GitHub PR URL
                # git@github.com:user/repo.git → https://github.com/user/repo/compare/branch
                # https://github.com/user/repo.git → https://github.com/user/repo/compare/branch

                if remote_url.startswith('git@github.com:'):
                    repo_path_str = remote_url.replace('git@github.com:', '').replace('.git', '')
                    pr_url = f"https://github.com/{repo_path_str}/compare/{branch_name}?expand=1"
                elif 'github.com' in remote_url:
                    repo_path_str = remote_url.split('github.com/')[-1].replace('.git', '')
                    pr_url = f"https://github.com/{repo_path_str}/compare/{branch_name}?expand=1"
                else:
                    return PRResult(
                        success=False,
                        error="Not a GitHub repository",
                        message="Repository is not hosted on GitHub"
                    )

                # Open in browser
                import webbrowser
                webbrowser.open(pr_url)

                return PRResult(
                    success=True,
                    pr_url=pr_url,
                    message="Opened browser for PR creation"
                )

        except Exception as e:
            logger.error(f"Fallback PR creation failed: {e}")
            return PRResult(
                success=False,
                error=str(e),
                message="Failed to open PR creation page"
            )

    def _get_existing_pr(self, repo_path: Path, branch_name: str) -> Optional[str]:
        """Get URL of existing PR for branch"""
        try:
            result = subprocess.run(
                ['gh', 'pr', 'view', branch_name, '--json', 'url', '--jq', '.url'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception as e:
            logger.debug(f"Error getting existing PR: {e}")

        return None

    def _generate_title(self, branch_name: str) -> str:
        """Generate PR title from branch name"""
        # Remove common prefixes
        title = branch_name
        for prefix in ['claude/', 'feature/', 'fix/', 'ai/', 'assistant/']:
            if title.startswith(prefix):
                title = title[len(prefix):]

        # Convert kebab-case or snake_case to Title Case
        title = title.replace('-', ' ').replace('_', ' ')
        title = ' '.join(word.capitalize() for word in title.split())

        # Remove session ID if present
        if 'session' in title.lower():
            parts = title.split()
            title = ' '.join(p for p in parts if not p.lower().startswith('session'))

        return title.strip() or "Update from Claude Code"

    def _generate_body(self, repo_path: Path, branch_name: str) -> str:
        """Generate PR body with commit summary"""
        try:
            # Get commit messages
            result = subprocess.run(
                ['git', 'log', '--format=%s', 'origin/main...HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                commits = result.stdout.strip().split('\n')
                body_parts = [
                    "## Changes",
                    ""
                ]
                body_parts.extend(f"- {commit}" for commit in commits)
                body_parts.extend([
                    "",
                    "---",
                    f"*Created by Claude Code from branch `{branch_name}`*"
                ])
                return '\n'.join(body_parts)

        except Exception as e:
            logger.debug(f"Error generating PR body: {e}")

        return f"Changes from Claude Code branch `{branch_name}`"

    def open_pr_in_terminal(
        self,
        repo_path: Path,
        branch_name: str,
        terminal_opener
    ) -> bool:
        """
        Open terminal with gh pr create command ready.

        Args:
            repo_path: Path to repository
            branch_name: Branch name
            terminal_opener: TerminalOpener instance

        Returns:
            True if terminal opened successfully
        """
        # Command to create PR interactively
        command = f'gh pr create --web'

        return terminal_opener.open_terminal(
            working_dir=repo_path,
            command=command,
            title=f"Create PR - {branch_name}"
        )
