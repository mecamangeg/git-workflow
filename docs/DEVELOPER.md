# Git Workflow Guardian - Developer Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Testing](#testing)
6. [Contributing](#contributing)
7. [Release Process](#release-process)

---

## Architecture Overview

### Hybrid Architecture

Git Workflow Guardian uses a **hybrid approach**:

```
┌─────────────────────────────────────────┐
│         GIT WORKFLOW GUARDIAN           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐     ┌──────────────┐  │
│  │ GIT HOOKS   │     │   SERVICE    │  │
│  │ (Critical)  │◄───►│ (Proactive)  │  │
│  └──────┬──────┘     └──────┬───────┘  │
│         │                    │          │
│         └────────┬───────────┘          │
│                  │                      │
│           ┌──────▼──────┐               │
│           │  NOTIFIER   │               │
│           └──────┬──────┘               │
│                  │                      │
│           ┌──────▼──────┐               │
│           │  STATE DB   │               │
│           └─────────────┘               │
└─────────────────────────────────────────┘
```

### Design Principles

1. **Fail-Safe:** Git hooks work even if service crashes
2. **Non-Intrusive:** Suggestions via toast, critical blocks via popup
3. **Configurable:** YAML-based configuration for all rules
4. **Auditable:** SQLite database tracks all violations
5. **Extensible:** Easy to add new rules and violation types

---

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment tool (venv)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/git-workflow-guardian.git
cd git-workflow-guardian

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify installation
pytest
```

### Development Tools

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=service --cov-report=html

# Format code
black service/ tests/

# Lint code
flake8 service/ tests/
pylint service/

# Type checking
mypy service/
```

---

## Project Structure

```
git-workflow-guardian/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── hooks/
│   ├── pre-commit.sh           # Block commits to main
│   ├── pre-push.sh             # Block pushes to main
│   ├── post-checkout.sh        # Suggest pulling main
│   ├── post-merge.sh           # Suggest branch deletion
│   └── notifier.py             # Popup notification handler
├── service/
│   ├── __init__.py
│   ├── monitor.py              # Main monitoring loop
│   ├── detector.py             # Violation detection logic
│   ├── notifier.py             # Toast notification handler
│   ├── state.py                # SQLite state management
│   ├── config.py               # YAML config loader
│   └── schema.sql              # Database schema
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_hooks.py
│   ├── test_monitor.py
│   ├── test_detector.py
│   ├── test_state.py
│   └── test_config.py
├── config/
│   ├── rules.yaml              # Workflow rules definition
│   └── config.yaml.example     # Example configuration
├── scripts/
│   ├── install_hooks.ps1       # Hook installer (Windows)
│   ├── install_hooks.sh        # Hook installer (Linux/macOS)
│   └── install_service.ps1     # Service installer (Windows)
├── docs/
│   ├── USER_GUIDE.md
│   ├── DEVELOPER.md
│   └── TROUBLESHOOTING.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pytest.ini
├── .gitignore
└── README.md
```

---

## Core Components

### 1. Git Hooks (`hooks/`)

**Purpose:** Critical enforcement at git operation time

**pre-commit.sh:**
- Detects current branch
- Blocks if on main/master
- Calls notifier.py for popup
- Returns exit code (0=allow, 1=block)

**notifier.py:**
- Shows tkinter popup dialog
- Checks for active overrides in SQLite
- Saves override if user chooses to proceed
- Session-level override tied to branch name

### 2. Monitoring Service (`service/monitor.py`)

**Purpose:** Proactive violation detection

```python
class MonitorService:
    def run(self):
        while self.is_running:
            repos = self.discover_repositories()
            for repo in repos:
                violations = self.check_repository(repo)
                self.process_violations(violations)
            time.sleep(self.poll_interval)
```

**Workflow:**
1. Discover repositories (auto or manual)
2. Check each repo for violations
3. Filter recently notified (5-min cooldown)
4. Send toast notifications
5. Log to database
6. Sleep until next poll

### 3. Violation Detector (`service/detector.py`)

**Detection Methods:**

```python
class ViolationDetector:
    def get_current_branch(repo_path) -> str
    def is_behind_remote(repo_path, branch) -> bool
    def get_merged_branches(repo_path) -> List[str]
    def has_uncommitted_changes(repo_path) -> bool
    def check_local_server() -> bool
    def is_branch_name_valid(branch_name) -> bool
```

**Implementation Notes:**
- All git commands have timeouts (5-10s)
- Errors are logged but don't crash service
- HTTP checks have 2s timeout

### 4. State Manager (`service/state.py`)

**Database Schema:**

```sql
repositories
  ├── id (PK)
  ├── path (unique)
  ├── name
  └── discovered_at

violations
  ├── id (PK)
  ├── repo_id (FK)
  ├── rule_name
  ├── severity
  ├── branch_name
  └── timestamp

overrides
  ├── id (PK)
  ├── repo_id (FK)
  ├── rule_name
  ├── session_id
  └── expires_at
```

**Key Methods:**
- `log_violation()` - Audit trail
- `is_overridden()` - Check active overrides
- `get_compliance_stats()` - Analytics

### 5. Configuration Manager (`service/config.py`)

**Features:**
- Loads YAML configuration
- Dot notation access: `config.get("rules.commit_to_main.severity")`
- Default values for missing keys
- Reload capability

---

## Testing

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_hooks.py         # Hook functionality
├── test_monitor.py       # Monitoring service
├── test_detector.py      # Violation detection
├── test_state.py         # Database operations
└── test_config.py        # Configuration loading
```

### Key Fixtures

```python
@pytest.fixture
def temp_git_repo(tmp_path):
    """Creates temporary git repository with initial commit"""

@pytest.fixture
def mock_config():
    """Provides test configuration dictionary"""

@pytest.fixture
def temp_db(tmp_path):
    """Creates temporary SQLite database with schema"""
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_hooks.py

# Specific test
pytest tests/test_hooks.py::test_pre_commit_hook_blocks_main

# With coverage
pytest --cov=service --cov-report=html
open htmlcov/index.html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Coverage Requirements

- **Minimum:** 80% overall coverage
- **Critical paths:** 100% coverage (hooks, violations)
- **Excluded:** GUI code (tkinter windows)

---

## Contributing

### Workflow

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b claude/feature-name-[sessionId]
   ```
3. **Make changes**
   - Write code
   - Add tests (maintain 80%+ coverage)
   - Update documentation
4. **Run quality checks**
   ```bash
   pytest
   black service/ tests/
   flake8 service/ tests/
   ```
5. **Commit with conventional commits**
   ```bash
   git commit -m "feat: add new violation detector"
   git commit -m "fix: handle timeout in git commands"
   git commit -m "docs: update developer guide"
   ```
6. **Push and create PR**
   ```bash
   git push origin claude/feature-name-[sessionId]
   ```

### Commit Convention

Format: `<type>(<scope>): <subject>`

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, no logic change)
- `refactor` - Code restructuring
- `test` - Adding/updating tests
- `chore` - Build process, dependencies

**Examples:**
```
feat(detector): add stale branch detection
fix(hooks): handle missing branch name
docs(readme): add installation instructions
test(monitor): add repository discovery tests
```

### Code Style

- **Formatter:** Black (line length: 88)
- **Linter:** Flake8
- **Type hints:** Preferred for public methods
- **Docstrings:** Google style

```python
def detect_violation(repo_path: Path, rule: str) -> Optional[Violation]:
    """
    Detect violation for given rule in repository.

    Args:
        repo_path: Absolute path to git repository
        rule: Rule name to check

    Returns:
        Violation object if detected, None otherwise

    Raises:
        ValueError: If repo_path is not a git repository
    """
    pass
```

### Pull Request Checklist

- [ ] Tests added/updated (coverage ≥80%)
- [ ] Code formatted with Black
- [ ] Linter passes (Flake8)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] CI/CD pipeline passes
- [ ] No breaking changes (or documented)

---

## Release Process

### Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

### Release Steps

1. **Update version**
   ```python
   # setup.py
   version="1.2.0"

   # service/__init__.py
   __version__ = "1.2.0"
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [1.2.0] - 2025-11-14
   ### Added
   - New violation detector for stale branches
   ### Fixed
   - Git timeout handling
   ```

3. **Create release branch**
   ```bash
   git checkout -b release/v1.2.0
   git add .
   git commit -m "chore: bump version to 1.2.0"
   git push origin release/v1.2.0
   ```

4. **Create PR and merge**

5. **Tag release**
   ```bash
   git checkout main
   git pull
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

6. **GitHub Release**
   - Go to GitHub → Releases → New Release
   - Select tag v1.2.0
   - Title: "v1.2.0 - Feature Name"
   - Description: Copy from CHANGELOG.md
   - Attach release artifacts (if any)

---

## Useful Commands

```bash
# Start monitoring service (manual)
python -m service.monitor

# Check compliance stats
python -c "from service.state import StateManager; print(StateManager().get_compliance_stats())"

# Test hook without install
bash hooks/pre-commit.sh

# Debug database
sqlite3 ~/.git-workflow-guardian/state.db "SELECT * FROM violations;"

# Clean test artifacts
rm -rf .pytest_cache htmlcov .coverage
```

---

## Need Help?

- **Questions:** [GitHub Discussions](https://github.com/yourusername/git-workflow-guardian/discussions)
- **Bug Reports:** [GitHub Issues](https://github.com/yourusername/git-workflow-guardian/issues)
- **Feature Requests:** [GitHub Issues](https://github.com/yourusername/git-workflow-guardian/issues)

---

**Happy coding! 🚀**
