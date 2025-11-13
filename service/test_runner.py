"""
Test Runner - Execute and report test results for synced branches.

Automatically runs tests when Claude branches are synced.
Supports multiple project types and test frameworks.
"""

import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of test execution"""
    passed: bool
    duration: float  # seconds
    exit_code: int
    stdout: str
    stderr: str
    command: str
    timestamp: datetime
    error: Optional[str] = None

    def get_summary(self) -> str:
        """Get one-line summary of test result"""
        if self.error:
            return f"Error: {self.error}"

        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"{status} in {self.duration:.1f}s"

    def get_short_output(self, max_lines: int = 10) -> str:
        """Get abbreviated output for notification"""
        output = self.stderr if self.stderr else self.stdout
        if not output:
            return "No output"

        lines = output.strip().split('\n')

        if len(lines) <= max_lines:
            return output

        # Show first few and last few lines
        half = max_lines // 2
        return '\n'.join([
            *lines[:half],
            f"... ({len(lines) - max_lines} lines omitted) ...",
            *lines[-half:]
        ])


class TestRunner:
    """
    Execute tests for different project types.

    Supports:
    - Node.js: npm test, yarn test
    - Python: pytest, python -m unittest, python manage.py test
    - Ruby: rake test, rspec
    - Custom commands via config
    """

    def __init__(self, config: dict):
        """
        Initialize test runner.

        Args:
            config: Configuration dict from sync.yaml
        """
        self.config = config
        self.enabled = config.get('auto_test', {}).get('enabled', True)
        self.timeout = config.get('auto_test', {}).get('timeout', 300)
        self.run_before_dev_server = config.get('auto_test', {}).get('run_before_dev_server', True)
        self.skip_dev_on_failure = config.get('auto_test', {}).get('skip_dev_on_failure', False)

        # Test commands per project type
        self.test_commands = config.get('auto_test', {}).get('commands', {
            'node': 'npm test',
            'next': 'npm test',
            'react': 'npm test',
            'vue': 'npm test',
            'python': 'pytest',
            'django': 'python manage.py test',
            'flask': 'pytest',
        })

    async def run_tests(
        self,
        repo_path: Path,
        project_type: Optional[str] = None
    ) -> TestResult:
        """
        Run tests for repository.

        Args:
            repo_path: Path to repository
            project_type: Project type (auto-detect if None)

        Returns:
            TestResult with test execution details
        """
        if not self.enabled:
            logger.info("Test runner disabled in config")
            return TestResult(
                passed=True,
                duration=0,
                exit_code=0,
                stdout="",
                stderr="",
                command="",
                timestamp=datetime.now(),
                error="Test runner disabled"
            )

        logger.info(f"Running tests for {repo_path.name}")

        # Detect project type if not provided
        if not project_type:
            project_type = self._detect_project_type(repo_path)

        if not project_type:
            logger.info(f"Could not detect project type for {repo_path.name}")
            return TestResult(
                passed=True,
                duration=0,
                exit_code=0,
                stdout="",
                stderr="",
                command="",
                timestamp=datetime.now(),
                error="No tests found - project type not detected"
            )

        # Get test command for project type
        test_command = self.test_commands.get(project_type)

        if not test_command:
            logger.info(f"No test command configured for {project_type}")
            return TestResult(
                passed=True,
                duration=0,
                exit_code=0,
                stdout="",
                stderr="",
                command="",
                timestamp=datetime.now(),
                error=f"No test command for {project_type}"
            )

        # Check if test command exists
        if not self._has_tests(repo_path, project_type):
            logger.info(f"No tests found in {repo_path.name}")
            return TestResult(
                passed=True,
                duration=0,
                exit_code=0,
                stdout="No tests found",
                stderr="",
                command=test_command,
                timestamp=datetime.now()
            )

        # Run tests
        logger.info(f"Executing: {test_command}")
        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_shell(
                test_command,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )

            # Wait for completion with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )

                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                exit_code = process.returncode

            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.wait()

                duration = time.time() - start_time
                logger.error(f"Tests timed out after {duration:.1f}s")

                return TestResult(
                    passed=False,
                    duration=duration,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Tests timed out after {self.timeout}s",
                    command=test_command,
                    timestamp=datetime.now(),
                    error=f"Timeout ({self.timeout}s)"
                )

            duration = time.time() - start_time
            passed = exit_code == 0

            if passed:
                logger.info(f"Tests passed in {duration:.1f}s")
            else:
                logger.warning(f"Tests failed in {duration:.1f}s (exit code: {exit_code})")

            return TestResult(
                passed=passed,
                duration=duration,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                command=test_command,
                timestamp=datetime.now()
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error running tests: {e}", exc_info=True)

            return TestResult(
                passed=False,
                duration=duration,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                command=test_command,
                timestamp=datetime.now(),
                error=str(e)
            )

    def _detect_project_type(self, repo_path: Path) -> Optional[str]:
        """Detect project type from filesystem"""

        # Node.js projects
        package_json = repo_path / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    package = json.load(f)

                # Check for scripts.test
                if 'scripts' in package and 'test' in package['scripts']:
                    dependencies = {**package.get('dependencies', {}), **package.get('devDependencies', {})}

                    # Detect specific frameworks
                    if 'next' in dependencies:
                        return 'next'
                    elif 'react-scripts' in dependencies or 'react' in dependencies:
                        return 'react'
                    elif 'vue' in dependencies:
                        return 'vue'
                    else:
                        return 'node'
            except Exception as e:
                logger.debug(f"Error reading package.json: {e}")

        # Python projects
        if (repo_path / 'pytest.ini').exists() or (repo_path / 'setup.py').exists():
            # Check for Django
            if (repo_path / 'manage.py').exists():
                return 'django'
            # Check for Flask
            elif (repo_path / 'app.py').exists() or (repo_path / 'wsgi.py').exists():
                return 'flask'
            else:
                return 'python'

        # Django specific
        if (repo_path / 'manage.py').exists():
            return 'django'

        # Generic Python with tests
        if list(repo_path.glob('test_*.py')) or list(repo_path.glob('**/test_*.py')):
            return 'python'

        return None

    def _has_tests(self, repo_path: Path, project_type: str) -> bool:
        """Check if project has tests"""

        if project_type in ['node', 'next', 'react', 'vue']:
            # Check for test files
            test_patterns = [
                '**/*.test.js',
                '**/*.test.ts',
                '**/*.test.jsx',
                '**/*.test.tsx',
                '**/*.spec.js',
                '**/*.spec.ts',
            ]

            for pattern in test_patterns:
                if list(repo_path.glob(pattern)):
                    return True

            # Check package.json for test script
            package_json = repo_path / 'package.json'
            if package_json.exists():
                try:
                    import json
                    with open(package_json) as f:
                        package = json.load(f)

                    test_script = package.get('scripts', {}).get('test', '')
                    # Some projects have dummy test scripts
                    if test_script and 'no test' not in test_script.lower():
                        return True
                except:
                    pass

        elif project_type in ['python', 'django', 'flask']:
            # Check for test files
            if list(repo_path.glob('test_*.py')) or list(repo_path.glob('**/test_*.py')):
                return True

            # Check for tests directory
            if (repo_path / 'tests').exists():
                return True

        return False

    def should_skip_dev_server(self, test_result: TestResult) -> bool:
        """
        Determine if dev server should be skipped based on test results.

        Args:
            test_result: Test execution result

        Returns:
            True if dev server should be skipped, False otherwise
        """
        # If tests passed, never skip
        if test_result.passed:
            return False

        # If tests failed and skip_dev_on_failure is True, skip
        if self.skip_dev_on_failure:
            logger.info("Skipping dev server because tests failed (skip_dev_on_failure=true)")
            return True

        # Default: don't skip (let user debug with dev server running)
        return False
