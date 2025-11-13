"""
Notification Queue Manager - Sequential notification display system.

Manages notification queue to show one notification at a time.
Only displays next notification after current is dismissed.
Maintains complete notification history for review.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Callable
from collections import deque

from .notification_storage import (
    NotificationStorage,
    Notification,
    NotificationAction
)

logger = logging.getLogger(__name__)


class NotificationQueue:
    """
    Manages sequential notification display.

    Features:
    - Shows one notification at a time
    - Queues additional notifications (FIFO)
    - Displays next after current dismissed
    - Persists all notifications to history
    - Tracks read/unread status
    """

    def __init__(self, storage: NotificationStorage):
        """Initialize queue with storage backend"""
        self.storage = storage
        self.current: Optional[Notification] = None
        self.queue: deque[str] = deque()  # Notification IDs
        self.lock = asyncio.Lock()
        self.display_callback: Optional[Callable] = None

        # Load existing queue from database on init
        self._load_queue_from_db()

    def _load_queue_from_db(self):
        """Load pending queue from database"""
        try:
            queue_ids = self.storage.get_queue()
            self.queue = deque(queue_ids)

            # Load current notification if any
            self.current = self.storage.get_current_notification()

            logger.info(f"Loaded {len(self.queue)} queued notifications")
            if self.current:
                logger.info(f"Current notification: {self.current.id}")
        except Exception as e:
            logger.error(f"Error loading queue from database: {e}")
            self.queue = deque()
            self.current = None

    def set_display_callback(self, callback: Callable):
        """Set callback function to display notifications"""
        self.display_callback = callback

    async def add_notification(
        self,
        type: str,
        severity: str,
        title: str,
        message: str,
        actions: Optional[List[NotificationAction]] = None,
        metadata: Optional[dict] = None,
        repo_path: Optional[str] = None,
        branch_name: Optional[str] = None
    ) -> str:
        """
        Add notification to queue.
        Returns notification ID.
        """
        async with self.lock:
            # Create notification
            notification = NotificationStorage.create_notification(
                type=type,
                severity=severity,
                title=title,
                message=message,
                actions=actions,
                metadata=metadata,
                repo_path=repo_path,
                branch_name=branch_name
            )

            # Save to history immediately
            try:
                self.storage.save_notification(notification)
                logger.info(f"Saved notification: {notification.id} - {notification.title}")
            except Exception as e:
                logger.error(f"Error saving notification: {e}")
                return notification.id

            # Add to queue
            self.queue.append(notification.id)
            self.storage.add_to_queue(notification.id)

            # Show if no current notification
            if self.current is None:
                await self._show_next()
            else:
                logger.info(f"Notification queued (current exists): {notification.id}")

            return notification.id

    async def _show_next(self):
        """Show next notification from queue"""
        if not self.queue:
            self.current = None
            self.storage.set_current_notification(None)
            logger.info("Queue empty, no notification to show")
            return

        # Get next notification ID
        notification_id = self.queue.popleft()

        # Remove from database queue
        self.storage.remove_from_queue(notification_id)

        # Load full notification
        notification = self.storage.get_notification(notification_id)
        if not notification:
            logger.warning(f"Notification {notification_id} not found in storage")
            # Try next in queue
            await self._show_next()
            return

        # Set as current
        self.current = notification
        notification.displayed_at = datetime.now()

        # Update database
        self.storage.update_notification(notification)
        self.storage.set_current_notification(notification.id)

        logger.info(f"Displaying notification: {notification.id} - {notification.title}")

        # Call display callback
        if self.display_callback:
            try:
                await self._call_display_callback(notification)
            except Exception as e:
                logger.error(f"Error in display callback: {e}")

    async def _call_display_callback(self, notification: Notification):
        """Call display callback (sync or async)"""
        if asyncio.iscoroutinefunction(self.display_callback):
            await self.display_callback(notification)
        else:
            self.display_callback(notification)

    async def dismiss_current(self):
        """Dismiss currently shown notification and show next"""
        async with self.lock:
            if not self.current:
                logger.warning("No current notification to dismiss")
                return

            # Mark as dismissed
            self.current.dismissed_at = datetime.now()
            self.storage.update_notification(self.current)

            logger.info(f"Dismissed notification: {self.current.id}")

            # Show next
            await self._show_next()

    async def mark_current_read(self):
        """Mark current notification as read"""
        if self.current and not self.current.read:
            self.current.read = True
            self.storage.mark_as_read(self.current.id)
            logger.info(f"Marked as read: {self.current.id}")

    def get_current(self) -> Optional[Notification]:
        """Get currently displayed notification"""
        return self.current

    def get_queue_size(self) -> int:
        """Get number of queued notifications"""
        return len(self.queue)

    def get_history(self, limit: int = 100) -> List[Notification]:
        """Get notification history"""
        return self.storage.get_all_notifications(limit)

    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return self.storage.get_unread_count()

    def search_history(
        self,
        type: Optional[str] = None,
        severity: Optional[str] = None,
        repo_path: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Notification]:
        """Search notification history with filters"""
        return self.storage.search_notifications(
            type=type,
            severity=severity,
            repo_path=repo_path,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

    async def clear_queue(self):
        """Clear all pending notifications (not history)"""
        async with self.lock:
            self.queue.clear()
            self.storage.clear_queue()
            logger.info("Cleared notification queue")

    def clear_history(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear notification history.
        Returns count of deleted notifications.
        """
        deleted = self.storage.clear_history(older_than_days)
        logger.info(f"Cleared {deleted} notifications from history")
        return deleted

    async def retry_current(self):
        """Re-display current notification (useful if window was closed)"""
        if self.current and self.display_callback:
            try:
                await self._call_display_callback(self.current)
                logger.info(f"Retried displaying: {self.current.id}")
            except Exception as e:
                logger.error(f"Error retrying display: {e}")

    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID from history"""
        return self.storage.get_notification(notification_id)

    async def handle_action(self, notification_id: str, action_name: str):
        """
        Handle action button click from notification.
        Marks notification as read.
        """
        notification = self.get_notification_by_id(notification_id)
        if not notification:
            logger.warning(f"Notification not found: {notification_id}")
            return

        # Find action
        action = next((a for a in notification.actions if a.action == action_name), None)
        if not action:
            logger.warning(f"Action not found: {action_name}")
            return

        # Mark as read
        if not notification.read:
            self.storage.mark_as_read(notification_id)
            if self.current and self.current.id == notification_id:
                self.current.read = True

        logger.info(f"Handled action '{action_name}' for notification {notification_id}")

        # Action handling is done by notification_ui.py
        # This just logs and marks as read

    def get_statistics(self) -> dict:
        """Get queue and history statistics"""
        return {
            'current': self.current.to_dict() if self.current else None,
            'queue_size': self.get_queue_size(),
            'unread_count': self.get_unread_count(),
            'total_history': len(self.get_history(limit=10000)),  # Reasonable limit
        }


class NotificationBuilder:
    """
    Helper class to build common notification types.
    Provides convenience methods for creating specific notification types.
    """

    @staticmethod
    def branch_sync_success(
        branch_name: str,
        repo_path: str,
        commit_count: int = 0,
        test_passed: Optional[bool] = None,
        server_url: Optional[str] = None
    ) -> dict:
        """Create branch sync success notification"""
        message_parts = [f"Successfully synced branch '{branch_name}'"]

        if commit_count:
            message_parts.append(f"{commit_count} new commit(s)")

        if test_passed is not None:
            test_status = "✅ passed" if test_passed else "❌ failed"
            message_parts.append(f"Tests: {test_status}")

        if server_url:
            message_parts.append(f"Server: {server_url}")

        # Use server_url if provided, otherwise fallback to default
        browser_url = server_url if server_url else 'http://localhost:3000'

        actions = [
            NotificationAction(
                label="Open Browser",
                action="open_browser",
                data={'url': browser_url}
            ),
            NotificationAction(
                label="Create PR",
                action="create_pr",
                data={'branch': branch_name, 'repo_path': repo_path}
            ),
            NotificationAction(
                label="View Diff",
                action="view_diff",
                data={'branch': branch_name, 'repo_path': repo_path}
            )
        ]

        return {
            'type': 'branch_sync',
            'severity': 'info',
            'title': 'Claude Branch Ready',
            'message': ' • '.join(message_parts),
            'actions': actions,
            'metadata': {
                'branch': branch_name,
                'commit_count': commit_count,
                'test_passed': test_passed
            },
            'repo_path': repo_path,
            'branch_name': branch_name
        }

    @staticmethod
    def test_result(
        branch_name: str,
        repo_path: str,
        passed: bool,
        duration: float,
        output: Optional[str] = None
    ) -> dict:
        """Create test result notification"""
        severity = 'info' if passed else 'warning'
        title = 'Tests Passed ✅' if passed else 'Tests Failed ❌'

        message = f"Branch '{branch_name}' - Tests completed in {duration:.1f}s"

        actions = []
        if not passed and output:
            actions.append(NotificationAction(
                label="View Output",
                action="view_test_output",
                data={'output': output}
            ))

        return {
            'type': 'test_result',
            'severity': severity,
            'title': title,
            'message': message,
            'actions': actions,
            'metadata': {
                'branch': branch_name,
                'passed': passed,
                'duration': duration
            },
            'repo_path': repo_path,
            'branch_name': branch_name
        }

    @staticmethod
    def dev_server_ready(
        repo_path: str,
        project_type: str,
        port: int,
        url: str = None
    ) -> dict:
        """Create dev server ready notification"""
        if not url:
            url = f'http://localhost:{port}'

        return {
            'type': 'dev_server',
            'severity': 'info',
            'title': 'Dev Server Ready',
            'message': f'{project_type} server running at {url}',
            'actions': [
                NotificationAction(
                    label="Open Browser",
                    action="open_browser",
                    data={'url': url}
                )
            ],
            'metadata': {
                'project_type': project_type,
                'port': port,
                'url': url
            },
            'repo_path': repo_path
        }

    @staticmethod
    def sync_error(
        branch_name: str,
        repo_path: str,
        error_message: str
    ) -> dict:
        """Create sync error notification"""
        return {
            'type': 'error',
            'severity': 'critical',
            'title': 'Sync Failed',
            'message': f"Failed to sync '{branch_name}': {error_message}",
            'actions': [
                NotificationAction(
                    label="View Logs",
                    action="view_logs",
                    data={'repo_path': repo_path}
                ),
                NotificationAction(
                    label="Retry",
                    action="retry_sync",
                    data={'branch': branch_name, 'repo_path': repo_path}
                )
            ],
            'metadata': {
                'branch': branch_name,
                'error': error_message
            },
            'repo_path': repo_path,
            'branch_name': branch_name
        }

    @staticmethod
    def cli_mode_detected(repo_path: str) -> dict:
        """Create CLI mode detected notification"""
        return {
            'type': 'info',
            'severity': 'info',
            'title': 'CLI Mode Detected',
            'message': 'Sync paused - uncommitted changes detected. Resume when ready.',
            'actions': [
                NotificationAction(
                    label="Resume Sync",
                    action="resume_sync",
                    data={'repo_path': repo_path}
                )
            ],
            'metadata': {},
            'repo_path': repo_path
        }
