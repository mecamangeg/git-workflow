#!/bin/bash
# Git Workflow Guardian - Dashboard Launcher (Bash)

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.8+"
    exit 1
fi

echo "========================================"
echo "🛡️  Git Workflow Guardian - Dashboard"
echo "========================================"
echo ""

# Check if Flask is installed
if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not installed. Installing dependencies..."
    $PYTHON_CMD -m pip install -r "$PROJECT_ROOT/requirements.txt"
    echo ""
fi

# Run dashboard
echo "Starting dashboard server..."
echo "📊 Dashboard will be available at: http://127.0.0.1:8765"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$PROJECT_ROOT"
$PYTHON_CMD scripts/run_dashboard.py "$@"
