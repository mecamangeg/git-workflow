# Claude Teleport Feature - Workflow Integration Analysis

## 🔍 Discovery: The `claude --teleport` Command

### What It Actually Does
```bash
# Example from Windows
D:\Projects\kliis>claude --teleport session_011CV51ciwJ6GFpnUvWFwEku
```

**This command teleports the ENTIRE conversation from Claude Code web to your local terminal.**

When you run teleport:
1. The full conversation history is copied to your terminal
2. Claude context and task understanding is preserved
3. Claude continues working in the same branch locally
4. You interact with Claude in your terminal instead of the browser
5. All file changes happen locally (not in cloud VM)

**This is NOT just checking out a branch** - it's bringing the whole Claude session to your local environment!

### Current Problem

**Our sync daemon doesn't know about teleport!**

If a user:
1. Starts task in Claude Code web
2. Claude creates branch `claude/task-session_011CV4zUPzgSkobBUdcow2EN`
3. User clicks "Open in CLI" → runs teleport command
4. User is now working in local terminal on that branch
5. **CONFLICT:** Sync daemon might also try to checkout/pull that branch!

---

## 🔄 Two Valid Workflows

### Workflow A: Auto-Sync (What We Implemented)
```
Claude Web → Push Branch → Sync Daemon Auto-Checkout → User Tests Locally
```
**User Action:** None (fully automated)
**Best For:** Quick testing, reviewing Claude's work

### Workflow B: Teleport (Not Implemented Yet)
```
Claude Web → Push Branch → User Runs Teleport → User Works in CLI
```
**User Action:** `claude --teleport session_XXX`
**Best For:** Complex changes, manual refinement, CLI tools

---

## ⚠️ Conflicts Between Workflows

### Scenario: User Teleports While Sync Daemon Running

```
Time    | Claude Web           | Sync Daemon          | User Local CLI
--------|---------------------|----------------------|-------------------
T=0     | Creates branch      |                      |
T=10    | Pushes commits      |                      |
T=20    |                     | Detects branch       |
T=30    |                     | Starts checkout      | User runs teleport
T=40    |                     | Checks out branch    | Teleport connects
T=45    |                     |                      | User edits files
T=50    |                     | Detects updates?     | Uncommitted changes
T=60    |                     | Tries to pull?       | 💥 CONFLICT!
```

**Problem:** Both sync daemon and teleport session working on same branch simultaneously.

---

## 🎯 Required Changes

### 1. Detect Active Teleport Sessions

**Option A: Check for Claude CLI Process**
```python
def is_teleport_active(repo_path: Path) -> bool:
    """Check if a Claude teleport session is active"""
    # Check for running claude CLI process
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        # Look for 'claude --teleport' or 'claude' processes
        for line in result.stdout.split('\n'):
            if 'claude' in line and str(repo_path) in line:
                return True
        return False
    except:
        return False
```

**Option B: Check for Teleport Lock File**
```python
def is_teleport_active(repo_path: Path) -> bool:
    """Check if a Claude teleport session is active"""
    # Claude CLI might create a lock file
    lock_file = repo_path / '.claude' / 'teleport.lock'
    if lock_file.exists():
        # Check if process is still alive
        try:
            pid = int(lock_file.read_text())
            # Check if process exists
            os.kill(pid, 0)  # Doesn't kill, just checks
            return True
        except:
            # Process dead, remove stale lock
            lock_file.unlink()
    return False
```

**Option C: Session ID Matching**
```python
def is_teleport_active(repo_path: Path, session_id: str) -> bool:
    """Check if specific session is being teleported to"""
    # Check git branch name for session ID
    current_branch = get_current_branch(repo_path)

    # Branch format: claude/task-session_011CV4zUPzgSkobBUdcow2EN
    if session_id in current_branch:
        # Check for recent activity
        if has_recent_uncommitted_changes(repo_path, within_seconds=300):
            return True

    return False
```

### 2. Update Sync Daemon to Respect Teleport

```python
# In sync_daemon.py

async def _check_repository(self, repo_config: dict):
    """Check single repository for Claude branch changes"""
    repo_path = Path(repo_config['path']).expanduser()

    # NEW: Check for active teleport session
    if self._is_teleport_active(repo_path):
        logger.info(f"Skipping {repo_path} - teleport session active")

        # Send notification once
        if not self._teleport_notified.get(str(repo_path)):
            await self.notification_queue.add_notification(
                type='info',
                severity='info',
                title='Teleport Session Active',
                message=f'Sync paused for {repo_path.name} - working in CLI',
                actions=[],
                repo_path=str(repo_path)
            )
            self._teleport_notified[str(repo_path)] = True

        return

    # Clear teleport notification flag
    self._teleport_notified[str(repo_path)] = False

    # Continue with normal sync...
```

### 3. Add Configuration Option

```yaml
# config/sync.yaml

sync:
  # Teleport detection
  teleport_detection:
    enabled: true
    methods:
      - process_check   # Check for 'claude' processes
      - lock_file       # Check for .claude/teleport.lock
      - activity_check  # Check for recent uncommitted changes

    # Pause sync when teleport detected
    pause_on_teleport: true

    # Resume sync after teleport inactive for N seconds
    resume_delay: 60
```

### 4. Update CLI Mode Detector

```python
# In cli_mode_detector.py (Phase 6)

class CLIModeDetector:
    """Detects when user is working in CLI mode"""

    def is_cli_mode_active(self, repo_path: Path) -> bool:
        """Check if user is in CLI mode"""
        # Check for teleport session
        if self._is_teleport_active(repo_path):
            return True

        # Check for git lock file
        if (repo_path / '.git/index.lock').exists():
            return True

        # Check for uncommitted changes (existing logic)
        if self.has_uncommitted_changes(repo_path):
            mtime = self.get_worktree_mtime(repo_path)
            if time.time() - mtime < 300:  # 5 minutes
                return True

        return False

    def _is_teleport_active(self, repo_path: Path) -> bool:
        """Check for active teleport session"""
        # Combine multiple detection methods
        return (
            self._check_teleport_process(repo_path) or
            self._check_teleport_lock_file(repo_path) or
            self._check_session_activity(repo_path)
        )
```

---

## 📋 Updated Workflow Logic

### Decision Tree: Should Sync Daemon Act?

```
New Claude branch detected
    ↓
Is teleport session active?
    ↓
   YES → Skip sync
    |    Send notification: "Teleport active, sync paused"
    |    Continue monitoring
    ↓
   NO → Is CLI mode active? (uncommitted changes)
    ↓
   YES → Skip sync
    |    Send notification: "CLI mode detected, sync paused"
    ↓
   NO → Safe to sync
         ↓
         Proceed with auto-sync
```

---

## 🎨 Enhanced User Experience

### Notification Types

**Teleport Detected:**
```
Title: "Teleport Session Active"
Message: "Sync paused for my-app - you're working in CLI"
Actions: [View in Terminal] [Resume Sync]
```

**Teleport Ended:**
```
Title: "Teleport Session Ended"
Message: "Sync resumed for my-app"
Actions: [View Changes] [Dismiss]
```

**Conflict Warning:**
```
Title: "Sync Conflict"
Message: "Cannot sync - teleport session has uncommitted changes"
Actions: [Commit Changes] [Stash Changes] [Abort Sync]
```

---

## 🔧 Implementation Strategy

### Phase 6 Update: CLI & Teleport Detection

**Original Plan:** Detect CLI mode (uncommitted changes)
**Updated Plan:** Detect CLI mode AND teleport sessions

**New Tasks:**

**TELEPORT-001: Teleport Detection Methods** (1 day)
- Implement process detection
- Implement lock file detection
- Implement session activity detection
- Combine methods for reliability

**TELEPORT-002: Sync Daemon Integration** (0.5 days)
- Update sync daemon to check teleport status
- Pause sync when teleport active
- Send appropriate notifications
- Resume when teleport ends

**TELEPORT-003: Configuration & Documentation** (0.5 days)
- Add teleport detection config
- Document teleport workflow
- Add troubleshooting guide

---

## 🤔 Open Questions

### Q1: Does `claude --teleport` create a lock file?
**Need to test:** Run teleport and check for:
- `.claude/` directory
- Lock files
- Process identifiers

### Q2: What is the session ID format?
**From your example:** `session_011CV4zUPzgSkobBUdcow2EN`
**Pattern:** `session_` + alphanumeric ID
**Usage:** Can match against branch names

### Q3: Can teleport and web session be active simultaneously?
**Scenario:** User teleports but also has web session open
**Behavior:** Need to understand which takes precedence

### Q4: Does teleport work on existing local branch?
**Option A:** Teleport checks out the branch for you
**Option B:** You must be on the correct branch first
**Impact:** Affects conflict detection logic

---

## 💡 Recommended Approach

### Immediate Fix (Can implement now without testing)

1. **Add basic teleport detection to existing CLI mode detector:**
   ```python
   # Simple heuristic: If branch name contains session ID AND has recent activity
   if 'session_' in current_branch and has_recent_activity:
       # Likely in teleport mode
       return True
   ```

2. **Use existing uncommitted changes detection:**
   - Already implemented in Phase 1
   - Works for both teleport and manual CLI work
   - Safe fallback

3. **Add notification when sync paused:**
   - Inform user why sync was skipped
   - Provide option to resume manually

### Full Implementation (After testing teleport)

1. **Test `claude --teleport` command:**
   - What files/processes does it create?
   - How to detect it's active?
   - How to detect it ended?

2. **Implement proper detection:**
   - Based on actual behavior
   - Multiple detection methods for reliability

3. **Update all relevant components:**
   - Sync daemon
   - CLI mode detector
   - Notification system

---

## 📝 Documentation Updates Needed

### User Guide Updates

**Add section: "Working with Teleport"**
```markdown
## Using Teleport with Auto-Sync

When you use "Open in CLI" in Claude Code web:

1. Click "Open in CLI" in Claude Code web
2. Run: `claude --teleport session_XXX`
3. Sync daemon will detect you're in CLI mode
4. Auto-sync will pause automatically
5. Work normally in your terminal
6. When done, exit Claude CLI
7. Sync daemon will resume automatically

**Note:** Sync daemon respects your CLI work and won't interfere.
```

### Troubleshooting Guide Updates

**Add section: "Sync Paused During Teleport"**
```markdown
## Sync Paused During Teleport

**Symptom:** Notification says "Teleport session active, sync paused"

**Cause:** You're using `claude --teleport` or have uncommitted changes

**Solution:**
- This is normal and expected
- Sync will resume when you exit CLI
- To force sync: commit or stash your changes
```

---

## ✅ Action Items

### High Priority (Do Now)
1. ☐ Update Phase 6 plan to include teleport detection
2. ☐ Add basic teleport awareness to existing code
3. ☐ Update documentation with teleport workflow
4. ☐ Add teleport detection config options

### Medium Priority (After Testing)
1. ☐ Test actual `claude --teleport` behavior
2. ☐ Implement proper detection based on findings
3. ☐ Add teleport-specific notifications
4. ☐ Create integration tests

### Low Priority (Nice to Have)
1. ☐ Add teleport session dashboard view
2. ☐ Track teleport session history
3. ☐ Metrics: teleport vs auto-sync usage

---

## 🎯 Conclusion

**Current Status:** Teleport workflow NOT fully integrated

**Risk Level:** MEDIUM
- If user never uses teleport: No issue
- If user uses teleport: Possible conflicts

**Recommended Action:**
1. Update Phase 6 to include teleport detection
2. Add basic detection using uncommitted changes (already works)
3. Test actual teleport behavior when available
4. Implement proper detection based on findings

**Timeline:** Add 1 day to Phase 6 for proper teleport support

---

**Created:** 2025-11-13
**Status:** Analysis complete, implementation pending
**Priority:** HIGH (core workflow feature)
