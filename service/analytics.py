"""
Git Workflow Guardian - Analytics Module
Generates reports, exports data, and analyzes trends
"""
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from .state import StateManager

logger = logging.getLogger(__name__)


class Analytics:
    """Analytics and reporting for Git Workflow Guardian"""

    def __init__(self, state_manager: Optional[StateManager] = None):
        self.state = state_manager or StateManager()

    def generate_daily_report(self, repo_path: Optional[Path] = None) -> Dict:
        """Generate daily compliance report"""
        stats = self.state.get_compliance_stats(repo_path)

        # Get today's violations
        today = datetime.now().date()
        violations_today = self._get_violations_by_date(today, repo_path)

        return {
            "date": today.isoformat(),
            "total_violations": len(violations_today),
            "critical_violations": len([v for v in violations_today if v["severity"] == "critical"]),
            "warnings": len([v for v in violations_today if v["severity"] == "warning"]),
            "suggestions": len([v for v in violations_today if v["severity"] == "suggestion"]),
            "overrides": len([v for v in violations_today if v["overridden"]]),
            "compliance_score": self._calculate_compliance_score(violations_today),
            "top_violations": self._get_top_violations(violations_today),
        }

    def generate_weekly_report(self, repo_path: Optional[Path] = None) -> Dict:
        """Generate weekly compliance report"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        violations = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            violations.extend(self._get_violations_by_date(date, repo_path))

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_violations": len(violations),
            "daily_average": len(violations) / 7,
            "compliance_score": self._calculate_compliance_score(violations),
            "violation_trend": self._calculate_trend(violations),
            "by_severity": self._group_by_severity(violations),
            "by_rule": self._group_by_rule(violations),
            "recommendations": self._generate_recommendations(violations),
        }

    def export_to_csv(self, output_path: Path, repo_path: Optional[Path] = None):
        """Export violations to CSV file"""
        violations = self._get_all_violations(repo_path)

        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'repository', 'branch', 'rule', 'severity', 'overridden']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for violation in violations:
                writer.writerow({
                    'timestamp': violation.get('timestamp', ''),
                    'repository': violation.get('repo', ''),
                    'branch': violation.get('branch', ''),
                    'rule': violation.get('rule_name', ''),
                    'severity': violation.get('severity', ''),
                    'overridden': violation.get('overridden', False)
                })

        logger.info(f"Exported {len(violations)} violations to {output_path}")

    def analyze_trends(self, days: int = 30, repo_path: Optional[Path] = None) -> Dict:
        """Analyze violation trends over time"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        daily_counts = []
        dates = []

        for i in range(days):
            date = start_date + timedelta(days=i)
            violations = self._get_violations_by_date(date, repo_path)
            daily_counts.append(len(violations))
            dates.append(date.isoformat())

        # Calculate trend (increasing/decreasing/stable)
        if len(daily_counts) >= 7:
            recent_avg = sum(daily_counts[-7:]) / 7
            previous_avg = sum(daily_counts[-14:-7]) / 7 if len(daily_counts) >= 14 else recent_avg

            if recent_avg > previous_avg * 1.2:
                trend = "increasing"
            elif recent_avg < previous_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "period": f"{start_date} to {end_date}",
            "daily_counts": daily_counts,
            "dates": dates,
            "average": sum(daily_counts) / len(daily_counts) if daily_counts else 0,
            "max": max(daily_counts) if daily_counts else 0,
            "min": min(daily_counts) if daily_counts else 0,
            "trend": trend,
            "improvement_rate": self._calculate_improvement_rate(daily_counts),
        }

    def get_compliance_score(self, repo_path: Optional[Path] = None) -> float:
        """Calculate overall compliance score (0-100)"""
        violations = self._get_violations_last_week(repo_path)

        if not violations:
            return 100.0

        # Scoring system
        total_score = 100.0
        critical_penalty = 10.0
        warning_penalty = 5.0
        suggestion_penalty = 2.0

        for violation in violations:
            severity = violation.get("severity", "suggestion")
            if severity == "critical":
                total_score -= critical_penalty
            elif severity == "warning":
                total_score -= warning_penalty
            else:
                total_score -= suggestion_penalty

        return max(0.0, total_score)

    def _get_violations_by_date(self, date: datetime.date, repo_path: Optional[Path]) -> List[Dict]:
        """Get violations for specific date"""
        import sqlite3

        conn = sqlite3.connect(str(self.state.db_path))
        cursor = conn.cursor()

        query = """
            SELECT v.id, v.rule_name, v.severity, v.branch_name, v.timestamp, v.overridden, r.path
            FROM violations v
            JOIN repositories r ON v.repo_id = r.id
            WHERE DATE(v.timestamp) = ?
        """
        params = [date.isoformat()]

        if repo_path:
            query += " AND r.path = ?"
            params.append(str(repo_path))

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "rule_name": row[1],
                "severity": row[2],
                "branch": row[3],
                "timestamp": row[4],
                "overridden": bool(row[5]),
                "repo": row[6]
            }
            for row in rows
        ]

    def _get_all_violations(self, repo_path: Optional[Path]) -> List[Dict]:
        """Get all violations"""
        import sqlite3

        conn = sqlite3.connect(str(self.state.db_path))
        cursor = conn.cursor()

        query = """
            SELECT v.rule_name, v.severity, v.branch_name, v.timestamp, v.overridden, r.path
            FROM violations v
            JOIN repositories r ON v.repo_id = r.id
            ORDER BY v.timestamp DESC
        """

        if repo_path:
            query = query.replace("ORDER BY", f"WHERE r.path = '{repo_path}' ORDER BY")

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "rule_name": row[0],
                "severity": row[1],
                "branch": row[2],
                "timestamp": row[3],
                "overridden": bool(row[4]),
                "repo": row[5]
            }
            for row in rows
        ]

    def _get_violations_last_week(self, repo_path: Optional[Path]) -> List[Dict]:
        """Get violations from last 7 days"""
        violations = []
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            violations.extend(self._get_violations_by_date(date, repo_path))
        return violations

    def _calculate_compliance_score(self, violations: List[Dict]) -> float:
        """Calculate compliance score from violations"""
        if not violations:
            return 100.0

        total = 100.0
        for v in violations:
            if v.get("severity") == "critical":
                total -= 10
            elif v.get("severity") == "warning":
                total -= 5
            else:
                total -= 2

        return max(0.0, total)

    def _calculate_trend(self, violations: List[Dict]) -> str:
        """Calculate trend direction"""
        if len(violations) < 2:
            return "stable"

        # Simple trend based on first half vs second half
        mid = len(violations) // 2
        first_half = violations[:mid]
        second_half = violations[mid:]

        if len(second_half) > len(first_half) * 1.2:
            return "worsening"
        elif len(second_half) < len(first_half) * 0.8:
            return "improving"
        else:
            return "stable"

    def _group_by_severity(self, violations: List[Dict]) -> Dict:
        """Group violations by severity"""
        grouped = {"critical": 0, "warning": 0, "suggestion": 0}
        for v in violations:
            severity = v.get("severity", "suggestion")
            grouped[severity] = grouped.get(severity, 0) + 1
        return grouped

    def _group_by_rule(self, violations: List[Dict]) -> Dict:
        """Group violations by rule"""
        grouped = {}
        for v in violations:
            rule = v.get("rule_name", "unknown")
            grouped[rule] = grouped.get(rule, 0) + 1
        return grouped

    def _get_top_violations(self, violations: List[Dict], limit: int = 5) -> List[Dict]:
        """Get most common violations"""
        by_rule = self._group_by_rule(violations)
        sorted_rules = sorted(by_rule.items(), key=lambda x: x[1], reverse=True)
        return [{"rule": rule, "count": count} for rule, count in sorted_rules[:limit]]

    def _generate_recommendations(self, violations: List[Dict]) -> List[str]:
        """Generate recommendations based on violations"""
        recommendations = []
        by_rule = self._group_by_rule(violations)

        if by_rule.get("commit_to_main", 0) > 5:
            recommendations.append("High number of commit-to-main violations. Consider enforcing feature branch workflow.")

        if by_rule.get("branch_naming", 0) > 3:
            recommendations.append("Branch naming violations detected. Review naming convention with team.")

        if by_rule.get("test_locally", 0) > 5:
            recommendations.append("Consider adding automated reminders to run local dev server.")

        by_severity = self._group_by_severity(violations)
        if by_severity.get("critical", 0) > 0:
            recommendations.append("Critical violations found. Review git workflow training with team.")

        if not recommendations:
            recommendations.append("Good compliance! Keep following best practices.")

        return recommendations

    def _calculate_improvement_rate(self, daily_counts: List[int]) -> float:
        """Calculate improvement rate percentage"""
        if len(daily_counts) < 7:
            return 0.0

        recent_avg = sum(daily_counts[-7:]) / 7
        previous_avg = sum(daily_counts[-14:-7]) / 7 if len(daily_counts) >= 14 else recent_avg

        if previous_avg == 0:
            return 0.0

        improvement = ((previous_avg - recent_avg) / previous_avg) * 100
        return round(improvement, 2)
