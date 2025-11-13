"""
Git Workflow Guardian - Advanced Notifications (PyQt5)
Enhanced notification system with action buttons and themes
"""
try:
    from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QPushButton, QFrame)
    from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
    from PyQt5.QtGui import QFont, QIcon
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    # Fallback to tkinter if PyQt5 not available

from pathlib import Path
from typing import Optional, Callable
import sys
import logging

logger = logging.getLogger(__name__)


class PyQt5Notifier:
    """Advanced notification system using PyQt5"""

    def __init__(self, config):
        self.config = config
        self.app = None
        self.active_notifications = []

        if not PYQT5_AVAILABLE:
            logger.warning("PyQt5 not available, falling back to tkinter")
            from .notifier import ToastNotifier
            self.fallback = ToastNotifier(config)

    def show_toast(
        self,
        rule_name: str,
        severity: str,
        message: str,
        repo_path: Path,
        branch: Optional[str] = None,
        actions: Optional[list] = None
    ):
        """Display advanced toast notification with actions"""

        if not PYQT5_AVAILABLE:
            # Fallback to tkinter
            self.fallback.show_toast(rule_name, severity, message, repo_path, branch)
            return

        # Initialize Qt application if needed
        if not self.app:
            self.app = QApplication.instance()
            if not self.app:
                self.app = QApplication(sys.argv)

        # Get rule configuration
        rule_config = self.config.get(f"rules.{rule_name}", {})

        # Build notification content
        title = self._get_title(severity)
        action_text = rule_config.get("action", "")
        why_text = rule_config.get("why", "")
        command = rule_config.get("command", "")

        # Format command with branch name if needed
        if command and branch:
            command = command.replace("{branch_name}", branch)

        # Create notification window
        notification = AdvancedToast(
            title=title,
            message=message,
            action=action_text,
            why=why_text,
            command=command,
            severity=severity,
            actions=actions or [],
            timeout=self.config.get(f"notifications.{severity}.timeout", 10)
        )

        self.active_notifications.append(notification)
        notification.show()

    def show_critical_popup(
        self,
        rule_name: str,
        message: str,
        branch: str,
        repo_path: Path,
        on_block: Optional[Callable] = None,
        on_override: Optional[Callable] = None
    ):
        """Display blocking popup for critical violations"""

        if not PYQT5_AVAILABLE:
            # Fallback to tkinter
            from hooks.notifier import HookNotifier
            notifier = HookNotifier(repo_path)
            return notifier.show_notification(rule_name, branch)

        if not self.app:
            self.app = QApplication.instance()
            if not self.app:
                self.app = QApplication(sys.argv)

        rule_config = self.config.get(f"rules.{rule_name}", {})

        dialog = CriticalDialog(
            rule_name=rule_name,
            message=message,
            action=rule_config.get("action", ""),
            why=rule_config.get("why", ""),
            command=rule_config.get("command", ""),
            on_block=on_block,
            on_override=on_override
        )

        result = dialog.exec_()
        return result == 1  # 1 = block, 0 = override

    def _get_title(self, severity: str) -> str:
        """Get notification title based on severity"""
        titles = {
            "critical": "🚨 CRITICAL: Git Workflow Guardian",
            "warning": "⚠️ WARNING: Git Workflow Guardian",
            "suggestion": "💡 Git Workflow Guardian"
        }
        return titles.get(severity, "Git Workflow Guardian")


class AdvancedToast(QWidget):
    """Advanced toast notification widget with animations"""

    def __init__(self, title, message, action, why, command, severity, actions, timeout):
        super().__init__()

        self.timeout = timeout
        self.severity = severity

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._setup_ui(title, message, action, why, command, actions)
        self._position_window()
        self._setup_animations()

        # Auto-dismiss timer
        if timeout and timeout > 0:
            QTimer.singleShot(timeout * 1000, self.fade_out)

    def _setup_ui(self, title, message, action, why, command, actions):
        """Set up the UI components"""

        # Main container
        container = QFrame()
        container.setObjectName("toast")
        container.setStyleSheet(self._get_stylesheet())

        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Segoe UI", 10))
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: white;")
        layout.addWidget(msg_label)

        # Action
        if action:
            action_label = QLabel(f"✅ WHAT TO DO:\n{action}")
            action_label.setFont(QFont("Segoe UI", 9))
            action_label.setWordWrap(True)
            action_label.setStyleSheet("color: #e5e7eb;")
            layout.addWidget(action_label)

        # Why
        if why:
            why_label = QLabel(f"📝 WHY:\n{why}")
            why_label.setFont(QFont("Segoe UI", 8))
            why_label.setWordWrap(True)
            why_label.setStyleSheet("color: #9ca3af;")
            layout.addWidget(why_label)

        # Command
        if command:
            cmd_label = QLabel(f"Suggested:\n{command}")
            cmd_label.setFont(QFont("Courier New", 8))
            cmd_label.setWordWrap(True)
            cmd_label.setStyleSheet("color: #d1d5db; background: rgba(0,0,0,0.3); padding: 5px; border-radius: 3px;")
            layout.addWidget(cmd_label)

        # Action buttons
        if actions:
            btn_layout = QHBoxLayout()
            for action_item in actions:
                btn = QPushButton(action_item.get("label", "Action"))
                btn.clicked.connect(action_item.get("callback", lambda: None))
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255,255,255,0.2);
                        color: white;
                        border: 1px solid rgba(255,255,255,0.3);
                        border-radius: 4px;
                        padding: 5px 15px;
                    }
                    QPushButton:hover {
                        background: rgba(255,255,255,0.3);
                    }
                """)
                btn_layout.addWidget(btn)
            layout.addLayout(btn_layout)

        # Dismiss button
        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.clicked.connect(self.fade_out)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        layout.addWidget(dismiss_btn, alignment=Qt.AlignRight)

        # Set container as central widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        self.setFixedSize(400, 250)

    def _get_stylesheet(self) -> str:
        """Get stylesheet based on severity"""
        colors = {
            "critical": "#dc2626",
            "warning": "#f59e0b",
            "suggestion": "#10b981"
        }

        bg_color = colors.get(self.severity, "#2563eb")

        return f"""
            QFrame#toast {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_color}, stop:1 rgba({bg_color}, 0.8));
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.2);
                padding: 15px;
            }}
        """

    def _position_window(self):
        """Position window in bottom-right corner"""
        from PyQt5.QtWidgets import QDesktopWidget

        screen = QDesktopWidget().screenGeometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60

        self.move(x, y)

    def _setup_animations(self):
        """Set up slide-in animation"""
        from PyQt5.QtWidgets import QDesktopWidget

        screen = QDesktopWidget().screenGeometry()
        start_x = screen.width()
        end_x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(QRect(start_x, y, self.width(), self.height()))
        self.animation.setEndValue(QRect(end_x, y, self.width(), self.height()))
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    def fade_out(self):
        """Fade out and close"""
        self.close()


class CriticalDialog(QWidget):
    """Critical violation dialog with block/override options"""

    def __init__(self, rule_name, message, action, why, command, on_block, on_override):
        super().__init__()

        self.result = 0  # 0 = override, 1 = block
        self.on_block = on_block
        self.on_override = on_override

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setWindowTitle("🚨 CRITICAL: Git Workflow Guardian")

        self._setup_ui(message, action, why, command)
        self.setFixedSize(500, 300)
        self._center_window()

    def _setup_ui(self, message, action, why, command):
        """Set up dialog UI"""

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Message
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Action
        if action:
            action_label = QLabel(f"✅ WHAT TO DO:\n{action}")
            action_label.setWordWrap(True)
            layout.addWidget(action_label)

        # Why
        if why:
            why_label = QLabel(f"📝 WHY:\n{why}")
            why_label.setWordWrap(True)
            why_label.setStyleSheet("color: #6b7280;")
            layout.addWidget(why_label)

        # Command
        if command:
            cmd_label = QLabel(f"Suggested:\n{command}")
            cmd_label.setFont(QFont("Courier New", 9))
            cmd_label.setWordWrap(True)
            cmd_label.setStyleSheet("background: #f3f4f6; padding: 10px; border-radius: 4px;")
            layout.addWidget(cmd_label)

        # Buttons
        btn_layout = QHBoxLayout()

        block_btn = QPushButton("🛑 Block this operation")
        block_btn.clicked.connect(self._on_block_clicked)
        block_btn.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #b91c1c;
            }
        """)
        btn_layout.addWidget(block_btn)

        override_btn = QPushButton("⚠️ Override (proceed anyway)")
        override_btn.clicked.connect(self._on_override_clicked)
        override_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #d97706;
            }
        """)
        btn_layout.addWidget(override_btn)

        layout.addLayout(btn_layout)

    def _center_window(self):
        """Center window on screen"""
        from PyQt5.QtWidgets import QDesktopWidget

        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _on_block_clicked(self):
        """Handle block button click"""
        self.result = 1
        if self.on_block:
            self.on_block()
        self.close()

    def _on_override_clicked(self):
        """Handle override button click"""
        self.result = 0
        if self.on_override:
            self.on_override()
        self.close()

    def exec_(self):
        """Execute dialog modally"""
        self.show()
        self.activateWindow()
        self.raise_()
        QApplication.instance().exec_()
        return self.result
