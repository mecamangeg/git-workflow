#!/bin/bash
#
# Auto-start sync watcher in a visible tmux session
# This runs automatically when Codespaces starts
#

echo "🚀 Starting Claude Code Workflow - Auto-Sync..."

# Get the workspace directory
WORKSPACE_DIR="/workspaces/$(basename $(pwd))"

# Check if mini_sync.py exists
if [ ! -f "$WORKSPACE_DIR/mini_sync.py" ]; then
    echo "❌ mini_sync.py not found in $WORKSPACE_DIR"
    echo "   Please add mini_sync.py to your repository"
    exit 1
fi

# Check if already running
if tmux has-session -t claude-sync 2>/dev/null; then
    echo "⚠️  Sync session already running"
    echo "   View logs: tmux attach -t claude-sync"
    exit 0
fi

# Create tmux session running in background but visible
tmux new-session -d -s claude-sync -c "$WORKSPACE_DIR" "
    echo '🚀 Claude Code Workflow - Auto-Sync'
    echo '=================================='
    echo ''
    echo '✅ Auto-sync is running!'
    echo '   - Detects Claude branches every 10 seconds'
    echo '   - Auto-checkout and pull'
    echo '   - Runs tests automatically'
    echo '   - Auto-starts dev server'
    echo ''
    echo '📊 Controls:'
    echo '   - View this terminal: tmux attach -t claude-sync'
    echo '   - Detach: Ctrl+b, then d'
    echo '   - Stop: Ctrl+C (in attached session)'
    echo '   - Restart: bash sync-control.sh restart'
    echo ''
    echo '📝 Logs will appear below:'
    echo '=================================='
    echo ''

    # Run mini_sync.py with auto-start enabled
    cd $WORKSPACE_DIR
    python mini_sync.py --watch --interval 10
"

# Wait a moment for session to start
sleep 1

# Check if session started successfully
if tmux has-session -t claude-sync 2>/dev/null; then
    echo "✅ Auto-sync started successfully!"
    echo ""
    echo "📊 Quick Commands:"
    echo "   - View sync logs:    tmux attach -t claude-sync"
    echo "   - Detach from logs:  Ctrl+b, then d"
    echo "   - Stop sync:         bash sync-control.sh stop"
    echo "   - Restart sync:      bash sync-control.sh restart"
    echo "   - Check status:      bash sync-control.sh status"
    echo ""
    echo "🎯 Just code in Claude Code web - everything else is automatic!"
    echo ""
else
    echo "❌ Failed to start sync session"
    exit 1
fi
