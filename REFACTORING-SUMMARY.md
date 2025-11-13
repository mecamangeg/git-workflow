# Automation Refactoring Summary

**Goal:** Make automation reliably serve the latest commit when Claude Code web generates random branch names for each response.

---

## 🎯 Core Problem

**Current Limitation:**
- Automation watches ONE branch (e.g., `claude/feature-ABC`)
- If Claude creates a NEW branch for next response (e.g., `claude/feature-XYZ`)
- Automation still watches old branch `claude/feature-ABC`
- Latest code on `claude/feature-XYZ` never gets deployed

**Real-World Example:**
```
User request 1 → claude/add-login-s1a2b3c
User request 2 → claude/add-logout-d4e5f6   ← New branch!
User request 3 → claude/fix-bugs-g7h8i9     ← Newer branch!

Current behavior: Stuck on claude/add-login-s1a2b3c
Desired behavior: Auto-switch to claude/fix-bugs-g7h8i9 (latest)
```

---

## ✅ Solution: "Latest Mode"

**New tracking mode that:**
1. Monitors ALL Claude branches simultaneously
2. Finds the branch with the most recent commit (by timestamp)
3. Automatically switches to that branch
4. Pulls and restarts server
5. Continues monitoring for even newer commits

**Result:** Always serves the absolute latest commit, regardless of which branch it's on.

---

## 🔧 Key Configuration Change

### New Option: `branch_tracking_mode`

```yaml
# .sync.yaml

# Branch Tracking Mode (NEW!)
branch_tracking_mode: 'latest'  # or 'sticky'

# 'latest' - Always switch to branch with newest commit (RECOMMENDED for Claude Code web)
# 'sticky' - Stay on current branch only (original behavior)

# Minimum seconds between branch switches (prevents thrashing)
min_branch_switch_interval: 30

# Branch patterns to monitor
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'

# Rest of config...
auto_start_server: true
run_tests: false
```

---

## 📊 Mode Comparison

### Sticky Mode (Original)
```
✓ Fast (only checks one branch)
✓ Simple
✗ Doesn't handle branch switching
✗ Gets stuck on old branches
✗ Won't work with Claude's random branch names

Use case: Single stable branch, traditional development
```

### Latest Mode (NEW - Recommended)
```
✓ Handles random branch names
✓ Always serves latest commit
✓ Works across multiple branches
✓ Perfect for Claude Code web workflow
~ Slightly more git operations

Use case: Claude Code on the web with random branch names
```

---

## 🚀 Implementation Details

### Algorithm (Latest Mode)

```python
Every [interval] seconds:
    1. git fetch --all --prune
    2. Get all remote branches matching patterns (claude/*, ai/*)
    3. For each branch:
       - Get latest commit timestamp: git log -1 --format=%ct origin/{branch}
    4. Sort branches by commit timestamp (newest first)
    5. If newest branch != current branch:
       - Check time difference > min_branch_switch_interval
       - If yes:
           a. Stash local changes (if any)
           b. git checkout {newest_branch}
           c. git pull origin {newest_branch}
           d. Kill old dev server
           e. Start new dev server
           f. Log branch switch
    6. Else if current branch has new commits:
       - git pull
       - Restart server
```

### Safety Features

1. **Local changes protection:**
   - Automatically stashes uncommitted changes before switching
   - Logged so user can recover with `git stash pop`

2. **Branch switch throttling:**
   - Won't switch if time difference < `min_branch_switch_interval` (default 30s)
   - Prevents thrashing when multiple sessions active

3. **Error handling:**
   - Gracefully handles deleted branches
   - Falls back to next newest branch if primary fails
   - Logs all errors for debugging

4. **Notification:**
   - Clear logs when switching branches
   - Shows old branch → new branch
   - Explains why switch occurred

---

## 📝 New Config Options

### Complete `.sync.yaml` Example

```yaml
# Branch Tracking Configuration
branch_tracking_mode: 'latest'        # NEW: 'latest' or 'sticky'
min_branch_switch_interval: 30        # NEW: Seconds between switches

# Branch Patterns
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'

# Testing
run_tests: false                      # Set true to run tests before restart
test_timeout: 300

# Dev Server
start_dev_server: true
auto_start_server: true               # CRITICAL: Must be true

# Custom Commands
dev_commands:
  next: "npm run dev -- -p 3011"      # Custom port
  django: "python manage.py runserver 0.0.0.0:8000"

test_commands:
  next: "npm test"
  django: "python manage.py test"
```

---

## 🎬 Example Flow (Latest Mode)

### Scenario: User makes 3 requests to Claude

```
10:00:00 - User: "Add login page"
           Claude pushes to: claude/add-login-abc123

           Automation detects:
           ✓ New branch: claude/add-login-abc123
           ✓ Latest commit: 10:00:00
           → Switch to claude/add-login-abc123
           → Pull and restart server

           Server now shows: Login page ✅

10:02:00 - User: "Add logout button"
           Claude pushes to: claude/add-logout-xyz789  ← NEW BRANCH!

           Automation detects:
           ✓ Multiple branches found:
             - claude/add-login-abc123 (last commit: 10:00:00)
             - claude/add-logout-xyz789 (last commit: 10:02:00) ← NEWEST
           ✓ Time diff: 120s > 30s threshold
           → Switch to claude/add-logout-xyz789
           → Pull and restart server

           Server now shows: Login + Logout ✅

10:05:00 - User: "Fix button styling"
           Claude pushes to: claude/fix-styling-qwe456  ← ANOTHER NEW BRANCH!

           Automation detects:
           ✓ Multiple branches found:
             - claude/add-login-abc123 (10:00:00)
             - claude/add-logout-xyz789 (10:02:00)
             - claude/fix-styling-qwe456 (10:05:00) ← NEWEST
           ✓ Time diff: 180s > 30s threshold
           → Switch to claude/fix-styling-qwe456
           → Pull and restart server

           Server now shows: Login + Logout + Fixed styling ✅
```

**Result:** Server always reflects the absolute latest code, no matter how many branches Claude creates.

---

## 🔍 Edge Cases Handled

### 1. Concurrent Sessions
```
Session A pushes at 10:00
Session B pushes at 10:01
Session A pushes again at 10:02

Result: Automation follows Session A (most recent commit at 10:02)
```

### 2. Out-of-Order Fetches
```
Branch A pushed at 10:00 (fetched at 10:05 due to network delay)
Branch B pushed at 10:03 (fetched immediately)

Result: Uses commit timestamp (10:03 > 10:00), not fetch time
        Correctly identifies Branch B as newer
```

### 3. Deleted Branches
```
Automation tries to switch to branch X
Branch X was deleted by Claude

Result: Error caught, falls back to next newest branch
        Logs warning for user
```

### 4. Local Changes
```
User has uncommitted changes in working directory
Automation needs to switch branches

Result: Automatically stashes changes
        Logs: "Changes stashed, recover with: git stash pop"
        Proceeds with branch switch
```

---

## 🎯 Recommended Configuration

### For Claude Code on the Web

```yaml
# .sync.yaml - Optimized for Claude Code web

branch_tracking_mode: 'latest'        # Always follow newest commit
min_branch_switch_interval: 30        # Min 30s between switches
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'
auto_start_server: true               # Auto restart server
run_tests: false                      # Skip tests (faster)
dev_commands:
  next: "npm run dev -- -p 3011"
```

**Start Command:**
```bash
python mini_sync.py --watch --interval 20
```

**Result:**
- Checks every 20 seconds for new commits on ANY Claude branch
- Automatically switches to branch with newest commit
- Pulls and restarts server
- Server always shows latest code within 20-50 seconds

---

## 📈 Performance Impact

### Sticky Mode (Original)
- Checks: 1 branch
- Git operations: ~2 per check (fetch + log)
- Time: ~1-2 seconds per check

### Latest Mode (New)
- Checks: N branches (typically 3-10)
- Git operations: ~2 + N per check
- Time: ~2-5 seconds per check

**Optimization:** Branch metadata cached, only updates on hash change.

**Recommendation:**
- Use 20-30 second intervals with Latest mode
- Use 10 second intervals with Sticky mode (if needed)

---

## 🚦 Migration Path

### For Existing Users

**Option 1: Opt-in (Safer)**
```yaml
# Keep original behavior by default
branch_tracking_mode: 'sticky'  # or omit (defaults to sticky)

# Users can enable latest mode when ready:
branch_tracking_mode: 'latest'
```

**Option 2: Opt-out (Better UX)**
```yaml
# Enable latest mode by default
# (best for Claude Code web workflow)

# Users can revert to original behavior if needed:
branch_tracking_mode: 'sticky'
```

**Recommendation:** Option 2 with clear documentation.

---

## 📚 Documentation Updates Needed

1. **CODESPACES-SETUP.md**
   - Add section on branch tracking modes
   - Explain when to use each mode
   - Show latest mode examples

2. **MINI-VERSION-README.md**
   - Document new config options
   - Add algorithm explanation
   - Include troubleshooting for mode switching

3. **AI-SETUP-INSTRUCTIONS.md**
   - Guide AI assistants on recommending correct mode
   - When to suggest sticky vs latest
   - How to debug branch switching issues

4. **.sync.yaml.example**
   - Add new options with comments
   - Set latest mode as default
   - Include examples for both modes

---

## ✅ Implementation Checklist

### Phase 1: Core Functionality
- [ ] Add `find_latest_claude_branch()` method
- [ ] Add `get_branch_timestamp()` method
- [ ] Add `should_switch_branch()` logic
- [ ] Add `switch_and_sync_branch()` method
- [ ] Update watch loop to support modes

### Phase 2: Safety Features
- [ ] Add local changes detection
- [ ] Add automatic stashing
- [ ] Add branch switch throttling
- [ ] Add deleted branch handling
- [ ] Add comprehensive error handling

### Phase 3: Configuration
- [ ] Add `branch_tracking_mode` to config
- [ ] Add `min_branch_switch_interval` to config
- [ ] Update `.sync.yaml.example`
- [ ] Add config validation

### Phase 4: Optimization
- [ ] Add branch metadata caching
- [ ] Optimize git operations
- [ ] Add parallel timestamp fetching (optional)

### Phase 5: Documentation
- [ ] Update CODESPACES-SETUP.md
- [ ] Update MINI-VERSION-README.md
- [ ] Update AI-SETUP-INSTRUCTIONS.md
- [ ] Add CHANGELOG entry

### Phase 6: Testing
- [ ] Test sticky mode (original behavior)
- [ ] Test latest mode (new behavior)
- [ ] Test edge cases (concurrent, deleted, etc.)
- [ ] Test performance with 10+ branches

---

## 🎯 Success Criteria

**The refactoring is successful when:**

1. ✅ User makes multiple requests to Claude Code web
2. ✅ Claude creates random branch names for each response
3. ✅ Automation detects ALL Claude branches
4. ✅ Automation identifies which has the newest commit
5. ✅ Automation switches to that branch automatically
6. ✅ Server restarts with latest code
7. ✅ **Server always shows the absolute latest code within [interval] seconds**

**Regardless of:**
- Branch naming convention
- Number of branches
- Order of commits
- Network delays
- Concurrent sessions

---

## 📞 Next Steps

1. **Review brainstorm:** Read AUTOMATION-REFACTORING-BRAINSTORM.md for detailed analysis
2. **Approve approach:** Confirm "Latest Mode" solution
3. **Implement:** Follow checklist above
4. **Test:** Verify with real Claude Code web workflow
5. **Document:** Update all docs
6. **Deploy:** Roll out to users

---

**This refactoring solves the core problem: Claude's random branch names no longer matter. The automation will always find and serve the latest commit, automatically.**
