# Git Workflow Guardian - Troubleshooting Guide

## Table of Contents

1. [Common Issues](#common-issues)
2. [Hook Problems](#hook-problems)
3. [Service Issues](#service-issues)
4. [Notification Problems](#notification-problems)
5. [Database Issues](#database-issues)
6. [Debug Mode](#debug-mode)
7. [Getting Support](#getting-support)

---

## Common Issues

### Issue: Hooks not running

**Symptoms:**
- Can commit to main without popup
- No violations detected

**Solutions:**

1. **Check if hooks are installed**
   ```bash
   ls -la .git/hooks/
   # Should see: pre-commit, pre-push, post-checkout, post-merge
   ```

2. **Verify hooks are executable**
   ```bash
   # Linux/macOS
   chmod +x .git/hooks/pre-commit
   chmod +x .git/hooks/pre-push

   # Check permissions
   ls -l .git/hooks/pre-commit
   # Should show: -rwxr-xr-x
   ```

3. **Reinstall hooks**
   ```bash
   .\scripts\install_hooks.ps1 -Force
   ```

4. **Check Python path in hooks**
   ```bash
   # Edit .git/hooks/pre-commit
   # Change python3 to python if needed

   # Test Python is accessible
   python3 --version
   # or
   python --version
   ```

---

### Issue: Python ModuleNotFoundError

**Symptoms:**
```
ModuleNotFoundError: No module named 'yaml'
```

**Solutions:**

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate

   # Then reinstall
   pip install -r requirements.txt
   ```

3. **Check Python version**
   ```bash
   python --version
   # Should be 3.8 or higher
   ```

---

### Issue: Hooks work but notifications don't appear

**Symptoms:**
- Hooks block commits
- But no popup window shows

**Solutions:**

1. **Check if tkinter is installed**
   ```python
   python -c "import tkinter; print('OK')"
   ```

2. **Install tkinter**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-tk

   # Fedora
   sudo dnf install python3-tkinter

   # macOS (should be included)
   # Windows (should be included)
   ```

3. **Check display environment**
   ```bash
   # Linux
   echo $DISPLAY
   # Should output something like :0 or :1

   # If empty, set it
   export DISPLAY=:0
   ```

---

## Hook Problems

### Issue: Hook blocks commit but shouldn't

**Symptoms:**
- On feature branch but hook blocks anyway
- Branch name is valid but gets flagged

**Solutions:**

1. **Check current branch**
   ```bash
   git branch --show-current
   ```

2. **Debug hook manually**
   ```bash
   # Run pre-commit hook manually
   bash .git/hooks/pre-commit
   echo $?  # Should be 0 on feature branch, 1 on main
   ```

3. **Check for typos in branch name**
   ```bash
   # Ensure branch follows pattern
   # claude/feature-name-sessionId
   ```

4. **Clear overrides**
   ```bash
   sqlite3 ~/.git-workflow-guardian/state.db "DELETE FROM overrides;"
   ```

---

### Issue: Override doesn't persist

**Symptoms:**
- Click "No" to override
- But next commit still shows popup

**Solutions:**

1. **Check database exists**
   ```bash
   ls -la ~/.git-workflow-guardian/
   # Should see state.db
   ```

2. **Verify override was saved**
   ```bash
   sqlite3 ~/.git-workflow-guardian/state.db "SELECT * FROM overrides;"
   ```

3. **Check session_id matches**
   - Override is tied to branch name
   - If you switch branches, override clears
   - This is intentional behavior

---

### Issue: Can't bypass hook in emergency

**Symptoms:**
- Need to commit to main urgently
- Hook blocks even with override

**Solutions:**

1. **Use --no-verify flag**
   ```bash
   git commit --no-verify -m "emergency fix"
   git push --no-verify
   ```

2. **Temporarily remove hook**
   ```bash
   mv .git/hooks/pre-commit .git/hooks/pre-commit.bak
   git commit -m "emergency fix"
   mv .git/hooks/pre-commit.bak .git/hooks/pre-commit
   ```

3. **Disable rule in config**
   ```yaml
   # config/rules.yaml
   rules:
     commit_to_main:
       enabled: false
   ```

---

## Service Issues

### Issue: Background service not starting

**Symptoms:**
- No toast notifications
- Service not in Task Scheduler

**Solutions:**

1. **Check Task Scheduler (Windows)**
   ```powershell
   Get-ScheduledTask -TaskName "GitWorkflowGuardian"
   ```

2. **Check service status**
   ```powershell
   Get-ScheduledTask -TaskName "GitWorkflowGuardian" | Get-ScheduledTaskInfo
   ```

3. **Reinstall service**
   ```powershell
   .\scripts\install_service.ps1 -Uninstall
   .\scripts\install_service.ps1
   ```

4. **Run service manually (debug)**
   ```bash
   python service/monitor.py
   # Should see: "Git Workflow Guardian monitoring service started"
   ```

---

### Issue: Service crashes or stops

**Symptoms:**
- Service was working, now stopped
- Toast notifications stopped appearing

**Solutions:**

1. **Check logs**
   ```bash
   # If running manually
   python service/monitor.py
   # Look for error messages
   ```

2. **Check for permission issues**
   ```bash
   # Ensure service can access repos
   ls -la /path/to/repos
   ```

3. **Reduce poll interval**
   ```yaml
   # config/rules.yaml
   monitoring:
     poll_interval: 60  # Increase from 30 to reduce load
   ```

4. **Limit search paths**
   ```yaml
   monitoring:
     repos:
       auto_discover: false
       manual_repos:
         - "D:/Projects/important-repo"
   ```

---

### Issue: Service uses too much CPU/memory

**Symptoms:**
- High CPU usage
- System slow when service running

**Solutions:**

1. **Increase poll interval**
   ```yaml
   monitoring:
     poll_interval: 120  # Check every 2 minutes
   ```

2. **Disable auto-discovery**
   ```yaml
   repos:
     auto_discover: false
     manual_repos:
       - "D:/Projects/repo1"
       - "D:/Projects/repo2"
   ```

3. **Exclude large directories**
   ```yaml
   repos:
     search_paths:
       - "D:/Projects"  # Instead of entire drive
   ```

---

## Notification Problems

### Issue: Toast notifications don't appear

**Symptoms:**
- Service running
- Violations detected (check logs)
- But no toast windows

**Solutions:**

1. **Check tkinter**
   ```python
   python -c "import tkinter; tkinter.Tk()"
   # Should open empty window
   ```

2. **Check notification settings (Windows)**
   - Settings → System → Notifications
   - Ensure notifications are enabled

3. **Run service manually to see errors**
   ```bash
   python service/monitor.py
   ```

4. **Check display environment (Linux)**
   ```bash
   export DISPLAY=:0
   python service/monitor.py
   ```

---

### Issue: Notifications appear but are blank

**Symptoms:**
- Toast window appears
- But no text visible

**Solutions:**

1. **Check font installation**
   - Windows: Should have Segoe UI
   - Linux: Install system fonts

2. **Update tkinter**
   ```bash
   pip install --upgrade tk
   ```

3. **Check rule configuration**
   ```yaml
   rules:
     test_locally:
       message: "Your message here"
       action: "Your action here"
       why: "Your reason here"
   ```

---

## Database Issues

### Issue: Database locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

1. **Close other connections**
   ```bash
   # Find processes using database
   lsof ~/.git-workflow-guardian/state.db

   # Kill if necessary
   kill <PID>
   ```

2. **Stop service temporarily**
   ```powershell
   Stop-ScheduledTask -TaskName "GitWorkflowGuardian"
   # Do your operation
   Start-ScheduledTask -TaskName "GitWorkflowGuardian"
   ```

3. **Reset database**
   ```bash
   # CAUTION: Deletes all data
   rm ~/.git-workflow-guardian/state.db
   python -c "from service.state import StateManager; StateManager().initialize()"
   ```

---

### Issue: Corrupted database

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions:**

1. **Backup and rebuild**
   ```bash
   # Backup
   cp ~/.git-workflow-guardian/state.db ~/state.db.bak

   # Try to dump
   sqlite3 ~/state.db.bak .dump > dump.sql

   # Recreate
   rm ~/.git-workflow-guardian/state.db
   sqlite3 ~/.git-workflow-guardian/state.db < dump.sql
   ```

2. **Start fresh**
   ```bash
   # CAUTION: Loses all history
   rm ~/.git-workflow-guardian/state.db
   python -c "from service.state import StateManager; StateManager().initialize()"
   ```

---

## Debug Mode

### Enable verbose logging

```python
# In service/monitor.py, change logging level
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Manual testing

```bash
# Test violation detection
python -c "
from service.detector import ViolationDetector
from service.config import ConfigManager
from pathlib import Path

detector = ViolationDetector(ConfigManager())
print(detector.get_current_branch(Path('.')))
print(detector.has_uncommitted_changes(Path('.')))
"
```

### Database inspection

```bash
# View all violations
sqlite3 ~/.git-workflow-guardian/state.db "SELECT * FROM violations ORDER BY timestamp DESC LIMIT 10;"

# View active overrides
sqlite3 ~/.git-workflow-guardian/state.db "SELECT * FROM overrides;"

# View repositories
sqlite3 ~/.git-workflow-guardian/state.db "SELECT * FROM repositories;"

# Get stats
sqlite3 ~/.git-workflow-guardian/state.db "SELECT rule_name, COUNT(*) as count FROM violations GROUP BY rule_name;"
```

---

## Getting Support

### Before asking for help

1. **Check logs**
   - Run service manually: `python service/monitor.py`
   - Check for error messages

2. **Verify configuration**
   - Validate YAML: `python -c "import yaml; yaml.safe_load(open('config/rules.yaml'))"`

3. **Test components individually**
   - Hooks: `bash .git/hooks/pre-commit`
   - Detector: See manual testing above
   - Database: Check with sqlite3

### Reporting issues

Include in your bug report:

1. **Environment**
   - OS: Windows/Linux/macOS
   - Python version: `python --version`
   - Git version: `git --version`

2. **Error message**
   - Full traceback
   - Steps to reproduce

3. **Configuration**
   - Relevant parts of `config/rules.yaml`
   - Hook installation method

4. **Logs**
   - Output from manual service run
   - Database contents (if relevant)

### Where to get help

- **GitHub Issues:** [Report bugs](https://github.com/yourusername/git-workflow-guardian/issues)
- **GitHub Discussions:** [Ask questions](https://github.com/yourusername/git-workflow-guardian/discussions)
- **Documentation:** [Full docs](https://github.com/yourusername/git-workflow-guardian/wiki)

---

## Emergency Reset

If everything is broken:

```bash
# 1. Uninstall service
.\scripts\install_service.ps1 -Uninstall

# 2. Remove all hooks
rm .git/hooks/pre-commit
rm .git/hooks/pre-push
rm .git/hooks/post-checkout
rm .git/hooks/post-merge
rm .git/hooks/notifier.py

# 3. Reset database
rm -rf ~/.git-workflow-guardian/

# 4. Reinstall from scratch
cd git-workflow-guardian
git pull origin main
pip install -r requirements.txt --upgrade
.\scripts\install_hooks.ps1
.\scripts\install_service.ps1
```

---

**Still having issues? [Open an issue](https://github.com/yourusername/git-workflow-guardian/issues) and we'll help!**
