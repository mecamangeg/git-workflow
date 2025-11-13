"""
Git Workflow Guardian - Toast Notifications
Windows toast notifications for suggestions
"""
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional
import threading
import logging

logger = logging.getLogger(__name__)


class ToastNotifier:
    """Display toast notifications for non-critical violations"""

    def __init__(self, config):
        self.config = config
        self.active_toasts = []

    def show_toast(
        self,
        rule_name: str,
        severity: str,
        message: str,
        repo_path: Path,
        branch: Optional[str] = None
    ):
        """Display toast notification"""

        # Get rule configuration
        rule_config = self.config.get(f"rules.{rule_name}", {})

        # Build notification content
        title = self._get_title(severity)
        action = rule_config.get("action", "")
        why = rule_config.get("why", "")
        command = rule_config.get("command", "")

        # Format command with branch name if needed
        if command and branch:
            command = command.replace("{branch_name}", branch)

        # Show in separate thread to not block
        thread = threading.Thread(
            target=self._show_toast_window,
            args=(title, message, action, why, command, severity),
            daemon=True
        )
        thread.start()

    def _get_title(self, severity: str) -> str:
        """Get notification title based on severity"""
        titles = {
            "critical": "🚨 Git Workflow Guardian - CRITICAL",
            "warning": "⚠️ Git Workflow Guardian - Warning",
            "suggestion": "💡 Git Workflow Guardian"
        }
        return titles.get(severity, "Git Workflow Guardian")

    def _show_toast_window(
        self,
        title: str,
        message: str,
        action: str,
        why: str,
        command: str,
        severity: str
    ):
        """Create and display toast window"""

        try:
            # Create window
            root = tk.Tk()
            root.title(title)
            root.attributes('-topmost', True)

            # Position in bottom-right corner
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            window_width = 400
            window_height = 200
            x = screen_width - window_width - 20
            y = screen_height - window_height - 60
            root.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Content
            frame = ttk.Frame(root, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)

            # Message
            ttk.Label(
                frame,
                text=message,
                wraplength=380,
                font=("Segoe UI", 10, "bold")
            ).pack(anchor=tk.W, pady=(0, 10))

            # Action
            if action:
                ttk.Label(
                    frame,
                    text=f"✅ WHAT TO DO:\n{action}",
                    wraplength=380,
                    font=("Segoe UI", 9)
                ).pack(anchor=tk.W, pady=(0, 5))

            # Why
            if why:
                ttk.Label(
                    frame,
                    text=f"📝 WHY:\n{why}",
                    wraplength=380,
                    font=("Segoe UI", 8),
                    foreground="gray"
                ).pack(anchor=tk.W, pady=(0, 5))

            # Command
            if command:
                cmd_label = ttk.Label(
                    frame,
                    text=f"Suggested:\n{command}",
                    wraplength=380,
                    font=("Courier New", 8)
                )
                cmd_label.pack(anchor=tk.W, pady=(0, 10))

            # Dismiss button
            ttk.Button(
                frame,
                text="Dismiss",
                command=root.destroy
            ).pack(side=tk.BOTTOM, anchor=tk.E)

            # Auto-dismiss after timeout
            timeout_key = f"notifications.{severity}.timeout"
            timeout = self.config.get(timeout_key, 10)
            if timeout:
                root.after(int(timeout * 1000), root.destroy)

            root.mainloop()

        except Exception as e:
            logger.error(f"Could not show toast notification: {e}")
            # Fallback to console output
            print(f"\n{title}")
            print(f"  {message}")
            if action:
                print(f"  Action: {action}")
            if command:
                print(f"  Command: {command}")
