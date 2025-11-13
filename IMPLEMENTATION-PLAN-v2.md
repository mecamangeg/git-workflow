# Cloud-First Workflow Refactor - Implementation Plan

## 📋 Overview

This document provides actionable tasks for refactoring the Git Workflow Guardian to support cloud-first development with Claude Code on the web.

**Based on:**
- Official Claude Code documentation analysis
- Cloud-first workflow requirements
- User feedback on notification system improvements

**Key Features:**
- Claude branch auto-detection and sync
- Automated test running (official recommendation)
- CLI mode detection (avoid conflicts with "Open in CLI")
- Sequential notification queue (one at a time)
- Notification history/review system
- Dev server auto-restart
- Webhook + polling hybrid approach

---

## 🎯 Project Goals

### Primary Objectives
1. **Eliminate manual git pull** - Automate branch sync when Claude pushes
2. **Fast local testing** - 100x faster than Vercel (5-10 min → 2-5 sec)
3. **Automated dev server** - Auto-restart on branch changes
4. **Better notifications** - Sequential queue, dismissible, reviewable history
5. **Hybrid workflow support** - Work seamlessly with "Open in CLI" feature

### Success Criteria
- ✅ Claude branch detected within 1-30 seconds of push
- ✅ Local checkout and dev server ready in < 5 seconds
- ✅ Tests run automatically on Claude branches
- ✅ One notification shown at a time (queue system)
- ✅ Notification history accessible for review
- ✅ No conflicts during CLI mode operations
- ✅ Works on Windows, Linux, macOS

---

## 📦 Implementation Phases

### Phase 0: Planning & Architecture (CURRENT)
**Status:** ✅ Complete
- Research and documentation complete
- Architecture designed
- Ready for implementation

### Phase 1: Core Sync Infrastructure (CRITICAL)
**Priority:** HIGH
**Estimated Time:** 3-4 days
**Dependencies:** None

Core components for detecting and syncing Claude branches.

### Phase 2: Notification Queue System (CRITICAL)
**Priority:** HIGH
**Estimated Time:** 2-3 days
**Dependencies:** None (can run parallel with Phase 1)

Refactor notification system for sequential display and history.

### Phase 3: Test Runner Integration (IMPORTANT)
**Priority:** MEDIUM
**Estimated Time:** 1-2 days
**Dependencies:** Phase 1 complete

Auto-run tests on Claude branches (official recommendation).

### Phase 4: Dev Server Management (IMPORTANT)
**Priority:** MEDIUM
**Estimated Time:** 2-3 days
**Dependencies:** Phase 1 complete

Automated dev server lifecycle management.

### Phase 5: Webhook Integration (ENHANCED)
**Priority:** MEDIUM
**Estimated Time:** 2-3 days
**Dependencies:** Phase 1 complete

Real-time sync via GitHub webhooks.

### Phase 6: CLI Mode Detection (SAFETY)
**Priority:** MEDIUM
**Estimated Time:** 1-2 days
**Dependencies:** Phase 1 complete

Detect "Open in CLI" mode and pause sync to avoid conflicts.

### Phase 7: Dashboard Integration (POLISH)
**Priority:** LOW
**Estimated Time:** 1-2 days
**Dependencies:** Phase 1, 2 complete

Update existing dashboard with sync status and notification history.

### Phase 8: Documentation & Testing (ESSENTIAL)
**Priority:** HIGH
**Estimated Time:** 2-3 days
**Dependencies:** All phases

Comprehensive documentation and integration tests.

---

## 📝 Detailed Task Breakdown

---

## PHASE 1: Core Sync Infrastructure

### SYNC-001: Claude Branch Detector
**Priority:** CRITICAL
**Time Estimate:** 1 day
**Dependencies:** None

**Description:**
Create service to detect Claude branches on remote repository using flexible pattern matching.

**Implementation:**
```python
# service/claude_branch_detector.py

class ClaudeBranchDetector:
    """Detect and track Claude Code branches on remote"""

    def __init__(self, config):
        self.config = config
        self.patterns = config.get('sync.claude_branches.patterns', [
            r'^claude/.*'
        ])
        self.known_branches = set()

    async def detect_new_branches(self, repo_path: Path) -> List[str]:
        """Detect newly created Claude branches"""
        pass

    async def detect_branch_updates(self, branch: str, repo_path: Path) -> bool:
        """Check if Claude branch has new commits"""
        pass

    def matches_claude_pattern(self, branch_name: str) -> bool:
        """Check if branch matches any Claude pattern"""
        pass

    def get_latest_claude_branch(self, repo_path: Path) -> Optional[str]:
        """Get most recently created Claude branch"""
        pass
```

**Files to Create:**
- `service/claude_branch_detector.py` (~250 lines)

**Tests:**
- `tests/test_claude_branch_detector.py`

**Acceptance Criteria:**
- ✅ Detects branches matching configurable patterns
- ✅ Returns only new branches since last check
- ✅ Identifies branch updates (new commits)
- ✅ Sorts by creation date to find latest
- ✅ Handles git fetch errors gracefully
- ✅ Works with multiple concurrent Claude branches

---

### SYNC-002: Branch Sync Manager
**Priority:** CRITICAL
**Time Estimate:** 1.5 days
**Dependencies:** SYNC-001

**Description:**
Manage synchronization of Claude branches to local environment. Handle checkout, pull, and coordination.

**Implementation:**
```python
# service/branch_sync_manager.py

class BranchSyncManager:
    """Manage syncing of Claude branches to local"""

    def __init__(self, config, notifier):
        self.config = config
        self.notifier = notifier
        self.active_branch = None

    async def sync_new_branch(self, repo_path: Path, branch_name: str):
        """Sync newly created Claude branch"""
        # 1. Fetch branch
        # 2. Checkout (create tracking branch if needed)
        # 3. Update active_branch
        # 4. Notify user
        pass

    async def sync_branch_update(self, repo_path: Path, branch_name: str):
        """Sync updates to existing Claude branch"""
        # 1. Ensure on correct branch
        # 2. Pull latest changes
        # 3. Notify user
        pass

    async def switch_active_branch(self, repo_path: Path, branch: str):
        """Manually switch to different Claude branch"""
        pass

    def get_active_branch(self) -> Optional[str]:
        """Get currently active Claude branch"""
        return self.active_branch

    async def handle_stash(self, repo_path: Path, operation: str):
        """Stash/unstash changes safely"""
        pass
```

**Files to Create:**
- `service/branch_sync_manager.py` (~300 lines)

**Tests:**
- `tests/test_branch_sync_manager.py`

**Acceptance Criteria:**
- ✅ Successfully checks out new Claude branches
- ✅ Creates local tracking branches automatically
- ✅ Pulls updates to existing branches
- ✅ Stashes uncommitted changes before sync (if configured)
- ✅ Tracks active branch state
- ✅ Handles branch switch conflicts gracefully
- ✅ Notifies user at each step

---

### SYNC-003: Sync Daemon Core
**Priority:** CRITICAL
**Time Estimate:** 1.5 days
**Dependencies:** SYNC-001, SYNC-002

**Description:**
Main orchestration daemon for Claude branch monitoring with polling support.

**Implementation:**
```python
# service/sync_daemon.py

class SyncDaemon:
    """Background daemon for Claude branch synchronization"""

    def __init__(self, config):
        self.config = config
        self.branch_detector = ClaudeBranchDetector(config)
        self.branch_sync_manager = BranchSyncManager(config, notifier)
        self.running = False

    async def start(self):
        """Start sync daemon"""
        self.running = True
        mode = self.config.get('sync.mode', 'polling')

        if mode in ['polling', 'hybrid']:
            asyncio.create_task(self.polling_loop())

    async def polling_loop(self):
        """Main polling loop for detecting Claude branches"""
        while self.running:
            for repo_config in self.config.get('sync.repositories', []):
                await self.check_repository(repo_config)
            await asyncio.sleep(self.config.get('sync.polling.interval', 30))

    async def check_repository(self, repo_config: dict):
        """Check single repository for Claude branch changes"""
        repo_path = Path(repo_config['path']).expanduser()

        # Detect new branches
        new_branches = await self.branch_detector.detect_new_branches(repo_path)
        if new_branches:
            latest = new_branches[0]
            await self.branch_sync_manager.sync_new_branch(repo_path, latest)

        # Check active branch for updates
        active = self.branch_sync_manager.get_active_branch()
        if active:
            has_updates = await self.branch_detector.detect_branch_updates(
                active, repo_path
            )
            if has_updates:
                await self.branch_sync_manager.sync_branch_update(
                    repo_path, active
                )

    async def stop(self):
        """Stop sync daemon"""
        self.running = False
```

**Files to Create:**
- `service/sync_daemon.py` (~350 lines)

**Tests:**
- `tests/test_sync_daemon.py`

**Acceptance Criteria:**
- ✅ Polls repositories at configured interval
- ✅ Detects new Claude branches
- ✅ Detects updates to active branch
- ✅ Handles multiple repositories
- ✅ Graceful shutdown
- ✅ Error handling and retry logic
- ✅ Logging for debugging

---

### SYNC-004: Configuration Schema
**Priority:** CRITICAL
**Time Estimate:** 0.5 days
**Dependencies:** None

**Description:**
Create configuration schema for sync daemon settings.

**Configuration File:**
```yaml
# config/sync.yaml

sync:
  # Sync mode: polling, webhook, hybrid
  mode: polling  # Start with polling, add webhook later

  # Claude branch detection
  claude_branches:
    # Flexible patterns (exact convention not in official docs)
    patterns:
      - '^claude/.*'
      - '^ai/.*'         # Potential alternative
      - '^assistant/.*'  # Another alternative

    # Auto-sync behavior
    auto_sync: true
    sync_latest_only: true  # Only sync most recent branch
    keep_history: 10  # Keep last 10 Claude branches locally

  # Polling settings
  polling:
    enabled: true
    interval: 30  # Check every 30 seconds
    active_branch_interval: 10  # Check active branch every 10s

  # Branch sync behavior
  branch_sync:
    auto_checkout: true
    stash_before_checkout: true
    auto_pop_stash: false  # Don't auto-pop (might conflict)
    create_tracking_branch: true

  # Repository monitoring
  repositories:
    - path: ~/Projects/my-app
      main_branch: main
      auto_sync_claude_branches: true

    - path: ~/Projects/my-api
      main_branch: develop
      auto_sync_claude_branches: true

  # Logging
  logging:
    level: INFO
    file: ~/.git-workflow-guardian/sync.log
    max_size_mb: 10
```

**Files to Create:**
- `config/sync.yaml` (~100 lines)
- `config/sync.schema.json` (JSON schema for validation)

**Acceptance Criteria:**
- ✅ All sync settings configurable
- ✅ Sensible defaults provided
- ✅ Schema validation implemented
- ✅ Multi-repository support
- ✅ Example configurations provided

---

### SYNC-005: Service Installer
**Priority:** HIGH
**Time Estimate:** 0.5 days
**Dependencies:** SYNC-003

**Description:**
Create installer script for sync daemon as system service.

**Files to Create:**
- `scripts/install_sync_daemon.sh` (Linux/macOS)
- `scripts/install_sync_daemon.ps1` (Windows)

**Implementation:**

**Linux (systemd):**
```bash
# scripts/install_sync_daemon.sh

#!/bin/bash
# Install sync daemon as systemd user service

SERVICE_FILE=~/.config/systemd/user/git-sync-daemon.service

cat > $SERVICE_FILE <<EOF
[Unit]
Description=Git Workflow Guardian - Claude Sync Daemon
After=network.target

[Service]
Type=simple
ExecStart=$(which python3) -m service.sync_daemon
WorkingDirectory=$(pwd)
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable git-sync-daemon
systemctl --user start git-sync-daemon
```

**Windows (Task Scheduler):**
```powershell
# scripts/install_sync_daemon.ps1

# Create scheduled task for sync daemon
$action = New-ScheduledTaskAction -Execute "python" -Argument "-m service.sync_daemon"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "GitSyncDaemon" -Action $action -Trigger $trigger -Settings $settings
```

**Acceptance Criteria:**
- ✅ Installs on Linux (systemd)
- ✅ Installs on macOS (launchd)
- ✅ Installs on Windows (Task Scheduler)
- ✅ Auto-starts on boot
- ✅ Auto-restarts on crash
- ✅ Includes uninstall option

---

## PHASE 2: Notification Queue System

### NOTIFY-001: Notification Queue Manager
**Priority:** CRITICAL
**Time Estimate:** 1.5 days
**Dependencies:** None

**Description:**
Create centralized notification queue that displays one notification at a time. Only shows next notification after previous is dismissed.

**Implementation:**
```python
# service/notification_queue.py

class NotificationQueue:
    """
    Manages notification queue - shows one notification at a time.
    Stores notification history for review.
    """

    def __init__(self, storage):
        self.queue = deque()  # Pending notifications
        self.current = None   # Currently displayed notification
        self.history = []     # All notifications (for review)
        self.storage = storage  # SQLite storage
        self.lock = asyncio.Lock()

    async def add_notification(self, notification: Notification):
        """Add notification to queue"""
        async with self.lock:
            # Save to history immediately
            self.history.append(notification)
            await self.storage.save_notification(notification)

            # Add to queue
            self.queue.append(notification)

            # Show if no current notification
            if self.current is None:
                await self.show_next()

    async def show_next(self):
        """Show next notification in queue"""
        if not self.queue:
            self.current = None
            return

        self.current = self.queue.popleft()
        await self.display_notification(self.current)

    async def dismiss_current(self):
        """Dismiss currently shown notification"""
        if self.current:
            # Mark as dismissed
            self.current.dismissed_at = datetime.now()
            await self.storage.update_notification(self.current)

            # Show next
            await self.show_next()

    def get_history(self, limit: int = 50) -> List[Notification]:
        """Get notification history for review"""
        return self.history[-limit:]

    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return len([n for n in self.history if not n.read])

    async def display_notification(self, notification: Notification):
        """Display notification using appropriate UI"""
        # Will use NotificationUI (tkinter/PyQt5)
        pass
```

**Data Model:**
```python
@dataclass
class Notification:
    id: str
    type: str  # 'branch_sync', 'test_result', 'conflict', 'error'
    severity: str  # 'info', 'warning', 'critical'
    title: str
    message: str
    actions: List[NotificationAction]  # Buttons/links
    created_at: datetime
    displayed_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    read: bool = False
    metadata: Dict = field(default_factory=dict)

@dataclass
class NotificationAction:
    label: str
    action: str  # 'open_browser', 'create_pr', 'view_diff', etc.
    data: Dict = field(default_factory=dict)
```

**Files to Create:**
- `service/notification_queue.py` (~400 lines)
- `service/notification_storage.py` (~150 lines) - SQLite persistence

**Tests:**
- `tests/test_notification_queue.py`

**Acceptance Criteria:**
- ✅ Shows one notification at a time
- ✅ Queues additional notifications
- ✅ Shows next after current dismissed
- ✅ Persists to SQLite
- ✅ Provides notification history
- ✅ Tracks read/unread status
- ✅ Thread-safe (async locks)

---

### NOTIFY-002: Notification UI Refactor
**Priority:** CRITICAL
**Time Estimate:** 1 day
**Dependencies:** NOTIFY-001

**Description:**
Refactor existing notification system (tkinter/PyQt5) to work with queue manager. Add dismiss button and better UI controls.

**Implementation:**
```python
# service/notification_ui.py

class NotificationUI:
    """
    UI for displaying notifications one at a time.
    Supports dismiss, action buttons, and history viewer.
    """

    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.current_window = None

    async def show_notification(self, notification: Notification):
        """Show notification popup"""
        if self.current_window:
            # Close previous if still open
            self.current_window.destroy()

        # Create new window
        self.current_window = self.create_notification_window(notification)

        # Mark as displayed
        notification.displayed_at = datetime.now()

    def create_notification_window(self, notification: Notification):
        """Create tkinter/PyQt5 notification window"""
        # Priority: Try PyQt5 first, fallback to tkinter
        if has_pyqt5():
            return self.create_pyqt5_window(notification)
        else:
            return self.create_tkinter_window(notification)

    def create_tkinter_window(self, notification: Notification):
        """Create tkinter notification (basic)"""
        window = tk.Toplevel()
        window.title(notification.title)

        # Icon based on severity
        icon = self.get_icon(notification.severity)

        # Message
        label = tk.Label(window, text=notification.message)
        label.pack(padx=20, pady=10)

        # Action buttons
        button_frame = tk.Frame(window)
        for action in notification.actions:
            btn = tk.Button(
                button_frame,
                text=action.label,
                command=lambda a=action: self.handle_action(a, notification)
            )
            btn.pack(side=tk.LEFT, padx=5)
        button_frame.pack(pady=10)

        # Dismiss button (always present)
        dismiss_btn = tk.Button(
            window,
            text="Dismiss",
            command=lambda: self.dismiss(notification, window)
        )
        dismiss_btn.pack(pady=5)

        # Close window after 60 seconds (auto-dismiss)
        window.after(60000, lambda: self.auto_dismiss(notification, window))

        return window

    def dismiss(self, notification: Notification, window):
        """Dismiss notification and show next"""
        window.destroy()
        asyncio.create_task(self.queue_manager.dismiss_current())

    def auto_dismiss(self, notification: Notification, window):
        """Auto-dismiss after timeout"""
        if window.winfo_exists():
            self.dismiss(notification, window)

    def handle_action(self, action: NotificationAction, notification: Notification):
        """Handle action button click"""
        if action.action == 'open_browser':
            webbrowser.open(action.data['url'])
        elif action.action == 'create_pr':
            self.open_pr_page(action.data)
        elif action.action == 'view_diff':
            self.show_diff(action.data)
        # ... more actions

        # Mark notification as read
        notification.read = True
```

**Files to Update:**
- `service/notifier.py` (refactor to use NotificationQueue)
- `service/notifier_pyqt5.py` (refactor to use NotificationQueue)

**Files to Create:**
- `service/notification_ui.py` (~350 lines)

**Tests:**
- `tests/test_notification_ui.py`

**Acceptance Criteria:**
- ✅ Shows one notification at a time
- ✅ Dismiss button works
- ✅ Action buttons work (open browser, create PR, etc.)
- ✅ Auto-dismisses after 60 seconds
- ✅ Supports both tkinter and PyQt5
- ✅ Visual distinction by severity (colors/icons)
- ✅ Properly positioned on screen
- ✅ Doesn't block other operations

---

### NOTIFY-003: Notification History Viewer
**Priority:** HIGH
**Time Estimate:** 1 day
**Dependencies:** NOTIFY-001, NOTIFY-002

**Description:**
Create UI for viewing notification history. Users can review dismissed/missed notifications.

**Implementation:**
```python
# service/notification_history_viewer.py

class NotificationHistoryViewer:
    """
    UI for viewing notification history.
    Shows all past notifications with filters.
    """

    def __init__(self, storage):
        self.storage = storage

    def show_history(self):
        """Show notification history window"""
        window = tk.Toplevel()
        window.title("Notification History")
        window.geometry("800x600")

        # Filter controls
        filter_frame = self.create_filter_controls(window)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        # Notification list
        list_frame = self.create_notification_list(window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Action buttons
        button_frame = self.create_action_buttons(window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

    def create_filter_controls(self, parent):
        """Create filter controls (date range, type, severity)"""
        frame = tk.Frame(parent)

        # Date range
        tk.Label(frame, text="Date Range:").pack(side=tk.LEFT)
        self.date_from = tk.Entry(frame)
        self.date_from.pack(side=tk.LEFT, padx=5)
        tk.Label(frame, text="to").pack(side=tk.LEFT)
        self.date_to = tk.Entry(frame)
        self.date_to.pack(side=tk.LEFT, padx=5)

        # Type filter
        tk.Label(frame, text="Type:").pack(side=tk.LEFT, padx=10)
        self.type_var = tk.StringVar(value="All")
        type_menu = tk.OptionMenu(frame, self.type_var,
            "All", "branch_sync", "test_result", "conflict", "error")
        type_menu.pack(side=tk.LEFT)

        # Apply filter button
        apply_btn = tk.Button(frame, text="Apply", command=self.apply_filters)
        apply_btn.pack(side=tk.LEFT, padx=10)

        return frame

    def create_notification_list(self, parent):
        """Create scrollable notification list"""
        frame = tk.Frame(parent)

        # Scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox
        self.listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Load notifications
        self.load_notifications()

        # Double-click to view details
        self.listbox.bind('<Double-Button-1>', self.show_notification_details)

        return frame

    def load_notifications(self):
        """Load notifications from storage"""
        notifications = self.storage.get_all_notifications(limit=100)
        self.listbox.delete(0, tk.END)

        for notif in notifications:
            # Format: "[Time] [Type] Title (Read/Unread)"
            status = "✓" if notif.read else "●"
            text = f"{status} [{notif.created_at:%H:%M}] {notif.title}"
            self.listbox.insert(tk.END, text)

    def show_notification_details(self, event):
        """Show detailed view of selected notification"""
        selection = self.listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        notification = self.notifications[idx]

        # Show details window
        self.show_details_window(notification)

    def show_details_window(self, notification: Notification):
        """Show notification details in popup"""
        details = tk.Toplevel()
        details.title(f"Notification Details - {notification.title}")
        details.geometry("600x400")

        # Title
        tk.Label(details, text=notification.title, font=('Arial', 14, 'bold')).pack(pady=10)

        # Message
        text = tk.Text(details, wrap=tk.WORD, height=10)
        text.insert('1.0', notification.message)
        text.config(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Metadata
        meta_frame = tk.LabelFrame(details, text="Details")
        meta_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(meta_frame, text=f"Type: {notification.type}").pack(anchor=tk.W)
        tk.Label(meta_frame, text=f"Severity: {notification.severity}").pack(anchor=tk.W)
        tk.Label(meta_frame, text=f"Created: {notification.created_at}").pack(anchor=tk.W)
        if notification.dismissed_at:
            tk.Label(meta_frame, text=f"Dismissed: {notification.dismissed_at}").pack(anchor=tk.W)

        # Action buttons (if still applicable)
        if notification.actions:
            action_frame = tk.Frame(details)
            for action in notification.actions:
                btn = tk.Button(
                    action_frame,
                    text=action.label,
                    command=lambda a=action: self.handle_action(a)
                )
                btn.pack(side=tk.LEFT, padx=5)
            action_frame.pack(pady=10)

        # Close button
        tk.Button(details, text="Close", command=details.destroy).pack(pady=5)
```

**Files to Create:**
- `service/notification_history_viewer.py` (~400 lines)

**Tests:**
- `tests/test_notification_history_viewer.py`

**Acceptance Criteria:**
- ✅ Shows all past notifications
- ✅ Filters by date range, type, severity
- ✅ Double-click to view details
- ✅ Shows read/unread status
- ✅ Can re-trigger actions from history
- ✅ Search functionality
- ✅ Export to CSV option
- ✅ Clear history option

---

### NOTIFY-004: Database Schema Update
**Priority:** HIGH
**Time Estimate:** 0.5 days
**Dependencies:** None

**Description:**
Update SQLite database schema to store notification queue and history.

**Schema:**
```sql
-- service/schema_notifications.sql

-- Notification history table
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'branch_sync', 'test_result', 'conflict', 'error'
    severity TEXT NOT NULL,  -- 'info', 'warning', 'critical'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    actions JSON,  -- List of NotificationAction as JSON
    metadata JSON,  -- Additional data as JSON
    created_at TIMESTAMP NOT NULL,
    displayed_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    read BOOLEAN DEFAULT 0,
    repo_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_notifications_created
    ON notifications(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_type
    ON notifications(type);

CREATE INDEX IF NOT EXISTS idx_notifications_severity
    ON notifications(severity);

CREATE INDEX IF NOT EXISTS idx_notifications_read
    ON notifications(read);

-- Notification queue table (pending notifications)
CREATE TABLE IF NOT EXISTS notification_queue (
    position INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id TEXT NOT NULL,
    added_at TIMESTAMP NOT NULL,
    FOREIGN KEY (notification_id) REFERENCES notifications(id)
);

-- Current notification (only one row)
CREATE TABLE IF NOT EXISTS current_notification (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Only one row
    notification_id TEXT,
    shown_at TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES notifications(id)
);
```

**Files to Update:**
- `service/schema.sql` (add notification tables)
- `service/state.py` (add notification storage methods)

**Files to Create:**
- `service/notification_storage.py` (~200 lines)

**Acceptance Criteria:**
- ✅ Stores notification history
- ✅ Tracks queue position
- ✅ Indexes for fast queries
- ✅ JSON support for actions/metadata
- ✅ Foreign key constraints
- ✅ Migration from old schema

---

### NOTIFY-005: System Tray Integration
**Priority:** MEDIUM
**Time Estimate:** 1 day
**Dependencies:** NOTIFY-001, NOTIFY-002

**Description:**
Add system tray icon to access notification history and controls without opening full UI.

**Implementation:**
```python
# service/system_tray.py

class SystemTrayIcon:
    """
    System tray icon for quick access to notifications.
    Shows unread count, history viewer, and settings.
    """

    def __init__(self, notification_queue, history_viewer):
        self.notification_queue = notification_queue
        self.history_viewer = history_viewer
        self.icon = self.create_tray_icon()

    def create_tray_icon(self):
        """Create system tray icon"""
        # Use pystray library
        icon = pystray.Icon(
            "git-workflow-guardian",
            self.create_icon_image(),
            "Git Workflow Guardian",
            self.create_menu()
        )
        return icon

    def create_menu(self):
        """Create tray icon menu"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda: f"Unread: {self.notification_queue.get_unread_count()}",
                self.show_unread,
                default=True
            ),
            pystray.MenuItem("View History", self.show_history),
            pystray.MenuItem("Settings", self.show_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pause Sync", self.toggle_sync),
            pystray.MenuItem("Exit", self.exit_app)
        )

    def update_icon(self):
        """Update icon badge with unread count"""
        unread = self.notification_queue.get_unread_count()
        self.icon.icon = self.create_icon_image(badge=unread if unread > 0 else None)

    def show_history(self):
        """Show notification history viewer"""
        self.history_viewer.show_history()
```

**Files to Create:**
- `service/system_tray.py` (~250 lines)

**Additional Dependencies:**
- `pystray` library for cross-platform system tray

**Acceptance Criteria:**
- ✅ Shows tray icon on Windows/Linux/macOS
- ✅ Badge shows unread count
- ✅ Right-click menu with options
- ✅ Quick access to history
- ✅ Can pause/resume sync
- ✅ Settings access
- ✅ Graceful exit

---

## PHASE 3: Test Runner Integration

### TEST-001: Test Runner Component
**Priority:** MEDIUM
**Time Estimate:** 1 day
**Dependencies:** SYNC-002

**Description:**
Auto-run test suite on Claude branches (official recommendation from docs).

**Implementation:**
```python
# service/test_runner.py

class TestRunner:
    """
    Automatically run tests on Claude branches.
    Follows official Claude Code recommendation.
    """

    def __init__(self, config):
        self.config = config

    async def run_tests(self, repo_path: Path, project_type: str) -> TestResult:
        """Run test suite for project type"""
        command = self.get_test_command(project_type)
        if not command:
            return TestResult(skipped=True, reason="No test command configured")

        try:
            # Run tests with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.get('sync.auto_test.timeout', 300)
            )

            return TestResult(
                passed=process.returncode == 0,
                output=stdout.decode(),
                errors=stderr.decode(),
                duration=time.time() - start_time
            )

        except asyncio.TimeoutError:
            process.kill()
            return TestResult(passed=False, errors="Test timeout (5 min)")
        except Exception as e:
            return TestResult(passed=False, errors=str(e))

    def get_test_command(self, project_type: str) -> Optional[str]:
        """Get test command from config"""
        return self.config.get(f'sync.auto_test.commands.{project_type}')

    def detect_project_type(self, repo_path: Path) -> Optional[str]:
        """Auto-detect project type"""
        if (repo_path / 'package.json').exists():
            return 'node'
        elif (repo_path / 'pytest.ini').exists() or (repo_path / 'setup.py').exists():
            return 'python'
        # ... more detection
        return None
```

**Data Model:**
```python
@dataclass
class TestResult:
    passed: bool
    output: str = ""
    errors: str = ""
    duration: float = 0.0
    skipped: bool = False
    reason: str = ""
```

**Files to Create:**
- `service/test_runner.py` (~200 lines)

**Tests:**
- `tests/test_test_runner.py`

**Acceptance Criteria:**
- ✅ Runs npm test, pytest, etc.
- ✅ Configurable commands per project type
- ✅ Timeout protection (5 min default)
- ✅ Returns detailed test results
- ✅ Handles test failures gracefully
- ✅ Auto-detects project type

---

### TEST-002: Test Integration with Sync
**Priority:** MEDIUM
**Time Estimate:** 0.5 days
**Dependencies:** TEST-001, SYNC-002

**Description:**
Integrate test runner into branch sync workflow.

**Integration Points:**
```python
# In branch_sync_manager.py

async def sync_new_branch(self, repo_path: Path, branch_name: str):
    """Sync newly created Claude branch"""
    # ... existing code ...

    # Run tests if enabled
    if self.config.get('sync.auto_test.enabled'):
        project_type = self.test_runner.detect_project_type(repo_path)
        test_result = await self.test_runner.run_tests(repo_path, project_type)

        # Notify user of test results
        await self.notify_test_result(branch_name, test_result)

        # Optionally skip dev server if tests fail
        if not test_result.passed and self.config.get('sync.auto_test.skip_dev_on_failure'):
            return

    # Continue with dev server...
```

**Configuration:**
```yaml
# config/sync.yaml

sync:
  auto_test:
    enabled: true
    run_before_dev_server: true
    skip_dev_on_failure: false  # Still start server even if tests fail
    timeout: 300  # 5 minutes

    commands:
      node: "npm test"
      next: "npm test"
      python: "pytest"
      django: "python manage.py test"
      flask: "pytest"

    notifications:
      on_pass: true
      on_fail: true
      show_output: true  # Show test output in notification
```

**Acceptance Criteria:**
- ✅ Tests run before dev server starts
- ✅ Test results sent to notification queue
- ✅ Configurable behavior on test failure
- ✅ Test output available in notification
- ✅ Can skip tests for specific repos

---

## PHASE 4: Dev Server Management

### DEV-001: Dev Server Manager
**Priority:** MEDIUM
**Time Estimate:** 2 days
**Dependencies:** SYNC-002

**Description:**
Manage dev server lifecycle (start, stop, restart) automatically.

**Implementation:**
```python
# service/dev_server_manager.py

class DevServerManager:
    """
    Manages development server lifecycle.
    Automatically restarts servers after branch sync.
    """

    def __init__(self, config):
        self.config = config
        self.running_servers = {}  # repo_path → ServerInfo

    def detect_project_type(self, repo_path: Path) -> Optional[str]:
        """Auto-detect project type based on files"""
        if (repo_path / 'next.config.js').exists():
            return 'next'
        elif (repo_path / 'package.json').exists():
            pkg = json.loads((repo_path / 'package.json').read_text())
            if 'react' in str(pkg.get('dependencies', {})):
                return 'react'
            elif 'vue' in str(pkg.get('dependencies', {})):
                return 'vue'
            return 'node'
        elif (repo_path / 'manage.py').exists():
            return 'django'
        elif (repo_path / 'app.py').exists():
            return 'flask'
        return None

    async def start_dev_server(self, repo_path: Path):
        """Start dev server for repository"""
        project_type = self.detect_project_type(repo_path)
        if not project_type:
            return  # No dev server needed

        # Get command from config
        command = self.config.get(f'sync.dev_server.commands.{project_type}')
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

        # Store server info
        port = self.config.get(f'sync.dev_server.ports.{project_type}', 3000)
        self.running_servers[repo_path] = ServerInfo(
            process=process,
            type=project_type,
            port=port,
            started_at=datetime.now()
        )

        # Wait for server to be ready
        if await self.wait_for_port(port, timeout=30):
            # Server ready!
            await self.notify_server_ready(repo_path, project_type, port)

            # Open browser if configured
            if self.config.get('sync.dev_server.open_browser'):
                webbrowser.open(f'http://localhost:{port}')
        else:
            # Server failed to start
            await self.notify_server_failed(repo_path, project_type)

    async def stop_dev_server(self, repo_path: Path):
        """Stop dev server for repository"""
        if repo_path not in self.running_servers:
            return

        server_info = self.running_servers[repo_path]
        process = server_info.process

        # Graceful shutdown
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except asyncio.TimeoutError:
            # Force kill if not responding
            process.kill()
            await process.wait()

        del self.running_servers[repo_path]

    async def restart_dev_server(self, repo_path: Path):
        """Restart dev server (called after git pull)"""
        await self.stop_dev_server(repo_path)
        await asyncio.sleep(1)  # Brief pause
        await self.start_dev_server(repo_path)

    async def wait_for_port(self, port: int, timeout: int = 30) -> bool:
        """Wait for port to be available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://localhost:{port}', timeout=1):
                        return True
            except:
                await asyncio.sleep(0.5)
        return False

@dataclass
class ServerInfo:
    process: asyncio.subprocess.Process
    type: str
    port: int
    started_at: datetime
```

**Files to Create:**
- `service/dev_server_manager.py` (~350 lines)

**Tests:**
- `tests/test_dev_server_manager.py`

**Configuration:**
```yaml
sync:
  dev_server:
    auto_restart: true
    restart_on_branch_change: true
    restart_on_branch_update: true
    open_browser: true
    wait_for_ready: true
    ready_timeout: 30

    # Dev server commands
    commands:
      node: "npm run dev"
      next: "npm run dev"
      react: "npm start"
      vue: "npm run serve"
      python: "python manage.py runserver"
      django: "python manage.py runserver"
      flask: "flask run"

    # Expected ports
    ports:
      node: 3000
      next: 3000
      react: 3000
      vue: 8080
      python: 8000
      django: 8000
      flask: 5000
```

**Acceptance Criteria:**
- ✅ Auto-detects project type
- ✅ Starts appropriate dev server command
- ✅ Waits for server to be ready
- ✅ Opens browser when ready
- ✅ Restarts on branch change
- ✅ Graceful shutdown
- ✅ Handles server failures
- ✅ Multiple repos support

---

### DEV-002: Dev Server Health Check
**Priority:** LOW
**Time Estimate:** 0.5 days
**Dependencies:** DEV-001

**Description:**
Monitor dev server health and restart if crashed.

**Implementation:**
```python
# In dev_server_manager.py

async def health_check_loop(self):
    """Periodic health check for running servers"""
    while True:
        for repo_path, server_info in list(self.running_servers.items()):
            # Check if process still running
            if server_info.process.returncode is not None:
                # Process died
                await self.notify_server_crashed(repo_path, server_info)

                # Auto-restart if configured
                if self.config.get('sync.dev_server.auto_restart_on_crash'):
                    await self.start_dev_server(repo_path)

            # Check if port still responsive
            elif not await self.is_port_responsive(server_info.port):
                # Port not responsive but process alive
                await self.notify_server_unresponsive(repo_path, server_info)

                # Restart
                await self.restart_dev_server(repo_path)

        await asyncio.sleep(30)  # Check every 30 seconds
```

**Acceptance Criteria:**
- ✅ Detects crashed servers
- ✅ Auto-restarts if configured
- ✅ Checks port responsiveness
- ✅ Notifies user of issues

---

## PHASE 5: Webhook Integration

### WEBHOOK-001: Webhook Receiver
**Priority:** MEDIUM
**Time Estimate:** 1.5 days
**Dependencies:** SYNC-003

**Description:**
Create webhook receiver for instant GitHub branch notifications.

**Implementation:**
```python
# service/webhook_receiver.py

from flask import Flask, request, jsonify
import hmac
import hashlib

class WebhookReceiver:
    """
    Receives GitHub webhooks for instant branch sync.
    Verifies webhook signatures for security.
    """

    def __init__(self, config):
        self.config = config
        self.app = Flask(__name__)
        self.secret = config.get('sync.webhook.secret')
        self.callbacks = []

        # Register routes
        self.app.route('/webhook/github', methods=['POST'])(self.handle_github_webhook)

    def start(self, callback):
        """Start webhook server"""
        self.callbacks.append(callback)
        port = self.config.get('sync.webhook.port', 8766)
        self.app.run(host='127.0.0.1', port=port, debug=False)

    def handle_github_webhook(self):
        """Handle incoming GitHub webhook"""
        # Verify signature
        if not self.verify_signature(request):
            return jsonify({'error': 'Invalid signature'}), 401

        # Parse payload
        payload = request.json
        event_type = request.headers.get('X-GitHub-Event')

        # Process based on event type
        if event_type == 'create':
            # Branch created
            ref = payload.get('ref')
            ref_type = payload.get('ref_type')

            if ref_type == 'branch' and self.is_claude_branch(ref):
                # Trigger sync
                asyncio.create_task(self.trigger_sync(payload))

        elif event_type == 'push':
            # Push to existing branch
            ref = payload.get('ref', '').replace('refs/heads/', '')

            if self.is_claude_branch(ref):
                asyncio.create_task(self.trigger_sync(payload))

        return jsonify({'status': 'ok'}), 200

    def verify_signature(self, request):
        """Verify GitHub webhook signature"""
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            return False

        # Calculate expected signature
        mac = hmac.new(
            self.secret.encode(),
            msg=request.data,
            digestmod=hashlib.sha256
        )
        expected = 'sha256=' + mac.hexdigest()

        return hmac.compare_digest(expected, signature)

    def is_claude_branch(self, branch_name: str) -> bool:
        """Check if branch is a Claude branch"""
        patterns = self.config.get('sync.claude_branches.patterns', [])
        return any(re.match(pattern, branch_name) for pattern in patterns)

    async def trigger_sync(self, payload: dict):
        """Trigger sync callbacks"""
        for callback in self.callbacks:
            await callback(payload)
```

**Files to Create:**
- `service/webhook_receiver.py` (~250 lines)

**Tests:**
- `tests/test_webhook_receiver.py`

**Configuration:**
```yaml
sync:
  webhook:
    enabled: true
    port: 8766
    secret: ${GITHUB_WEBHOOK_SECRET}  # From environment
    endpoint: /webhook/github

    events:
      - create  # Branch created
      - push    # Commits pushed
```

**Setup Script:**
```bash
# scripts/setup_webhook.sh

#!/bin/bash
# Helper script to set up GitHub webhook

echo "Setting up GitHub webhook..."
echo "1. Generate webhook secret:"
WEBHOOK_SECRET=$(openssl rand -hex 32)
echo "   $WEBHOOK_SECRET"
echo ""
echo "2. Set environment variable:"
echo "   export GITHUB_WEBHOOK_SECRET='$WEBHOOK_SECRET'"
echo ""
echo "3. Start ngrok tunnel:"
echo "   ngrok http 8766"
echo ""
echo "4. Add webhook to GitHub:"
echo "   - Go to repository Settings → Webhooks → Add webhook"
echo "   - Payload URL: https://YOUR-NGROK-URL/webhook/github"
echo "   - Content type: application/json"
echo "   - Secret: (paste the secret above)"
echo "   - Events: Branch or tag creation, Pushes"
echo ""
```

**Acceptance Criteria:**
- ✅ Receives GitHub webhooks
- ✅ Verifies webhook signatures
- ✅ Filters Claude branches
- ✅ Triggers sync callbacks
- ✅ Handles create and push events
- ✅ Error handling and logging
- ✅ Setup documentation

---

### WEBHOOK-002: Ngrok/Tailscale Integration
**Priority:** LOW
**Time Estimate:** 1 day
**Dependencies:** WEBHOOK-001

**Description:**
Automatically set up tunnel (ngrok/tailscale) for webhook endpoint.

**Implementation:**
```python
# service/tunnel_manager.py

class TunnelManager:
    """
    Manages tunnel (ngrok/tailscale) for webhook endpoint.
    Automatically starts tunnel and registers with GitHub.
    """

    def __init__(self, config):
        self.config = config
        self.tunnel_url = None

    async def start_tunnel(self):
        """Start ngrok/tailscale tunnel"""
        tunnel_type = self.config.get('sync.webhook.tunnel', 'ngrok')

        if tunnel_type == 'ngrok':
            self.tunnel_url = await self.start_ngrok()
        elif tunnel_type == 'tailscale':
            self.tunnel_url = await self.start_tailscale()

        return self.tunnel_url

    async def start_ngrok(self):
        """Start ngrok tunnel"""
        port = self.config.get('sync.webhook.port', 8766)

        # Start ngrok process
        process = await asyncio.create_subprocess_shell(
            f'ngrok http {port} --log=stdout',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for ngrok to start and get URL
        await asyncio.sleep(2)

        # Get tunnel URL from ngrok API
        async with aiohttp.ClientSession() as session:
            async with session.get('http://127.0.0.1:4040/api/tunnels') as resp:
                data = await resp.json()
                tunnel_url = data['tunnels'][0]['public_url']

        return tunnel_url
```

**Acceptance Criteria:**
- ✅ Starts ngrok automatically
- ✅ Retrieves public URL
- ✅ Optionally registers with GitHub (if API token provided)
- ✅ Handles tunnel failures
- ✅ Documentation for setup

---

## PHASE 6: CLI Mode Detection

### CLI-001: CLI Mode Detector
**Priority:** MEDIUM
**Time Estimate:** 1 day
**Dependencies:** SYNC-003

**Description:**
Detect when user is in "Open in CLI" mode to avoid sync conflicts.

**Implementation:**
```python
# service/cli_mode_detector.py

class CLIModeDetector:
    """
    Detects when user is working in CLI mode.
    Prevents sync conflicts during manual operations.
    """

    def __init__(self):
        self.manual_pause = False

    def is_cli_mode_active(self, repo_path: Path) -> bool:
        """Check if user is likely in CLI mode"""
        # Check for git lock file
        if (repo_path / '.git/index.lock').exists():
            return True

        # Check for uncommitted changes
        if self.has_uncommitted_changes(repo_path):
            # Check if changes are recent (< 5 min)
            mtime = self.get_worktree_mtime(repo_path)
            if time.time() - mtime < 300:  # 5 minutes
                return True

        # Check for active git processes
        if self.has_active_git_processes(repo_path):
            return True

        return False

    def should_pause_sync(self, repo_path: Path) -> bool:
        """Determine if sync should be paused"""
        return self.manual_pause or self.is_cli_mode_active(repo_path)

    def pause_sync(self):
        """Manually pause sync"""
        self.manual_pause = True

    def resume_sync(self):
        """Manually resume sync"""
        self.manual_pause = False

    def has_uncommitted_changes(self, repo_path: Path) -> bool:
        """Check for uncommitted changes"""
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())

    def get_worktree_mtime(self, repo_path: Path) -> float:
        """Get most recent modification time in worktree"""
        # Check .git/index mtime (updated on git operations)
        index_file = repo_path / '.git/index'
        if index_file.exists():
            return index_file.stat().st_mtime
        return 0

    def has_active_git_processes(self, repo_path: Path) -> bool:
        """Check for active git processes"""
        try:
            # Check for git processes in this repo
            output = subprocess.check_output(['ps', 'aux'], text=True)
            git_processes = [
                line for line in output.split('\n')
                if 'git' in line and str(repo_path) in line
            ]
            return len(git_processes) > 0
        except:
            return False
```

**Files to Create:**
- `service/cli_mode_detector.py` (~200 lines)

**Tests:**
- `tests/test_cli_mode_detector.py`

**Integration:**
```python
# In sync_daemon.py

async def check_repository(self, repo_config: dict):
    """Check single repository for Claude branch changes"""
    repo_path = Path(repo_config['path']).expanduser()

    # Check if CLI mode active
    if self.cli_detector.should_pause_sync(repo_path):
        # Skip sync, user is working in CLI
        return

    # Continue with normal sync...
```

**Acceptance Criteria:**
- ✅ Detects git lock files
- ✅ Detects recent uncommitted changes
- ✅ Detects active git processes
- ✅ Manual pause/resume support
- ✅ Notifies user when sync paused
- ✅ Auto-resumes when safe

---

## PHASE 7: Dashboard Integration

### DASH-001: Sync Status Dashboard
**Priority:** LOW
**Time Estimate:** 1 day
**Dependencies:** Phase 1, 2 complete

**Description:**
Update existing Flask dashboard with sync status and notification history.

**New Dashboard Features:**
- Real-time sync status
- Active Claude branches
- Notification history viewer
- Sync controls (pause/resume)
- Test results history

**New API Endpoints:**
```python
# In service/dashboard.py

@app.route('/api/sync/status')
def get_sync_status():
    """Get current sync daemon status"""
    return {
        'running': sync_daemon.running,
        'mode': config.get('sync.mode'),
        'active_branches': [
            {
                'repo': str(repo_path),
                'branch': manager.get_active_branch()
            }
            for repo_path, manager in sync_managers.items()
        ],
        'paused': cli_detector.manual_pause
    }

@app.route('/api/notifications/history')
def get_notification_history():
    """Get notification history"""
    limit = request.args.get('limit', 50, type=int)
    notifications = notification_queue.get_history(limit)
    return jsonify([n.to_dict() for n in notifications])

@app.route('/api/notifications/unread')
def get_unread_count():
    """Get unread notification count"""
    return {'count': notification_queue.get_unread_count()}

@app.route('/api/sync/pause', methods=['POST'])
def pause_sync():
    """Pause sync daemon"""
    cli_detector.pause_sync()
    return {'status': 'paused'}

@app.route('/api/sync/resume', methods=['POST'])
def resume_sync():
    """Resume sync daemon"""
    cli_detector.resume_sync()
    return {'status': 'resumed'}
```

**Dashboard UI Updates:**
```html
<!-- In dashboard/templates/index.html -->

<!-- Sync Status Widget -->
<div class="sync-status-widget">
    <h3>Sync Status</h3>
    <div id="sync-status">
        <span class="status-badge">Running</span>
        <button onclick="toggleSync()">Pause</button>
    </div>

    <div class="active-branches">
        <h4>Active Claude Branches</h4>
        <ul id="active-branches-list"></ul>
    </div>
</div>

<!-- Notification History Widget -->
<div class="notification-history-widget">
    <h3>Recent Notifications <span class="badge" id="unread-count">0</span></h3>
    <div id="notification-list"></div>
</div>
```

**Acceptance Criteria:**
- ✅ Shows sync daemon status
- ✅ Lists active Claude branches
- ✅ Displays notification history
- ✅ Pause/resume controls
- ✅ Real-time updates
- ✅ Responsive design

---

## PHASE 8: Documentation & Testing

### DOC-001: User Documentation
**Priority:** HIGH
**Time Estimate:** 1 day
**Dependencies:** All phases

**Description:**
Create comprehensive user documentation for cloud-first workflow.

**Documents to Create:**

1. **CLOUD_FIRST_SETUP.md** - Setup guide
   - Installation instructions
   - Configuration guide
   - Webhook setup (optional)
   - Troubleshooting

2. **NOTIFICATION_GUIDE.md** - Notification system guide
   - How notification queue works
   - Viewing notification history
   - Customizing notifications
   - System tray usage

3. **FAQ.md** - Frequently asked questions
   - Why isn't my branch syncing?
   - How to pause sync temporarily?
   - What if I'm working in CLI?
   - Webhook vs polling trade-offs

4. Update existing docs:
   - `README.md` - Add cloud-first workflow section
   - `docs/USER_GUIDE.md` - Add sync daemon usage
   - `docs/TROUBLESHOOTING.md` - Add sync issues

**Acceptance Criteria:**
- ✅ Step-by-step setup guide
- ✅ Configuration examples
- ✅ Screenshots/GIFs
- ✅ Troubleshooting section
- ✅ All features documented

---

### DOC-002: API Documentation
**Priority:** MEDIUM
**Time Estimate:** 0.5 days
**Dependencies:** All phases

**Description:**
Document all new API endpoints and CLI commands.

**Files to Create:**
- `docs/API.md` - REST API documentation
- `docs/CLI.md` - CLI command reference

**Acceptance Criteria:**
- ✅ All endpoints documented
- ✅ Request/response examples
- ✅ CLI command examples
- ✅ Configuration options

---

### TEST-001: Integration Tests
**Priority:** HIGH
**Time Estimate:** 2 days
**Dependencies:** All phases

**Description:**
Create integration tests for complete workflow.

**Test Scenarios:**

1. **End-to-End Sync Test**
   ```python
   async def test_complete_sync_workflow():
       # 1. Simulate Claude pushing branch
       # 2. Verify branch detected
       # 3. Verify checkout
       # 4. Verify tests run
       # 5. Verify dev server started
       # 6. Verify notification sent
   ```

2. **Notification Queue Test**
   ```python
   async def test_notification_queue():
       # 1. Add multiple notifications
       # 2. Verify only one shown
       # 3. Dismiss current
       # 4. Verify next shown
       # 5. Check history
   ```

3. **CLI Mode Detection Test**
   ```python
   async def test_cli_mode_detection():
       # 1. Make uncommitted changes
       # 2. Verify sync paused
       # 3. Commit changes
       # 4. Verify sync resumed
   ```

4. **Webhook Test**
   ```python
   async def test_webhook_receiver():
       # 1. Send mock GitHub webhook
       # 2. Verify signature validation
       # 3. Verify sync triggered
   ```

**Files to Create:**
- `tests/integration/test_sync_workflow.py`
- `tests/integration/test_notification_system.py`
- `tests/integration/test_cli_mode.py`
- `tests/integration/test_webhook.py`

**Acceptance Criteria:**
- ✅ All critical paths tested
- ✅ Tests run in CI/CD
- ✅ >80% code coverage
- ✅ All tests pass

---

### TEST-002: Performance Testing
**Priority:** LOW
**Time Estimate:** 1 day
**Dependencies:** TEST-001

**Description:**
Test performance and measure actual speedup.

**Metrics to Measure:**
- Time from push to checkout complete
- Time from checkout to dev server ready
- Notification latency
- Resource usage (CPU, memory)
- Multiple repository handling

**Acceptance Criteria:**
- ✅ Sync completes in < 5 seconds (polling)
- ✅ Sync completes in < 2 seconds (webhook)
- ✅ Handles 5+ repositories simultaneously
- ✅ Memory usage < 100MB
- ✅ CPU usage < 5% when idle

---

## 📊 Implementation Summary

### Task Count by Phase

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Core Sync | 5 tasks | 3-4 days |
| Phase 2: Notifications | 5 tasks | 2-3 days |
| Phase 3: Test Runner | 2 tasks | 1-2 days |
| Phase 4: Dev Server | 2 tasks | 2-3 days |
| Phase 5: Webhook | 2 tasks | 2-3 days |
| Phase 6: CLI Detection | 1 task | 1-2 days |
| Phase 7: Dashboard | 1 task | 1-2 days |
| Phase 8: Docs & Tests | 4 tasks | 2-3 days |
| **TOTAL** | **22 tasks** | **14-22 days** |

### Priority Breakdown

- **CRITICAL**: 8 tasks (Core sync, notifications)
- **HIGH**: 4 tasks (Tests, docs, installers)
- **MEDIUM**: 7 tasks (Dev server, webhook, CLI detection)
- **LOW**: 3 tasks (Dashboard, performance, tunnel)

### Dependencies Graph

```
Phase 1 (Core Sync)
    ↓
    ├─→ Phase 3 (Test Runner)
    ├─→ Phase 4 (Dev Server)
    ├─→ Phase 5 (Webhook)
    └─→ Phase 6 (CLI Detection)

Phase 2 (Notifications) ─→ Phase 7 (Dashboard)

All Phases → Phase 8 (Docs & Tests)
```

---

## 🚀 Recommended Implementation Order

### Week 1: Core Foundation
1. **SYNC-001** - Claude Branch Detector
2. **SYNC-002** - Branch Sync Manager
3. **SYNC-003** - Sync Daemon Core
4. **SYNC-004** - Configuration Schema
5. **NOTIFY-001** - Notification Queue Manager

### Week 2: User Interface
6. **NOTIFY-002** - Notification UI Refactor
7. **NOTIFY-003** - Notification History Viewer
8. **NOTIFY-004** - Database Schema Update
9. **SYNC-005** - Service Installer
10. **TEST-001** - Test Runner Component

### Week 3: Integration & Polish
11. **TEST-002** - Test Integration
12. **DEV-001** - Dev Server Manager
13. **CLI-001** - CLI Mode Detector
14. **WEBHOOK-001** - Webhook Receiver
15. **NOTIFY-005** - System Tray Integration

### Week 4: Documentation & Testing
16. **DOC-001** - User Documentation
17. **DOC-002** - API Documentation
18. **TEST-001** - Integration Tests
19. **DASH-001** - Dashboard Updates
20. Final testing and bug fixes

---

## ✅ Success Metrics

### Technical Metrics
- ✅ Branch sync time: < 5 seconds (polling) or < 2 seconds (webhook)
- ✅ Test execution: Configurable per project
- ✅ Dev server startup: < 30 seconds
- ✅ Notification latency: < 1 second
- ✅ Resource usage: < 100MB RAM, < 5% CPU idle

### User Experience Metrics
- ✅ Zero manual git pulls required
- ✅ One notification at a time (no spam)
- ✅ Complete notification history available
- ✅ Works seamlessly with "Open in CLI"
- ✅ Cross-platform support (Windows/Linux/macOS)

### Reliability Metrics
- ✅ Handles network failures gracefully
- ✅ Detects and avoids sync conflicts
- ✅ Auto-recovery from errors
- ✅ No data loss on crashes
- ✅ Comprehensive logging

---

## 🔧 Configuration Examples

### Minimal Setup (Polling Only)
```yaml
sync:
  mode: polling
  polling:
    interval: 30
  claude_branches:
    patterns: ['^claude/.*']
  repositories:
    - path: ~/Projects/my-app
```

### Recommended Setup (Hybrid)
```yaml
sync:
  mode: hybrid
  webhook:
    enabled: true
    port: 8766
  polling:
    interval: 60
  auto_test:
    enabled: true
  dev_server:
    auto_restart: true
    open_browser: true
  repositories:
    - path: ~/Projects/my-app
      dev_server_type: next
```

### Advanced Setup (Full Features)
```yaml
sync:
  mode: hybrid
  webhook:
    enabled: true
    tunnel: ngrok
  polling:
    interval: 60
  auto_test:
    enabled: true
    skip_dev_on_failure: false
  dev_server:
    auto_restart: true
    open_browser: true
    health_check: true
  notifications:
    sequential: true
    show_history: true
    system_tray: true
  cli_mode_detection:
    enabled: true
    pause_on_uncommitted: true
  repositories:
    - path: ~/Projects/frontend
      dev_server_type: next
    - path: ~/Projects/backend
      dev_server_type: flask
```

---

## 📝 Notes

### Important Considerations

1. **Backward Compatibility**
   - Existing git hooks remain functional
   - Old notification system deprecated but not removed
   - Migration path for existing users

2. **Security**
   - Webhook signature verification required
   - Local-only by default (no public exposure)
   - Sensitive data in environment variables

3. **Performance**
   - Async operations throughout
   - Minimal resource usage when idle
   - Configurable intervals to balance speed vs resources

4. **User Control**
   - Manual pause/resume support
   - Per-repository configuration
   - Notification preferences

---

**Status:** Ready for Implementation
**Version:** 2.0.0-refactor
**Created:** 2025-11-13
**Last Updated:** 2025-11-13
