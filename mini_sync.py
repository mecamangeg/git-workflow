#!/usr/bin/env python3
"""
Mini Git Workflow - Claude Code Branch Sync (Project-Based)

A simplified, project-based version of the Git Workflow Guardian.
Run this in your project directory to automatically sync Claude branches,
run tests, and start your dev server.

Usage:
    python mini_sync.py              # One-time sync
    python mini_sync.py --watch      # Watch mode (continuous)
    python mini_sync.py --check      # Check current branch only
"""

import argparse
import asyncio
import json
import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Optional, List


class Colors:
    """Console colors for output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}✗{Colors.ENDC} {msg}")


def log_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{msg}{Colors.ENDC}")


class MiniSync:
    """Mini sync tool for Claude Code branches"""

    def __init__(self, project_dir: Path, config: dict):
        self.project_dir = project_dir
        self.config = config
        self.claude_patterns = config.get('claude_branch_patterns', ['^claude/.*'])

    def run_command(self, cmd: List[str], timeout: int = 30) -> tuple[int, str, str]:
        """Run a command and return (exit_code, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)

    def detect_claude_branches(self) -> List[str]:
        """Detect Claude branches on remote"""
        log_info("Checking for Claude branches...")

        # Fetch from remote
        code, _, _ = self.run_command(['git', 'fetch', '--all', '--prune'])
        if code != 0:
            log_warning("Failed to fetch from remote")
            return []

        # Get remote branches
        code, stdout, _ = self.run_command(['git', 'branch', '-r'])
        if code != 0:
            return []

        # Filter for Claude branches
        branches = []
        for line in stdout.strip().split('\n'):
            branch = line.strip().replace('origin/', '')
            if any(branch.startswith(pattern.replace('^', '').replace('.*', ''))
                   for pattern in self.claude_patterns):
                branches.append(branch)

        if branches:
            log_success(f"Found {len(branches)} Claude branch(es): {', '.join(branches)}")
        else:
            log_info("No Claude branches found")

        return branches

    def get_current_branch(self) -> Optional[str]:
        """Get current git branch"""
        code, stdout, _ = self.run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        if code == 0:
            return stdout.strip()
        return None

    def sync_branch(self, branch_name: str) -> bool:
        """Sync a Claude branch"""
        log_header(f"Syncing branch: {branch_name}")

        current_branch = self.get_current_branch()

        # Check if already on this branch
        if current_branch == branch_name:
            log_info(f"Already on {branch_name}, pulling latest...")
            code, _, stderr = self.run_command(['git', 'pull', 'origin', branch_name])
            if code == 0:
                log_success("Pull successful")
                return True
            else:
                log_error(f"Pull failed: {stderr}")
                return False

        # Checkout branch
        log_info(f"Checking out {branch_name}...")

        # Check if branch exists locally
        code, _, _ = self.run_command(['git', 'rev-parse', '--verify', branch_name])

        if code == 0:
            # Branch exists locally, checkout and pull
            code, _, stderr = self.run_command(['git', 'checkout', branch_name])
            if code != 0:
                log_error(f"Checkout failed: {stderr}")
                return False

            code, _, stderr = self.run_command(['git', 'pull', 'origin', branch_name])
            if code != 0:
                log_error(f"Pull failed: {stderr}")
                return False
        else:
            # Create new tracking branch
            code, _, stderr = self.run_command([
                'git', 'checkout', '-b', branch_name, f'origin/{branch_name}'
            ])
            if code != 0:
                log_error(f"Failed to create tracking branch: {stderr}")
                return False

        log_success(f"Successfully synced {branch_name}")
        return True

    def detect_project_type(self) -> Optional[str]:
        """Detect project type"""
        # Check for Node.js
        if (self.project_dir / 'package.json').exists():
            try:
                with open(self.project_dir / 'package.json') as f:
                    package = json.load(f)
                    deps = {**package.get('dependencies', {}), **package.get('devDependencies', {})}

                    if 'next' in deps:
                        return 'next'
                    elif 'react' in deps:
                        return 'react'
                    elif 'vue' in deps:
                        return 'vue'
                    else:
                        return 'node'
            except:
                return 'node'

        # Check for Python
        if (self.project_dir / 'manage.py').exists():
            return 'django'
        elif (self.project_dir / 'app.py').exists() or (self.project_dir / 'wsgi.py').exists():
            return 'flask'
        elif list(self.project_dir.glob('*.py')):
            return 'python'

        return None

    def run_tests(self) -> bool:
        """Run tests if configured"""
        if not self.config.get('run_tests', True):
            log_info("Tests disabled in config, skipping...")
            return True

        project_type = self.detect_project_type()
        if not project_type:
            log_info("No project type detected, skipping tests")
            return True

        test_commands = self.config.get('test_commands', {
            'node': 'npm test',
            'next': 'npm test',
            'react': 'npm test',
            'vue': 'npm test',
            'python': 'pytest',
            'django': 'python manage.py test',
            'flask': 'pytest'
        })

        test_cmd = test_commands.get(project_type)
        if not test_cmd:
            log_info(f"No test command for {project_type}, skipping tests")
            return True

        log_header("Running tests...")
        log_info(f"Command: {test_cmd}")

        code, stdout, stderr = self.run_command(
            test_cmd.split(),
            timeout=self.config.get('test_timeout', 300)
        )

        if code == 0:
            log_success("Tests passed ✅")
            return True
        else:
            log_error("Tests failed ❌")
            if stderr:
                print(f"\n{Colors.RED}Test output:{Colors.ENDC}")
                print(stderr[:500])  # Show first 500 chars
            return False

    def start_dev_server(self) -> bool:
        """Start dev server"""
        if not self.config.get('start_dev_server', True):
            log_info("Dev server disabled in config, skipping...")
            return True

        project_type = self.detect_project_type()
        if not project_type:
            log_info("No project type detected, skipping dev server")
            return True

        dev_commands = self.config.get('dev_commands', {
            'node': 'npm run dev',
            'next': 'npm run dev',
            'react': 'npm start',
            'vue': 'npm run serve',
            'python': 'python manage.py runserver',
            'django': 'python manage.py runserver',
            'flask': 'flask run'
        })

        dev_cmd = dev_commands.get(project_type)
        if not dev_cmd:
            log_info(f"No dev command for {project_type}, skipping dev server")
            return True

        log_header("Starting dev server...")
        log_success(f"Run this command in a new terminal:")
        print(f"{Colors.CYAN}{dev_cmd}{Colors.ENDC}")
        print(f"\nOr press Ctrl+C and run it manually")

        return True


def load_config(project_dir: Path) -> dict:
    """Load project config"""
    config_file = project_dir / '.sync.yaml'

    if config_file.exists():
        try:
            with open(config_file) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            log_warning(f"Failed to load config: {e}")
            return {}

    # Default config
    return {
        'claude_branch_patterns': ['^claude/.*'],
        'run_tests': True,
        'start_dev_server': True,
        'test_timeout': 300
    }


def main():
    parser = argparse.ArgumentParser(description='Mini Git Workflow - Claude Code Branch Sync')
    parser.add_argument('--watch', action='store_true', help='Watch mode (continuous polling)')
    parser.add_argument('--check', action='store_true', help='Check current branch only')
    parser.add_argument('--interval', type=int, default=30, help='Watch interval in seconds')

    args = parser.parse_args()

    # Get project directory
    project_dir = Path.cwd()

    # Check if it's a git repo
    if not (project_dir / '.git').exists():
        log_error("Not a git repository!")
        sys.exit(1)

    log_header("Mini Git Workflow - Claude Code Sync")
    log_info(f"Project: {project_dir.name}")

    # Load config
    config = load_config(project_dir)

    # Create sync instance
    sync = MiniSync(project_dir, config)

    if args.check:
        # Just check current branch
        current = sync.get_current_branch()
        if current:
            log_info(f"Current branch: {current}")
        sys.exit(0)

    if args.watch:
        # Watch mode
        log_info(f"Watch mode enabled (checking every {args.interval}s)")
        log_info("Press Ctrl+C to stop")

        try:
            while True:
                branches = sync.detect_claude_branches()
                if branches:
                    latest = branches[-1]  # Get most recent
                    current = sync.get_current_branch()

                    if current != latest:
                        log_info(f"New Claude branch detected: {latest}")
                        if sync.sync_branch(latest):
                            if sync.run_tests():
                                sync.start_dev_server()

                time.sleep(args.interval)
        except KeyboardInterrupt:
            log_info("\nStopping watch mode")
            sys.exit(0)
    else:
        # One-time sync
        branches = sync.detect_claude_branches()

        if not branches:
            log_info("No Claude branches found. Nothing to do.")
            sys.exit(0)

        # Sync latest branch
        latest = branches[-1]
        if sync.sync_branch(latest):
            if sync.run_tests():
                sync.start_dev_server()
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
