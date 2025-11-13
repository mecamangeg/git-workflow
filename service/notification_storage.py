"""
Notification Storage - SQLite persistence for notification queue and history.

Handles CRUD operations for notifications, queue management, and history queries.
"""

import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field


@dataclass
class NotificationAction:
    """Action button for notification"""
    label: str
    action: str  # 'open_browser', 'create_pr', 'view_diff', etc.
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'NotificationAction':
        return cls(**data)


@dataclass
class Notification:
    """Notification model"""
    id: str
    type: str  # 'branch_sync', 'test_result', 'conflict', 'error', 'dev_server'
    severity: str  # 'info', 'warning', 'critical'
    title: str
    message: str
    actions: List[NotificationAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    displayed_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    read: bool = False
    repo_path: Optional[str] = None
    branch_name: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime to ISO format
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['displayed_at'] = self.displayed_at.isoformat() if self.displayed_at else None
        data['dismissed_at'] = self.dismissed_at.isoformat() if self.dismissed_at else None
        # Convert actions to dict
        data['actions'] = [action.to_dict() for action in self.actions]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Notification':
        """Create from dictionary"""
        # Parse datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'displayed_at' in data and isinstance(data['displayed_at'], str):
            data['displayed_at'] = datetime.fromisoformat(data['displayed_at'])
        if 'dismissed_at' in data and isinstance(data['dismissed_at'], str):
            data['dismissed_at'] = datetime.fromisoformat(data['dismissed_at'])
        # Parse actions
        if 'actions' in data and isinstance(data['actions'], list):
            data['actions'] = [NotificationAction.from_dict(a) if isinstance(a, dict) else a
                             for a in data['actions']]
        return cls(**data)


class NotificationStorage:
    """
    SQLite storage for notifications.
    Handles queue, history, and current notification tracking.
    """

    def __init__(self, db_path: Path):
        """Initialize storage with database path"""
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self):
        """Ensure database and tables exist"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Tables are created by schema.sql, but we ensure connection works
        with self._get_connection() as conn:
            conn.execute("SELECT 1")  # Test connection

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_notification(self, notification: Notification) -> None:
        """Save notification to database"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO notifications (
                    id, type, severity, title, message, actions, metadata,
                    created_at, displayed_at, dismissed_at, read, repo_path, branch_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification.id,
                notification.type,
                notification.severity,
                notification.title,
                notification.message,
                json.dumps([a.to_dict() for a in notification.actions]),
                json.dumps(notification.metadata),
                notification.created_at,
                notification.displayed_at,
                notification.dismissed_at,
                1 if notification.read else 0,
                notification.repo_path,
                notification.branch_name
            ))
            conn.commit()

    def update_notification(self, notification: Notification) -> None:
        """Update existing notification"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE notifications SET
                    displayed_at = ?,
                    dismissed_at = ?,
                    read = ?
                WHERE id = ?
            """, (
                notification.displayed_at,
                notification.dismissed_at,
                1 if notification.read else 0,
                notification.id
            ))
            conn.commit()

    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM notifications WHERE id = ?",
                (notification_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_notification(row)

    def get_all_notifications(self, limit: int = 100) -> List[Notification]:
        """Get all notifications ordered by created_at DESC"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM notifications
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [self._row_to_notification(row) for row in rows]

    def get_unread_notifications(self) -> List[Notification]:
        """Get all unread notifications"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM notifications
                WHERE read = 0
                ORDER BY created_at DESC
            """).fetchall()

            return [self._row_to_notification(row) for row in rows]

    def search_notifications(
        self,
        type: Optional[str] = None,
        severity: Optional[str] = None,
        repo_path: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Notification]:
        """Search notifications with filters"""
        conditions = []
        params = []

        if type:
            conditions.append("type = ?")
            params.append(type)
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        if repo_path:
            conditions.append("repo_path = ?")
            params.append(repo_path)
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(f"""
                SELECT * FROM notifications
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params).fetchall()

            return [self._row_to_notification(row) for row in rows]

    def add_to_queue(self, notification_id: str) -> None:
        """Add notification to queue"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO notification_queue (notification_id, added_at)
                VALUES (?, ?)
            """, (notification_id, datetime.now()))
            conn.commit()

    def get_queue(self) -> List[str]:
        """Get notification IDs in queue order"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT notification_id FROM notification_queue
                ORDER BY position ASC
            """).fetchall()

            return [row['notification_id'] for row in rows]

    def remove_from_queue(self, notification_id: str) -> None:
        """Remove notification from queue"""
        with self._get_connection() as conn:
            conn.execute("""
                DELETE FROM notification_queue
                WHERE notification_id = ?
            """, (notification_id,))
            conn.commit()

    def clear_queue(self) -> None:
        """Clear entire queue"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM notification_queue")
            conn.commit()

    def set_current_notification(self, notification_id: Optional[str]) -> None:
        """Set currently displayed notification"""
        with self._get_connection() as conn:
            # Delete existing (max 1 row due to CHECK constraint)
            conn.execute("DELETE FROM current_notification")

            if notification_id:
                # Insert new current
                conn.execute("""
                    INSERT INTO current_notification (id, notification_id, shown_at)
                    VALUES (1, ?, ?)
                """, (notification_id, datetime.now()))

            conn.commit()

    def get_current_notification(self) -> Optional[Notification]:
        """Get currently displayed notification"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT n.* FROM notifications n
                JOIN current_notification c ON n.id = c.notification_id
            """).fetchone()

            if not row:
                return None

            return self._row_to_notification(row)

    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        with self._get_connection() as conn:
            result = conn.execute("""
                SELECT COUNT(*) as count FROM notifications
                WHERE read = 0
            """).fetchone()

            return result['count'] if result else 0

    def mark_as_read(self, notification_id: str) -> None:
        """Mark notification as read"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE notifications SET read = 1
                WHERE id = ?
            """, (notification_id,))
            conn.commit()

    def delete_notification(self, notification_id: str) -> None:
        """Delete notification (will cascade to queue)"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
            conn.commit()

    def clear_history(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear notification history.
        If older_than_days specified, only delete old notifications.
        Returns count of deleted notifications.
        """
        with self._get_connection() as conn:
            if older_than_days:
                cutoff = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
                result = conn.execute("""
                    DELETE FROM notifications
                    WHERE created_at < ?
                """, (cutoff,))
            else:
                result = conn.execute("DELETE FROM notifications")

            deleted = result.rowcount
            conn.commit()
            return deleted

    def _row_to_notification(self, row: sqlite3.Row) -> Notification:
        """Convert database row to Notification object"""
        # Parse JSON fields
        actions_data = json.loads(row['actions']) if row['actions'] else []
        actions = [NotificationAction.from_dict(a) for a in actions_data]

        metadata = json.loads(row['metadata']) if row['metadata'] else {}

        # Parse datetime fields
        created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        displayed_at = datetime.fromisoformat(row['displayed_at']) if row['displayed_at'] else None
        dismissed_at = datetime.fromisoformat(row['dismissed_at']) if row['dismissed_at'] else None

        return Notification(
            id=row['id'],
            type=row['type'],
            severity=row['severity'],
            title=row['title'],
            message=row['message'],
            actions=actions,
            metadata=metadata,
            created_at=created_at,
            displayed_at=displayed_at,
            dismissed_at=dismissed_at,
            read=bool(row['read']),
            repo_path=row['repo_path'],
            branch_name=row['branch_name']
        )

    @staticmethod
    def create_notification(
        type: str,
        severity: str,
        title: str,
        message: str,
        actions: Optional[List[NotificationAction]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        repo_path: Optional[str] = None,
        branch_name: Optional[str] = None
    ) -> Notification:
        """Helper method to create a new notification"""
        return Notification(
            id=str(uuid.uuid4()),
            type=type,
            severity=severity,
            title=title,
            message=message,
            actions=actions or [],
            metadata=metadata or {},
            repo_path=repo_path,
            branch_name=branch_name
        )
