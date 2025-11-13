"""Tests for analytics module"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from service.analytics import Analytics


def test_analytics_initialization(temp_db):
    """Test Analytics initializes correctly"""
    from service.state import StateManager

    state = StateManager(str(temp_db))
    analytics = Analytics(state)

    assert analytics.state is not None


def test_generate_daily_report(temp_db):
    """Test daily report generation"""
    from service.state import StateManager

    state = StateManager(str(temp_db))
    analytics = Analytics(state)

    # Log some violations
    repo_path = Path("/tmp/test-repo")
    state.log_violation(repo_path, "commit_to_main", "critical", "main")
    state.log_violation(repo_path, "test_locally", "suggestion", "feature")

    report = analytics.generate_daily_report(repo_path)

    assert "date" in report
    assert "total_violations" in report
    assert "compliance_score" in report
    assert report["total_violations"] >= 0


def test_compliance_score_calculation(temp_db):
    """Test compliance score calculation"""
    from service.state import StateManager

    state = StateManager(str(temp_db))
    analytics = Analytics(state)

    # No violations = perfect score
    score = analytics.get_compliance_score()
    assert score == 100.0

    # Add some violations
    repo_path = Path("/tmp/test-repo")
    state.log_violation(repo_path, "commit_to_main", "critical", "main")

    score = analytics.get_compliance_score(repo_path)
    assert score < 100.0
    assert score >= 0.0


def test_export_to_csv(temp_db, tmp_path):
    """Test CSV export"""
    from service.state import StateManager

    state = StateManager(str(temp_db))
    analytics = Analytics(state)

    # Log violations
    repo_path = Path("/tmp/test-repo")
    state.log_violation(repo_path, "commit_to_main", "critical", "main")
    state.log_violation(repo_path, "branch_naming", "warning", "feature")

    # Export
    csv_path = tmp_path / "violations.csv"
    analytics.export_to_csv(csv_path, repo_path)

    assert csv_path.exists()
    content = csv_path.read_text()
    assert "timestamp" in content
    assert "repository" in content
    assert "rule" in content


def test_analyze_trends(temp_db):
    """Test trend analysis"""
    from service.state import StateManager

    state = StateManager(str(temp_db))
    analytics = Analytics(state)

    repo_path = Path("/tmp/test-repo")
    state.log_violation(repo_path, "test_locally", "suggestion", "feature")

    trends = analytics.analyze_trends(days=7, repo_path=repo_path)

    assert "period" in trends
    assert "daily_counts" in trends
    assert "trend" in trends
    assert isinstance(trends["daily_counts"], list)


def test_weekly_report(temp_db):
    """Test weekly report generation"""
    from service.state import StateManager

    state = StateManager(str(temp_db))
    analytics = Analytics(state)

    repo_path = Path("/tmp/test-repo")
    state.log_violation(repo_path, "commit_to_main", "critical", "main")

    report = analytics.generate_weekly_report(repo_path)

    assert "start_date" in report
    assert "end_date" in report
    assert "total_violations" in report
    assert "compliance_score" in report
    assert "by_severity" in report
    assert "recommendations" in report
