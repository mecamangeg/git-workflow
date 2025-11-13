#!/bin/bash
# Git Workflow Guardian - Service Installation Script (macOS/launchd)

set -e

SERVICE_NAME="com.git-workflow-guardian"
SERVICE_DISPLAY_NAME="Git Workflow Guardian Monitor"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_SCRIPT="$PROJECT_ROOT/service/monitor.py"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=$(which python3)
elif command -v python &> /dev/null; then
    PYTHON_CMD=$(which python)
else
    echo "Error: Python not found. Please install Python 3.8+"
    exit 1
fi

PLIST_FILE="$HOME/Library/LaunchAgents/$SERVICE_NAME.plist"

# Check for uninstall flag
if [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
    echo "Uninstalling $SERVICE_DISPLAY_NAME..."

    # Unload service
    if [ -f "$PLIST_FILE" ]; then
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        rm -f "$PLIST_FILE"
        echo "  ✓ Service unloaded and removed"
    else
        echo "  ℹ Service not found"
    fi

    echo "Uninstallation complete!"
    exit 0
fi

echo "======================================"
echo " Git Workflow Guardian - Service Installer (macOS)"
echo "======================================"

echo ""
echo "[1/4] Validating environment..."

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "  ✓ Python found: $PYTHON_VERSION"

# Check service script
if [ ! -f "$SERVICE_SCRIPT" ]; then
    echo "  ✗ Service script not found: $SERVICE_SCRIPT"
    exit 1
fi
echo "  ✓ Service script found"

echo ""
echo "[2/4] Creating launchd plist..."

# Create LaunchAgents directory
mkdir -p "$HOME/Library/LaunchAgents"

# Create plist file
cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$SERVICE_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_CMD</string>
        <string>$SERVICE_SCRIPT</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/git-workflow-guardian.log</string>

    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/git-workflow-guardian-error.log</string>
</dict>
</plist>
EOF

echo "  ✓ Plist file created"

echo ""
echo "[3/4] Loading service..."

# Load service
launchctl load "$PLIST_FILE"
echo "  ✓ Service loaded"

echo ""
echo "[4/4] Verifying service..."

# Wait a moment
sleep 2

# Check if process is running
if launchctl list | grep -q "$SERVICE_NAME"; then
    echo "  ✓ Service started successfully"
else
    echo "  ⚠ Service may not be running. Check logs:"
    echo "    $HOME/Library/Logs/git-workflow-guardian-error.log"
fi

echo ""
echo "======================================"
echo " Installation Complete!"
echo "======================================"

echo ""
echo "Service details:"
echo "  Name: $SERVICE_NAME"
echo "  Script: $SERVICE_SCRIPT"
echo "  Plist: $PLIST_FILE"

echo ""
echo "Useful commands:"
echo "  Status:  launchctl list | grep $SERVICE_NAME"
echo "  Stop:    launchctl unload $PLIST_FILE"
echo "  Start:   launchctl load $PLIST_FILE"
echo "  Logs:    tail -f ~/Library/Logs/git-workflow-guardian.log"
echo "  Errors:  tail -f ~/Library/Logs/git-workflow-guardian-error.log"
echo "  Uninstall: $0 --uninstall"
