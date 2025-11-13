#!/bin/bash
#
# Install Claude Code Workflow Automation to a project
# Usage: bash install-to-project.sh /path/to/your/project
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header() {
    echo -e "\n${CYAN}$1${NC}"
}

# Check if destination provided
if [ -z "$1" ]; then
    print_error "No destination directory specified"
    echo ""
    echo "Usage: bash install-to-project.sh /path/to/your/project"
    echo ""
    echo "Example:"
    echo "  bash install-to-project.sh ~/Projects/my-nextjs-app"
    exit 1
fi

DEST_DIR="$1"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if destination exists
if [ ! -d "$DEST_DIR" ]; then
    print_error "Directory does not exist: $DEST_DIR"
    exit 1
fi

# Check if it's a git repo
if [ ! -d "$DEST_DIR/.git" ]; then
    print_error "Not a git repository: $DEST_DIR"
    echo "   Please initialize git first: git init"
    exit 1
fi

print_header "Installing Claude Code Workflow Automation"
print_info "Source: $SOURCE_DIR"
print_info "Destination: $DEST_DIR"
echo ""

# Core files
print_header "📦 Core Files"

cp "$SOURCE_DIR/mini_sync.py" "$DEST_DIR/"
print_success "Copied mini_sync.py"

if [ -f "$DEST_DIR/.sync.yaml" ]; then
    print_info ".sync.yaml already exists, skipping (use .sync.yaml.example as reference)"
else
    cp "$SOURCE_DIR/.sync.yaml.example" "$DEST_DIR/.sync.yaml"
    print_success "Copied .sync.yaml (configure this for your project)"
fi

cp "$SOURCE_DIR/sync-control.sh" "$DEST_DIR/"
chmod +x "$DEST_DIR/sync-control.sh"
print_success "Copied sync-control.sh"

# Devcontainer files
print_header "🐳 Devcontainer Files (for GitHub Codespaces)"

mkdir -p "$DEST_DIR/.devcontainer"

cp "$SOURCE_DIR/.devcontainer/devcontainer.json" "$DEST_DIR/.devcontainer/"
print_success "Copied .devcontainer/devcontainer.json"

cp "$SOURCE_DIR/.devcontainer/start-sync.sh" "$DEST_DIR/.devcontainer/"
chmod +x "$DEST_DIR/.devcontainer/start-sync.sh"
print_success "Copied .devcontainer/start-sync.sh"

# Documentation
print_header "📚 Documentation"

cp "$SOURCE_DIR/AI-SETUP-INSTRUCTIONS.md" "$DEST_DIR/"
print_success "Copied AI-SETUP-INSTRUCTIONS.md"

cp "$SOURCE_DIR/CODESPACES-SETUP.md" "$DEST_DIR/"
print_success "Copied CODESPACES-SETUP.md"

cp "$SOURCE_DIR/MINI-VERSION-README.md" "$DEST_DIR/"
print_success "Copied MINI-VERSION-README.md"

cp "$SOURCE_DIR/MINI-VERSION-SUMMARY.md" "$DEST_DIR/"
print_success "Copied MINI-VERSION-SUMMARY.md"

cp "$SOURCE_DIR/CODESPACES-WORKFLOW-BRAINSTORM.md" "$DEST_DIR/"
print_success "Copied CODESPACES-WORKFLOW-BRAINSTORM.md"

# Summary
print_header "✅ Installation Complete!"
echo ""
print_info "Files installed in: $DEST_DIR"
echo ""

print_header "📋 Next Steps"
echo ""
echo "1. Configure for your project:"
echo "   ${CYAN}cd $DEST_DIR${NC}"
echo "   ${CYAN}vim .sync.yaml${NC}  # Edit configuration"
echo ""
echo "2. Install dependencies:"
echo "   ${CYAN}pip install pyyaml${NC}"
echo ""
echo "3. For Codespaces (100% automation):"
echo "   - Set ${CYAN}auto_start_server: true${NC} in .sync.yaml"
echo "   - Commit and push devcontainer files"
echo "   - Open in Codespaces"
echo ""
echo "4. For local development:"
echo "   - Set ${CYAN}auto_start_server: false${NC} in .sync.yaml"
echo "   - Run: ${CYAN}python mini_sync.py --watch${NC}"
echo ""
echo "5. Control commands:"
echo "   ${CYAN}bash sync-control.sh status${NC}   # Check status"
echo "   ${CYAN}bash sync-control.sh logs${NC}     # View logs"
echo "   ${CYAN}bash sync-control.sh restart${NC}  # Restart"
echo ""

print_header "📖 Documentation"
echo "   - Quick start: ${CYAN}MINI-VERSION-README.md${NC}"
echo "   - Codespaces: ${CYAN}CODESPACES-SETUP.md${NC}"
echo "   - AI setup: ${CYAN}AI-SETUP-INSTRUCTIONS.md${NC}"
echo ""

print_success "Ready to use!"
