# Cloud-First Git Workflow - Architecture Brainstorm

## 🎯 Problem Statement

**Current Situation:**
The existing Git Workflow Guardian was designed for traditional **local-first development** where:
- Developers code locally on their machines
- Git hooks enforce workflow rules locally
- Code is pushed to remote for deployment

**Desired Situation:**
Need to support **cloud-first development** where:
- Primary coding happens in Claude Code on the web (cloud environment)
- Local CLI/PC is used for fast testing and viewing results
- Automated synchronization from cloud to local for testing
- Local modifications can be pushed as feature branches

**Key Insight:** Local environment becomes a "test viewer" rather than primary development environment.

---

## 🔄 Desired Workflow Analysis

### Step 1: Cloud Coding (Primary)
**Environment:** Claude Code on the web
**Actions:**
- Write code, fix bugs, add features
- Commit directly to working branch
- Push changes to remote repository

**Current Problem:** No automated trigger to local environment

### Step 2: Automated Local Sync (New Feature Needed)
**Environment:** Local PC/CLI
**Actions Needed:**
- Detect when remote branch has new commits
- Automatically run `git pull` to fetch latest changes
- Handle merge conflicts gracefully
- Notify user when sync is complete

**Current Problem:** This automation doesn't exist yet

### Step 3: Local Testing (Fast Feedback)
**Environment:** Local PC with dev server
**Actions:**
- Dev server automatically restarts (if applicable)
- View results in browser immediately
- Test functionality without waiting for Vercel build (5-10 min)

**Current Problem:** Manual `git pull` and dev server restart

### Step 4: Sync Back to Remote (Satisfaction)
**Environment:** Local PC/CLI
**Actions:**
- If satisfied, changes already in remote (from Step 1)
- No action needed unless local modifications made

### Step 5: Local Modifications (Optional)
**Environment:** Local PC/CLI
**Actions:**
- Make quick fixes or adjustments locally
- Commit to feature branch (not main)
- Push to remote
- Trigger Step 2 again if testing in cloud

---

## 🏗️ Proposed Architecture Changes

### Component 1: Cloud Commit Webhook Handler (NEW)

**Purpose:** Detect when commits are pushed from cloud environment

**Options:**

#### Option A: GitHub Webhooks (Recommended)
```yaml
Trigger: Push event to repository
→ GitHub sends webhook to local endpoint
→ Local service receives webhook
→ Triggers git pull + dev server restart
```

**Pros:**
- Real-time (< 1 second latency)
- Reliable
- No polling overhead

**Cons:**
- Requires local endpoint to be accessible (ngrok, tailscale, or public IP)
- More complex setup

#### Option B: Polling Remote (Simpler)
```yaml
Every 10-30 seconds:
→ Check remote for new commits (git fetch)
→ Compare local HEAD with remote HEAD
→ If different, trigger git pull + dev server restart
```

**Pros:**
- Simple to implement
- No external dependencies
- Works behind firewalls

**Cons:**
- 10-30 second delay
- Unnecessary git fetch calls
- Network overhead

#### Option C: Hybrid Approach (Best of Both)
```yaml
Primary: GitHub webhook for instant sync
Fallback: Polling every 60 seconds if webhook fails
```

**Pros:**
- Fast when webhooks work
- Reliable with polling fallback
- Best user experience

**Cons:**
- More complex implementation

### Component 2: Local Sync Daemon (NEW)

**Purpose:** Background service that keeps local environment in sync with remote

**Core Responsibilities:**
1. Listen for webhook notifications OR poll remote
2. Detect branch changes
3. Execute `git pull` safely
4. Handle merge conflicts
5. Trigger dev server lifecycle hooks
6. Notify user of sync status

**Implementation:**

```python
# service/sync_daemon.py

class SyncDaemon:
    """
    Background daemon that syncs local repository with remote.
    Optimized for cloud-first development workflow.
    """

    def __init__(self, config):
        self.config = config
        self.webhook_port = config.get('sync.webhook_port', 8766)
        self.poll_interval = config.get('sync.poll_interval', 30)
        self.mode = config.get('sync.mode', 'hybrid')  # webhook, polling, hybrid

    async def start(self):
        """Start sync daemon based on configured mode"""
        if self.mode in ['webhook', 'hybrid']:
            asyncio.create_task(self.start_webhook_server())

        if self.mode in ['polling', 'hybrid']:
            asyncio.create_task(self.start_polling_loop())

    async def start_webhook_server(self):
        """Start Flask/FastAPI webhook receiver"""
        # Listen on http://localhost:8766/webhook/github
        # Verify webhook signature
        # Trigger sync on valid webhook
        pass

    async def start_polling_loop(self):
        """Poll remote for changes every N seconds"""
        while True:
            for repo in self.get_monitored_repos():
                if await self.has_remote_changes(repo):
                    await self.sync_repository(repo)
            await asyncio.sleep(self.poll_interval)

    async def has_remote_changes(self, repo_path: Path) -> bool:
        """Check if remote has new commits"""
        result = await self.run_git(repo_path, 'fetch', '--dry-run')
        # Parse output to detect changes
        return "would update" in result.stdout.lower()

    async def sync_repository(self, repo_path: Path):
        """Safely sync repository with remote"""
        try:
            # 1. Stash local changes if any
            if self.has_uncommitted_changes(repo_path):
                await self.run_git(repo_path, 'stash', 'push', '-m', 'Auto-stash before cloud sync')

            # 2. Fetch latest changes
            await self.run_git(repo_path, 'fetch', 'origin')

            # 3. Get current branch
            branch = await self.get_current_branch(repo_path)

            # 4. Pull changes
            result = await self.run_git(repo_path, 'pull', 'origin', branch)

            # 5. Pop stash if any
            if self.has_stashed_changes(repo_path):
                await self.run_git(repo_path, 'stash', 'pop')

            # 6. Trigger dev server restart
            await self.trigger_dev_server_restart(repo_path)

            # 7. Notify user
            self.notify_sync_complete(repo_path, branch)

        except GitConflictError as e:
            # Handle merge conflicts
            self.notify_conflict(repo_path, e)
        except Exception as e:
            # Handle other errors
            self.notify_error(repo_path, e)

    async def trigger_dev_server_restart(self, repo_path: Path):
        """Restart dev server after sync"""
        project_type = self.detect_project_type(repo_path)

        if project_type == 'node':
            # Kill existing process, restart npm run dev
            await self.restart_npm_dev(repo_path)
        elif project_type == 'python':
            # Restart Flask/Django/FastAPI
            await self.restart_python_dev(repo_path)
        elif project_type == 'next':
            # Restart Next.js dev server
            await self.restart_next_dev(repo_path)
        # ... more project types
```

**Configuration:**

```yaml
# config/sync.yaml

sync:
  # Mode: webhook (real-time), polling (simple), hybrid (both)
  mode: hybrid

  # Webhook settings
  webhook:
    enabled: true
    port: 8766
    secret: ${GITHUB_WEBHOOK_SECRET}
    endpoint: /webhook/github

  # Polling settings (fallback or primary)
  polling:
    enabled: true
    interval: 30  # seconds

  # Auto-pull settings
  auto_pull:
    enabled: true
    stash_changes: true  # Stash uncommitted changes before pull
    auto_pop_stash: true  # Restore stashed changes after pull

  # Dev server settings
  dev_server:
    auto_restart: true
    detection:
      # Auto-detect project type
      node: ["package.json"]
      python: ["requirements.txt", "Pipfile", "pyproject.toml"]
      next: ["next.config.js", "next.config.ts"]
      react: ["package.json + src/"]
      vue: ["package.json + vue.config.js"]
      django: ["manage.py"]
      flask: ["app.py", "wsgi.py"]

    # Commands to restart dev server
    commands:
      node: "npm run dev"
      next: "npm run dev"
      react: "npm start"
      vue: "npm run serve"
      python: "python manage.py runserver"
      flask: "flask run"

    # Ports to check
    ports:
      node: 3000
      next: 3000
      react: 3000
      vue: 8080
      python: 8000
      flask: 5000

  # Notification settings
  notifications:
    on_sync_start: true
    on_sync_complete: true
    on_conflict: true
    on_error: true
    show_diff_summary: true  # Show what changed

  # Repository monitoring
  repositories:
    - path: ~/Projects/my-app
      branch: main
      auto_sync: true
      dev_server: node
    - path: ~/Projects/my-api
      branch: develop
      auto_sync: true
      dev_server: python
```

### Component 3: Modified Git Hooks (UPDATED)

**Purpose:** Relax restrictions for cloud-first workflow while maintaining safety

**Changes Needed:**

#### Pre-commit Hook (Updated)
```bash
#!/bin/bash
# hooks/pre-commit.sh (Cloud-first version)

BRANCH=$(git branch --show-current)
COMMIT_SOURCE="${2:-manual}"  # manual, merge, squash, etc.

# Allow commits to main ONLY from cloud environment
# Detect cloud environment by checking for CLAUDE_CODE_SESSION or similar
if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
    if [[ -z "$CLAUDE_CODE_SESSION" && -z "$CLOUD_COMMIT_ALLOWED" ]]; then
        # Local commit to main - block it
        echo "🚨 LOCAL commits to main are not allowed"
        echo "📋 Cloud commits to main are OK (from Claude Code)"
        echo "💡 For local changes, create a feature branch:"
        echo "   git checkout -b feature/my-changes"
        exit 1
    fi
fi

# Continue with other checks...
```

#### New Hook: Post-merge (Updated)
```bash
#!/bin/bash
# hooks/post-merge.sh (Cloud-first version)

# Triggered after git pull completes
BRANCH=$(git branch --show-current)

# Check if this was an auto-sync pull
if [[ -n "$AUTO_SYNC_PULL" ]]; then
    echo "✅ Auto-sync complete from cloud"
    echo "📊 Branch: $BRANCH"
    echo "🔄 Dev server will restart shortly..."
fi

# Trigger dev server restart signal
touch .git/restart-dev-server
```

### Component 4: Dev Server Manager (NEW)

**Purpose:** Manage dev server lifecycle (start, stop, restart)

```python
# service/dev_server_manager.py

class DevServerManager:
    """
    Manages development server lifecycle for cloud-first workflow.
    Automatically restarts servers after git pull.
    """

    def __init__(self, config):
        self.config = config
        self.running_servers = {}  # repo_path → process

    def detect_project_type(self, repo_path: Path) -> Optional[str]:
        """Auto-detect project type based on files"""
        if (repo_path / "next.config.js").exists():
            return "next"
        elif (repo_path / "package.json").exists():
            pkg = json.loads((repo_path / "package.json").read_text())
            if "react" in pkg.get("dependencies", {}):
                return "react"
            elif "vue" in pkg.get("dependencies", {}):
                return "vue"
            return "node"
        elif (repo_path / "manage.py").exists():
            return "django"
        elif (repo_path / "app.py").exists() or (repo_path / "wsgi.py").exists():
            return "flask"
        return None

    async def start_dev_server(self, repo_path: Path):
        """Start dev server for repository"""
        project_type = self.detect_project_type(repo_path)
        if not project_type:
            return  # No dev server needed

        command = self.config.get(f'dev_server.commands.{project_type}')
        if not command:
            return

        # Kill existing server if running
        if repo_path in self.running_servers:
            await self.stop_dev_server(repo_path)

        # Start new server process
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self.running_servers[repo_path] = {
            'process': process,
            'type': project_type,
            'started_at': datetime.now()
        }

        # Wait for server to be ready
        port = self.config.get(f'dev_server.ports.{project_type}', 3000)
        await self.wait_for_port(port, timeout=30)

        # Notify user
        self.notify_server_ready(repo_path, project_type, port)

    async def stop_dev_server(self, repo_path: Path):
        """Stop dev server for repository"""
        if repo_path not in self.running_servers:
            return

        server_info = self.running_servers[repo_path]
        process = server_info['process']

        # Graceful shutdown
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except asyncio.TimeoutError:
            # Force kill if not responding
            process.kill()

        del self.running_servers[repo_path]

    async def restart_dev_server(self, repo_path: Path):
        """Restart dev server (called after git pull)"""
        await self.stop_dev_server(repo_path)
        await asyncio.sleep(1)  # Brief pause
        await self.start_dev_server(repo_path)

    async def wait_for_port(self, port: int, timeout: int = 30):
        """Wait for port to be available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://localhost:{port}'):
                        return True
            except:
                await asyncio.sleep(0.5)
        return False
```

### Component 5: Cloud Environment Detection (NEW)

**Purpose:** Differentiate between cloud and local commits

**Implementation:**

```python
# service/environment.py

class EnvironmentDetector:
    """Detect if code is running in cloud or local environment"""

    @staticmethod
    def is_cloud_environment() -> bool:
        """Check if running in Claude Code or other cloud IDE"""
        # Check environment variables
        cloud_indicators = [
            'CLAUDE_CODE_SESSION',
            'CODESPACES',  # GitHub Codespaces
            'GITPOD_WORKSPACE_ID',  # Gitpod
            'REPL_ID',  # Replit
            'CLOUD_SHELL',  # Google Cloud Shell
        ]

        return any(os.getenv(indicator) for indicator in cloud_indicators)

    @staticmethod
    def get_environment_type() -> str:
        """Get specific environment type"""
        if os.getenv('CLAUDE_CODE_SESSION'):
            return 'claude-code'
        elif os.getenv('CODESPACES'):
            return 'github-codespaces'
        elif os.getenv('GITPOD_WORKSPACE_ID'):
            return 'gitpod'
        else:
            return 'local'

    @staticmethod
    def allow_main_commit() -> bool:
        """Determine if commits to main should be allowed"""
        # Allow in cloud, block in local
        return EnvironmentDetector.is_cloud_environment()
```

**Usage in Git Hooks:**

```bash
# In pre-commit hook
if python -c "from service.environment import EnvironmentDetector; import sys; sys.exit(0 if EnvironmentDetector.allow_main_commit() else 1)"; then
    echo "✅ Cloud environment detected - commit allowed"
    exit 0
else
    echo "🚨 Local environment - create feature branch"
    exit 1
fi
```

---

## 🔧 Implementation Phases

### Phase 1: Core Sync Infrastructure (CRITICAL)
**Priority:** HIGH
**Time Estimate:** 2-3 days

**Tasks:**
1. Create `SyncDaemon` class with polling support
2. Implement safe `git pull` with stash/unstash
3. Add conflict detection and user notification
4. Create basic configuration in `config/sync.yaml`
5. Add systemd/launchd service installer for sync daemon
6. Test basic sync workflow

**Deliverables:**
- `service/sync_daemon.py` (~400 lines)
- `config/sync.yaml` (configuration)
- `scripts/install_sync_service.sh`
- `tests/test_sync_daemon.py`

### Phase 2: Dev Server Management (IMPORTANT)
**Priority:** HIGH
**Time Estimate:** 2-3 days

**Tasks:**
1. Create `DevServerManager` class
2. Implement project type detection (Node, Python, Next.js, etc.)
3. Add process lifecycle management (start/stop/restart)
4. Implement port availability checking
5. Add dev server status monitoring
6. Create notification system for server readiness

**Deliverables:**
- `service/dev_server_manager.py` (~300 lines)
- Dev server configuration in `config/sync.yaml`
- `tests/test_dev_server_manager.py`

### Phase 3: Webhook Support (ENHANCED)
**Priority:** MEDIUM
**Time Estimate:** 2-3 days

**Tasks:**
1. Create Flask/FastAPI webhook receiver
2. Implement GitHub webhook signature verification
3. Add ngrok/tailscale integration for local endpoint
4. Create webhook registration helper
5. Add webhook → sync trigger integration
6. Test with real GitHub webhooks

**Deliverables:**
- `service/webhook_receiver.py` (~200 lines)
- Webhook setup documentation
- `scripts/setup_webhook.sh` (helper script)
- `tests/test_webhook.py`

### Phase 4: Modified Git Hooks (ADAPTATION)
**Priority:** MEDIUM
**Time Estimate:** 1-2 days

**Tasks:**
1. Update pre-commit hook to detect cloud environment
2. Add `CLOUD_COMMIT_ALLOWED` environment variable support
3. Modify post-merge hook for auto-sync notifications
4. Create environment detector utility
5. Update hook installation scripts
6. Test in both cloud and local environments

**Deliverables:**
- Updated `hooks/pre-commit.sh`
- Updated `hooks/post-merge.sh`
- `service/environment.py` (~100 lines)
- `tests/test_environment.py`

### Phase 5: Dashboard Integration (POLISH)
**Priority:** LOW
**Time Estimate:** 1-2 days

**Tasks:**
1. Add sync status to dashboard
2. Show last sync time, sync history
3. Add manual sync trigger button
4. Display dev server status
5. Show sync errors/conflicts in UI
6. Add sync statistics and graphs

**Deliverables:**
- Updated `service/dashboard.py`
- Updated dashboard UI templates
- New API endpoints for sync data

### Phase 6: Documentation & Testing (ESSENTIAL)
**Priority:** HIGH
**Time Estimate:** 1-2 days

**Tasks:**
1. Update README with cloud-first workflow
2. Create setup guide for webhook configuration
3. Document ngrok/tailscale setup
4. Add troubleshooting for sync issues
5. Create video/GIF demos
6. Write integration tests

**Deliverables:**
- Updated `README.md`
- `docs/CLOUD_FIRST_SETUP.md`
- `docs/WEBHOOK_SETUP.md`
- Integration test suite

---

## 🎯 User Experience Flow

### Scenario 1: Cloud Coding → Local Testing

1. **Developer codes in Claude Code**
   ```
   [Cloud IDE] → Edit files → Git commit → Git push
   ```

2. **Webhook triggers (< 1 second) or Polling detects (10-30 seconds)**
   ```
   GitHub → Webhook → Local PC (port 8766)
   OR
   Local PC polls GitHub every 30s
   ```

3. **Sync daemon executes**
   ```
   [Local PC]
   📥 Detecting changes...
   🔄 Pulling latest code...
   ✅ Sync complete (5 files changed)
   🔄 Restarting dev server...
   ✅ Server ready at http://localhost:3000
   🌐 Opening browser...
   ```

4. **Developer tests in browser**
   ```
   [Browser] → http://localhost:3000 → View changes
   ```

5. **Developer satisfied**
   ```
   No action needed - changes already in remote!
   ```

### Scenario 2: Local Quick Fix → Cloud Sync

1. **Developer makes quick fix locally**
   ```
   [Local PC] → Edit files → Test in browser
   ```

2. **Developer commits to feature branch**
   ```
   [Local PC]
   $ git checkout -b fix/quick-adjustment
   $ git add .
   $ git commit -m "fix: quick UI adjustment"
   $ git push origin fix/quick-adjustment
   ```

3. **Feature branch available in cloud**
   ```
   [Cloud IDE] → Git pull (if needed) → Continue work
   ```

### Scenario 3: Conflict Handling

1. **Conflict detected during auto-pull**
   ```
   [Local PC]
   ⚠️  Sync conflict detected!
   📝 You have uncommitted changes in:
       - src/components/Header.tsx

   Options:
   1. Stash your changes and pull
   2. Commit your changes to a feature branch
   3. Skip this sync
   ```

2. **Developer chooses action**
   ```
   User clicks: "Stash and pull"
   → Changes stashed
   → Git pull executes
   → Stash popped (may need manual merge)
   ```

---

## 📊 Configuration Examples

### Minimal Setup (Polling Only)

```yaml
# config/sync.yaml

sync:
  mode: polling  # Simple, no webhooks needed

  polling:
    enabled: true
    interval: 30  # Check every 30 seconds

  auto_pull:
    enabled: true
    stash_changes: true

  dev_server:
    auto_restart: true

  repositories:
    - path: ~/Projects/my-app
      branch: main
```

### Advanced Setup (Webhook + Polling Fallback)

```yaml
# config/sync.yaml

sync:
  mode: hybrid  # Best of both worlds

  webhook:
    enabled: true
    port: 8766
    secret: ${GITHUB_WEBHOOK_SECRET}
    tunnel: ngrok  # or tailscale

  polling:
    enabled: true
    interval: 60  # Slower polling as fallback

  auto_pull:
    enabled: true
    stash_changes: true
    auto_pop_stash: true
    conflict_strategy: stash  # stash, abort, force

  dev_server:
    auto_restart: true
    restart_delay: 2  # seconds
    health_check: true
    open_browser: true  # Auto-open browser after restart

  notifications:
    desktop: true
    sound: true
    show_diff: true

  repositories:
    - path: ~/Projects/frontend
      branch: main
      dev_server: next
      auto_sync: true

    - path: ~/Projects/backend
      branch: main
      dev_server: flask
      auto_sync: true
```

---

## 🔒 Security Considerations

### 1. Webhook Security
- **Signature Verification:** Always verify GitHub webhook signatures
- **Secret Management:** Store webhook secret in environment variables
- **Endpoint Protection:** Use HTTPS with ngrok/tailscale
- **Rate Limiting:** Prevent webhook spam

### 2. Auto-Pull Safety
- **Stash First:** Always stash uncommitted changes before pull
- **Conflict Detection:** Never force-pull, alert user on conflicts
- **Backup Strategy:** Keep stash history for recovery
- **Branch Protection:** Only auto-pull allowed branches

### 3. Dev Server Security
- **Localhost Binding:** Dev servers bind to localhost by default
- **No Public Exposure:** Don't expose dev servers to internet
- **Process Isolation:** Run dev servers with user permissions
- **Port Conflict Detection:** Check for port conflicts before starting

---

## 🚀 Quick Start Commands

### Install Sync Daemon

```bash
# Install sync service
./scripts/install_sync_service.sh

# Start sync daemon
systemctl --user start git-sync-daemon
# OR
launchctl load ~/Library/LaunchAgents/com.git-sync-daemon.plist

# Check status
systemctl --user status git-sync-daemon

# View logs
journalctl --user -u git-sync-daemon -f
```

### Setup Webhook (Optional)

```bash
# Install ngrok
brew install ngrok  # or download from ngrok.com

# Start ngrok tunnel
ngrok http 8766

# Copy webhook URL (e.g., https://abc123.ngrok.io)
# Add to GitHub repository:
#   Settings → Webhooks → Add webhook
#   Payload URL: https://abc123.ngrok.io/webhook/github
#   Content type: application/json
#   Secret: <your-secret>
#   Events: Just the push event

# Set webhook secret
export GITHUB_WEBHOOK_SECRET="your-secret-here"
echo "GITHUB_WEBHOOK_SECRET=your-secret-here" >> ~/.env
```

### Test Sync

```bash
# Trigger manual sync
git-sync --repo ~/Projects/my-app

# Check sync status
git-sync status

# View sync history
git-sync log
```

---

## 📈 Benefits of Cloud-First Workflow

### Speed
- ✅ No waiting for Vercel builds (5-10 min → 2-5 seconds)
- ✅ Instant local testing with hot reload
- ✅ Faster iteration cycles

### Flexibility
- ✅ Code anywhere (cloud IDE always available)
- ✅ Test locally (fast feedback)
- ✅ Push from anywhere (local or cloud)

### Reliability
- ✅ Automated sync (no manual git pull)
- ✅ Conflict detection (safe auto-pull)
- ✅ Dev server always ready

### Developer Experience
- ✅ Less context switching
- ✅ Focus on coding in cloud
- ✅ Local environment just works

---

## 🎬 Next Steps

1. **Review this brainstorm** - Ensure it matches your vision
2. **Prioritize features** - What's most critical for your workflow?
3. **Create implementation plan** - Break down into actionable tasks
4. **Prototype core sync** - Start with polling-based auto-pull
5. **Test with real project** - Validate workflow with your actual codebase
6. **Iterate and enhance** - Add webhooks, dev server management, etc.

---

## 💡 Alternative Approaches

### Option A: Git-based File Watching (Simpler)
Instead of webhooks/polling, use git's built-in capabilities:
```bash
# In local repo, watch for remote changes
git fetch --all && git log HEAD..origin/main --oneline
```

### Option B: Cloud Shell Script (Minimal)
Simple bash script that runs in background:
```bash
#!/bin/bash
while true; do
    git fetch origin
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    if [ $LOCAL != $REMOTE ]; then
        git pull && npm run dev
    fi
    sleep 30
done
```

### Option C: VS Code Remote Development
Use VS Code Remote SSH to code locally but execute in cloud:
- Combines cloud and local benefits
- No sync needed (remote editing)
- Might be simpler than custom sync daemon

---

## ❓ Questions to Consider

1. **How many projects will you sync?**
   - Single project → Simple polling sufficient
   - Multiple projects → Need robust daemon

2. **How fast do you need sync?**
   - Immediate (< 5s) → Need webhooks
   - Within 30s → Polling is fine

3. **What dev servers do you use?**
   - Node/React/Next → npm run dev
   - Python/Flask → flask run
   - Others → Need to support

4. **Do you commit locally often?**
   - Rarely → Focus on cloud→local sync
   - Often → Need bidirectional sync

5. **Conflict resolution preference?**
   - Auto-stash → Automated workflow
   - Manual merge → More control

---

**Status:** 📝 Brainstorm Complete - Ready for Review
**Next:** Create actionable implementation plan based on your feedback
