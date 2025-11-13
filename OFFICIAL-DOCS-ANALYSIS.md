# Claude Code on the Web - Official Documentation Analysis

## 📚 Source
Official Documentation: https://support.claude.com/en/articles/12618689-claude-code-on-the-web

## ✅ Confirmed Facts from Official Documentation

### 1. Git Operations & Branch Management

**How Claude Code Works:**
```
1. User gives Claude a task
2. Claude works in isolated VM
3. Upon completion: "pushes the changes to a new branch in your GitHub repository"
4. User receives notification
5. User can "create a pull request directly from the interface"
6. Pull request includes all of Claude's work, ready for review
```

**Key Confirmation:**
- ✅ Claude **creates new branches** (not commits to main)
- ✅ Branches are **automatically pushed** to GitHub
- ✅ User **reviews changes** before merging
- ✅ **PR creation interface** available in Claude Code web UI

**Not Specified in Docs:**
- ❌ Exact branch naming convention (e.g., `claude/*` pattern)
- ❌ Branch lifecycle management
- ❌ What happens to branches after merge
- ❌ How multiple concurrent tasks are handled

### 2. Environment & Session Management

**Isolated Virtual Machines:**
- Each task runs in a **separate VM**
- Pre-configured development tools included
- Repository cloned into isolated space
- Setup commands executed automatically (based on repo config)

**Security:**
- Restricted network access
- Protected credential handling
- GitHub authentication via **secure proxy**
- Credentials never exist directly in Claude's environment

**Implications:**
- Each session is ephemeral
- No persistent state between tasks
- Clean environment per task

### 3. User Interaction Modes

**Primary Mode: Web Interface**
- Monitor progress in real-time
- Provide guidance mid-task if needed
- Review completed work
- Create pull request from UI

**Secondary Mode: "Open in CLI"**
- Can switch to **terminal mode** if needed
- Useful when "guidance becomes necessary"
- Suggests hybrid web + CLI workflow possible

**Implications:**
- Not all work has to stay in web mode
- Can transition to CLI for complex scenarios

### 4. Recommended Workflows

**✅ Good Use Cases for Web Mode:**
- "Well-defined tasks with clear requirements"
- "Background work on bug backlogs" (parallel execution)
- Batch similar work
- Delegate during focused periods

**❌ Avoid Web Mode When:**
- "Frequent course correction" anticipated
- Requirements unclear or exploratory
- Uncommitted local changes exist
- Immediate feedback essential

**Testing Recommendation (Important!):**
- "Consider adding a test suite to your repository"
- Enables Claude to "verify that it has successfully completed a task"
- Provides "clear validation criteria to work towards"
- Enables "independent iteration without supervision"

### 5. Workflow Implications

**Pull Request Flow (Primary):**
```
Claude Web → Create Branch → Push to GitHub → Notification →
→ Review in UI → Create PR → Merge
```

**Local Testing Flow (Current Pain Point):**
```
Claude Web → Create Branch → Push to GitHub →
→ [USER MANUAL ACTION] git fetch + checkout + test locally →
→ If satisfied: Merge
```

**Identified Gap:**
The documentation doesn't describe automated local testing workflow.
This is where our sync daemon solution fits!

---

## 🔄 Revised Workflow Understanding

### What We Now Know for Certain

#### 1. Branch Creation Pattern
```yaml
Confirmed:
- Claude creates new branches automatically ✅
- Branches pushed to GitHub automatically ✅
- Each branch represents completed task ✅

Unknown:
- Exact naming convention (likely claude/* but not confirmed)
- Session ID format
- Branch prefix customization
```

#### 2. User's Testing Workflow Options

**Option A: Test on Vercel (Slow)**
```
Claude finishes → Push to GitHub → Vercel builds preview →
→ 5-10 min wait → Test on preview URL
```
**Downside:** Slow feedback loop

**Option B: Pull Locally (Manual)**
```
Claude finishes → Push to GitHub → User manually:
  - git fetch
  - git checkout claude/branch-name
  - npm run dev
  - test on localhost
```
**Downside:** Manual steps, repetitive

**Option C: Create PR and Review (No Testing)**
```
Claude finishes → Push to GitHub → Create PR → Merge without testing
```
**Downside:** Risky without testing

**Option D: Our Sync Daemon (Automated)** 🎯
```
Claude finishes → Push to GitHub → Webhook/Polling detects →
→ Auto-checkout → Auto dev server restart → Test on localhost
```
**Advantage:** Fast + Automated ✅

#### 3. The "Open in CLI" Feature

**Implication:** Users might have local checkout already
```
Scenario:
1. Start task in Claude Web
2. Mid-task, realize need manual intervention
3. Click "Open in CLI"
4. Continue in local terminal
5. Commit and push manually
```

**Question:** How does this affect our sync daemon?
- If user already has local checkout, sync should detect
- Should sync daemon pause when CLI mode active?
- How to coordinate web + CLI hybrid workflow?

---

## 🎯 Updated Architecture Insights

### Core Problem Reframed

**User's Actual Workflow:**
1. Give Claude task in web UI
2. Claude creates branch, pushes code
3. User wants to test locally (fast)
4. **Currently manual:** fetch, checkout, run dev server
5. **Desired:** Automatic sync and dev server ready

**Our Solution Fits Because:**
- Addresses the gap between "code pushed" and "testing locally"
- Automates the manual steps (fetch, checkout, dev server)
- Maintains Claude's PR-based workflow
- Works with existing GitHub integration

### Key Design Decisions

#### 1. Branch Detection Strategy

**Webhook-Based (Recommended):**
```yaml
Trigger: GitHub webhook on branch creation
Event: "create" event with ref_type: "branch"
Action: Check if branch matches Claude pattern
Result: Instant sync (< 1 second)
```

**Polling-Based (Fallback):**
```yaml
Interval: Every 10-30 seconds
Action: git fetch --prune, compare branches
Filter: Only Claude branches (pattern match)
Result: 10-30 second delay
```

**Hybrid (Best):**
```yaml
Primary: Webhook for instant sync
Fallback: Polling if webhook fails
Benefits: Speed + reliability
```

#### 2. Branch Naming Detection

Since docs don't specify exact pattern, we should:
```python
# Flexible pattern matching
BRANCH_PATTERNS = [
    r'^claude/.*',           # claude/feature-name-sessionId
    r'^ai/.*',               # Potential alternative
    r'^assistant/.*',        # Another possibility
    # Or configure in sync.yaml
]

# Or: Let user specify in config
sync:
  claude_branches:
    patterns:
      - '^claude/.*'
      - '^feature/claude-.*'
    custom_patterns: []  # User can add more
```

#### 3. Integration with "Open in CLI" Mode

**Conflict Scenario:**
```
Problem: User clicks "Open in CLI" while sync daemon running
Risk: Sync daemon might checkout branch while user working

Solution:
- Detect uncommitted changes before sync
- Prompt user: "Uncommitted changes found. Stash and sync?"
- Pause sync when CLI mode detected (check for .git/index.lock)
```

**Detection Strategy:**
```python
def should_skip_sync(repo_path: Path) -> bool:
    """Check if sync should be skipped"""
    # Check for git lock (user might be in CLI)
    if (repo_path / '.git/index.lock').exists():
        return True

    # Check for uncommitted changes
    if has_uncommitted_changes(repo_path):
        return True  # Or prompt user

    return False
```

#### 4. Test Suite Integration

Docs recommend: "Consider adding a test suite to your repository"

**Enhanced Workflow:**
```
Claude finishes → Branch pushed → Sync daemon:
  1. Checkout branch
  2. Run tests automatically (pytest, npm test, etc.)
  3. Notify user: "Tests passed ✅" or "Tests failed ❌"
  4. Start dev server
  5. Open browser
```

**Config:**
```yaml
sync:
  auto_test:
    enabled: true
    commands:
      node: "npm test"
      python: "pytest"
    on_failure:
      notify: true
      skip_dev_server: false  # Still start server for debugging
```

---

## 📊 Workflow Comparison: Official vs Our Enhancement

### Official Claude Code Workflow
```
┌──────────────┐
│ User defines │
│   task in    │
│  Claude Web  │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Claude works │
│  in isolated │
│     VM       │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Push branch  │
│  to GitHub   │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Notification │
│   sent to    │
│     user     │
└──────┬───────┘
       │
       ├─────────────────────┐
       ↓                     ↓
┌──────────────┐    ┌──────────────┐
│ Create PR    │    │ "Open in CLI"│
│  in web UI   │    │   (optional) │
└──────────────┘    └──────────────┘
       │
       ↓
┌──────────────┐
│ Review & PR  │
│    merge     │
└──────────────┘

PROBLEM: No easy way to test locally before PR
```

### Enhanced Workflow with Sync Daemon
```
┌──────────────┐
│ User defines │
│   task in    │
│  Claude Web  │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Claude works │
│  in isolated │
│     VM       │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Push branch  │
│  to GitHub   │
└──────┬───────┘
       │
       │ Webhook/Polling
       ↓
┌─────────────────────────────────┐
│    LOCAL PC - SYNC DAEMON        │
│                                  │
│  1. Detect new branch ⚡         │
│  2. git fetch + checkout         │
│  3. npm test (optional) 🧪       │
│  4. npm run dev 🚀               │
│  5. Notify user ✅               │
│  6. Open browser 🌐              │
│                                  │
│  Time: 2-5 seconds               │
└─────────────┬───────────────────┘
              │
              ↓
┌──────────────┐
│ User tests   │
│  locally on  │
│ localhost    │
└──────┬───────┘
       │
       ├─────────────────────┐
       ↓                     ↓
┌──────────────┐    ┌──────────────┐
│  Satisfied   │    │   Issues     │
│ Create PR    │    │ found, use   │
│  and merge   │    │ "Open in CLI"│
└──────────────┘    └──────────────┘

SOLUTION: Automated local testing bridge!
```

---

## 🎯 Refined Solution Architecture

### Component 1: Claude Branch Detector (UPDATED)

**Purpose:** Detect branches created by Claude Code on the web

**Detection Strategy:**
```python
class ClaudeBranchDetector:
    """
    Detects branches created by Claude Code on the web.
    Uses flexible pattern matching since exact convention not documented.
    """

    def __init__(self, config):
        # Load patterns from config
        self.patterns = config.get('sync.claude_branches.patterns', [
            r'^claude/.*'
        ])

    async def detect_new_branches(self, repo_path: Path) -> List[str]:
        """
        Detect new branches matching Claude patterns.
        Returns list of new branch names.
        """
        # Fetch all remote branches
        await self.run_git(repo_path, 'fetch', '--prune')

        # Get remote branches
        result = await self.run_git(repo_path, 'branch', '-r')
        remote_branches = [
            b.strip().replace('origin/', '')
            for b in result.stdout.split('\n')
            if b.strip() and 'origin/' in b
        ]

        # Filter branches matching Claude patterns
        claude_branches = []
        for branch in remote_branches:
            if self.matches_claude_pattern(branch):
                claude_branches.append(branch)

        # Compare with known branches to find new ones
        new_branches = [
            b for b in claude_branches
            if b not in self.known_branches
        ]

        self.known_branches.update(claude_branches)
        return new_branches

    def matches_claude_pattern(self, branch_name: str) -> bool:
        """Check if branch matches any Claude pattern"""
        return any(
            re.match(pattern, branch_name)
            for pattern in self.patterns
        )
```

### Component 2: Test Runner Integration (NEW)

**Purpose:** Automatically run tests on Claude branches before starting dev server

```python
class TestRunner:
    """
    Runs test suites on Claude branches before dev server starts.
    Follows official recommendation to use tests for validation.
    """

    async def run_tests(self, repo_path: Path, project_type: str) -> TestResult:
        """
        Run test suite for project type.
        Returns TestResult with pass/fail and output.
        """
        command = self.get_test_command(project_type)
        if not command:
            return TestResult(skipped=True)

        try:
            result = await asyncio.create_subprocess_shell(
                command,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=300  # 5 min max
            )

            stdout, stderr = await result.communicate()

            return TestResult(
                passed=result.returncode == 0,
                output=stdout.decode(),
                errors=stderr.decode()
            )

        except asyncio.TimeoutError:
            return TestResult(passed=False, errors="Test timeout")

    def get_test_command(self, project_type: str) -> Optional[str]:
        """Get test command for project type"""
        commands = {
            'node': 'npm test',
            'next': 'npm test',
            'python': 'pytest',
            'django': 'python manage.py test',
            'flask': 'pytest',
        }
        return commands.get(project_type)
```

### Component 3: CLI Mode Detector (NEW)

**Purpose:** Detect when user has "Open in CLI" mode active to avoid conflicts

```python
class CLIModeDetector:
    """
    Detects when user is working in CLI mode.
    Prevents sync conflicts during manual operations.
    """

    def is_cli_mode_active(self, repo_path: Path) -> bool:
        """
        Check if user is likely in CLI mode.
        Indicators: git lock files, recent git commands, uncommitted changes
        """
        # Check for git lock file
        if (repo_path / '.git/index.lock').exists():
            return True

        # Check for uncommitted changes
        if self.has_uncommitted_changes(repo_path):
            # Check if changes are recent (< 5 min)
            mtime = self.get_worktree_mtime(repo_path)
            if time.time() - mtime < 300:  # 5 minutes
                return True

        return False

    def should_pause_sync(self, repo_path: Path) -> bool:
        """Determine if sync should be paused"""
        return self.is_cli_mode_active(repo_path)
```

---

## ⚙️ Updated Configuration

```yaml
# config/sync.yaml

sync:
  mode: hybrid  # webhook + polling

  # Claude branch detection
  claude_branches:
    # Flexible patterns (exact convention not documented)
    patterns:
      - '^claude/.*'       # Most likely pattern
      - '^ai/.*'           # Alternative
      - '^assistant/.*'    # Another alternative

    # Auto-sync behavior
    auto_sync: true
    sync_latest_only: true  # Or sync all new branches

  # Webhook settings
  webhook:
    enabled: true
    port: 8766
    events:
      - create  # Branch creation
      - push    # New commits

  # Test automation (follows official recommendation)
  auto_test:
    enabled: true
    run_before_dev_server: true
    notify_on_failure: true
    commands:
      node: "npm test"
      python: "pytest"
      django: "python manage.py test"

  # CLI mode detection
  cli_mode_detection:
    enabled: true
    pause_sync_when_active: true
    uncommitted_changes_threshold: 300  # seconds

  # Dev server
  dev_server:
    auto_restart: true
    open_browser: true
    wait_for_ready: true

  # Notifications
  notifications:
    on_new_branch: true
    on_test_pass: true
    on_test_fail: true
    on_dev_server_ready: true
    include_pr_link: true  # Link to create PR on GitHub
```

---

## 🎬 Updated User Experience Flow

### Complete End-to-End Workflow

```
1. USER: Give task to Claude in web UI
   "Add user authentication to the app"

2. CLAUDE: Works in isolated VM
   - Clones repository
   - Makes changes
   - Runs tests (if configured)
   - Creates branch: claude/add-auth-xyz123
   - Pushes to GitHub

3. GITHUB: Sends webhook to local PC
   Event: "branch created: claude/add-auth-xyz123"

4. SYNC DAEMON (Local PC):
   📥 New branch detected: claude/add-auth-xyz123

   Checks:
   ✅ Not in CLI mode
   ✅ No git locks
   ✅ Safe to proceed

   Actions:
   - git fetch origin claude/add-auth-xyz123
   - git checkout claude/add-auth-xyz123
   - npm test (auto-test enabled)
     ✅ Tests passed!
   - npm run dev
   - Wait for localhost:3000...
   - Open browser

   ⏱️ Total time: 5 seconds

5. NOTIFICATION (Desktop):
   ╔════════════════════════════════════╗
   ║  ✅ Claude Branch Ready            ║
   ║                                    ║
   ║  Branch: claude/add-auth-xyz123   ║
   ║  Tests: ✅ Passed                  ║
   ║  Server: http://localhost:3000    ║
   ║                                    ║
   ║  [Open Browser] [Create PR]       ║
   ╚════════════════════════════════════╝

6. USER: Tests in browser
   - Checks authentication flow
   - Tests login/logout
   - Verifies UI changes

   Decision:
   ✅ Satisfied → Click "Create PR" button
   ❌ Issues → Click "Open in CLI" in Claude UI

7. IF SATISFIED:
   - Browser opens GitHub PR creation page
   - PR title: "Add user authentication"
   - PR body: Claude's description
   - User reviews diff, creates PR
   - Merge when ready

8. IF ISSUES:
   - User clicks "Open in CLI" in Claude UI
   - Makes manual adjustments locally
   - Commits to same branch
   - Pushes to GitHub
   - Sync daemon detects update, restarts server
```

---

## ✅ Key Takeaways from Official Docs

1. **Branch-Based Workflow Confirmed** ✅
   - Claude creates branches automatically
   - Not committing to main

2. **PR Creation Interface Exists** ✅
   - Can create PR directly from Claude UI
   - Our sync daemon should provide quick link

3. **Test Suite Recommended** ✅
   - Official docs emphasize testing
   - Our auto-test feature aligns with this

4. **"Open in CLI" Feature** ✅
   - Users can switch to terminal mid-task
   - Our sync daemon should detect and pause

5. **Isolated VMs** ✅
   - Each task is ephemeral
   - No persistent state in cloud
   - Local environment is the persistent workspace

6. **Well-Defined Tasks Work Best** ✅
   - Claude Web best for clear requirements
   - Exploratory work better in CLI
   - Our solution bridges both modes

---

## 🚀 Next Steps

Now with official documentation understanding:

1. ✅ **Confirmed:** Branch-based workflow is correct
2. ✅ **Confirmed:** Automated sync fills a real gap
3. ✅ **New insight:** Test automation is officially recommended
4. ✅ **New insight:** Need CLI mode detection for "Open in CLI" feature
5. ✅ **Ready:** Create accurate implementation plan

**Shall I proceed with creating the implementation plan?**

The plan will include:
- Claude branch detection (flexible patterns)
- Test runner integration (official recommendation)
- CLI mode detection (avoid conflicts)
- Webhook + polling hybrid approach
- Dev server management
- Notification system with PR link
