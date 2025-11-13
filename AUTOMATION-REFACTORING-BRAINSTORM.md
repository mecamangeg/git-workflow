# Automation Refactoring: Always Serve Latest Commit

**Problem Statement:** Claude Code on the web generates random branch names for each response. The automation must reliably detect and serve the absolute latest commit across all Claude branches, regardless of branch naming.

---

## 🎯 Core Challenge

### Current Behavior
```
User makes request 1 → Claude creates claude/fix-bug-ABC123
User makes request 2 → Claude creates claude/add-feature-XYZ789
User makes request 3 → Claude creates claude/refactor-code-QWE456
```

**Problem:**
- Automation watches one branch at a time
- If Claude switches branches between responses, old branch is still being watched
- Latest code might be on a different branch
- No way to know which branch has the "latest" work

### Desired Behavior
```
Automation should:
1. Detect ALL Claude branches (claude/*, ai/*)
2. Determine which has the LATEST commit (by timestamp)
3. Automatically switch to that branch
4. Pull and restart server with latest code
5. Continue watching for even newer commits on ANY Claude branch
```

---

## 💡 Solution Approaches

### Approach 1: Latest Commit Timestamp (RECOMMENDED)

**Concept:** Find the branch with the most recent commit timestamp.

**Algorithm:**
```python
1. Fetch all remote branches
2. Filter by patterns (claude/*, ai/*)
3. For each matching branch:
   - Get latest commit timestamp
   - Get latest commit hash
4. Sort by timestamp (newest first)
5. Switch to branch with newest commit
6. Pull and restart server
```

**Pros:**
✅ Works with any branch naming scheme
✅ Reliable - uses git commit metadata
✅ Handles out-of-order pushes
✅ No dependency on branch name patterns

**Cons:**
⚠️ Requires fetching commit info for all branches (more git operations)
⚠️ May switch branches frequently if multiple sessions active

**Implementation:**
```python
def find_latest_claude_branch(self):
    """Find Claude branch with most recent commit"""
    # Fetch all branches
    subprocess.run(['git', 'fetch', '--all', '--prune'])

    # Get all remote branches matching patterns
    result = subprocess.run(
        ['git', 'branch', '-r'],
        capture_output=True, text=True
    )

    branches = []
    for line in result.stdout.split('\n'):
        branch = line.strip()
        for pattern in self.config['claude_branch_patterns']:
            if re.match(pattern, branch.replace('origin/', '')):
                branches.append(branch)

    # Get commit timestamp for each branch
    branch_timestamps = []
    for branch in branches:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', branch],
            capture_output=True, text=True
        )
        timestamp = int(result.stdout.strip())
        branch_timestamps.append((branch, timestamp))

    # Sort by timestamp (newest first)
    branch_timestamps.sort(key=lambda x: x[1], reverse=True)

    if branch_timestamps:
        latest_branch = branch_timestamps[0][0].replace('origin/', '')
        latest_timestamp = branch_timestamps[0][1]
        return latest_branch, latest_timestamp

    return None, None
```

---

### Approach 2: Session ID Parsing (If predictable naming)

**Concept:** Parse session IDs from branch names if they follow a pattern.

**Assumptions:**
- Branch names contain session IDs or timestamps
- Example: `claude/feature-20250113-103045` or `claude/session-abc123`

**Algorithm:**
```python
1. Fetch all Claude branches
2. Extract session ID or timestamp from branch name
3. Sort by session ID/timestamp
4. Switch to newest session's branch
```

**Pros:**
✅ Fast - no need to fetch commit metadata
✅ Works well if naming is consistent

**Cons:**
❌ Fragile - breaks if naming convention changes
❌ Doesn't work with truly random names
❌ Can't detect which session is actually latest if naming is unreliable

---

### Approach 3: GitHub API Integration (Cloud-native)

**Concept:** Use GitHub API to find most recently pushed branch.

**Algorithm:**
```python
1. Call GitHub API: GET /repos/{owner}/{repo}/branches
2. Sort by 'push_date' or last commit date
3. Find latest Claude branch
4. Switch to that branch
```

**Pros:**
✅ Authoritative - GitHub knows the truth
✅ Can get additional metadata (pusher, commit message, etc.)
✅ No heavy git operations needed

**Cons:**
⚠️ Requires GitHub token and API setup
⚠️ Rate limited (60 requests/hour without auth, 5000 with auth)
⚠️ Doesn't work with non-GitHub remotes
⚠️ Network dependency

---

### Approach 4: Multi-Branch Concurrent Monitoring

**Concept:** Monitor ALL Claude branches simultaneously, switch on any update.

**Algorithm:**
```python
1. Fetch all Claude branches
2. Track commit hash for EACH branch
3. On each check:
   - Fetch all branches
   - Compare each branch's remote vs local commit
   - If ANY branch has new commits:
     - Switch to that branch
     - Pull
     - Restart server
```

**Pros:**
✅ Most responsive - catches updates immediately
✅ Handles concurrent development on multiple branches

**Cons:**
⚠️ Complex - more state to track
⚠️ May thrash between branches if multiple active
⚠️ Higher resource usage

---

### Approach 5: Hybrid - Configurable Modes

**Concept:** Support multiple modes via configuration.

**Modes:**
1. **Sticky Mode** (current behavior)
   - Stay on current branch
   - Only sync that branch

2. **Latest Mode** (new)
   - Always switch to branch with newest commit
   - Follow the latest work wherever it is

3. **Session Mode** (advanced)
   - Track session ID from branch name
   - Follow branches from same session
   - Switch sessions when new one detected

**Configuration:**
```yaml
# .sync.yaml
branch_tracking_mode: 'latest'  # sticky | latest | session

# Sticky mode: stay on current branch
# Latest mode: always follow newest commit
# Session mode: follow session-based branches
```

---

## 🏆 Recommended Solution

**Implement Approach 1 (Latest Commit Timestamp) + Approach 5 (Configurable Modes)**

### Why This Combination?

1. **Solves the core problem**: Works with random branch names
2. **Flexible**: Users can choose behavior via config
3. **Reliable**: Uses git metadata (timestamps), not naming conventions
4. **Future-proof**: Works regardless of how Claude names branches

### Configuration

```yaml
# .sync.yaml

# Branch tracking mode
branch_tracking_mode: 'latest'  # sticky | latest

# When 'latest': always switch to branch with newest commit
# When 'sticky': stay on current branch (original behavior)

# Minimum time difference to trigger branch switch (seconds)
min_branch_switch_interval: 60  # Don't switch if commits <60s apart

# Claude branch patterns
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'

# Rest of config...
```

### Behavior by Mode

#### Mode: `sticky` (Original Behavior)
```
Current branch: claude/feature-A
Watch loop:
  1. Check claude/feature-A for new commits
  2. If found, pull and restart
  3. Never switch branches

Use case: Single development session, stable branch
```

#### Mode: `latest` (New Behavior)
```
Available branches:
  - claude/feature-A (last commit: 10:00 AM)
  - claude/feature-B (last commit: 10:15 AM)  ← Latest!
  - claude/feature-C (last commit: 9:45 AM)

Watch loop:
  1. Fetch all Claude branches
  2. Find branch with newest commit (feature-B)
  3. If different from current:
     - Switch to feature-B
     - Pull
     - Restart server
  4. Continue monitoring all branches

Use case: Claude creating new branches per response
```

---

## 🔧 Implementation Plan

### Phase 1: Core Latest-Branch Detection

**File:** `mini_sync.py`

**New methods:**
```python
class MiniSync:
    def find_latest_claude_branch(self) -> tuple[str, int]:
        """Find Claude branch with most recent commit

        Returns:
            (branch_name, commit_timestamp)
        """
        pass

    def should_switch_branch(self, current_branch, latest_branch,
                            current_ts, latest_ts) -> bool:
        """Determine if should switch to latest branch

        Considers:
        - Time difference (min_branch_switch_interval)
        - Current tracking mode
        - Local changes
        """
        pass

    def switch_and_sync_branch(self, branch_name) -> bool:
        """Switch to branch and sync

        Steps:
        1. Check for local changes (stash if needed)
        2. Checkout branch
        3. Pull latest
        4. Restart server
        """
        pass
```

**Modified watch loop:**
```python
def watch(self):
    """Watch for changes based on tracking mode"""

    while True:
        try:
            mode = self.config.get('branch_tracking_mode', 'sticky')

            if mode == 'latest':
                # Latest mode: find and switch to newest branch
                latest_branch, latest_ts = self.find_latest_claude_branch()
                current_branch = self.get_current_branch()
                current_ts = self.get_branch_timestamp(current_branch)

                if self.should_switch_branch(current_branch, latest_branch,
                                            current_ts, latest_ts):
                    log_info(f"Switching to latest branch: {latest_branch}")
                    self.switch_and_sync_branch(latest_branch)
                elif self.has_new_commits(current_branch):
                    log_info(f"New commits on current branch: {current_branch}")
                    self.sync_current_branch()

            else:  # sticky mode
                # Original behavior: stay on current branch
                if self.has_new_commits():
                    self.sync_current_branch()

            time.sleep(self.interval)

        except Exception as e:
            log_error(f"Error in watch loop: {e}")
            time.sleep(self.interval)
```

### Phase 2: Configuration

**File:** `.sync.yaml.example`

```yaml
# Branch Tracking Mode
# - 'sticky': Stay on current branch (original behavior)
# - 'latest': Always switch to branch with newest commit
branch_tracking_mode: 'latest'

# Minimum seconds between branch switches
# Prevents thrashing if multiple branches active
min_branch_switch_interval: 60

# Claude branch patterns to monitor
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'

# Auto-start dev server (CRITICAL)
auto_start_server: true

# Run tests before restarting server
run_tests: false

# Rest of config...
```

### Phase 3: Safety Features

**Prevent issues:**

1. **Local changes protection:**
   ```python
   def has_local_changes(self) -> bool:
       result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True)
       return bool(result.stdout.strip())

   def switch_and_sync_branch(self, branch_name):
       if self.has_local_changes():
           log_warning("Local changes detected, stashing...")
           subprocess.run(['git', 'stash', 'push', '-m',
                          f'Auto-stash before switch to {branch_name}'])
   ```

2. **Branch switch throttling:**
   ```python
   def should_switch_branch(self, current_branch, latest_branch,
                           current_ts, latest_ts):
       # Don't switch if time difference too small
       min_interval = self.config.get('min_branch_switch_interval', 60)
       time_diff = latest_ts - current_ts

       if time_diff < min_interval:
           log_info(f"Time diff {time_diff}s < {min_interval}s, not switching")
           return False

       return True
   ```

3. **Notification of branch switches:**
   ```python
   def switch_and_sync_branch(self, branch_name):
       old_branch = self.get_current_branch()

       # Switch and sync...

       log_header(f"Branch Switch: {old_branch} → {branch_name}")
       log_info(f"Reason: Latest commit found on {branch_name}")
       log_success("Server now serving latest code from newest branch")
   ```

---

## 📊 Comparison Matrix

| Feature | Sticky Mode | Latest Mode |
|---------|-------------|-------------|
| **Branch switching** | Never | Automatic |
| **Tracks** | Current branch only | All Claude branches |
| **Use case** | Single session | Multi-session/random branches |
| **Responsiveness** | Fast (1 branch) | Medium (all branches) |
| **Complexity** | Low | Medium |
| **Resource usage** | Low | Medium |
| **Handles random names** | ❌ No | ✅ Yes |
| **Best for** | Stable development | Claude Code web workflow |

---

## 🎬 Example Scenarios

### Scenario 1: Multiple Quick Responses

**Timeline:**
```
10:00 - User: "Add login page"
        Claude pushes to: claude/add-login-session_ABC
        Automation: Switches to claude/add-login-session_ABC
                   Pulls, restarts server

10:02 - User: "Also add logout"
        Claude pushes to: claude/add-logout-session_XYZ  ← New branch!
        Automation: Detects newer commit (10:02 > 10:00)
                   Switches to claude/add-logout-session_XYZ
                   Pulls, restarts server

10:05 - User: "Fix styling"
        Claude pushes to: claude/fix-styling-session_QWE ← Newer!
        Automation: Detects newer commit (10:05 > 10:02)
                   Switches to claude/fix-styling-session_QWE
                   Pulls, restarts server
```

**Result:** Server always shows the latest work, regardless of branch names.

### Scenario 2: Concurrent Sessions (Edge Case)

**Timeline:**
```
10:00 - Session A pushes to: claude/feature-A-session_111
10:01 - Session B pushes to: claude/feature-B-session_222
10:02 - Session A pushes again to: claude/feature-A-session_111

Branch timestamps:
- claude/feature-A-session_111: 10:02 (most recent)
- claude/feature-B-session_222: 10:01

Automation: Switches to claude/feature-A-session_111 (newest)
```

**With throttling (60s interval):**
```
10:00 - Switch to session_111
10:01 - Detect session_222 (newer by 1 min)
        But: Only 1 min newer, < 60s threshold
        Action: Stay on session_111
10:02 - Detect update on session_111
        Action: Pull and restart (same branch)
```

### Scenario 3: Returning to Old Work

**Timeline:**
```
10:00 - Claude pushes to: claude/feature-new-session_ABC
        Automation: Switches to session_ABC

11:00 - User: "Go back and fix the old feature"
        Claude pushes to: claude/feature-old-session_XYZ

        Problem: session_XYZ might be an older branch
        Solution: Check commit timestamp, not branch creation

        If commit on session_XYZ is at 11:00, it's newer than 10:00
        Automation: Switches to session_XYZ (newest commit)
```

---

## 🚦 Edge Cases & Solutions

### Edge Case 1: Network Delays

**Problem:** Branch A pushed at 10:00, but fetch delay means we see it at 10:05.
Meanwhile Branch B pushed at 10:03, seen immediately.

**Solution:** Use commit timestamp from git metadata, not fetch time.
```python
# Use: git log -1 --format=%ct (commit timestamp)
# Not: current time or fetch time
```

### Edge Case 2: Rebased Branches

**Problem:** Branch gets rebased, commit timestamps change.

**Solution:** Track both commit hash and timestamp. If hash changes, it's a new commit.
```python
def has_new_commits(self, branch):
    old_hash = self.tracked_commits.get(branch)
    new_hash = self.get_branch_commit_hash(branch)
    return old_hash != new_hash
```

### Edge Case 3: Deleted Branches

**Problem:** Claude deletes old branches, automation tries to switch to deleted branch.

**Solution:** Prune deleted branches and handle errors gracefully.
```python
try:
    subprocess.run(['git', 'checkout', branch], check=True)
except subprocess.CalledProcessError:
    log_warning(f"Branch {branch} no longer exists, finding next latest")
    # Continue to next newest branch
```

### Edge Case 4: Local Uncommitted Changes

**Problem:** Can't switch branches with uncommitted changes.

**Solution:** Stash automatically with descriptive message.
```python
if self.has_local_changes():
    subprocess.run(['git', 'stash', 'push', '-m',
                   f'Auto-stash at {datetime.now()} before switch'])
    log_info("Local changes stashed (retrieve with: git stash pop)")
```

---

## 📈 Performance Optimization

### Optimization 1: Cache Branch Metadata

**Problem:** Fetching commit timestamps for all branches is slow.

**Solution:** Cache timestamps, only update on fetch.
```python
class MiniSync:
    def __init__(self):
        self.branch_cache = {}  # {branch: (commit_hash, timestamp)}

    def get_branch_timestamp(self, branch):
        # Check cache first
        if branch in self.branch_cache:
            cached_hash, cached_ts = self.branch_cache[branch]
            current_hash = self.get_branch_commit_hash(branch)
            if current_hash == cached_hash:
                return cached_ts  # Use cached timestamp

        # Fetch fresh timestamp
        timestamp = self._fetch_branch_timestamp(branch)
        commit_hash = self.get_branch_commit_hash(branch)
        self.branch_cache[branch] = (commit_hash, timestamp)
        return timestamp
```

### Optimization 2: Incremental Fetch

**Problem:** `git fetch --all` is slow with many branches.

**Solution:** Only fetch Claude branches.
```python
def fetch_claude_branches(self):
    for pattern in self.config['claude_branch_patterns']:
        # Fetch only matching refs
        subprocess.run(['git', 'fetch', 'origin',
                       f'refs/heads/{pattern}:refs/remotes/origin/{pattern}'])
```

### Optimization 3: Parallel Timestamp Fetching

**Problem:** Getting timestamps for 10+ branches serially is slow.

**Solution:** Use concurrent execution.
```python
from concurrent.futures import ThreadPoolExecutor

def get_all_branch_timestamps(self, branches):
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(self.get_branch_timestamp, branches)
    return list(results)
```

---

## 🎯 Final Recommendation

### Implement "Latest Mode" as Default for Claude Code Web

**Configuration:**
```yaml
# .sync.yaml - Optimized for Claude Code on the web

# CRITICAL: Use 'latest' mode for Claude Code web
branch_tracking_mode: 'latest'

# Don't switch too frequently (prevents thrashing)
min_branch_switch_interval: 30  # 30 seconds minimum between switches

# Claude branch patterns
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'

# Fast polling for responsive updates
# (Set via: python mini_sync.py --watch --interval 20)

# Auto-start server
auto_start_server: true

# Skip tests for faster iteration (optional)
run_tests: false

# Custom dev server command
dev_commands:
  next: "npm run dev -- -p 3011"
```

**Start command:**
```bash
python mini_sync.py --watch --interval 20
```

**Result:**
- Checks every 20 seconds
- Finds branch with newest commit across ALL Claude branches
- Switches automatically if different and >30s newer
- Pulls latest code
- Restarts server
- **Always serves the absolute latest commit, regardless of branch name**

---

## 📝 Summary

**Problem:** Claude creates random branch names, need to serve latest commit always.

**Solution:** Track ALL Claude branches, find the one with the newest commit timestamp, switch to it automatically.

**Implementation:** Add `branch_tracking_mode: 'latest'` config option with timestamp-based branch detection.

**Benefits:**
✅ Works with any branch naming scheme
✅ Always serves latest code
✅ Handles concurrent development
✅ Robust and reliable
✅ Configurable (can use old behavior if needed)

**Next Steps:**
1. Implement `find_latest_claude_branch()` method
2. Add `branch_tracking_mode` config option
3. Update watch loop to support both modes
4. Add safety features (stashing, throttling)
5. Test with multiple concurrent branches
6. Update documentation
