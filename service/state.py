"""
Git Workflow Guardian - State Management
SQLite database for tracking state and analytics
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """Manage state using SQLite database"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path.home() / ".git-workflow-guardian" / "state.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.initialize()

    def initialize(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Load schema from file
        schema_path = Path(__file__).parent.parent / "service" / "schema.sql"

        # If schema file doesn't exist, use embedded schema
        if schema_path.exists():
            with open(schema_path) as f:
                schema = f.read()
        else:
            schema = self._get_embedded_schema()

        try:
            cursor.executescript(schema)
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
        finally:
            conn.close()

    def _get_embedded_schema(self) -> str:
        """Return embedded schema as fallback"""
        return """
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_checked TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL,
            rule_name TEXT NOT NULL,
            severity TEXT NOT NULL,
            branch_name TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            overridden BOOLEAN DEFAULT 0,
            override_reason TEXT,
            FOREIGN KEY (repo_id) REFERENCES repositories(id)
        );

        CREATE TABLE IF NOT EXISTS overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL,
            rule_name TEXT NOT NULL,
            session_id TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (repo_id) REFERENCES repositories(id)
        );

        CREATE INDEX IF NOT EXISTS idx_violations_repo ON violations(repo_id);
        CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp);
        CREATE INDEX IF NOT EXISTS idx_overrides_repo ON overrides(repo_id);
        CREATE INDEX IF NOT EXISTS idx_overrides_expires ON overrides(expires_at);
        """

    def log_violation(
        self,
        repo_path: Path,
        rule_name: str,
        severity: str,
        branch_name: Optional[str] = None,
        overridden: bool = False
    ):
        """Log violation to database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get or create repo
            repo_id = self._get_or_create_repo(cursor, repo_path)

            # Insert violation
            cursor.execute("""
                INSERT INTO violations (repo_id, rule_name, severity, branch_name, overridden)
                VALUES (?, ?, ?, ?, ?)
            """, (repo_id, rule_name, severity, branch_name, overridden))

            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error logging violation: {e}")
        finally:
            conn.close()

    def is_overridden(self, rule_name: str, session_id: Optional[str] = None) -> bool:
        """Check if rule is currently overridden"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id FROM overrides
                WHERE rule_name = ?
                AND (expires_at IS NULL OR expires_at > ?)
                AND (session_id = ? OR session_id IS NULL)
            """, (rule_name, datetime.now().isoformat(), session_id))

            result = cursor.fetchone()
            conn.close()

            return result is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking override: {e}")
            return False

    def get_last_notification(
        self,
        rule_name: str,
        repo_path: Path
    ) -> Optional[datetime]:
        """Get timestamp of last notification for rule"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            repo_id = self._get_repo_id(cursor, repo_path)
            if not repo_id:
                return None

            cursor.execute("""
                SELECT MAX(timestamp) FROM violations
                WHERE repo_id = ? AND rule_name = ?
            """, (repo_id, rule_name))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return datetime.fromisoformat(result[0])
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting last notification: {e}")
            return None

    def _get_or_create_repo(self, cursor, repo_path: Path) -> int:
        """Get or create repository record"""
        cursor.execute("SELECT id FROM repositories WHERE path = ?", (str(repo_path),))
        result = cursor.fetchone()

        if result:
            return result[0]

        cursor.execute(
            "INSERT INTO repositories (path, name) VALUES (?, ?)",
            (str(repo_path), repo_path.name)
        )
        return cursor.lastrowid

    def _get_repo_id(self, cursor, repo_path: Path) -> Optional[int]:
        """Get repository ID"""
        cursor.execute("SELECT id FROM repositories WHERE path = ?", (str(repo_path),))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_compliance_stats(self, repo_path: Path = None) -> Dict:
        """Get compliance statistics"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            query = """
                SELECT
                    COUNT(*) as total_violations,
                    SUM(CASE WHEN overridden = 1 THEN 1 ELSE 0 END) as overridden_count,
                    severity,
                    rule_name
                FROM violations
            """

            if repo_path:
                repo_id = self._get_repo_id(cursor, repo_path)
                if repo_id:
                    query += f" WHERE repo_id = {repo_id}"

            query += " GROUP BY severity, rule_name"

            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()

            stats = {
                "total_violations": sum(r[0] for r in results),
                "overridden_count": sum(r[1] for r in results),
                "by_severity": {},
                "by_rule": {}
            }

            for row in results:
                severity = row[2]
                rule = row[3]
                stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + row[0]
                stats["by_rule"][rule] = row[0]

            return stats

        except sqlite3.Error as e:
            logger.error(f"Error getting compliance stats: {e}")
            return {"total_violations": 0, "overridden_count": 0}
