#!/usr/bin/env python3
"""
Git Workflow Guardian - Notification Handler for Hooks
Displays popup and handles override logic
"""
import sys
import argparse
import tkinter as tk
from tkinter import messagebox
import json
from pathlib import Path
import sqlite3
from datetime import datetime


class HookNotifier:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.db_path = Path.home() / ".git-workflow-guardian" / "state.db"
        self.config_path = self.repo_path / ".git" / "hooks" / "config.json"

    def check_override(self, rule_name, branch_name):
        """Check if violation is currently overridden"""
        if not self.db_path.exists():
            return False

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Check for active override
            cursor.execute("""
                SELECT id FROM overrides
                WHERE rule_name = ?
                AND session_id = ?
                AND (expires_at IS NULL OR expires_at > ?)
            """, (rule_name, branch_name, datetime.now().isoformat()))

            result = cursor.fetchone()
            conn.close()

            return result is not None
        except Exception:
            return False

    def save_override(self, rule_name, branch_name):
        """Save override to database (session-level)"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create tables if not exist (simplified for hook usage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS overrides (
                id INTEGER PRIMARY KEY,
                rule_name TEXT,
                session_id TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert override (session-level, no expiry)
        cursor.execute("""
            INSERT INTO overrides (rule_name, session_id, expires_at)
            VALUES (?, ?, NULL)
        """, (rule_name, branch_name))

        conn.commit()
        conn.close()

    def show_notification(self, violation_type, branch_name, non_blocking=False):
        """Display tkinter popup with override option"""

        messages = {
            "commit_to_main": {
                "title": "🚨 CRITICAL: Committing to Main",
                "message": f"You're about to commit to '{branch_name}' branch.",
                "action": "Create a feature branch first",
                "why": "Main should only receive reviewed code via PRs.\nDirect commits bypass the review process.",
                "command": f"git checkout -b claude/feature-name-[sessionId]"
            },
            "push_to_main": {
                "title": "🚨 CRITICAL: Pushing to Main",
                "message": f"You're about to push to '{branch_name}' branch.",
                "action": "Create a feature branch and PR instead",
                "why": "Pushing to main bypasses code review and CI checks.",
                "command": "git checkout -b claude/feature-name-[sessionId]"
            },
            "pull_before_work": {
                "title": "💡 SUGGESTION: Pull Main",
                "message": f"The '{branch_name}' branch is behind the remote.",
                "action": "Pull latest changes before working",
                "why": "Ensures you're working with latest code.",
                "command": f"git pull origin {branch_name}"
            },
            "delete_merged_branch": {
                "title": "💡 SUGGESTION: Clean Up Branches",
                "message": f"Branch '{branch_name}' has been merged.",
                "action": "Delete the branch to keep repo clean",
                "why": "Stale branches clutter the repository.",
                "command": f"git branch -d {branch_name}"
            }
        }

        msg = messages.get(violation_type, {
            "title": "Git Workflow Guardian",
            "message": f"Violation: {violation_type}",
            "action": "Please review your workflow",
            "why": "Best practices are important.",
            "command": ""
        })

        # For non-blocking notifications, just print to console
        if non_blocking:
            print(f"[INFO] {msg['title']}")
            print(f"  {msg['message']}")
            print(f"  Action: {msg['action']}")
            return False

        # Build message
        full_message = f"{msg['message']}\n\n"
        full_message += f"✅ WHAT TO DO:\n{msg['action']}\n\n"
        full_message += f"📝 WHY:\n{msg['why']}\n\n"
        full_message += f"Suggested:\n{msg['command']}"

        try:
            # Create tkinter popup
            root = tk.Tk()
            root.withdraw()  # Hide main window

            # Custom dialog with two buttons
            response = messagebox.askyesno(
                msg["title"],
                full_message + "\n\nBlock this operation?",
                icon=messagebox.ERROR if "CRITICAL" in msg["title"] else messagebox.INFO
            )

            root.destroy()

            return response  # True = block, False = override
        except Exception as e:
            # Fallback if GUI not available
            print(f"[WARNING] {msg['title']}")
            print(f"  {full_message}")
            print(f"  (GUI not available: {e})")
            return True  # Block by default if can't show popup

    def run(self, violation_type, branch_name, non_blocking=False):
        """Main execution logic"""

        # Check if already overridden
        if self.check_override(violation_type, branch_name):
            print(f"[Override Active] {violation_type} is overridden for this session")
            return 0  # Allow operation

        # Show notification
        should_block = self.show_notification(violation_type, branch_name, non_blocking)

        if non_blocking:
            return 0  # Always allow for non-blocking notifications

        if should_block:
            print(f"[BLOCKED] {violation_type}")
            return 1  # Block operation
        else:
            # User chose to override
            self.save_override(violation_type, branch_name)
            print(f"[Override] {violation_type} overridden for this session")
            return 0  # Allow operation


def main():
    parser = argparse.ArgumentParser(description="Git Workflow Guardian Hook Notifier")
    parser.add_argument("--violation", required=True, help="Violation type")
    parser.add_argument("--branch", required=True, help="Current branch")
    parser.add_argument("--repo", required=True, help="Repository path")
    parser.add_argument("--non-blocking", action="store_true", help="Non-blocking notification")

    args = parser.parse_args()

    notifier = HookNotifier(args.repo)
    exit_code = notifier.run(args.violation, args.branch, args.non_blocking)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
