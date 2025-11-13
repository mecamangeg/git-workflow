"""
Notification History Viewer - UI for viewing past notifications.

Allows users to:
- Browse notification history
- Filter by type, severity, date
- Search notifications
- Re-trigger actions from history
- Export history to CSV
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

from .notification_storage import Notification, NotificationStorage

logger = logging.getLogger(__name__)


class NotificationHistoryViewer:
    """
    UI for viewing notification history.

    Features:
    - Scrollable notification list
    - Filter by type, severity, date range
    - Search functionality
    - View details
    - Re-trigger actions
    - Export to CSV
    - Clear history
    """

    def __init__(self, storage: NotificationStorage):
        """
        Initialize history viewer.

        Args:
            storage: NotificationStorage instance
        """
        self.storage = storage
        self.current_notifications: List[Notification] = []
        self.window = None

    def show_history(self):
        """Show notification history window"""
        if not HAS_TKINTER:
            logger.error("tkinter not available, cannot show history")
            return

        # Create window
        self.window = tk.Toplevel()
        self.window.title("Notification History")
        self.window.geometry("900x700")

        # Create UI
        self._create_ui()

        # Load initial data
        self._load_notifications()

    def _create_ui(self):
        """Create UI components"""
        # Filter controls at top
        filter_frame = tk.Frame(self.window, padx=10, pady=10)
        filter_frame.pack(fill=tk.X)

        # Type filter
        tk.Label(filter_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.type_var,
            values=["All", "branch_sync", "test_result", "dev_server", "error", "info"],
            width=15,
            state='readonly'
        )
        type_combo.grid(row=0, column=1, padx=5)

        # Severity filter
        tk.Label(filter_frame, text="Severity:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.severity_var = tk.StringVar(value="All")
        severity_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.severity_var,
            values=["All", "critical", "warning", "info"],
            width=10,
            state='readonly'
        )
        severity_combo.grid(row=0, column=3, padx=5)

        # Date range
        tk.Label(filter_frame, text="Last:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.date_range_var = tk.StringVar(value="7 days")
        date_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.date_range_var,
            values=["1 day", "7 days", "30 days", "All time"],
            width=10,
            state='readonly'
        )
        date_combo.grid(row=0, column=5, padx=5)

        # Apply filter button
        apply_btn = tk.Button(
            filter_frame,
            text="Apply Filter",
            command=self._apply_filter
        )
        apply_btn.grid(row=0, column=6, padx=5)

        # Search
        tk.Label(filter_frame, text="Search:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var, width=40)
        search_entry.grid(row=1, column=1, columnspan=4, sticky=tk.EW, padx=5, pady=5)
        search_entry.bind('<Return>', lambda e: self._apply_filter())

        # Stats frame
        stats_frame = tk.Frame(self.window, padx=10, pady=5)
        stats_frame.pack(fill=tk.X)

        self.stats_label = tk.Label(stats_frame, text="Loading...", font=('Arial', 9))
        self.stats_label.pack(side=tk.LEFT)

        # Notification list
        list_frame = tk.Frame(self.window, padx=10, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox
        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Arial', 10),
            height=20
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Double-click to view details
        self.listbox.bind('<Double-Button-1>', self._on_double_click)

        # Action buttons at bottom
        button_frame = tk.Frame(self.window, padx=10, pady=10)
        button_frame.pack(fill=tk.X)

        view_btn = tk.Button(
            button_frame,
            text="View Details",
            command=self._view_selected
        )
        view_btn.pack(side=tk.LEFT, padx=5)

        export_btn = tk.Button(
            button_frame,
            text="Export CSV",
            command=self._export_csv
        )
        export_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            button_frame,
            text="Clear History",
            command=self._clear_history
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = tk.Button(
            button_frame,
            text="Refresh",
            command=self._load_notifications
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

    def _load_notifications(self):
        """Load notifications from storage"""
        try:
            # Get all notifications
            self.current_notifications = self.storage.get_all_notifications(limit=500)

            # Update listbox
            self.listbox.delete(0, tk.END)

            for notif in self.current_notifications:
                # Format: [Time] [Type] Title (Read/Unread)
                status = "✓" if notif.read else "●"
                severity_symbol = self._get_severity_symbol(notif.severity)
                time_str = notif.created_at.strftime('%Y-%m-%d %H:%M') if notif.created_at else "Unknown"

                text = f"{status} {severity_symbol} [{time_str}] {notif.title}"
                self.listbox.insert(tk.END, text)

            # Update stats
            total = len(self.current_notifications)
            unread = sum(1 for n in self.current_notifications if not n.read)
            self.stats_label.config(
                text=f"Total: {total} | Unread: {unread}"
            )

        except Exception as e:
            logger.error(f"Error loading notifications: {e}")
            messagebox.showerror("Error", f"Failed to load notifications: {e}")

    def _apply_filter(self):
        """Apply filters to notification list"""
        try:
            # Parse filters
            type_filter = None if self.type_var.get() == "All" else self.type_var.get()
            severity_filter = None if self.severity_var.get() == "All" else self.severity_var.get()

            # Date range
            end_date = datetime.now()
            start_date = None
            date_range = self.date_range_var.get()

            if date_range == "1 day":
                start_date = end_date - timedelta(days=1)
            elif date_range == "7 days":
                start_date = end_date - timedelta(days=7)
            elif date_range == "30 days":
                start_date = end_date - timedelta(days=30)
            # "All time" = None

            # Search
            search_term = self.search_var.get().lower()

            # Get filtered notifications
            self.current_notifications = self.storage.search_notifications(
                type=type_filter,
                severity=severity_filter,
                start_date=start_date,
                end_date=end_date,
                limit=500
            )

            # Apply search filter
            if search_term:
                self.current_notifications = [
                    n for n in self.current_notifications
                    if search_term in n.title.lower() or search_term in n.message.lower()
                ]

            # Update listbox
            self.listbox.delete(0, tk.END)

            for notif in self.current_notifications:
                status = "✓" if notif.read else "●"
                severity_symbol = self._get_severity_symbol(notif.severity)
                time_str = notif.created_at.strftime('%Y-%m-%d %H:%M') if notif.created_at else "Unknown"

                text = f"{status} {severity_symbol} [{time_str}] {notif.title}"
                self.listbox.insert(tk.END, text)

            # Update stats
            total = len(self.current_notifications)
            unread = sum(1 for n in self.current_notifications if not n.read)
            self.stats_label.config(
                text=f"Filtered: {total} | Unread: {unread}"
            )

        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            messagebox.showerror("Error", f"Failed to apply filter: {e}")

    def _on_double_click(self, event):
        """Handle double-click on notification"""
        self._view_selected()

    def _view_selected(self):
        """View details of selected notification"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a notification")
            return

        idx = selection[0]
        if idx >= len(self.current_notifications):
            return

        notification = self.current_notifications[idx]
        self._show_details(notification)

    def _show_details(self, notification: Notification):
        """Show notification details in popup"""
        details = tk.Toplevel(self.window)
        details.title(f"Notification Details")
        details.geometry("700x500")

        # Main frame with scrollbar
        main_frame = tk.Frame(details)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = tk.Label(
            main_frame,
            text=notification.title,
            font=('Arial', 14, 'bold'),
            wraplength=680
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # Metadata frame
        meta_frame = tk.LabelFrame(main_frame, text="Details", padx=10, pady=5)
        meta_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(meta_frame, text=f"Type: {notification.type}", anchor=tk.W).pack(fill=tk.X)
        tk.Label(meta_frame, text=f"Severity: {notification.severity}", anchor=tk.W).pack(fill=tk.X)

        if notification.created_at:
            tk.Label(
                meta_frame,
                text=f"Created: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                anchor=tk.W
            ).pack(fill=tk.X)

        if notification.dismissed_at:
            tk.Label(
                meta_frame,
                text=f"Dismissed: {notification.dismissed_at.strftime('%Y-%m-%d %H:%M:%S')}",
                anchor=tk.W
            ).pack(fill=tk.X)

        status = "Read" if notification.read else "Unread"
        tk.Label(meta_frame, text=f"Status: {status}", anchor=tk.W).pack(fill=tk.X)

        if notification.repo_path:
            tk.Label(meta_frame, text=f"Repository: {notification.repo_path}", anchor=tk.W).pack(fill=tk.X)

        if notification.branch_name:
            tk.Label(meta_frame, text=f"Branch: {notification.branch_name}", anchor=tk.W).pack(fill=tk.X)

        # Message
        message_frame = tk.LabelFrame(main_frame, text="Message", padx=10, pady=5)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        message_text = tk.Text(
            message_frame,
            wrap=tk.WORD,
            height=8,
            font=('Arial', 10)
        )
        message_text.insert('1.0', notification.message)
        message_text.config(state=tk.DISABLED)
        message_text.pack(fill=tk.BOTH, expand=True)

        # Action buttons (if still applicable)
        if notification.actions:
            action_frame = tk.Frame(main_frame)
            action_frame.pack(fill=tk.X, pady=(0, 10))

            tk.Label(action_frame, text="Actions:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

            for action in notification.actions:
                btn = tk.Button(
                    action_frame,
                    text=action.label,
                    command=lambda a=action: self._trigger_action(a, notification)
                )
                btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Close button
        close_btn = tk.Button(main_frame, text="Close", command=details.destroy)
        close_btn.pack(pady=5)

    def _trigger_action(self, action, notification):
        """Trigger action from history"""
        # Import here to avoid circular dependency
        from .notification_ui import NotificationUI

        # Use notification UI to handle action
        # This is a bit of a workaround, but works
        try:
            ui = NotificationUI(None)
            ui._handle_action(action, notification, None)
        except Exception as e:
            logger.error(f"Error triggering action: {e}")
            messagebox.showerror("Error", f"Failed to trigger action: {e}")

    def _export_csv(self):
        """Export notifications to CSV"""
        try:
            # Ask for file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )

            if not file_path:
                return

            # Export using storage
            import csv

            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # Header
                writer.writerow([
                    'ID', 'Type', 'Severity', 'Title', 'Message',
                    'Created At', 'Displayed At', 'Dismissed At',
                    'Read', 'Repo Path', 'Branch Name'
                ])

                # Data
                for notif in self.current_notifications:
                    writer.writerow([
                        notif.id,
                        notif.type,
                        notif.severity,
                        notif.title,
                        notif.message,
                        notif.created_at.isoformat() if notif.created_at else '',
                        notif.displayed_at.isoformat() if notif.displayed_at else '',
                        notif.dismissed_at.isoformat() if notif.dismissed_at else '',
                        'Yes' if notif.read else 'No',
                        notif.repo_path or '',
                        notif.branch_name or ''
                    ])

            messagebox.showinfo("Success", f"Exported {len(self.current_notifications)} notifications to {file_path}")

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            messagebox.showerror("Error", f"Failed to export: {e}")

    def _clear_history(self):
        """Clear notification history"""
        result = messagebox.askyesno(
            "Confirm",
            "Are you sure you want to clear all notification history?\nThis cannot be undone."
        )

        if not result:
            return

        try:
            deleted = self.storage.clear_history()
            messagebox.showinfo("Success", f"Cleared {deleted} notifications")
            self._load_notifications()

        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            messagebox.showerror("Error", f"Failed to clear history: {e}")

    def _get_severity_symbol(self, severity: str) -> str:
        """Get symbol for severity level"""
        symbols = {
            'critical': '🔴',
            'warning': '🟠',
            'info': '🟢'
        }
        return symbols.get(severity, '●')
