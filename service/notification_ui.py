"""
Notification UI - Display notifications using tkinter or PyQt5.

Integrates with NotificationQueue for sequential display.
Shows one notification at a time with dismiss button.
"""

import logging
import webbrowser
import subprocess
from pathlib import Path
from typing import Optional, Callable

try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

try:
    from PyQt5 import QtWidgets, QtCore, QtGui
    HAS_PYQT5 = True
except ImportError:
    HAS_PYQT5 = False

from .notification_storage import Notification, NotificationAction

logger = logging.getLogger(__name__)


class NotificationUI:
    """
    UI for displaying notifications one at a time.

    Features:
    - Sequential display (one notification at a time)
    - Dismiss button
    - Action buttons
    - Auto-dismiss after timeout
    - Fallback from PyQt5 to tkinter
    """

    def __init__(self, notification_queue):
        """
        Initialize notification UI.

        Args:
            notification_queue: NotificationQueue instance
        """
        self.notification_queue = notification_queue
        self.current_window = None

        # Set display callback
        self.notification_queue.set_display_callback(self.show_notification)

        # Check what UI library is available
        if HAS_PYQT5:
            logger.info("Using PyQt5 for notifications")
            self.ui_backend = 'pyqt5'
        elif HAS_TKINTER:
            logger.info("Using tkinter for notifications")
            self.ui_backend = 'tkinter'
        else:
            logger.error("No UI library available (tkinter or PyQt5)")
            self.ui_backend = None

    async def show_notification(self, notification: Notification):
        """
        Show notification popup.

        Args:
            notification: Notification to display
        """
        if not self.ui_backend:
            logger.warning("No UI backend available, cannot show notification")
            return

        logger.info(f"Showing notification: {notification.title}")

        # Close previous window if still open
        if self.current_window:
            try:
                self.current_window.destroy()
            except:
                pass

        # Create new window based on backend
        if self.ui_backend == 'pyqt5':
            self.current_window = self._create_pyqt5_window(notification)
        else:
            self.current_window = self._create_tkinter_window(notification)

    def _create_tkinter_window(self, notification: Notification):
        """Create tkinter notification window"""
        if not HAS_TKINTER:
            return None

        # Create window
        window = tk.Toplevel()
        window.title(notification.title)
        window.geometry("500x300")

        # Severity colors
        severity_colors = {
            'critical': '#ff4444',
            'warning': '#ff9800',
            'info': '#4caf50'
        }
        bg_color = severity_colors.get(notification.severity, '#333')

        # Header with severity indicator
        header = tk.Frame(window, bg=bg_color, height=5)
        header.pack(fill=tk.X)

        # Main content
        content_frame = tk.Frame(window, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            content_frame,
            text=notification.title,
            font=('Arial', 14, 'bold'),
            wraplength=460
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # Message
        message_text = tk.Text(
            content_frame,
            wrap=tk.WORD,
            height=6,
            font=('Arial', 10),
            relief=tk.FLAT,
            bg='#f5f5f5'
        )
        message_text.insert('1.0', notification.message)
        message_text.config(state=tk.DISABLED)
        message_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Action buttons
        if notification.actions:
            action_frame = tk.Frame(content_frame)
            action_frame.pack(fill=tk.X, pady=(0, 10))

            for action in notification.actions:
                btn = tk.Button(
                    action_frame,
                    text=action.label,
                    command=lambda a=action: self._handle_action(a, notification, window)
                )
                btn.pack(side=tk.LEFT, padx=5)

        # Bottom buttons
        bottom_frame = tk.Frame(content_frame)
        bottom_frame.pack(fill=tk.X)

        dismiss_btn = tk.Button(
            bottom_frame,
            text="Dismiss",
            command=lambda: self._dismiss(notification, window),
            bg='#2196f3',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=5
        )
        dismiss_btn.pack(side=tk.RIGHT)

        # Keep window on top
        window.attributes('-topmost', True)

        # Auto-dismiss after timeout
        auto_timeout = 60000  # 60 seconds
        window.after(auto_timeout, lambda: self._auto_dismiss(notification, window))

        return window

    def _create_pyqt5_window(self, notification: Notification):
        """Create PyQt5 notification window (more polished)"""
        if not HAS_PYQT5:
            return None

        # For PyQt5, we would create a QWidget with better styling
        # For now, fall back to tkinter
        # Full PyQt5 implementation would go here
        logger.info("PyQt5 backend not fully implemented yet, using tkinter")
        return self._create_tkinter_window(notification)

    def _handle_action(self, action: NotificationAction, notification: Notification, window):
        """Handle action button click"""
        logger.info(f"Action clicked: {action.action}")

        try:
            if action.action == 'open_browser':
                url = action.data.get('url', 'http://localhost:3000')
                webbrowser.open(url)

            elif action.action == 'create_pr':
                # Open GitHub PR creation page
                repo_path = action.data.get('repo_path')
                branch = action.data.get('branch')
                if repo_path and branch:
                    # Get remote URL
                    result = subprocess.run(
                        ['git', 'config', '--get', 'remote.origin.url'],
                        cwd=repo_path,
                        capture_output=True,
                        text=True
                    )
                    remote_url = result.stdout.strip()

                    # Convert to GitHub URL
                    if 'github.com' in remote_url:
                        # Parse repo from URL
                        # git@github.com:user/repo.git -> https://github.com/user/repo
                        if remote_url.startswith('git@'):
                            remote_url = remote_url.replace(':', '/').replace('git@', 'https://')
                        remote_url = remote_url.replace('.git', '')

                        pr_url = f"{remote_url}/compare/{branch}?expand=1"
                        webbrowser.open(pr_url)

            elif action.action == 'view_diff':
                repo_path = action.data.get('repo_path')
                branch = action.data.get('branch')
                if repo_path and branch:
                    # Open diff in default text editor or terminal
                    subprocess.run(['git', 'diff', f'main...{branch}'], cwd=repo_path)

            elif action.action == 'view_test_output':
                output = action.data.get('output', '')
                # Show in new window
                self._show_text_window("Test Output", output)

            elif action.action == 'view_logs':
                # Open logs directory
                logs_dir = Path.home() / '.git-workflow-guardian'
                if logs_dir.exists():
                    subprocess.run(['xdg-open', str(logs_dir)])  # Linux
                    # On macOS: subprocess.run(['open', str(logs_dir)])
                    # On Windows: subprocess.run(['explorer', str(logs_dir)])

            # Mark as read
            if notification and not notification.read:
                self.notification_queue.storage.mark_as_read(notification.id)

        except Exception as e:
            logger.error(f"Error handling action: {e}")

    def _dismiss(self, notification: Notification, window):
        """Dismiss notification and show next"""
        logger.info(f"Dismissing notification: {notification.id}")

        try:
            window.destroy()
        except:
            pass

        # Tell queue to show next
        import asyncio
        asyncio.create_task(self.notification_queue.dismiss_current())

    def _auto_dismiss(self, notification: Notification, window):
        """Auto-dismiss after timeout"""
        if window.winfo_exists():
            logger.info(f"Auto-dismissing notification: {notification.id}")
            self._dismiss(notification, window)

    def _show_text_window(self, title: str, text: str):
        """Show text in a new window"""
        if not HAS_TKINTER:
            return

        window = tk.Toplevel()
        window.title(title)
        window.geometry("800x600")

        text_widget = tk.Text(window, wrap=tk.WORD, font=('Courier', 10))
        text_widget.insert('1.0', text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        close_btn = tk.Button(window, text="Close", command=window.destroy)
        close_btn.pack(pady=5)


def has_ui_support() -> bool:
    """Check if any UI library is available"""
    return HAS_TKINTER or HAS_PYQT5


def get_ui_backend() -> Optional[str]:
    """Get available UI backend"""
    if HAS_PYQT5:
        return 'pyqt5'
    elif HAS_TKINTER:
        return 'tkinter'
    return None
