# Git Workflow Guardian - User Guide

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Understanding Notifications](#understanding-notifications)
6. [Overrides](#overrides)
7. [FAQ](#faq)

---

## Installation

### Prerequisites

- **Python 3.8+** - Check with `python --version`
- **Git** - Check with `git --version`
- **Windows, Linux, or macOS**

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/git-workflow-guardian.git
cd git-workflow-guardian
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Install Git Hooks

```powershell
# Windows (PowerShell)
.\scripts\install_hooks.ps1 -RepoPath "C:\Your\Project\Path"

# Linux/macOS
./scripts/install_hooks.sh /path/to/your/project
```

### Step 4: Install Background Service (Optional)

```powershell
# Windows only
.\scripts\install_service.ps1
```

---

## Quick Start

### Basic Workflow

1. **Work on feature branches**
   ```bash
   git checkout -b claude/feature-name-[sessionId]
   ```

2. **Make your changes**
   ```bash
   # Edit files
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push to remote**
   ```bash
   git push origin claude/feature-name-[sessionId]
   ```

4. **Create Pull Request**
   - Use GitHub web interface
   - Request review from team members
   - Merge after approval

5. **Clean up**
   ```bash
   git checkout main
   git pull origin main
   git branch -d claude/feature-name-[sessionId]
   ```

---

## Configuration

### Rules Configuration

Edit `config/rules.yaml` to customize workflow rules:

```yaml
rules:
  commit_to_main:
    severity: critical
    enabled: true
    blocking: true

  branch_naming:
    severity: warning
    enabled: true
    pattern: "^claude/[a-z0-9-]+-[A-Za-z0-9]{24}$"

  test_locally:
    severity: suggestion
    enabled: true
    check_url: "http://localhost:3011"

monitoring:
  poll_interval: 30  # Check every 30 seconds
  repos:
    auto_discover: true
    search_paths:
      - "D:/Projects"
      - "C:/Users/YourName/Projects"
```

### Severity Levels

- **CRITICAL** - Blocks operations, shows popup dialog
- **WARNING** - Shows non-blocking popup
- **SUGGESTION** - Shows toast notification

### Customizing Notifications

```yaml
notifications:
  critical:
    type: popup
    blocking: true
    timeout: null  # No auto-dismiss

  warning:
    type: popup
    blocking: false
    timeout: 30  # Auto-dismiss after 30s

  suggestion:
    type: toast
    timeout: 10  # Auto-dismiss after 10s
```

---

## Usage

### Working with Protected Branches

**✅ DO:**
- Create feature branches for all work
- Use PR workflow for code review
- Keep main branch clean

**❌ DON'T:**
- Commit directly to main
- Push to main without PR
- Bypass hooks with `--no-verify` unless emergency

### Branch Naming Convention

Follow this pattern:
```
claude/[feature-name]-[sessionId]
```

Examples:
- `claude/add-user-auth-011CV4zUPzgSkobBUdcow2EN`
- `claude/fix-login-bug-abc123def456ghi789jkl012`

### Emergency Bypass

If you absolutely must bypass hooks:

```bash
# Bypass pre-commit hook
git commit --no-verify -m "emergency fix"

# Bypass pre-push hook
git push --no-verify
```

**⚠️ Use sparingly! Overuse defeats the purpose of workflow protection.**

---

## Understanding Notifications

### Critical Violations (Blocking)

**Commit to Main:**
- **Trigger:** Attempting to commit while on main/master branch
- **Action:** Create a feature branch first
- **Override:** Click "No" to proceed anyway (session-level)

**Push to Main:**
- **Trigger:** Attempting to push to main/master branch
- **Action:** Create feature branch and PR instead
- **Override:** Click "No" to proceed anyway

### Warnings (Non-blocking)

**Branch Naming:**
- **Trigger:** Branch name doesn't match pattern
- **Action:** Rename branch to follow convention
- **Dismisses:** After 30 seconds

### Suggestions (Toast)

**Pull Before Work:**
- **Trigger:** Main branch is behind remote
- **Action:** Run `git pull origin main`
- **Dismisses:** After 10 seconds

**Test Locally:**
- **Trigger:** Uncommitted changes but dev server not running
- **Action:** Start dev server with `npm run dev`
- **Dismisses:** After 10 seconds

**Delete Merged Branch:**
- **Trigger:** Branch has been merged but not deleted
- **Action:** Run `git branch -d [branch-name]`
- **Dismisses:** After 10 seconds

---

## Overrides

### Session-Level Overrides

When you override a critical violation, it applies for the current session (until you switch branches).

**Example:**
1. Attempt commit to main → Popup appears
2. Click "No" (don't block) → Override saved
3. Next commit to main → No popup (override active)
4. Switch to feature branch → Override cleared
5. Switch back to main → Popup appears again

### Time-Based Overrides

Configure in `config/rules.yaml`:

```yaml
overrides:
  mode: time-based  # Change from 'session'
  time_duration: 3600  # 1 hour in seconds
```

### Permanent Overrides

Disable a rule entirely:

```yaml
rules:
  commit_to_main:
    enabled: false  # Disables this rule
```

---

## FAQ

### Q: How do I uninstall hooks from a repository?

```bash
# Simply delete the hook files
rm .git/hooks/pre-commit
rm .git/hooks/pre-push
rm .git/hooks/post-checkout
rm .git/hooks/post-merge
```

### Q: How do I stop the background service?

```powershell
# Windows
.\scripts\install_service.ps1 -Uninstall

# Or manually in Task Scheduler
# Search "Task Scheduler" → Find "GitWorkflowGuardian" → Delete
```

### Q: Can I customize violation messages?

Yes! Edit `config/rules.yaml`:

```yaml
rules:
  commit_to_main:
    message: "Your custom message here"
    action: "Your suggested action"
    why: "Your explanation"
```

### Q: How do I see my compliance stats?

```bash
# Check the database
python -c "from service.state import StateManager; print(StateManager().get_compliance_stats())"
```

### Q: Can I use this in a team setting?

Yes! Each team member should:
1. Clone the repository
2. Install hooks in their local repos
3. (Optional) Install background service

Consider creating a shared config file for team-wide rules.

### Q: What if I don't have Python installed?

You must install Python 3.8+ from [python.org](https://www.python.org/downloads/).
Git hooks require Python to run the notifier script.

### Q: Does this work on macOS/Linux?

Yes! All core functionality works cross-platform. Some features:
- Git hooks: ✅ Full support
- Background service: ⚠️ Windows Task Scheduler script provided, adapt for cron/systemd on Linux

### Q: How do I update to the latest version?

```bash
cd git-workflow-guardian
git pull origin main
pip install -r requirements.txt --upgrade

# Reinstall hooks (if needed)
.\scripts\install_hooks.ps1 -Force
```

---

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/git-workflow-guardian/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/git-workflow-guardian/discussions)
- **Documentation:** [GitHub Wiki](https://github.com/yourusername/git-workflow-guardian/wiki)

---

**Made with ❤️ by the Git Workflow Guardian team**
