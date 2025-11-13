"""
Git Workflow Guardian - Compliance Dashboard
Flask web interface for viewing violations and analytics
"""
from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
from datetime import datetime, timedelta
import json

from .state import StateManager
from .analytics import Analytics

app = Flask(__name__, template_folder='../dashboard/templates', static_folder='../dashboard/static')

# Initialize services
state_manager = StateManager()
analytics = Analytics(state_manager)


@app.route('/')
def index():
    """Dashboard home page"""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    stats = state_manager.get_compliance_stats()
    compliance_score = analytics.get_compliance_score()

    return jsonify({
        "total_violations": stats.get("total_violations", 0),
        "overridden_count": stats.get("overridden_count", 0),
        "compliance_score": compliance_score,
        "by_severity": stats.get("by_severity", {}),
        "by_rule": stats.get("by_rule", {})
    })


@app.route('/api/violations')
def get_violations():
    """Get recent violations"""
    limit = request.args.get('limit', 50, type=int)
    violations = analytics._get_all_violations(None)[:limit]

    return jsonify({
        "violations": violations,
        "count": len(violations)
    })


@app.route('/api/violations/live')
def get_live_violations():
    """Get violations from last hour for live feed"""
    violations = analytics._get_all_violations(None)
    one_hour_ago = datetime.now() - timedelta(hours=1)

    recent = [
        v for v in violations
        if datetime.fromisoformat(v["timestamp"]) > one_hour_ago
    ]

    return jsonify({
        "violations": recent,
        "count": len(recent)
    })


@app.route('/api/daily-report')
def get_daily_report():
    """Get daily compliance report"""
    report = analytics.generate_daily_report()
    return jsonify(report)


@app.route('/api/weekly-report')
def get_weekly_report():
    """Get weekly compliance report"""
    report = analytics.generate_weekly_report()
    return jsonify(report)


@app.route('/api/trends')
def get_trends():
    """Get violation trends"""
    days = request.args.get('days', 30, type=int)
    trends = analytics.analyze_trends(days)
    return jsonify(trends)


@app.route('/api/export/csv')
def export_csv():
    """Export violations to CSV"""
    import tempfile
    import os

    # Create temporary file
    fd, temp_path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)

    analytics.export_to_csv(Path(temp_path))

    return send_file(
        temp_path,
        as_attachment=True,
        download_name=f'violations_{datetime.now().strftime("%Y%m%d")}.csv',
        mimetype='text/csv'
    )


@app.route('/api/repositories')
def get_repositories():
    """Get monitored repositories"""
    import sqlite3

    conn = sqlite3.connect(str(state_manager.db_path))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, path, name, discovered_at, last_checked, is_active
        FROM repositories
        WHERE is_active = 1
        ORDER BY name
    """)

    rows = cursor.fetchall()
    conn.close()

    repos = [
        {
            "id": row[0],
            "path": row[1],
            "name": row[2],
            "discovered_at": row[3],
            "last_checked": row[4],
            "is_active": bool(row[5])
        }
        for row in rows
    ]

    return jsonify({"repositories": repos, "count": len(repos)})


def start_dashboard(host='127.0.0.1', port=8765, debug=False):
    """Start the Flask dashboard server"""
    print(f"🚀 Starting Git Workflow Guardian Dashboard")
    print(f"📊 Dashboard: http://{host}:{port}")
    print(f"📈 Analytics: http://{host}:{port}/api/stats")
    print(f"Press Ctrl+C to stop")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    start_dashboard(debug=True)
