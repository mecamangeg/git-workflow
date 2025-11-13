-- Git Workflow Guardian - SQLite Schema
-- Version: 1.0.0

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
