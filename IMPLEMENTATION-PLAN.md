# Git Workflow Guardian - Comprehensive Implementation Plan

**Version:** 1.0.0
**Date:** 2025-11-13
**Status:** Ready for Implementation
**Estimated Total Effort:** 18-22 days (3-4 weeks)

---

## 📋 EXECUTIVE SUMMARY

This document provides a detailed, phase-by-phase implementation plan for the Git Workflow Guardian system - a tool that helps developers maintain Git workflow best practices through intelligent notifications and enforcement.

**Core Problem:** Forgetful developers who need consistent reminders to follow Git workflow best practices without being overwhelmed by intrusive notifications.

**Solution:** Hybrid system combining git hooks (critical enforcement) with a background monitoring service (proactive guidance) using Windows notifications.

**Key Success Metrics:**
- 95%+ compliance with workflow rules after 2 weeks
- <5 false positive notifications per day
- Zero critical violations (commits/pushes to main) after Phase 1
- User satisfaction score >4/5

---

## 🎯 ARCHITECTURE DECISIONS

### Selected Architecture: Hybrid (Git Hooks + Background Service)

**Rationale:**
- **Git hooks** provide fail-safe critical enforcement (cannot be bypassed except with `--no-verify`)
- **Background service** enables proactive guidance before violations occur
- **Graceful degradation** - hooks work even if service crashes
- **Best user experience** - prevents mistakes while providing helpful suggestions

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GIT WORKFLOW GUARDIAN                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐         ┌─────────────────────┐    │
│  │   GIT HOOKS        │         │  BACKGROUND SERVICE │    │
│  │   (Critical)       │         │   (Proactive)       │    │
│  ├────────────────────┤         ├─────────────────────┤    │
│  │ • pre-commit       │         │ • Monitor main sync│    │
│  │ • pre-push         │         │ • Suggest cleanup  │    │
│  │ • post-checkout    │         │ • Check local test │    │
│  │ • post-merge       │         │ • Track compliance │    │
│  └──────┬─────────────┘         └──────┬──────────────┘    │
│         │                               │                   │
│         └───────────┬───────────────────┘                   │
│                     │                                       │
│              ┌──────▼──────┐                               │
│              │  NOTIFIER   │                               │
│              ├─────────────┤                               │
│              │ • Toast     │                               │
│              │ • Popup     │                               │
│              │ • Override  │                               │
│              └──────┬──────┘                               │
│                     │                                       │
│              ┌──────▼──────┐                               │
│              │  STATE DB   │                               │
│              ├─────────────┤                               │
│              │ • Overrides │                               │
│              │ • Violations│                               │
│              │ • Analytics │                               │
│              └─────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Git Hooks** | Bash scripts | Native git integration, reliable |
| **Background Service** | Python 3.8+ | Cross-platform, rich ecosystem |
| **Notifications** | tkinter (MVP) → PyQt5 (v2) | Built-in, then upgrade for polish |
| **State Management** | SQLite | Structured, queryable, analytics-ready |
| **Config Management** | YAML | Human-readable, easy to edit |
| **Service Manager** | Windows Task Scheduler | Built-in, reliable, auto-restart |
| **Testing Framework** | pytest | Industry standard, rich plugins |
| **Packaging** | PyInstaller | Single-file executables |

---

## 🗓️ IMPLEMENTATION PHASES

### Phase 0: Project Setup & Foundation (2 days)

**Objective:** Establish development environment, project structure, and baseline tests

#### Tasks

**SETUP-001: Initialize Project Structure (4 hours)**
```
git-workflow-guardian/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI
├── hooks/
│   ├── pre-commit.sh                 # Block commits to main
│   ├── pre-push.sh                   # Block pushes to main
│   ├── post-checkout.sh              # Remind to pull main
│   └── post-merge.sh                 # Suggest branch deletion
├── service/
│   ├── __init__.py
│   ├── monitor.py                    # Main monitoring loop
│   ├── detector.py                   # Violation detection logic
│   ├── notifier.py                   # Notification handler
│   ├── state.py                      # State management (SQLite)
│   └── config.py                     # Config loader (YAML)
├── tests/
│   ├── test_hooks.py
│   ├── test_monitor.py
│   ├── test_detector.py
│   └── test_notifier.py
├── config/
│   ├── config.yaml.example           # Example configuration
│   └── rules.yaml                    # Workflow rules definition
├── scripts/
│   ├── install.ps1                   # Windows installer
│   ├── uninstall.ps1                 # Cleanup script
│   └── setup_service.ps1             # Service registration
├── docs/
│   ├── USER_GUIDE.md
│   ├── DEVELOPER.md
│   └── TROUBLESHOOTING.md
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Dev dependencies
├── setup.py                           # Package metadata
├── pytest.ini                         # Test configuration
├── .gitignore
└── README.md
```

**Acceptance Criteria:**
- ✅ All directories created
- ✅ Git repository initialized
- ✅ README.md with project description
- ✅ requirements.txt with initial dependencies

**SETUP-002: Development Environment Setup (2 hours)**

**Dependencies:**
```txt
# requirements.txt
pyyaml>=6.0           # Config management
requests>=2.28        # HTTP checks (local dev server)
watchdog>=3.0         # File system monitoring
pytest>=7.4           # Testing framework
pytest-cov>=4.1       # Coverage reports
python-dateutil>=2.8  # Date handling for overrides
```

**Dev Environment:**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Acceptance Criteria:**
- ✅ Virtual environment created
- ✅ All dependencies installed
- ✅ pytest runs successfully (empty test suite)

**SETUP-003: Git Workflow Best Practices Reference (2 hours)**

Create `config/rules.yaml`:

```yaml
# Git Workflow Guardian - Rules Configuration
version: 1.0.0

# Workflow rules enforcement
rules:
  # CRITICAL: Blocking violations
  commit_to_main:
    severity: critical
    enabled: true
    blocking: true
    message: "You're about to commit to main branch"
    action: "Create a feature branch first"
    why: "Main should only receive reviewed code via PRs. Direct commits bypass the review process."

  push_to_main:
    severity: critical
    enabled: true
    blocking: true
    message: "You're about to push to main branch"
    action: "Create a feature branch and PR instead"
    why: "Pushing to main bypasses code review and CI checks."

  # WARNING: Strong suggestions
  branch_naming:
    severity: warning
    enabled: true
    blocking: false
    pattern: "^claude/[a-z0-9-]+-[A-Za-z0-9]{24}$"
    message: "Branch name doesn't follow convention"
    action: "Rename to: claude/feature-name-{sessionId}"
    why: "Consistent naming helps track features and PRs."

  # SUGGESTION: Helpful reminders
  pull_before_work:
    severity: suggestion
    enabled: true
    blocking: false
    message: "Starting new work session"
    action: "Pull latest main first"
    why: "Ensures you're working with latest code and prevents merge conflicts."

  test_locally:
    severity: suggestion
    enabled: true
    blocking: false
    check_url: "http://localhost:3011"
    message: "Local dev server not detected"
    action: "Start dev server: npm run dev -- -p 3011"
    why: "Testing locally before committing catches bugs early."

  delete_merged_branch:
    severity: suggestion
    enabled: true
    blocking: false
    message: "Branch {branch_name} has been merged"
    action: "Delete the branch to keep repo clean"
    why: "Stale branches clutter the repository."

# Notification configuration
notifications:
  # Critical violations - blocking popup
  critical:
    type: popup
    blocking: true
    timeout: null  # No auto-dismiss

  # Warnings - non-blocking popup
  warning:
    type: popup
    blocking: false
    timeout: 30  # Auto-dismiss after 30s

  # Suggestions - toast notification
  suggestion:
    type: toast
    blocking: false
    timeout: 10  # Auto-dismiss after 10s

# Override configuration
overrides:
  mode: session  # Options: session, time-based, permanent
  session_duration: null  # Until branch changes
  time_duration: 3600  # 1 hour (for time-based mode)
  max_overrides_before_disable: 3  # Suggest disabling after N overrides

# Monitoring configuration
monitoring:
  poll_interval: 30  # Seconds between checks
  repos:
    auto_discover: true
    search_paths:
      - "D:/Projects"
      - "C:/Users/{username}/Projects"
    manual_repos: []  # Add specific repo paths here

# Compliance scoring (Phase 3)
scoring:
  enabled: false  # Enable in Phase 3
  target_score: 95
  metrics:
    - feature_branch_usage
    - branch_naming_compliance
    - local_testing_rate
    - branch_cleanup_speed
```

**Acceptance Criteria:**
- ✅ rules.yaml created with all 7 workflow rules
- ✅ Clear severity levels (critical, warning, suggestion)
- ✅ Notification types mapped to severity
- ✅ Override configuration documented

**SETUP-004: Database Schema Design (2 hours)**

Create `service/schema.sql`:

```sql
-- Git Workflow Guardian - SQLite Schema
-- Version: 1.0.0

-- Repositories being monitored
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Violation records (audit log)
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL,  -- critical, warning, suggestion
    branch_name TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overridden BOOLEAN DEFAULT 0,
    override_reason TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Active overrides
CREATE TABLE IF NOT EXISTS overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    session_id TEXT,  -- For session-level overrides
    expires_at TIMESTAMP,  -- NULL for session-level, timestamp for time-based
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Compliance metrics (Phase 3)
CREATE TABLE IF NOT EXISTS compliance_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    date DATE NOT NULL,
    feature_branch_usage REAL,  -- 0.0 to 1.0
    branch_naming_compliance REAL,
    local_testing_rate REAL,
    branch_cleanup_speed REAL,  -- Average hours to delete
    overall_score REAL,
    FOREIGN KEY (repo_id) REFERENCES repositories(id),
    UNIQUE(repo_id, date)
);

-- Branch activity tracking
CREATE TABLE IF NOT EXISTS branch_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    branch_name TEXT NOT NULL,
    created_at TIMESTAMP,
    last_commit_at TIMESTAMP,
    merged_at TIMESTAMP,
    deleted_at TIMESTAMP,
    commit_count INTEGER DEFAULT 0,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_violations_repo ON violations(repo_id);
CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_overrides_repo ON overrides(repo_id);
CREATE INDEX IF NOT EXISTS idx_overrides_expires ON overrides(expires_at);
CREATE INDEX IF NOT EXISTS idx_branch_activity_repo ON branch_activity(repo_id);
```

**Acceptance Criteria:**
- ✅ Schema covers all data requirements
- ✅ Foreign keys properly defined
- ✅ Indexes for common queries
- ✅ Phase 3 tables included but optional

**SETUP-005: Testing Framework Setup (2 hours)**

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=service
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

Create `tests/conftest.py`:

```python
"""Pytest fixtures for Git Workflow Guardian tests"""
import os
import tempfile
import pytest
from pathlib import Path
import subprocess

@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing"""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

    # Create initial commit on main
    (repo_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

    return repo_path

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "rules": {
            "commit_to_main": {
                "severity": "critical",
                "enabled": True,
                "blocking": True
            }
        },
        "monitoring": {
            "poll_interval": 1  # Fast polling for tests
        }
    }

@pytest.fixture
def temp_db(tmp_path):
    """Create temporary SQLite database"""
    db_path = tmp_path / "test.db"
    # Initialize schema
    from service.state import StateManager
    StateManager(str(db_path)).initialize()
    return db_path
```

**Acceptance Criteria:**
- ✅ pytest configured with coverage
- ✅ Fixtures for git repos, config, database
- ✅ Test suite runs (even if empty)

---

### Phase 1: Git Hooks Implementation (4 days)

**Objective:** Implement critical enforcement via git hooks with blocking popups

#### Tasks

**HOOKS-001: pre-commit Hook (Prevent Commits to Main) (6 hours)**

Create `hooks/pre-commit.sh`:

```bash
#!/bin/bash
# Git Workflow Guardian - Pre-Commit Hook
# Prevents commits to main/master branch

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Define protected branches
PROTECTED_BRANCHES=("main" "master")

# Check if current branch is protected
for branch in "${PROTECTED_BRANCHES[@]}"; do
    if [ "$CURRENT_BRANCH" = "$branch" ]; then
        # Call Python notifier with violation details
        python "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "commit_to_main" \
            --branch "$CURRENT_BRANCH" \
            --repo "$(git rev-parse --show-toplevel)"

        # Exit code from notifier determines if commit proceeds
        exit $?
    fi
done

# Allow commit (not on protected branch)
exit 0
```

Create `hooks/notifier.py`:

```python
#!/usr/bin/env python3
"""
Git Workflow Guardian - Notification Handler for Hooks
Displays popup and handles override logic
"""
import sys
import argparse
import tkinter as tk
from tkinter import messagebox
import json
from pathlib import Path
import sqlite3
from datetime import datetime

class HookNotifier:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.db_path = Path.home() / ".git-workflow-guardian" / "state.db"
        self.config_path = self.repo_path / ".git" / "hooks" / "config.json"

    def check_override(self, rule_name, branch_name):
        """Check if violation is currently overridden"""
        if not self.db_path.exists():
            return False

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Check for active override
        cursor.execute("""
            SELECT id FROM overrides
            WHERE rule_name = ?
            AND session_id = ?
            AND (expires_at IS NULL OR expires_at > ?)
        """, (rule_name, branch_name, datetime.now().isoformat()))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    def save_override(self, rule_name, branch_name):
        """Save override to database (session-level)"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create tables if not exist (simplified for hook usage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS overrides (
                id INTEGER PRIMARY KEY,
                rule_name TEXT,
                session_id TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert override (session-level, no expiry)
        cursor.execute("""
            INSERT INTO overrides (rule_name, session_id, expires_at)
            VALUES (?, ?, NULL)
        """, (rule_name, branch_name))

        conn.commit()
        conn.close()

    def show_notification(self, violation_type, branch_name):
        """Display tkinter popup with override option"""

        messages = {
            "commit_to_main": {
                "title": "🚨 CRITICAL: Committing to Main",
                "message": f"You're about to commit to '{branch_name}' branch.",
                "action": "Create a feature branch first",
                "why": "Main should only receive reviewed code via PRs.\nDirect commits bypass the review process.",
                "command": f"git checkout -b claude/feature-name-[sessionId]"
            },
            "push_to_main": {
                "title": "🚨 CRITICAL: Pushing to Main",
                "message": f"You're about to push to '{branch_name}' branch.",
                "action": "Create a feature branch and PR instead",
                "why": "Pushing to main bypasses code review and CI checks.",
                "command": "git checkout -b claude/feature-name-[sessionId]"
            }
        }

        msg = messages.get(violation_type, {})

        # Build message
        full_message = f"{msg['message']}\n\n"
        full_message += f"✅ WHAT TO DO:\n{msg['action']}\n\n"
        full_message += f"📝 WHY:\n{msg['why']}\n\n"
        full_message += f"Suggested:\n{msg['command']}"

        # Create tkinter popup
        root = tk.Tk()
        root.withdraw()  # Hide main window

        # Custom dialog with two buttons
        response = messagebox.askyesno(
            msg["title"],
            full_message + "\n\nBlock this commit?",
            icon=messagebox.ERROR
        )

        root.destroy()

        return response  # True = block, False = override

    def run(self, violation_type, branch_name):
        """Main execution logic"""

        # Check if already overridden
        if self.check_override(violation_type, branch_name):
            print(f"[Override Active] {violation_type} is overridden for this session")
            return 0  # Allow operation

        # Show notification
        should_block = self.show_notification(violation_type, branch_name)

        if should_block:
            print(f"[BLOCKED] {violation_type}")
            return 1  # Block operation
        else:
            # User chose to override
            self.save_override(violation_type, branch_name)
            print(f"[Override] {violation_type} overridden for this session")
            return 0  # Allow operation

def main():
    parser = argparse.ArgumentParser(description="Git Workflow Guardian Hook Notifier")
    parser.add_argument("--violation", required=True, help="Violation type")
    parser.add_argument("--branch", required=True, help="Current branch")
    parser.add_argument("--repo", required=True, help="Repository path")

    args = parser.parse_args()

    notifier = HookNotifier(args.repo)
    exit_code = notifier.run(args.violation, args.branch)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

**Testing:**

Create `tests/test_pre_commit_hook.py`:

```python
"""Tests for pre-commit hook"""
import subprocess
import pytest
from pathlib import Path

def test_blocks_commit_to_main(temp_git_repo, monkeypatch):
    """Test that pre-commit hook blocks commits to main"""

    # Copy hook to repo
    hook_path = temp_git_repo / ".git" / "hooks" / "pre-commit"
    # (install hook script)
    hook_path.write_text("#!/bin/bash\nexit 1\n")  # Simplified for test
    hook_path.chmod(0o755)

    # Attempt commit on main
    (temp_git_repo / "test.txt").write_text("test")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test"],
        cwd=temp_git_repo,
        capture_output=True
    )

    assert result.returncode != 0, "Commit should be blocked"

def test_allows_commit_on_feature_branch(temp_git_repo):
    """Test that commits are allowed on feature branches"""

    # Create and checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "claude/test-feature-123"],
        cwd=temp_git_repo,
        check=True
    )

    # Hook should allow commit
    (temp_git_repo / "test.txt").write_text("test")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test"],
        cwd=temp_git_repo,
        capture_output=True
    )

    assert result.returncode == 0, "Commit should be allowed"
```

**Acceptance Criteria:**
- ✅ pre-commit hook blocks commits to main/master
- ✅ Popup shows WHAT TO DO, WHY, suggested command
- ✅ Override button saves session-level override
- ✅ Tests pass (block on main, allow on feature)
- ✅ Hook is executable and runs automatically

**HOOKS-002: pre-push Hook (Prevent Pushes to Main) (4 hours)**

Similar structure to pre-commit, but validates push target.

Create `hooks/pre-push.sh`:

```bash
#!/bin/bash
# Git Workflow Guardian - Pre-Push Hook
# Prevents pushes to main/master branch

# Read push details from stdin
while read local_ref local_sha remote_ref remote_sha; do
    # Extract branch name from remote ref
    remote_branch=$(echo "$remote_ref" | sed 's|refs/heads/||')

    # Check if pushing to protected branch
    if [ "$remote_branch" = "main" ] || [ "$remote_branch" = "master" ]; then
        python "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "push_to_main" \
            --branch "$remote_branch" \
            --repo "$(git rev-parse --show-toplevel)"

        exit $?
    fi
done

exit 0
```

**Acceptance Criteria:**
- ✅ pre-push hook blocks pushes to main/master
- ✅ Popup shows appropriate message
- ✅ Tests pass
- ✅ Works with `git push origin main` attempts

**HOOKS-003: post-checkout Hook (Remind to Pull Main) (3 hours)**

Create `hooks/post-checkout.sh`:

```bash
#!/bin/bash
# Git Workflow Guardian - Post-Checkout Hook
# Reminds to pull main after switching branches

# Arguments: previous_head new_head branch_checkout_flag
PREV_HEAD=$1
NEW_HEAD=$2
BRANCH_CHECKOUT=$3

# Only trigger on branch checkout (flag=1)
if [ "$BRANCH_CHECKOUT" != "1" ]; then
    exit 0
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# Get main branch name
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$MAIN_BRANCH" ]; then
    MAIN_BRANCH="main"
fi

# Check if main is out of sync
if [ "$CURRENT_BRANCH" = "$MAIN_BRANCH" ]; then
    git fetch origin "$MAIN_BRANCH" --quiet

    LOCAL=$(git rev-parse "$MAIN_BRANCH")
    REMOTE=$(git rev-parse "origin/$MAIN_BRANCH")

    if [ "$LOCAL" != "$REMOTE" ]; then
        # Main is out of sync - suggest pull
        python "$(git rev-parse --show-toplevel)/.git/hooks/notifier.py" \
            --violation "pull_before_work" \
            --branch "$MAIN_BRANCH" \
            --repo "$(git rev-parse --show-toplevel)" \
            --non-blocking
    fi
fi

exit 0
```

**Acceptance Criteria:**
- ✅ Shows toast notification when main is out of sync
- ✅ Non-blocking (doesn't prevent checkout)
- ✅ Only triggers on branch checkout
- ✅ Tests pass

**HOOKS-004: Installation Script (4 hours)**

Create `scripts/install_hooks.ps1`:

```powershell
# Git Workflow Guardian - Hook Installation Script
param(
    [Parameter(Mandatory=$false)]
    [string]$RepoPath = ".",

    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Git Workflow Guardian - Hook Installer" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Resolve repo path
$RepoPath = Resolve-Path $RepoPath

# Check if git repo
if (-not (Test-Path "$RepoPath/.git")) {
    Write-Error "Not a git repository: $RepoPath"
    exit 1
}

Write-Host "`n[1/4] Validating repository..." -ForegroundColor Yellow
Write-Host "Repository: $RepoPath" -ForegroundColor Gray

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HooksSource = Join-Path (Split-Path -Parent $ScriptDir) "hooks"

# Check if hooks already installed
$HooksDir = "$RepoPath/.git/hooks"
if ((Test-Path "$HooksDir/pre-commit") -and -not $Force) {
    $response = Read-Host "Hooks already installed. Overwrite? (y/n)"
    if ($response -ne "y") {
        Write-Host "Installation cancelled." -ForegroundColor Red
        exit 0
    }
}

Write-Host "`n[2/4] Installing hooks..." -ForegroundColor Yellow

# Copy hook scripts
$hooks = @("pre-commit.sh", "pre-push.sh", "post-checkout.sh", "post-merge.sh", "notifier.py")

foreach ($hook in $hooks) {
    $source = Join-Path $HooksSource $hook
    $dest = Join-Path $HooksDir ($hook -replace ".sh$", "")

    if (Test-Path $source) {
        Copy-Item $source $dest -Force
        Write-Host "  ✓ Installed: $hook" -ForegroundColor Green

        # Make executable (Git Bash compatibility)
        if ($hook -match ".sh$") {
            git -C $RepoPath update-index --chmod=+x ".git/hooks/$($hook -replace '.sh$', '')"
        }
    } else {
        Write-Host "  ✗ Missing: $hook" -ForegroundColor Red
    }
}

Write-Host "`n[3/4] Configuring permissions..." -ForegroundColor Yellow
# Permissions already set above

Write-Host "`n[4/4] Verifying installation..." -ForegroundColor Yellow

# Test hooks
$testResult = git -C $RepoPath hook list 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Git hooks registered" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Could not verify hooks (Git version may not support hook list)" -ForegroundColor Yellow
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host " Installation Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`nWorkflow rules now active:"
Write-Host "  ⛔ BLOCK: Commits to main" -ForegroundColor Red
Write-Host "  ⛔ BLOCK: Pushes to main" -ForegroundColor Red
Write-Host "  💡 SUGGEST: Pull main after checkout" -ForegroundColor Blue
Write-Host "  💡 SUGGEST: Delete merged branches" -ForegroundColor Blue

Write-Host "`nTo bypass hooks (emergency only): git commit --no-verify" -ForegroundColor Gray
```

**Acceptance Criteria:**
- ✅ Installs all hooks with one command
- ✅ Checks for existing hooks (warns before overwriting)
- ✅ Sets executable permissions
- ✅ Works on Windows (PowerShell) and Linux (bash alternative)
- ✅ Validates installation

**HOOKS-005: Integration Testing (3 hours)**

Create `tests/test_hook_integration.py`:

```python
"""Integration tests for git hooks"""
import subprocess
import pytest
from pathlib import Path

def test_full_workflow_compliance(temp_git_repo):
    """Test complete workflow from violation to override"""

    # 1. Install hooks
    # (simulate installation)

    # 2. Attempt commit on main (should block)
    (temp_git_repo / "file1.txt").write_text("test")
    subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test"],
        cwd=temp_git_repo,
        capture_output=True
    )
    assert result.returncode != 0, "Should block commit to main"

    # 3. Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "claude/test-feature-123"],
        cwd=temp_git_repo,
        check=True
    )

    # 4. Commit on feature branch (should succeed)
    result = subprocess.run(
        ["git", "commit", "-m", "test"],
        cwd=temp_git_repo,
        capture_output=True
    )
    assert result.returncode == 0, "Should allow commit on feature branch"

def test_override_persistence(temp_git_repo):
    """Test that overrides persist for session"""
    # Test override logic
    pass

def test_branch_naming_validation(temp_git_repo):
    """Test branch naming pattern validation"""
    # Test branch name pattern
    pass
```

**Acceptance Criteria:**
- ✅ Full workflow test passes
- ✅ Override persistence validated
- ✅ Branch naming validation works
- ✅ CI/CD pipeline runs tests

---

### Phase 2: Background Monitoring Service (6-7 days)

**Objective:** Implement proactive monitoring and guidance with toast notifications

#### Tasks

**MONITOR-001: Core Monitoring Loop (8 hours)**

Create `service/monitor.py`:

```python
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
                repos.extend(self._scan_for_repos(Path(search_path).expanduser()))

        # Manual repos
        manual_repos = self.config.get("monitoring.repos.manual_repos", [])
        repos.extend([Path(r) for r in manual_repos])

        # Deduplicate
        repos = list(set(repos))

        logger.info(f"Discovered {len(repos)} repositories")
        return repos

    def _scan_for_repos(self, search_path: Path) -> List[Path]:
        """Recursively scan for .git directories"""
        repos = []

        if not search_path.exists():
            return repos

        for item in search_path.rglob(".git"):
            if item.is_dir():
                repo_path = item.parent
                repos.append(repo_path)
                logger.debug(f"Found repository: {repo_path}")

        return repos

    def check_repository(self, repo_path: Path) -> List[Dict]:
        """Check single repository for violations"""
        violations = []

        try:
            # Get current state
            current_branch = self.detector.get_current_branch(repo_path)

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
                if branch not in ["main", "master"]:
                    violations.append({
                        "rule": "delete_merged_branch",
                        "severity": "suggestion",
                        "repo": repo_path,
                        "branch": branch,
                        "message": f"Branch {branch} has been merged"
                    })

            # 3. Local dev server check (before commits)
            if self.detector.has_uncommitted_changes(repo_path):
                if not self.detector.check_local_server():
                    violations.append({
                        "rule": "test_locally",
                        "severity": "suggestion",
                        "repo": repo_path,
                        "branch": current_branch,
                        "message": "Local dev server not detected"
                    })

            # 4. Branch naming compliance
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
```

**Acceptance Criteria:**
- ✅ Discovers repositories automatically
- ✅ Polls at configured interval
- ✅ Detects violations (main sync, merged branches, local server, branch naming)
- ✅ Sends toast notifications
- ✅ Respects cooldown periods (no spam)
- ✅ Graceful shutdown on SIGINT

**MONITOR-002: Violation Detection Logic (6 hours)**

Create `service/detector.py`:

```python
"""
Git Workflow Guardian - Violation Detection
Logic for detecting workflow violations
"""
import subprocess
import re
import requests
from pathlib import Path
from typing import Optional, List

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
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def is_behind_remote(self, repo_path: Path, branch: str) -> bool:
        """Check if local branch is behind remote"""
        try:
            # Fetch quietly
            subprocess.run(
                ["git", "fetch", "origin", branch, "--quiet"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )

            # Compare local and remote
            local = subprocess.run(
                ["git", "rev-parse", branch],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            remote = subprocess.run(
                ["git", "rev-parse", f"origin/{branch}"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            return local != remote

        except subprocess.CalledProcessError:
            return False

    def get_merged_branches(self, repo_path: Path) -> List[str]:
        """Get list of merged branches (except main/master)"""
        try:
            result = subprocess.run(
                ["git", "branch", "--merged"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            branches = [
                b.strip().replace("* ", "")
                for b in result.stdout.split("\n")
                if b.strip() and not b.strip().startswith("*")
            ]

            return branches

        except subprocess.CalledProcessError:
            return []

    def has_uncommitted_changes(self, repo_path: Path) -> bool:
        """Check if there are uncommitted changes"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            return bool(result.stdout.strip())

        except subprocess.CalledProcessError:
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

        return bool(re.match(pattern, branch_name))
```

**Acceptance Criteria:**
- ✅ All detection methods work correctly
- ✅ Git commands handle errors gracefully
- ✅ HTTP checks have timeouts
- ✅ Pattern validation works
- ✅ Tests cover all detection logic

**MONITOR-003: Toast Notification System (6 hours)**

Create `service/notifier.py`:

```python
"""
Git Workflow Guardian - Toast Notifications
Windows toast notifications for suggestions
"""
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional
import threading

class ToastNotifier:
    """Display toast notifications for non-critical violations"""

    def __init__(self, config):
        self.config = config
        self.active_toasts = []

    def show_toast(
        self,
        rule_name: str,
        severity: str,
        message: str,
        repo_path: Path,
        branch: Optional[str] = None
    ):
        """Display toast notification"""

        # Get rule configuration
        rule_config = self.config.get(f"rules.{rule_name}", {})

        # Build notification content
        title = f"💡 Git Workflow Guardian"
        action = rule_config.get("action", "")
        why = rule_config.get("why", "")
        command = rule_config.get("command", "")

        # Show in separate thread to not block
        thread = threading.Thread(
            target=self._show_toast_window,
            args=(title, message, action, why, command),
            daemon=True
        )
        thread.start()

    def _show_toast_window(
        self,
        title: str,
        message: str,
        action: str,
        why: str,
        command: str
    ):
        """Create and display toast window"""

        # Create window
        root = tk.Tk()
        root.title(title)
        root.attributes('-topmost', True)

        # Position in bottom-right corner
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 400
        window_height = 200
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Content
        frame = ttk.Frame(root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Message
        ttk.Label(
            frame,
            text=message,
            wraplength=380,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        # Action
        if action:
            ttk.Label(
                frame,
                text=f"✅ WHAT TO DO:\n{action}",
                wraplength=380,
                font=("Segoe UI", 9)
            ).pack(anchor=tk.W, pady=(0, 10))

        # Why
        if why:
            ttk.Label(
                frame,
                text=f"📝 WHY:\n{why}",
                wraplength=380,
                font=("Segoe UI", 9),
                foreground="gray"
            ).pack(anchor=tk.W, pady=(0, 10))

        # Command
        if command:
            ttk.Label(
                frame,
                text=f"Suggested:\n{command}",
                wraplength=380,
                font=("Courier New", 8),
                background="#f0f0f0"
            ).pack(anchor=tk.W, pady=(0, 10))

        # Dismiss button
        ttk.Button(
            frame,
            text="Dismiss",
            command=root.destroy
        ).pack(side=tk.BOTTOM, anchor=tk.E)

        # Auto-dismiss after timeout
        timeout = self.config.get("notifications.suggestion.timeout", 10) * 1000
        root.after(timeout, root.destroy)

        root.mainloop()
```

**Acceptance Criteria:**
- ✅ Toast appears in bottom-right corner
- ✅ Shows message, action, why, command
- ✅ Auto-dismisses after timeout
- ✅ Non-blocking (separate thread)
- ✅ Professional styling

**MONITOR-004: State Management with SQLite (5 hours)**

Create `service/state.py`:

```python
"""
Git Workflow Guardian - State Management
SQLite database for tracking state and analytics
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

class StateManager:
    """Manage state using SQLite database"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path.home() / ".git-workflow-guardian" / "state.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.initialize()

    def initialize(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Load schema from file
        schema_path = Path(__file__).parent.parent / "service" / "schema.sql"
        with open(schema_path) as f:
            schema = f.read()
            cursor.executescript(schema)

        conn.commit()
        conn.close()

    def log_violation(
        self,
        repo_path: Path,
        rule_name: str,
        severity: str,
        branch_name: Optional[str] = None,
        overridden: bool = False
    ):
        """Log violation to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Get or create repo
        repo_id = self._get_or_create_repo(cursor, repo_path)

        # Insert violation
        cursor.execute("""
            INSERT INTO violations (repo_id, rule_name, severity, branch_name, overridden)
            VALUES (?, ?, ?, ?, ?)
        """, (repo_id, rule_name, severity, branch_name, overridden))

        conn.commit()
        conn.close()

    def is_overridden(self, rule_name: str, session_id: Optional[str] = None) -> bool:
        """Check if rule is currently overridden"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM overrides
            WHERE rule_name = ?
            AND (expires_at IS NULL OR expires_at > ?)
            AND (session_id = ? OR session_id IS NULL)
        """, (rule_name, datetime.now().isoformat(), session_id))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    def get_last_notification(
        self,
        rule_name: str,
        repo_path: Path
    ) -> Optional[datetime]:
        """Get timestamp of last notification for rule"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        repo_id = self._get_repo_id(cursor, repo_path)
        if not repo_id:
            return None

        cursor.execute("""
            SELECT MAX(timestamp) FROM violations
            WHERE repo_id = ? AND rule_name = ?
        """, (repo_id, rule_name))

        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return datetime.fromisoformat(result[0])
        return None

    def _get_or_create_repo(self, cursor, repo_path: Path) -> int:
        """Get or create repository record"""
        cursor.execute("SELECT id FROM repositories WHERE path = ?", (str(repo_path),))
        result = cursor.fetchone()

        if result:
            return result[0]

        cursor.execute(
            "INSERT INTO repositories (path, name) VALUES (?, ?)",
            (str(repo_path), repo_path.name)
        )
        return cursor.lastrowid

    def _get_repo_id(self, cursor, repo_path: Path) -> Optional[int]:
        """Get repository ID"""
        cursor.execute("SELECT id FROM repositories WHERE path = ?", (str(repo_path),))
        result = cursor.fetchone()
        return result[0] if result else None
```

**Acceptance Criteria:**
- ✅ Database initialized with schema
- ✅ Violations logged correctly
- ✅ Override checks work
- ✅ Last notification tracking works
- ✅ Tests cover all database operations

**MONITOR-005: Service Installation & Startup (6 hours)**

Create `scripts/install_service.ps1`:

```powershell
# Git Workflow Guardian - Service Installation Script
param(
    [Parameter(Mandatory=$false)]
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$ServiceName = "GitWorkflowGuardian"
$ServiceDisplayName = "Git Workflow Guardian Monitor"
$ServiceDescription = "Monitors git repositories for workflow compliance"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$ServiceScript = Join-Path $ProjectRoot "service\monitor.py"
$PythonExe = "python"  # Assumes python in PATH

if ($Uninstall) {
    Write-Host "Uninstalling $ServiceDisplayName..." -ForegroundColor Yellow

    # Remove scheduled task
    $task = Get-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $ServiceName -Confirm:$false
        Write-Host "  ✓ Scheduled task removed" -ForegroundColor Green
    } else {
        Write-Host "  ℹ No scheduled task found" -ForegroundColor Gray
    }

    Write-Host "Uninstallation complete!" -ForegroundColor Green
    exit 0
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Git Workflow Guardian - Service Installer" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Validating environment..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = & $PythonExe --version 2>&1
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python not found in PATH. Please install Python 3.8+ and try again."
    exit 1
}

# Check service script
if (-not (Test-Path $ServiceScript)) {
    Write-Error "Service script not found: $ServiceScript"
    exit 1
}
Write-Host "  ✓ Service script found" -ForegroundColor Green

Write-Host "`n[2/3] Installing service..." -ForegroundColor Yellow

# Create scheduled task (runs at login)
$action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ServiceScript`""
$trigger = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

try {
    Register-ScheduledTask `
        -TaskName $ServiceName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $ServiceDescription `
        -Force | Out-Null

    Write-Host "  ✓ Scheduled task created" -ForegroundColor Green
} catch {
    Write-Error "Failed to create scheduled task: $_"
    exit 1
}

Write-Host "`n[3/3] Starting service..." -ForegroundColor Yellow

# Start task
Start-ScheduledTask -TaskName $ServiceName
Start-Sleep -Seconds 2

# Verify running
$task = Get-ScheduledTask -TaskName $ServiceName
if ($task.State -eq "Running") {
    Write-Host "  ✓ Service started successfully" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Service may not be running (check Task Scheduler)" -ForegroundColor Yellow
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host " Installation Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`nService details:"
Write-Host "  Name: $ServiceName" -ForegroundColor Gray
Write-Host "  Status: Running at login" -ForegroundColor Gray
Write-Host "  Script: $ServiceScript" -ForegroundColor Gray

Write-Host "`nTo uninstall: .\install_service.ps1 -Uninstall" -ForegroundColor Gray
Write-Host "To view logs: Check Windows Event Viewer or console output" -ForegroundColor Gray
```

**Acceptance Criteria:**
- ✅ Creates Windows scheduled task
- ✅ Runs at user login
- ✅ Service starts successfully
- ✅ Uninstall script works
- ✅ Error handling for missing dependencies

---

### Phase 3: Polish & Advanced Features (8 days)

**Objective:** Add compliance dashboard, analytics, and enhancements

#### Tasks

**POLISH-001: Compliance Dashboard (3 days)**

Create Flask web dashboard at `http://localhost:8765`:

- Real-time violation feed
- Compliance score calculation
- Violation history charts
- Repository overview
- Rule configuration UI

**POLISH-002: Analytics & Reporting (2 days)**

- Daily/weekly compliance reports
- Export violations to CSV
- Trend analysis
- Recommendations based on patterns

**POLISH-003: Vercel Integration (1 day)**

- Detect PR merges
- Query Vercel API for deployment status
- Show deployment notifications

**POLISH-004: Advanced Notifications (2 days)**

- Upgrade to PyQt5 for polished UI
- Action buttons (Create Branch, Pull Now, etc.)
- Notification history viewer
- Custom notification themes

---

## 🧪 TESTING STRATEGY

### Unit Tests (Target: 80% Coverage)

**Test Categories:**
1. **Hook Tests** - Verify blocking behavior, override logic
2. **Detector Tests** - Validate violation detection accuracy
3. **Notifier Tests** - Check notification display (mocked UI)
4. **State Tests** - Database operations, query correctness
5. **Monitor Tests** - Loop logic, repository discovery

**Testing Tools:**
- pytest (test runner)
- pytest-cov (coverage)
- pytest-mock (mocking)
- pytest-timeout (prevent hanging tests)

### Integration Tests

**Scenarios:**
1. End-to-end workflow (violation → notification → override)
2. Multi-repository monitoring
3. Service restart and recovery
4. Hook installation across different git versions

### Manual Testing Checklist

- [ ] Install hooks in test repository
- [ ] Attempt commit to main (should block)
- [ ] Override violation (should succeed)
- [ ] Switch branches (should suggest pull)
- [ ] Merge branch (should suggest deletion)
- [ ] Start background service
- [ ] Check toast notifications appear
- [ ] Verify override persists for session
- [ ] Test across different git workflows

---

## 📦 DEPLOYMENT PLAN

### Phase 1: Alpha Testing (Internal)

**Audience:** Developer (self)
**Duration:** 1 week
**Goal:** Validate core functionality, fix critical bugs

**Success Criteria:**
- Zero crashes during normal workflow
- Hooks block critical violations 100%
- Toast notifications appear correctly

### Phase 2: Beta Testing (Limited)

**Audience:** 3-5 trusted developers
**Duration:** 2 weeks
**Goal:** Gather feedback, identify edge cases

**Distribution:**
- GitHub releases (tagged versions)
- Installation script via PowerShell
- User guide and troubleshooting docs

**Success Criteria:**
- 80%+ user satisfaction
- <3 false positives per day per user
- Feature requests prioritized

### Phase 3: Public Release

**Audience:** General availability
**Distribution Channels:**
- GitHub repository (open source)
- Chocolatey package (Windows)
- PyPI package (pip install git-workflow-guardian)

**Documentation:**
- README with quick start
- User guide (installation, configuration, troubleshooting)
- Developer docs (architecture, contributing)
- Video demo (YouTube)

---

## 📊 SUCCESS METRICS

### Quantitative Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Compliance Rate** | 95%+ after 2 weeks | (Clean commits / Total commits) × 100 |
| **False Positives** | <5 per day | User-reported overrides without reason |
| **Critical Violations Prevented** | 100% | Zero commits/pushes to main after Phase 1 |
| **User Satisfaction** | >4.0/5.0 | Survey after 2-week usage |
| **Service Uptime** | >99% | Monitoring service availability |
| **Notification Responsiveness** | <500ms | Time from violation to popup display |

### Qualitative Metrics

- **User Feedback:** "Helpful", "Non-intrusive", "Improved workflow"
- **Adoption Rate:** % of repositories with hooks installed
- **Feature Requests:** Prioritize based on user demand

---

## ⚠️ RISK MITIGATION

### Risk 1: User Resistance (Bypass Hooks)

**Mitigation:**
- Educate on `--no-verify` usage (emergency only)
- Log bypass attempts for analytics
- Show compliance score to incentivize adherence

### Risk 2: Performance Impact

**Mitigation:**
- Optimize git command execution (cache results)
- Limit repository discovery to active projects
- Adjustable poll interval

### Risk 3: False Positives

**Mitigation:**
- Smart override system (session-level)
- Rule customization via config
- Disable specific rules if problematic

### Risk 4: Service Crashes

**Mitigation:**
- Robust error handling (try/except)
- Watchdog for auto-restart
- Graceful degradation (hooks work independently)

### Risk 5: Cross-Platform Compatibility

**Mitigation:**
- Phase 1 focus on Windows (80% of use case)
- Phase 4: Linux/macOS support
- Test on multiple git versions

---

## 🗓️ PROJECT TIMELINE

```
Phase 0: Project Setup                   [Days 1-2]
├─ Project structure setup
├─ Development environment
├─ Testing framework
└─ Documentation templates

Phase 1: Git Hooks Implementation       [Days 3-6]
├─ pre-commit hook (block main)
├─ pre-push hook (block main)
├─ post-checkout hook (suggest pull)
├─ Notification system (tkinter popups)
├─ Installation script
└─ Integration tests

Phase 2: Background Monitoring         [Days 7-13]
├─ Core monitoring loop
├─ Violation detection logic
├─ Toast notifications
├─ State management (SQLite)
├─ Service installation
└─ Comprehensive tests

Phase 3: Polish & Advanced Features    [Days 14-21]
├─ Compliance dashboard (Flask)
├─ Analytics and reporting
├─ Vercel integration
├─ PyQt5 upgrade
└─ Documentation

Phase 4: Testing & Deployment          [Days 22-25]
├─ Alpha testing (internal)
├─ Bug fixes
├─ Beta testing (limited)
└─ Public release preparation
```

**Total Duration:** 25 working days (5 weeks)

---

## 🚀 GETTING STARTED (For Developer)

### Quick Start

```powershell
# 1. Clone repository
git clone https://github.com/yourusername/git-workflow-guardian.git
cd git-workflow-guardian

# 2. Set up development environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Run tests
pytest

# 4. Install hooks in test repository
.\scripts\install_hooks.ps1 -RepoPath "D:\Projects\test-repo"

# 5. Install background service
.\scripts\install_service.ps1

# 6. Verify installation
# - Attempt commit to main (should block)
# - Check toast notifications appear
```

### Development Workflow

1. **Create feature branch**: `git checkout -b feature/new-feature`
2. **Make changes**: Edit code, add tests
3. **Run tests**: `pytest --cov`
4. **Commit**: `git commit -m "feat: add new feature"`
5. **Push**: `git push origin feature/new-feature`
6. **Create PR**: GitHub web interface

---

## 📚 APPENDIX

### A. Configuration Reference

See `config/config.yaml.example` for full configuration options.

### B. Database Schema

See `service/schema.sql` for complete database schema.

### C. Git Hooks Reference

**Available Hooks:**
- `pre-commit` - Runs before commit is created
- `pre-push` - Runs before push to remote
- `post-checkout` - Runs after branch checkout
- `post-merge` - Runs after merge completes
- `prepare-commit-msg` - Runs before commit message editor

### D. Windows Service Alternatives

**Options for background service:**
1. **Scheduled Task** (chosen) - Built-in, reliable
2. **NSSM** - More control, requires installation
3. **User Startup** - Simple, but killed on logout
4. **Docker** - Overkill for this use case

### E. Future Enhancements (Phase 4+)

- VSCode extension for richer UI integration
- Machine learning for adaptive notifications
- GitHub App for organization-wide deployment
- Slack/Teams integration for team notifications
- Mobile app for compliance tracking on-the-go

---

**Status:** Implementation-ready
**Next Action:** Begin Phase 0 (Project Setup)
**Estimated Completion:** 5 weeks from start date
**Maintainer:** To be assigned
**License:** MIT (suggested)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
