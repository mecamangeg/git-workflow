# Claude Code Web - Actual Workflow Analysis

## 🔍 How Claude Code on the Web Actually Works

### Automatic Branch Creation
When Claude Code on the web writes code, it:
1. **Automatically creates a feature branch** with pattern: `claude/feature-name-{sessionId}`
2. **Commits code to that branch** (not to main)
3. **Pushes the branch to remote** automatically

### Current Manual Workflow
```bash
# 1. User checks what branches Claude created
git fetch --all
git branch -r | grep claude/

# 2. User manually pulls the Claude branch
git pull origin claude/feature-name-xyz123

# 3. User manually checks out the branch
git checkout claude/feature-name-xyz123

# 4. User manually restarts dev server
npm run dev  # or whatever command

# 5. User tests in browser
# → If satisfied: merge and push
# → If changes needed: go back to Claude Code

# 6. If satisfied, merge
git checkout main
git merge claude/feature-name-xyz123
git push origin main

# Or create PR for the Claude branch
```

### Key Insights
- ✅ **Branch-centric workflow** (not main-centric)
- ✅ **Predictable naming**: `claude/*` prefix
- ✅ **Session-specific**: Each Claude session = unique branch
- ✅ **Isolated changes**: No risk of conflicting with main
- ✅ **Review-friendly**: Can see exactly what Claude did

---

## 🎯 Revised Automation Requirements

### What Needs to be Automated

#### 1. Detect New Claude Branches
```yaml
Problem: User has to manually check for new branches
Solution: Watch for branches matching pattern 'claude/*'

Trigger:
- Webhook: GitHub notifies when new branch created
- Polling: Check every 10-30s for new 'claude/*' branches
```

#### 2. Auto-Checkout Claude Branch
```yaml
Problem: User has to manually checkout the branch
Solution: Automatically switch to latest Claude branch

Action:
- git fetch origin claude/feature-name-xyz
- git checkout claude/feature-name-xyz
- Or: git checkout -b claude/feature-name-xyz origin/claude/feature-name-xyz
```

#### 3. Auto-Restart Dev Server
```yaml
Problem: User has to manually restart dev server
Solution: Restart automatically after branch checkout

Action:
- Kill existing dev server process
- Start dev server in new branch context
- Wait for server to be ready
- Notify user + open browser
```

#### 4. Track Active Claude Branch
```yaml
Problem: Multiple Claude branches can exist
Solution: Track which branch is "active" for testing

Strategy:
- Latest created branch = active
- User can manually switch active branch
- Sync daemon syncs ONLY active branch
```

#### 5. Handle Branch Updates
```yaml
Problem: Claude might push more commits to same branch
Solution: Detect updates to current branch and auto-pull

Trigger:
- Watch the currently checked-out claude/* branch
- If remote has new commits, auto-pull
- Restart dev server after pull
```

---

## 🔄 Revised Workflow Architecture

### Automated Cloud-First Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              CLAUDE CODE (CLOUD/WEB)                         │
│                                                              │
│  Session: abc123                                            │
│  Branch: claude/add-user-auth-abc123                        │
│                                                              │
│  1. Create branch (automatic)                               │
│  2. Write code                                              │
│  3. Commit to claude/add-user-auth-abc123                   │
│  4. Push to remote (automatic)                              │
│                                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ git push (branch: claude/add-user-auth-abc123)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    GITHUB REMOTE                             │
│                                                              │
│  Branches:                                                   │
│  - main                                                      │
│  - claude/add-user-auth-abc123  ← NEW BRANCH                │
│                                                              │
└─────────────┬────────────────────────────────────────────────┘
              │
              │ webhook: "branch created" or "push to claude/*"
              ↓
┌─────────────────────────────────────────────────────────────┐
│              LOCAL PC - SYNC DAEMON                          │
│                                                              │
│  🔍 Detected: New branch 'claude/add-user-auth-abc123'      │
│                                                              │
│  Automated Actions:                                          │
│  1. git fetch origin claude/add-user-auth-abc123            │
│  2. git checkout claude/add-user-auth-abc123                │
│  3. Kill dev server (if running)                            │
│  4. npm run dev (restart in new branch)                     │
│  5. Wait for localhost:3000 to be ready                     │
│  6. Notify: "Ready to test: claude/add-user-auth-abc123"    │
│  7. Open browser → http://localhost:3000                    │
│                                                              │
│  ⏱️  Total time: 2-5 seconds                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│              BROWSER - LOCAL TESTING                         │
│                                                              │
│  http://localhost:3000                                       │
│  Testing changes from Claude branch...                       │
│                                                              │
│  User decision:                                              │
│  ✅ Satisfied → Merge branch (locally or PR)                │
│  ❌ Changes needed → Go back to Claude Code                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Component Design Updates

### Component 1: Claude Branch Detector (NEW)

**Purpose:** Monitor remote for new/updated Claude branches

```python
# service/claude_branch_detector.py

class ClaudeBranchDetector:
    """
    Detects Claude Code branches on remote repository.
    Monitors for new branches and updates to existing branches.
    """

    BRANCH_PATTERN = r'^claude/.*'  # Matches claude/* branches

    async def detect_new_branches(self, repo_path: Path) -> List[str]:
        """
        Detect newly created Claude branches.
        Returns list of branch names that are new since last check.
        """
        # Fetch all remote branches
        await self.run_git(repo_path, 'fetch', '--all')

        # Get all remote claude/* branches
        result = await self.run_git(
            repo_path,
            'branch', '-r',
            '--list', 'origin/claude/*'
        )

        remote_claude_branches = [
            branch.strip().replace('origin/', '')
            for branch in result.stdout.split('\n')
            if branch.strip()
        ]

        # Compare with previously known branches
        new_branches = [
            b for b in remote_claude_branches
            if b not in self.known_branches
        ]

        # Update known branches
        self.known_branches.update(remote_claude_branches)

        return new_branches

    async def detect_branch_updates(self, branch_name: str, repo_path: Path) -> bool:
        """
        Check if a Claude branch has new commits.
        Returns True if remote has updates.
        """
        # Fetch specific branch
        await self.run_git(repo_path, 'fetch', 'origin', branch_name)

        # Compare local and remote HEADs
        local_head = await self.get_commit_hash(repo_path, branch_name)
        remote_head = await self.get_commit_hash(repo_path, f'origin/{branch_name}')

        return local_head != remote_head

    def get_latest_claude_branch(self, repo_path: Path) -> Optional[str]:
        """
        Get the most recently created Claude branch.
        Uses commit timestamp to determine latest.
        """
        claude_branches = self.get_all_claude_branches(repo_path)
        if not claude_branches:
            return None

        # Sort by commit date (most recent first)
        branches_with_dates = []
        for branch in claude_branches:
            commit_date = self.get_branch_commit_date(repo_path, branch)
            branches_with_dates.append((branch, commit_date))

        branches_with_dates.sort(key=lambda x: x[1], reverse=True)
        return branches_with_dates[0][0]

    def extract_session_id(self, branch_name: str) -> Optional[str]:
        """
        Extract session ID from Claude branch name.
        Example: 'claude/add-feature-xyz123' → 'xyz123'
        """
        # Pattern: claude/{feature-name}-{sessionId}
        match = re.match(r'claude/.*-([A-Za-z0-9]+)$', branch_name)
        return match.group(1) if match else None
```

### Component 2: Branch Sync Manager (UPDATED)

**Purpose:** Manage syncing of specific Claude branches

```python
# service/branch_sync_manager.py

class BranchSyncManager:
    """
    Manages synchronization of Claude branches to local environment.
    Handles checkout, pull, and dev server coordination.
    """

    def __init__(self, config, dev_server_manager):
        self.config = config
        self.dev_server_manager = dev_server_manager
        self.active_branch = None  # Currently checked-out Claude branch

    async def sync_new_branch(self, repo_path: Path, branch_name: str):
        """
        Sync a newly created Claude branch.
        1. Fetch branch
        2. Checkout branch
        3. Restart dev server
        4. Notify user
        """
        try:
            self.notify_sync_start(branch_name)

            # Fetch the branch
            await self.run_git(repo_path, 'fetch', 'origin', branch_name)

            # Check if branch exists locally
            local_branches = await self.get_local_branches(repo_path)

            if branch_name in local_branches:
                # Branch exists, just switch to it
                await self.run_git(repo_path, 'checkout', branch_name)
                await self.run_git(repo_path, 'pull', 'origin', branch_name)
            else:
                # Create local branch tracking remote
                await self.run_git(
                    repo_path,
                    'checkout', '-b', branch_name,
                    f'origin/{branch_name}'
                )

            # Update active branch
            self.active_branch = branch_name

            # Restart dev server in context of new branch
            await self.dev_server_manager.restart_dev_server(repo_path)

            # Notify user
            self.notify_sync_complete(branch_name, repo_path)

        except Exception as e:
            self.notify_error(branch_name, e)

    async def sync_branch_update(self, repo_path: Path, branch_name: str):
        """
        Sync updates to existing Claude branch.
        Called when Claude pushes more commits to the same branch.
        """
        try:
            # Ensure we're on the correct branch
            current_branch = await self.get_current_branch(repo_path)
            if current_branch != branch_name:
                await self.run_git(repo_path, 'checkout', branch_name)

            # Pull latest changes
            await self.run_git(repo_path, 'pull', 'origin', branch_name)

            # Restart dev server to reflect changes
            await self.dev_server_manager.restart_dev_server(repo_path)

            # Notify user of update
            self.notify_branch_updated(branch_name)

        except Exception as e:
            self.notify_error(branch_name, e)

    async def switch_active_branch(self, repo_path: Path, branch_name: str):
        """
        Manually switch to a different Claude branch.
        User can call this to test older Claude branches.
        """
        if not branch_name.startswith('claude/'):
            raise ValueError("Only Claude branches can be set as active")

        await self.sync_new_branch(repo_path, branch_name)

    def get_active_branch(self) -> Optional[str]:
        """Get currently active Claude branch"""
        return self.active_branch
```

### Component 3: Sync Daemon (UPDATED)

**Purpose:** Main orchestration loop for Claude branch monitoring

```python
# service/sync_daemon.py

class SyncDaemon:
    """
    Background daemon optimized for Claude Code web workflow.
    Monitors for Claude branches and auto-syncs them.
    """

    def __init__(self, config):
        self.config = config
        self.branch_detector = ClaudeBranchDetector()
        self.branch_sync_manager = BranchSyncManager(
            config,
            DevServerManager(config)
        )
        self.webhook_receiver = WebhookReceiver(config)

    async def start(self):
        """Start sync daemon"""
        mode = self.config.get('sync.mode', 'hybrid')

        if mode in ['webhook', 'hybrid']:
            asyncio.create_task(self.webhook_receiver.start(self.on_webhook))

        if mode in ['polling', 'hybrid']:
            asyncio.create_task(self.polling_loop())

    async def polling_loop(self):
        """Main polling loop for detecting Claude branches"""
        while True:
            for repo_config in self.config.get('sync.repositories', []):
                repo_path = Path(repo_config['path']).expanduser()

                # Check for new Claude branches
                new_branches = await self.branch_detector.detect_new_branches(repo_path)

                if new_branches:
                    # Sync the latest branch
                    latest_branch = new_branches[0]  # Or use get_latest_claude_branch
                    await self.branch_sync_manager.sync_new_branch(
                        repo_path,
                        latest_branch
                    )

                # Check for updates to active branch
                active_branch = self.branch_sync_manager.get_active_branch()
                if active_branch:
                    has_updates = await self.branch_detector.detect_branch_updates(
                        active_branch,
                        repo_path
                    )
                    if has_updates:
                        await self.branch_sync_manager.sync_branch_update(
                            repo_path,
                            active_branch
                        )

            await asyncio.sleep(self.config.get('sync.polling.interval', 30))

    async def on_webhook(self, payload: dict):
        """
        Handle GitHub webhook for Claude branch events.
        Called when webhook is received.
        """
        event_type = payload.get('ref_type')  # 'branch'
        ref = payload.get('ref')  # 'claude/feature-name-xyz'

        # Only process Claude branches
        if not ref or not ref.startswith('claude/'):
            return

        repo_path = self.get_repo_path_from_payload(payload)

        if event_type == 'branch':
            # New branch created
            await self.branch_sync_manager.sync_new_branch(repo_path, ref)
        elif payload.get('commits'):
            # Push to existing branch
            await self.branch_sync_manager.sync_branch_update(repo_path, ref)
```

---

## ⚙️ Configuration Updates

```yaml
# config/sync.yaml

sync:
  mode: hybrid  # webhook (fast) + polling (reliable)

  # Claude branch detection
  claude_branches:
    pattern: '^claude/.*'  # Match all branches starting with 'claude/'
    auto_sync: true  # Automatically sync new Claude branches
    sync_latest_only: true  # Only sync the most recent Claude branch
    keep_history: 10  # Keep last 10 Claude branches locally

  # Webhook settings
  webhook:
    enabled: true
    port: 8766
    events:
      - create  # Branch created
      - push    # Commits pushed

  # Polling settings (fallback)
  polling:
    enabled: true
    interval: 30  # Check every 30 seconds
    check_active_branch_interval: 10  # Check active branch every 10s

  # Branch sync behavior
  branch_sync:
    auto_checkout: true  # Automatically checkout new Claude branch
    stash_before_checkout: true  # Stash uncommitted changes
    auto_pop_stash: false  # Don't auto-pop (might conflict)

  # Dev server behavior
  dev_server:
    auto_restart: true
    restart_on_branch_change: true  # Restart when switching branches
    restart_on_branch_update: true  # Restart when branch gets new commits
    open_browser: true  # Open browser after server ready
    browser_url: 'http://localhost:3000'  # Or auto-detect

  # Notification preferences
  notifications:
    on_new_branch: true
    on_branch_update: true
    on_sync_complete: true
    show_branch_name: true
    show_commit_count: true

  # Repository configuration
  repositories:
    - path: ~/Projects/my-app
      main_branch: main
      auto_sync_claude_branches: true
      dev_server_type: next
      dev_server_port: 3000
```

---

## 🔄 Revised Workflow Examples

### Example 1: New Feature from Claude

```
T=0s: Claude Code creates branch 'claude/add-auth-xyz123'
      Commits code, pushes to GitHub

T=1s: GitHub webhook → Local sync daemon
      "New branch detected: claude/add-auth-xyz123"

T=2s: Sync daemon:
      - git fetch origin claude/add-auth-xyz123
      - git checkout claude/add-auth-xyz123

T=3s: Dev server manager:
      - Kills old server
      - npm run dev

T=5s: Server ready
      - Notification: "Ready to test: claude/add-auth-xyz123"
      - Browser opens: http://localhost:3000

T=6s: User tests in browser
      ✅ Looks good!

T=60s: User merges:
       Option A: git checkout main && git merge claude/add-auth-xyz123
       Option B: Create PR on GitHub and merge
```

### Example 2: Claude Updates Existing Branch

```
T=0s: User testing on branch 'claude/add-auth-xyz123'
      Finds a bug, reports to Claude

T=10s: Claude fixes bug, pushes to same branch
       'claude/add-auth-xyz123'

T=11s: Sync daemon detects update
       "Branch claude/add-auth-xyz123 has new commits"

T=12s: Auto-pull:
       - git pull origin claude/add-auth-xyz123

T=13s: Dev server restarts automatically

T=15s: Notification: "Branch updated! Ready to retest."
       Browser refreshes (if hot reload enabled)

T=16s: User tests fix
       ✅ Bug fixed!
```

### Example 3: Multiple Claude Branches

```
Scenario: User has multiple Claude sessions

Branches:
- claude/add-auth-abc123 (created 2 hours ago)
- claude/fix-ui-def456 (created 1 hour ago)
- claude/new-feature-ghi789 (created 5 min ago) ← LATEST

Sync daemon behavior:
1. Detects all 3 branches
2. Auto-syncs LATEST: claude/new-feature-ghi789
3. User can manually switch:
   $ git-sync switch claude/fix-ui-def456
   → Daemon switches and restarts server

Active branch tracking:
- Only monitors active branch for updates
- Ignores updates to non-active Claude branches
- User can configure to sync all or latest-only
```

---

## 🎯 Critical Differences from Original Brainstorm

| Aspect | Original (Wrong) | Revised (Correct) |
|--------|------------------|-------------------|
| **Branch target** | main/master | claude/* branches |
| **Sync trigger** | Any commit to main | New Claude branch or update |
| **Checkout behavior** | Stay on main | Switch to Claude branch |
| **Merge responsibility** | N/A | User merges after testing |
| **Branch lifecycle** | N/A | Temporary (Claude session) |
| **Conflict risk** | High (main) | Low (isolated branches) |

---

## ✅ Next Steps

Now that we understand the actual Claude Code workflow, we can:

1. **Create accurate implementation plan**
   - Focus on Claude branch detection
   - Auto-checkout specific branches
   - Track active branch for updates

2. **Adjust component priorities**
   - Claude Branch Detector (CRITICAL)
   - Branch Sync Manager (CRITICAL)
   - Dev Server Manager (HIGH)
   - Webhook for instant sync (MEDIUM)

3. **Update git hooks logic**
   - Don't need environment detection for main
   - Claude uses feature branches already
   - Focus on branch cleanup after merge

**Ready to create the implementation plan with this correct understanding?**
