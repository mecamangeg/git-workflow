#!/bin/bash
#
# Control script for Claude Code Workflow sync watcher
# Provides easy commands to control the auto-sync system
#

set -e

TMUX_SESSION="claude-sync"
WORKSPACE_DIR="/workspaces/$(basename $(pwd))"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo -e "\n${CYAN}$1${NC}"
}

# Check if session exists
session_exists() {
    tmux has-session -t "$TMUX_SESSION" 2>/dev/null
}

# Commands
cmd_status() {
    print_header "Claude Code Workflow - Status"

    if session_exists; then
        print_success "Auto-sync is running"

        # Get session info
        echo ""
        echo "📊 Session Info:"
        tmux list-sessions | grep "$TMUX_SESSION" || true

        echo ""
        echo "🔗 Commands:"
        echo "   - View logs:  bash sync-control.sh logs"
        echo "   - Stop:       bash sync-control.sh stop"
        echo "   - Restart:    bash sync-control.sh restart"
    else
        print_warning "Auto-sync is not running"
        echo ""
        echo "🚀 Start with: bash sync-control.sh start"
    fi
}

cmd_start() {
    print_header "Starting Auto-Sync..."

    if session_exists; then
        print_warning "Auto-sync is already running"
        echo "   View logs: bash sync-control.sh logs"
        return 0
    fi

    # Run start script
    bash .devcontainer/start-sync.sh
}

cmd_stop() {
    print_header "Stopping Auto-Sync..."

    if ! session_exists; then
        print_warning "Auto-sync is not running"
        return 0
    fi

    tmux kill-session -t "$TMUX_SESSION"
    print_success "Auto-sync stopped"
}

cmd_restart() {
    print_header "Restarting Auto-Sync..."

    cmd_stop
    sleep 2
    cmd_start
}

cmd_logs() {
    print_header "Viewing Auto-Sync Logs"
    echo ""
    print_info "Attaching to sync session..."
    print_info "Press Ctrl+b, then d to detach (leave running)"
    echo ""
    sleep 2

    if ! session_exists; then
        print_error "Auto-sync is not running"
        echo "   Start with: bash sync-control.sh start"
        return 1
    fi

    # Attach to tmux session
    tmux attach-session -t "$TMUX_SESSION"
}

cmd_dev_logs() {
    print_header "Viewing Dev Server Logs"

    if [ -f "$WORKSPACE_DIR/.dev-server.log" ]; then
        tail -f "$WORKSPACE_DIR/.dev-server.log"
    else
        print_error "Dev server log file not found"
        echo "   Dev server may not be running yet"
    fi
}

cmd_help() {
    cat << 'EOF'
Claude Code Workflow - Control Script

Usage: bash sync-control.sh <command>

Commands:
  status      Show sync status
  start       Start auto-sync (runs in background)
  stop        Stop auto-sync
  restart     Restart auto-sync
  logs        View sync logs (attach to session)
  dev-logs    View dev server logs
  help        Show this help message

Examples:
  bash sync-control.sh status     # Check if running
  bash sync-control.sh logs       # View what's happening
  bash sync-control.sh restart    # Restart if having issues

Tips:
  - Auto-sync runs in a tmux session named 'claude-sync'
  - Logs are visible and scrollable
  - Ctrl+b, then d to detach (leave running)
  - Ctrl+C in attached session to stop

Quick Start:
  1. bash sync-control.sh start   # Start auto-sync
  2. Code in Claude Code web      # Claude pushes branches
  3. bash sync-control.sh logs    # Watch it sync automatically
  4. Test in browser preview URL  # Everything is ready!
EOF
}

# Main command router
case "${1:-}" in
    status)
        cmd_status
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    logs)
        cmd_logs
        ;;
    dev-logs)
        cmd_dev_logs
        ;;
    help|--help|-h)
        cmd_help
        ;;
    "")
        print_error "No command specified"
        echo ""
        cmd_help
        exit 1
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
