# Git Workflow Guardian - Brainstorm

**Created:** 2025-11-13
**Purpose:** Design a background monitoring system that enforces Git workflow best practices with Windows popup notifications
**Status:** Initial brainstorming

---

## 🎯 CORE REQUIREMENTS

**User Profile:** Forgetful developer who needs reminders to follow Git workflow best practices

**Key Workflow Rules:**
1. ✅ Always work on feature branches (never commit to main)
2. ✅ Keep main synced (pull before starting)
3. ✅ One feature = one branch = one PR
4. ✅ Delete branches after merge
5. ✅ Test locally first (http://localhost:3011)
6. ✅ Never push to main directly
7. ✅ Use proper branch naming: `claude/feature-name-{sessionId}`

**Notification Requirements:**
- Windows popup messages
- Show WHAT TO DO (not what not to do)
- Include brief justification WHY
- Override button for user flexibility
- Non-intrusive but proactive

---

## 🏗️ IMPLEMENTATION ARCHITECTURE OPTIONS

### Option 1: Git Hooks (Lightweight, Native)

**Concept:** Install git hooks that trigger on specific git operations

**Hooks to use:**
- `pre-commit` - Check branch before allowing commit
- `pre-push` - Validate push target (block if pushing to main)
- `post-checkout` - Remind to pull main when switching branches
- `post-merge` - Suggest branch deletion after merge

**Pros:**
- ✅ Native git integration (runs automatically)
- ✅ Zero background processes
- ✅ Reliable triggering (git enforces hooks)
- ✅ Per-repository configuration

**Cons:**
- ❌ Can't monitor working directory changes (only git operations)
- ❌ User can bypass with --no-verify flag
- ❌ Limited to git event-based detection
- ❌ No persistent state between operations

**Notification mechanism:**
- Hook scripts call Python/PowerShell notification script
- Windows toast notification or custom popup
- Synchronous (blocks git operation until acknowledged)

**Implementation complexity:** Low (2-3 days)

---

### Option 2: Background Service/Daemon

**Concept:** Long-running process that monitors git repository for violations

**Architecture:**
```
[Background Service]
    ↓ Poll every 30s
[Git Status Check]
    ↓ Detect violations
[Notification Engine]
    ↓ Show popup
[User Action] → [Update State]
```

**Monitoring checks:**
- Git branch (are we on main?)
- Git status (uncommitted changes on main?)
- Branch age (working on same branch >24 hours?)
- Local vs remote sync status
- Branch naming compliance
- Stale branches (merged but not deleted)

**Pros:**
- ✅ Continuous monitoring (catch violations anytime)
- ✅ Predictive warnings (before git operations)
- ✅ State management (track patterns, learning)
- ✅ Rich notifications (can show context, history)

**Cons:**
- ❌ Background process overhead
- ❌ More complex state management
- ❌ Need service installation/startup
- ❌ Potential for false positives

**Implementation complexity:** Medium (5-7 days)

**Technologies:**
- Python daemon with systemd/Windows Service
- Or: PowerShell background job
- Or: Node.js electron app (background mode)

---

### Option 3: Hybrid (Git Hooks + Background Monitor)

**Concept:** Combine git hooks for critical violations + background service for proactive guidance

**Division of responsibility:**

**Git Hooks (Critical enforcement):**
- ⛔ BLOCK: Committing to main
- ⛔ BLOCK: Pushing to main
- ⚠️ WARN: Branch naming violations

**Background Service (Proactive guidance):**
- 💡 SUGGEST: Pull main before starting work
- 💡 SUGGEST: Delete merged branches
- 💡 SUGGEST: Test locally before commit
- 💡 REMIND: Branch has been active >8 hours

**Pros:**
- ✅ Best of both worlds (critical + proactive)
- ✅ Hooks prevent catastrophic mistakes
- ✅ Service provides helpful guidance
- ✅ Graceful degradation (hooks work even if service down)

**Cons:**
- ❌ Most complex to implement
- ❌ Two systems to maintain
- ❌ Potential for duplicate notifications

**Implementation complexity:** High (7-10 days)

---

### Option 4: VSCode Extension (IDE-Integrated)

**Concept:** VSCode extension that monitors git operations within editor

**Features:**
- Status bar indicator (green = compliant, yellow = warning, red = violation)
- Sidebar panel with workflow checklist
- Inline notifications (toast within VSCode)
- Git operations intercepted via VSCode API

**Pros:**
- ✅ Rich UI integration
- ✅ Context-aware (knows what user is editing)
- ✅ No separate process needed
- ✅ NPM ecosystem (easy distribution)

**Cons:**
- ❌ Only works within VSCode (not terminal git)
- ❌ JavaScript/TypeScript learning curve
- ❌ VSCode-specific (not editor-agnostic)
- ❌ Longer development time

**Implementation complexity:** High (10-14 days)

---

### Option 5: CLI Wrapper (Explicit, Simple)

**Concept:** Replace `git` command with wrapper script that validates workflow

**Usage:**
```bash
# Instead of: git checkout -b feature
# User runs: wg checkout -b feature
# (wg = workflow guardian)

# Wrapper validates, then calls real git
```

**Pros:**
- ✅ Explicit opt-in (user calls wrapper)
- ✅ Simple implementation
- ✅ Easy to debug
- ✅ No background processes

**Cons:**
- ❌ Requires user behavior change (remember to use wrapper)
- ❌ Easy to forget and use git directly
- ❌ No proactive monitoring
- ❌ Not transparent

**Implementation complexity:** Low (1-2 days)

---

## 🔔 NOTIFICATION SYSTEM DESIGN

### Notification Type 1: Windows Toast Notifications (Native)

**Technology:** PowerShell `BurntToast` module or Windows API

**Appearance:**
```
┌────────────────────────────────┐
│ 🚨 Git Workflow Guardian       │
│                                │
│ ✅ Switch to feature branch    │
│                                │
│ You're on main. Create a       │
│ feature branch before coding.  │
│                                │
│ Why? Keeps main stable.        │
│                                │
│ [Switch Now] [Override]        │
└────────────────────────────────┘
```

**Pros:**
- ✅ Native Windows appearance
- ✅ Non-intrusive (system tray area)
- ✅ Auto-dismiss after timeout
- ✅ No custom UI needed

**Cons:**
- ❌ Limited customization
- ❌ Button actions limited (can open URLs or apps)
- ❌ May not support complex override logic
- ❌ User might dismiss without reading

**Implementation:** PowerShell script or Python `win10toast` library

---

### Notification Type 2: Custom Popup Window (Tkinter/PyQt)

**Technology:** Python GUI with tkinter (built-in) or PyQt5

**Appearance:**
```
┌─────────────────────────────────────────┐
│ Git Workflow Guardian            [✕]    │
├─────────────────────────────────────────┤
│                                         │
│  🚨 WORKFLOW VIOLATION                  │
│                                         │
│  You're about to commit to main.        │
│                                         │
│  ✅ WHAT TO DO:                         │
│  Create a feature branch first          │
│                                         │
│  📝 WHY:                                │
│  Main should only receive merges from   │
│  reviewed PRs. Direct commits bypass    │
│  the review process.                    │
│                                         │
│  Suggested command:                     │
│  git checkout -b claude/fix-auth-{id}   │
│                                         │
│  [ Create Branch ]  [ Override & Commit ]│
└─────────────────────────────────────────┘
```

**Pros:**
- ✅ Full UI control (buttons, colors, layout)
- ✅ Can execute commands directly (Create Branch button → run git command)
- ✅ Rich content (code snippets, multi-line explanations)
- ✅ Modal blocking (requires acknowledgment)

**Cons:**
- ❌ More intrusive (requires focus)
- ❌ Custom UI development effort
- ❌ May feel jarring if user is in flow state
- ❌ Accessibility concerns (screen readers, etc.)

**Implementation:** Python tkinter (simpler) or PyQt5 (more polished)

---

### Notification Type 3: Browser-Based Dashboard

**Concept:** Local web server (Flask/FastAPI) with real-time dashboard

**Features:**
- Dashboard at http://localhost:8765
- WebSocket updates for real-time violations
- Violation history log
- Workflow compliance score
- Browser notifications API

**Pros:**
- ✅ Rich UI (HTML/CSS/JS)
- ✅ Cross-platform (works anywhere)
- ✅ Can show trends over time
- ✅ Easy to customize

**Cons:**
- ❌ Requires browser tab open
- ❌ More complex infrastructure
- ❌ Less immediate than popups
- ❌ Background server overhead

**Implementation complexity:** Medium (4-6 days)

---

### Notification Type 4: Hybrid (Toast + Popup)

**Concept:** Use toast for minor warnings, popup for critical violations

**Toast notifications (non-blocking):**
- 💡 Reminder: Pull main before starting new feature
- 💡 Suggestion: Delete merged branch `old-feature`
- 💡 Tip: Test locally before committing

**Popup notifications (blocking):**
- ⛔ CRITICAL: You're about to commit to main!
- ⛔ CRITICAL: You're about to push to main!
- ⚠️ WARNING: Branch name doesn't follow convention

**Pros:**
- ✅ Right tool for severity level
- ✅ Critical violations can't be ignored
- ✅ Minor guidance doesn't interrupt flow

**Cons:**
- ❌ Two notification systems to maintain
- ❌ Need clear severity classification

---

## 🔍 DETECTION MECHANISMS

### Detection Strategy 1: Git Command Parsing

**How it works:**
- Parse `git status`, `git branch`, `git log` output
- Extract current branch, staged files, remote sync status
- Compare against workflow rules

**Example checks:**
```bash
# Check if on main
git branch --show-current
# Output: main → VIOLATION

# Check for uncommitted changes on main
git status --porcelain
# Output: M file.txt → VIOLATION (if on main)

# Check branch naming
git branch --show-current
# Output: feature-123 → VIOLATION (should be claude/feature-123-{id})
```

**Pros:**
- ✅ Reliable (uses official git commands)
- ✅ Cross-platform
- ✅ No direct .git manipulation

**Cons:**
- ❌ Slower (shell command overhead)
- ❌ Parsing output can be fragile

---

### Detection Strategy 2: .git Directory Monitoring

**How it works:**
- Watch `.git/HEAD` file for branch changes
- Watch `.git/refs/heads/` for new branches
- Parse `.git/config` for remote tracking

**Example checks:**
```bash
# Current branch from HEAD
cat .git/HEAD
# Output: ref: refs/heads/main → VIOLATION

# List all branches
ls .git/refs/heads/
# Output: main, feature-1, feature-2 → Check naming

# Check remote tracking
cat .git/config
# [branch "main"]
#   remote = origin
#   merge = refs/heads/main
```

**Pros:**
- ✅ Faster (direct file reads)
- ✅ No shell command overhead
- ✅ Real-time monitoring (file watchers)

**Cons:**
- ❌ Fragile (git internal structure changes)
- ❌ Complex parsing (git config format)
- ❌ May miss some git state

---

### Detection Strategy 3: Git Hooks Integration

**How it works:**
- Hooks call detection script
- Script analyzes git operation context
- Return exit code to allow/block operation

**Example hooks:**

**pre-commit:**
```bash
#!/bin/bash
# Check if on main
current_branch=$(git branch --show-current)
if [ "$current_branch" = "main" ]; then
  python notify.py --violation "committing-to-main"
  exit 1  # Block commit
fi
```

**pre-push:**
```bash
#!/bin/bash
# Check if pushing to main
if grep -q "refs/heads/main" "$1"; then
  python notify.py --violation "pushing-to-main"
  exit 1  # Block push
fi
```

**Pros:**
- ✅ Native git integration
- ✅ Can block operations (exit code)
- ✅ Event-driven (no polling)

**Cons:**
- ❌ Only triggers on git operations
- ❌ Can't provide proactive guidance
- ❌ User can bypass with --no-verify

---

## 🎨 USER EXPERIENCE & OVERRIDE LOGIC

### Notification Message Structure

**Template:**
```
[ICON] [SEVERITY LABEL]

[SITUATION DESCRIPTION]

✅ WHAT TO DO:
[Clear, actionable instruction]

📝 WHY:
[Brief justification - 1-2 sentences]

[Suggested command or action]

[Primary Action Button]  [Override Button]
```

**Example 1: Critical violation**
```
🚨 CRITICAL

You're about to commit to main branch.

✅ WHAT TO DO:
Create a feature branch first

📝 WHY:
Main should only receive reviewed code via PRs.
Direct commits bypass your workflow and make
tracking changes harder.

Suggested:
git checkout -b claude/fix-auth-011CV4BKNuix3SrqRsZXoqX2

[Create Branch]  [Override & Commit Anyway]
```

**Example 2: Proactive suggestion**
```
💡 SUGGESTION

Starting new work session.

✅ WHAT TO DO:
Pull latest main first

📝 WHY:
Ensures you're working with latest code and
prevents merge conflicts later.

Suggested:
git checkout main && git pull origin main

[Pull Now]  [Skip This Time]
```

---

### Override Button Behavior

**Option A: Simple Override (No tracking)**
- User clicks "Override" → notification dismissed
- No state saved
- Same notification appears next time

**Pros:** Simple implementation
**Cons:** User annoyed by repeated dismissals

---

**Option B: Session-Level Override**
- User clicks "Override" → violation ignored for current session
- Session = until branch changes or new shell
- Next session, notification reappears

**Pros:** Balanced (allows temporary overrides)
**Cons:** Need session state management

---

**Option C: Time-Based Override**
- User clicks "Override for 1 hour"
- Violation suppressed for 60 minutes
- After timeout, notifications resume

**Pros:** Flexible duration
**Cons:** Need persistent state with timestamps

---

**Option D: Rule-Specific Disable**
- User clicks "Disable this rule"
- Specific violation type never notifies again
- Can re-enable in settings/config

**Pros:** User control over rules
**Cons:** Risk of permanently ignoring important rules

---

**Option E: Smart Override (Context-Aware)**
- Track override frequency per rule
- If user overrides same rule 3+ times → suggest disabling
- "You've overridden this rule 3 times. Disable it permanently?"

**Pros:** Adapts to user behavior
**Cons:** Complex logic, need analytics

---

**RECOMMENDATION:** Start with **Option B (Session-Level)** for MVP, add **Option C (Time-Based)** later if needed.

---

### Non-Intrusive Design Principles

**1. Respect Flow State**
- Don't interrupt during active typing (IDE integration)
- Delay notifications if rapid git commands (batch operations)
- Group related violations (don't show 5 popups in a row)

**2. Frequency Limiting**
- Same violation: max 1 notification per 5 minutes
- Different violations: queue and batch display
- Learning mode: fewer notifications as user improves

**3. Visibility Without Annoyance**
- Status bar indicator (always visible, low friction)
- Toast for minor issues (auto-dismiss)
- Modal popup only for critical violations

**4. Positive Reinforcement**
- Show "✅ Workflow compliant" message occasionally
- Track compliance score (gamification)
- Weekly summary: "You followed workflow 95% this week!"

---

## 🚧 TECHNICAL CHALLENGES & SOLUTIONS

### Challenge 1: Windows Popup Implementation

**Problem:** Need cross-platform popup that doesn't require user to install heavy GUI frameworks

**Solutions:**

**A. PowerShell BurntToast (Windows-only)**
```powershell
Import-Module BurntToast
New-BurntToastNotification -Text "Git Workflow Guardian", "You're on main branch" -AppLogo "icon.png"
```
**Pros:** Native Windows, no dependencies
**Cons:** Windows-only, limited button actions

**B. Python tkinter (Cross-platform, built-in)**
```python
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()  # Hide main window
response = messagebox.askyesno("Git Workflow Guardian", "Create feature branch?")
```
**Pros:** Cross-platform, Python built-in
**Cons:** Basic styling, can look dated

**C. Python win10toast (Windows-only, simple)**
```python
from win10toast import ToastNotifier
toaster = ToastNotifier()
toaster.show_toast("Git Workflow Guardian", "You're on main", duration=10, threaded=True)
```
**Pros:** Easy to use, async
**Cons:** Windows 10+ only, no button callbacks

**D. PyQt5 (Cross-platform, polished)**
```python
from PyQt5.QtWidgets import QApplication, QMessageBox
app = QApplication([])
reply = QMessageBox.question(None, "Git Workflow Guardian", "Create feature branch?", QMessageBox.Yes | QMessageBox.No)
```
**Pros:** Professional UI, rich controls
**Cons:** Requires pip install PyQt5

**RECOMMENDATION:** Start with **tkinter** (MVP), upgrade to **PyQt5** if UI polish needed.

---

### Challenge 2: Background Service Reliability

**Problem:** Background service must survive system restarts, crashes, updates

**Solutions:**

**A. Windows Service (systemd equivalent)**
- Use NSSM (Non-Sucking Service Manager)
- Register Python script as Windows Service
- Auto-start on boot

**B. Scheduled Task (Task Scheduler)**
- Create task that runs on login
- Trigger: "At log on of any user"
- Run Python script with flag `--background`

**C. User-Level Startup (Simple)**
- Add shortcut to `shell:startup` folder
- Runs on user login only (not system-wide)

**D. Docker Container (Overkill)**
- Package service in container
- Docker Desktop auto-starts container
- Pros: Isolated environment
- Cons: Heavy, requires Docker

**RECOMMENDATION:** **Scheduled Task** for MVP (easy to set up), **Windows Service** for production (more robust).

---

### Challenge 3: Git Repository Discovery

**Problem:** Service needs to find all active git repos on system

**Solutions:**

**A. Config File (Manual)**
- User specifies repos in config: `repos: ["D:/Projects/app1", "D:/Projects/app2"]`
- Service monitors only listed repos
- Pros: Explicit control
- Cons: Manual setup, can forget repos

**B. Auto-Discovery (File System Scan)**
- Scan common directories: `D:/Projects/`, `C:/Users/{user}/Projects/`
- Find all `.git` directories
- Pros: Automatic
- Cons: Slow, may find too many repos

**C. Recent Activity (Git Config)**
- Parse recent git commands from shell history
- Extract repo paths from recent activity
- Pros: Only active repos
- Cons: May miss repos not used recently

**D. Hybrid (Auto-Discover + Config)**
- Auto-discover on first run
- Save to config file
- User can add/remove manually

**RECOMMENDATION:** **Hybrid** - best balance of automation and control.

---

### Challenge 4: State Management

**Problem:** Need to track violation history, override state, user patterns

**Solutions:**

**A. JSON File (Simple)**
```json
{
  "overrides": {
    "committing-to-main": {
      "session_id": "011CV4BKNuix3SrqRsZXoqX2",
      "expires": "2025-11-13T18:00:00Z"
    }
  },
  "violation_history": [
    {"type": "committing-to-main", "timestamp": "2025-11-13T10:30:00Z", "overridden": true}
  ]
}
```
**Pros:** Simple, human-readable
**Cons:** Concurrent access issues

**B. SQLite Database**
```sql
CREATE TABLE overrides (
  violation_type TEXT,
  session_id TEXT,
  expires TIMESTAMP
);

CREATE TABLE violations (
  id INTEGER PRIMARY KEY,
  type TEXT,
  timestamp TIMESTAMP,
  overridden BOOLEAN
);
```
**Pros:** Structured, queryable, concurrent-safe
**Cons:** Requires SQLite library

**C. In-Memory (No Persistence)**
- State stored in Python dict
- Lost on service restart
- Pros: Fast, simple
- Cons: No history tracking

**RECOMMENDATION:** **SQLite** for production (enables analytics), **JSON** for MVP.

---

## 🔌 INTEGRATION POINTS

### Integration 1: Claude Code Session ID

**Concept:** Extract Claude Code session ID for branch naming compliance

**Detection:**
- Parse branch name: `claude/feature-name-{sessionId}`
- Extract `{sessionId}` (e.g., `011CV4BKNuix3SrqRsZXoqX2`)
- If missing or wrong format → violation

**Validation:**
```python
import re

branch_name = "claude/fix-auth-011CV4BKNuix3SrqRsZXoqX2"
pattern = r"^claude/[\w-]+-([A-Za-z0-9]{24})$"

if not re.match(pattern, branch_name):
    notify("Branch naming violation", "Use format: claude/feature-name-{sessionId}")
```

**Enhancement:**
- Auto-suggest correct branch name with current session ID
- Store session ID mapping (session ID → feature description)
- Detect if reusing old session ID

---

### Integration 2: Local Dev Server Check

**Concept:** Verify user tested locally before committing

**Detection:**
- Before commit: Check if `http://localhost:3011` is accessible
- If not running → warning (not blocking)

**Implementation:**
```python
import requests

def check_local_server():
    try:
        response = requests.get("http://localhost:3011", timeout=2)
        return response.status_code == 200
    except:
        return False

if not check_local_server():
    notify("Local server not running", "Start dev server: npm run dev -- -p 3011")
```

**Override logic:**
- Not blocking (user may be working on backend-only changes)
- Reminder only

---

### Integration 3: Vercel Deployment Status

**Concept:** Notify user of auto-deployment status after merge

**Implementation:**
- After PR merge detected (git log shows merge commit)
- Query Vercel API for deployment status
- Show notification: "✅ Vercel deployed to production" or "⚠️ Deployment failed"

**API integration:**
```python
import requests

def check_vercel_deployment(branch_name):
    # Requires Vercel API token
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    response = requests.get("https://api.vercel.com/v6/deployments", headers=headers)
    # Parse response for deployment status
    return deployment_status
```

**Enhancement:**
- Show deployment URL in notification
- Link to Vercel dashboard

---

## 📊 IMPLEMENTATION RECOMMENDATIONS

### Minimum Viable Product (MVP)

**Scope:** Core functionality with minimal complexity

**Architecture:**
- **Git hooks** for critical violations (pre-commit, pre-push)
- **Python tkinter** for popup notifications
- **JSON file** for state management
- **Manual repo config** (user specifies paths)

**Features:**
- ⛔ BLOCK: Committing to main
- ⛔ BLOCK: Pushing to main
- ⚠️ WARN: Branch naming violations
- 💡 SUGGEST: Pull main before starting (post-checkout hook)

**Estimated effort:** 3-4 days

---

### Phase 2: Background Monitoring

**Add:**
- **Background service** (Python daemon or scheduled task)
- **Proactive notifications** (remind to delete merged branches, test locally)
- **SQLite database** for analytics
- **Auto-discovery** of git repositories

**Estimated effort:** +5-6 days

---

### Phase 3: Advanced Features

**Add:**
- **VSCode extension** (optional, parallel effort)
- **Compliance dashboard** (Flask web UI)
- **Machine learning** (detect user patterns, adaptive notifications)
- **Vercel API integration**

**Estimated effort:** +10-14 days

---

## 🔍 OPEN QUESTIONS

1. **Notification tone:** Strict enforcer vs helpful assistant?
   - Strict: Block operations, require acknowledgment
   - Helpful: Suggest improvements, easy to dismiss

2. **Override persistence:** How long should overrides last?
   - Session-level (until branch changes)
   - Time-based (1 hour, 1 day)
   - Permanent (disable rule)

3. **Multiple repo handling:** Monitor all repos or single active repo?
   - All repos: More comprehensive, more CPU
   - Active repo: Focused, less overhead

4. **Installation complexity:** How much setup is acceptable?
   - Auto-installer script (1 command)
   - Manual steps (edit config, run script)
   - Package (pip install, chocolatey, etc.)

5. **Cross-platform support:** Windows-only or cross-platform?
   - Windows-only: Simpler, faster development
   - Cross-platform: Broader usability, more complexity

---

## 💡 CREATIVE ENHANCEMENTS

### Enhancement 1: Workflow Compliance Score

**Concept:** Gamification - track adherence to workflow rules

**Metrics:**
- % of commits on feature branches (target: 100%)
- % of branches properly named (target: 100%)
- Average time to delete merged branches (target: <1 day)
- Local testing rate before commits (target: >80%)

**UI:**
```
╔═══════════════════════════════════════╗
║  GIT WORKFLOW COMPLIANCE SCORE        ║
╠═══════════════════════════════════════╣
║                                       ║
║  Overall:  87%  🟢                    ║
║                                       ║
║  ✅ Feature branch usage:     100%   ║
║  ⚠️  Branch naming:            75%   ║
║  ✅ Local testing:             90%   ║
║  ⚠️  Branch cleanup:           80%   ║
║                                       ║
║  🎯 Goal: Reach 95% by end of week   ║
╚═══════════════════════════════════════╝
```

---

### Enhancement 2: AI-Powered Commit Message Suggestions

**Concept:** Analyze staged changes, suggest conventional commit messages

**Example:**
```
Staged files: src/auth.ts, src/utils/jwt.ts

Suggested commit message:
"feat(auth): implement JWT token refresh

- Add token expiration checking
- Implement refresh token rotation
- Update auth middleware"

[Use This Message]  [Edit]  [Cancel]
```

---

### Enhancement 3: Branch Dependency Visualization

**Concept:** Show which branches depend on each other (stacked PRs)

**UI (Terminal ASCII):**
```
main ──────────────────────────────────
       │
       └─→ claude/auth-foundation-{id}
              │
              └─→ claude/auth-jwt-{id} (current)
                     │
                     └─→ claude/auth-refresh-{id}
```

**Value:** Helps user understand branch relationships, avoid merge conflicts

---

### Enhancement 4: Smart Merge Conflict Prevention

**Concept:** Warn if current branch likely to conflict with main

**Detection:**
- Compare modified files in current branch vs recent main commits
- If overlap detected → warning

**Notification:**
```
⚠️ POTENTIAL CONFLICT

Your branch modified: src/auth.ts
Main recently changed: src/auth.ts (2 hours ago)

✅ WHAT TO DO:
Merge main into your branch now to resolve conflicts

📝 WHY:
Resolving conflicts early prevents surprises during PR

Suggested:
git merge origin/main

[Merge Now]  [Check Diff First]  [Remind Later]
```

---

## 🎯 NEXT STEPS (User Decision)

**Questions for user:**

1. **Architecture preference:**
   - Start with Git hooks only (MVP, 3-4 days)?
   - Go straight to background service (more proactive, 8-10 days)?
   - Hybrid approach (hooks + service)?

2. **Notification style:**
   - Simple toast notifications (low friction)?
   - Rich popups with buttons (more control)?
   - Browser dashboard (analytics-focused)?

3. **Override behavior:**
   - Session-level (override until branch changes)?
   - Time-based (override for X hours)?
   - Permanent disable per rule?

4. **Scope:**
   - Just workflow enforcement?
   - Include compliance scoring?
   - Add AI-powered suggestions?

5. **Installation:**
   - Manual setup (clone repo, run install script)?
   - Packaged installer (one-click setup)?
   - VSCode extension marketplace?

---

**Status:** Ready for user feedback and architecture decision
**Next:** Choose architecture → Create detailed implementation plan
