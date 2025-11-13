-- Git Workflow Guardian - SQLite Schema
-- Version: 2.0.0 (Cloud-First Refactor)

-- Repositories being monitored
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Violation records (audit log)
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL,  -- critical, warning, suggestion
    branch_name TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overridden BOOLEAN DEFAULT 0,
    override_reason TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Active overrides
CREATE TABLE IF NOT EXISTS overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    session_id TEXT,  -- For session-level overrides
    expires_at TIMESTAMP,  -- NULL for session-level, timestamp for time-based
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Compliance metrics (Phase 3)
CREATE TABLE IF NOT EXISTS compliance_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    date DATE NOT NULL,
    feature_branch_usage REAL,  -- 0.0 to 1.0
    branch_naming_compliance REAL,
    local_testing_rate REAL,
    branch_cleanup_speed REAL,  -- Average hours to delete
    overall_score REAL,
    FOREIGN KEY (repo_id) REFERENCES repositories(id),
    UNIQUE(repo_id, date)
);

-- Branch activity tracking
CREATE TABLE IF NOT EXISTS branch_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    branch_name TEXT NOT NULL,
    created_at TIMESTAMP,
    last_commit_at TIMESTAMP,
    merged_at TIMESTAMP,
    deleted_at TIMESTAMP,
    commit_count INTEGER DEFAULT 0,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_violations_repo ON violations(repo_id);
CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_overrides_repo ON overrides(repo_id);
CREATE INDEX IF NOT EXISTS idx_overrides_expires ON overrides(expires_at);
CREATE INDEX IF NOT EXISTS idx_branch_activity_repo ON branch_activity(repo_id);

-- ============================================================================
-- CLOUD-FIRST WORKFLOW ADDITIONS (v2.0)
-- ============================================================================

-- Notification history (for sequential queue and history viewer)
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,  -- UUID
    type TEXT NOT NULL,  -- 'branch_sync', 'test_result', 'conflict', 'error', 'dev_server'
    severity TEXT NOT NULL,  -- 'info', 'warning', 'critical'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    actions TEXT,  -- JSON array of NotificationAction objects
    metadata TEXT,  -- JSON object with additional data
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    displayed_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    read BOOLEAN DEFAULT 0,
    repo_path TEXT,
    branch_name TEXT
);

-- Notification queue (pending notifications to be shown)
CREATE TABLE IF NOT EXISTS notification_queue (
    position INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id TEXT NOT NULL,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE
);

-- Current notification (only one row - the currently displayed notification)
CREATE TABLE IF NOT EXISTS current_notification (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Enforces single row
    notification_id TEXT,
    shown_at TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE SET NULL
);

-- Claude branch tracking (for sync daemon)
CREATE TABLE IF NOT EXISTS claude_branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_path TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    first_commit_hash TEXT,
    first_commit_date TIMESTAMP,
    last_synced_at TIMESTAMP,
    sync_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,  -- Currently checked out
    UNIQUE(repo_path, branch_name)
);

-- Sync events (audit log for sync operations)
CREATE TABLE IF NOT EXISTS sync_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_path TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'detected', 'checkout', 'pull', 'test', 'dev_server'
    status TEXT NOT NULL,  -- 'success', 'failed', 'skipped'
    message TEXT,
    metadata TEXT,  -- JSON with additional context
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dev server tracking (running servers)
CREATE TABLE IF NOT EXISTS dev_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_path TEXT UNIQUE NOT NULL,
    project_type TEXT NOT NULL,  -- 'next', 'react', 'flask', etc.
    port INTEGER NOT NULL,
    process_id INTEGER,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_health_check TIMESTAMP,
    is_healthy BOOLEAN DEFAULT 1,
    restart_count INTEGER DEFAULT 0
);

-- Test results (auto-test feature)
CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_path TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    project_type TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    output TEXT,
    errors TEXT,
    duration REAL,  -- Seconds
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for cloud-first features
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_severity ON notifications(severity);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_repo ON notifications(repo_path);

CREATE INDEX IF NOT EXISTS idx_claude_branches_repo ON claude_branches(repo_path);
CREATE INDEX IF NOT EXISTS idx_claude_branches_active ON claude_branches(is_active);
CREATE INDEX IF NOT EXISTS idx_claude_branches_detected ON claude_branches(detected_at);

CREATE INDEX IF NOT EXISTS idx_sync_events_repo ON sync_events(repo_path);
CREATE INDEX IF NOT EXISTS idx_sync_events_branch ON sync_events(branch_name);
CREATE INDEX IF NOT EXISTS idx_sync_events_timestamp ON sync_events(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_test_results_repo ON test_results(repo_path);
CREATE INDEX IF NOT EXISTS idx_test_results_branch ON test_results(branch_name);
CREATE INDEX IF NOT EXISTS idx_test_results_timestamp ON test_results(timestamp DESC);
