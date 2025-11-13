#!/bin/bash
# Git Workflow Guardian - Service Installation Script (Linux/systemd)

set -e

SERVICE_NAME="git-workflow-guardian"
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

# Check for uninstall flag
if [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
    echo "Uninstalling $SERVICE_DISPLAY_NAME..."

    # Stop and disable service
    systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true

    # Remove service file
    rm -f "$HOME/.config/systemd/user/$SERVICE_NAME.service"

    # Reload systemd
    systemctl --user daemon-reload

    echo "✓ Service uninstalled successfully"
    exit 0
fi

echo "======================================"
echo " Git Workflow Guardian - Service Installer (Linux)"
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
echo "[2/4] Creating systemd service..."

# Create systemd user directory
mkdir -p "$HOME/.config/systemd/user"

# Create service file
cat > "$HOME/.config/systemd/user/$SERVICE_NAME.service" <<EOF
[Unit]
Description=$SERVICE_DISPLAY_NAME
After=network.target

[Service]
Type=simple
ExecStart=$PYTHON_CMD $SERVICE_SCRIPT
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

echo "  ✓ Service file created"

echo ""
echo "[3/4] Enabling service..."

# Reload systemd
systemctl --user daemon-reload

# Enable service
systemctl --user enable "$SERVICE_NAME"
echo "  ✓ Service enabled"

echo ""
echo "[4/4] Starting service..."

# Start service
systemctl --user start "$SERVICE_NAME"

# Wait a moment
sleep 2

# Check status
if systemctl --user is-active --quiet "$SERVICE_NAME"; then
    echo "  ✓ Service started successfully"
else
    echo "  ⚠ Service may not be running. Check status with:"
    echo "    systemctl --user status $SERVICE_NAME"
fi

echo ""
echo "======================================"
echo " Installation Complete!"
echo "======================================"

echo ""
echo "Service details:"
echo "  Name: $SERVICE_NAME"
echo "  Status: $(systemctl --user is-active $SERVICE_NAME)"
echo "  Script: $SERVICE_SCRIPT"

echo ""
echo "Useful commands:"
echo "  Status:  systemctl --user status $SERVICE_NAME"
echo "  Stop:    systemctl --user stop $SERVICE_NAME"
echo "  Start:   systemctl --user start $SERVICE_NAME"
echo "  Restart: systemctl --user restart $SERVICE_NAME"
echo "  Logs:    journalctl --user -u $SERVICE_NAME -f"
echo "  Uninstall: $0 --uninstall"
