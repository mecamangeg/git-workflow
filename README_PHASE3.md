# Git Workflow Guardian - Phase 3 Features

## 🎨 Advanced Features (v2.0)

Phase 3 adds polish and advanced capabilities to the Git Workflow Guardian system.

---

## 📊 Compliance Dashboard

**Flask-based web interface for monitoring workflow compliance**

### Features:
- 📈 **Real-time violation feed** - See violations as they happen
- 📊 **Compliance score** - Track overall adherence (0-100%)
- 📉 **Trend charts** - Visualize violation patterns over 30 days
- 📁 **Repository overview** - Monitor multiple repos
- 📥 **CSV export** - Download violation data for analysis

### Starting the Dashboard:

```bash
# Method 1: Python script
python scripts/run_dashboard.py

# Method 2: Bash script
./scripts/run_dashboard.sh

# Custom port
python scripts/run_dashboard.py --port 9000

# Public access (network accessible)
python scripts/run_dashboard.py --public
```

### Accessing:
- **Local:** http://127.0.0.1:8765
- **Network:** http://your-ip:8765 (with --public flag)

### API Endpoints:
- `GET /api/stats` - Overall statistics
- `GET /api/violations` - Recent violations
- `GET /api/violations/live` - Last hour violations
- `GET /api/daily-report` - Daily compliance report
- `GET /api/weekly-report` - Weekly compliance report
- `GET /api/trends?days=30` - Trend data
- `GET /api/export/csv` - Download CSV export
- `GET /api/repositories` - List monitored repos

---

## 📈 Analytics & Reporting

**Advanced analytics for compliance tracking**

### Features:
- 📊 **Daily/Weekly Reports** - Automated compliance summaries
- 📉 **Trend Analysis** - Track improvement over time
- 📥 **CSV Export** - Export data for spreadsheets
- 💡 **Recommendations** - AI-driven workflow improvements

### Usage:

```python
from service.analytics import Analytics
from service.state import StateManager

# Initialize
state = StateManager()
analytics = Analytics(state)

# Generate daily report
report = analytics.generate_daily_report()
print(f"Compliance Score: {report['compliance_score']}%")

# Generate weekly report
weekly = analytics.generate_weekly_report()
print(f"Recommendations: {weekly['recommendations']}")

# Export to CSV
from pathlib import Path
analytics.export_to_csv(Path("violations.csv"))

# Analyze trends
trends = analytics.analyze_trends(days=30)
print(f"Trend: {trends['trend']}")  # improving/stable/worsening
```

### Report Contents:

**Daily Report:**
- Total violations today
- Critical/Warning/Suggestion breakdown
- Compliance score
- Top violations

**Weekly Report:**
- 7-day violation summary
- Daily average
- Compliance trend
- Violation breakdown by severity and rule
- Improvement recommendations

---

## 🚀 Vercel Integration

**Detect PR merges and deployment status**

### Features:
- 🔍 **Deployment Detection** - Find deployments for branches
- ⏱️ **Status Monitoring** - Track deployment progress
- 🔗 **Preview URLs** - Get deployment URLs automatically
- ✅ **Completion Tracking** - Know when deployments finish

### Configuration:

```bash
# Set environment variables
export VERCEL_API_TOKEN="your_vercel_token"
export VERCEL_TEAM_ID="your_team_id"  # Optional
```

Or in your monitoring service config:

```yaml
# config/rules.yaml
vercel:
  enabled: true
  api_token: "your_token_here"
  team_id: "your_team_id"  # Optional
```

### Usage:

```python
from service.vercel import VercelIntegration

# Initialize
vercel = VercelIntegration()

# Check if configured
if vercel.is_configured():
    # Get recent deployments
    deployments = vercel.get_recent_deployments(limit=10)

    for d in deployments:
        print(f"{d['name']}: {d['state']} - {d['url']}")

    # Check deployment for PR branch
    deployment = vercel.detect_pr_deployment("feature-branch")
    if deployment:
        print(f"Found deployment: {deployment['url']}")

    # Get deployment URL
    url = vercel.get_deployment_url("feature-branch")
    if url:
        print(f"Preview: {url}")

    # Wait for deployment to complete
    success = vercel.wait_for_deployment("deployment_id", timeout=300)
```

### Deployment States:
- `BUILDING` - In progress
- `READY` - Completed successfully
- `ERROR` - Failed
- `CANCELED` - Canceled by user

---

## 🎨 PyQt5 Advanced Notifications

**Enhanced notification system with modern UI**

### Features:
- 🎨 **Modern design** - Polished, gradient backgrounds
- 🎬 **Smooth animations** - Slide-in effects
- 🔘 **Action buttons** - Interactive notifications
- 🎨 **Themes** - Severity-based color schemes
- ⚡ **Better performance** - Native Qt rendering

### Usage:

The system automatically uses PyQt5 if available, falls back to tkinter otherwise.

#### In Python Code:

```python
from service.notifier_pyqt5 import PyQt5Notifier
from service.config import ConfigManager

config = ConfigManager()
notifier = PyQt5Notifier(config)

# Show toast with actions
notifier.show_toast(
    rule_name="test_locally",
    severity="suggestion",
    message="Local dev server not detected",
    repo_path=Path("/path/to/repo"),
    branch="feature-branch",
    actions=[
        {
            "label": "Start Server",
            "callback": lambda: os.system("npm run dev")
        },
        {
            "label": "Ignore",
            "callback": lambda: print("Ignored")
        }
    ]
)

# Show critical popup
should_block = notifier.show_critical_popup(
    rule_name="commit_to_main",
    message="You're about to commit to main",
    branch="main",
    repo_path=Path("/path/to/repo")
)

if should_block:
    print("Operation blocked")
else:
    print("User overrode")
```

#### Installation:

```bash
# Install PyQt5
pip install PyQt5>=5.15.0

# Or install all Phase 3 dependencies
pip install -r requirements.txt
```

#### Fallback Behavior:

If PyQt5 is not installed, the system automatically falls back to tkinter-based notifications. No configuration needed!

---

## 🔧 Integration with Monitoring Service

### Enable Vercel Notifications:

Add to `service/monitor.py`:

```python
from .vercel import VercelIntegration

class MonitorService:
    def __init__(self, config_path: str = None):
        # ... existing code ...
        self.vercel = VercelIntegration()

    def check_repository(self, repo_path: Path) -> List[Dict]:
        violations = []
        # ... existing checks ...

        # Check Vercel deployments
        if self.vercel.is_configured():
            current_branch = self.detector.get_current_branch(repo_path)
            deployment = self.vercel.detect_pr_deployment(current_branch)

            if deployment and deployment.get("state") == "READY":
                # Notify about successful deployment
                self.notifier.show_toast(
                    rule_name="vercel_deployment",
                    severity="suggestion",
                    message=f"Deployment ready: {deployment['url']}",
                    repo_path=repo_path,
                    branch=current_branch
                )

        return violations
```

---

## 📦 Dependencies

Phase 3 adds these dependencies:

```txt
# Dashboard
flask>=2.3.0
flask-cors>=4.0.0

# Advanced Notifications (optional)
PyQt5>=5.15.0
```

Install all:

```bash
pip install -r requirements.txt
```

---

## 🎯 Use Cases

### 1. Team Compliance Monitoring

Use the dashboard to monitor team compliance in real-time:

```bash
# Start dashboard on network
python scripts/run_dashboard.py --public --port 8765

# Share with team
# http://your-server-ip:8765
```

### 2. CI/CD Integration

Export compliance data for CI/CD:

```bash
# In your CI script
curl http://localhost:8765/api/stats > compliance-stats.json

# Check compliance score
score=$(jq '.compliance_score' compliance-stats.json)
if [ $score -lt 95 ]; then
    echo "Compliance below 95%: $score%"
    exit 1
fi
```

### 3. Automated Reports

Generate weekly reports automatically:

```python
# weekly_report.py
from service.analytics import Analytics

analytics = Analytics()
report = analytics.generate_weekly_report()

# Email report
send_email(
    to="team@company.com",
    subject=f"Weekly Git Compliance Report",
    body=format_report(report)
)
```

### 4. Vercel Deployment Tracking

Track deployments in notifications:

```python
# After PR merge
deployment = vercel.detect_pr_deployment("feature-branch")
if deployment:
    print(f"Preview URL: {deployment['url']}")

    # Wait for deployment
    if vercel.wait_for_deployment(deployment['id']):
        send_notification("Deployment successful!")
```

---

## 🧪 Testing Phase 3 Features

```bash
# Test dashboard
python scripts/run_dashboard.py --debug

# Test analytics
python -c "from service.analytics import Analytics; print(Analytics().generate_daily_report())"

# Test Vercel (requires token)
export VERCEL_API_TOKEN="your_token"
python -c "from service.vercel import VercelIntegration; print(VercelIntegration().test_connection())"

# Test PyQt5 notifications
python -c "from service.notifier_pyqt5 import PYQT5_AVAILABLE; print('PyQt5 available:', PYQT5_AVAILABLE)"
```

---

## 📊 Dashboard Screenshots

The dashboard provides:
- Real-time compliance score
- Violation counts by severity
- 30-day trend charts
- Live violation feed
- Repository list
- CSV export

Access at **http://127.0.0.1:8765** after starting.

---

## 🎉 Phase 3 Complete

All advanced features are now available:
- ✅ Compliance Dashboard (Flask)
- ✅ Analytics & Reporting
- ✅ Vercel Integration
- ✅ PyQt5 Notifications

**Git Workflow Guardian is now feature-complete!** 🚀

---

**Version:** 2.0.0 (Phase 3)
**Status:** Production Ready
**Dependencies:** Flask, PyQt5 (optional)
