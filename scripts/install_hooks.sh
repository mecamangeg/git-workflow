#!/bin/bash
# Git Workflow Guardian - Hook Installation Script (Linux/macOS)

set -e

REPO_PATH="${1:-.}"
FORCE="${2:-false}"

echo "======================================"
echo " Git Workflow Guardian - Hook Installer"
echo "======================================"

# Resolve repo path
REPO_PATH=$(cd "$REPO_PATH" && pwd)

# Check if git repo
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "ERROR: Not a git repository: $REPO_PATH"
    exit 1
fi

echo ""
echo "[1/4] Validating repository..."
echo "Repository: $REPO_PATH"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SOURCE="$(dirname "$SCRIPT_DIR")/hooks"

# Check if hooks already installed
HOOKS_DIR="$REPO_PATH/.git/hooks"
if [ -f "$HOOKS_DIR/pre-commit" ] && [ "$FORCE" != "true" ]; then
    read -p "Hooks already installed. Overwrite? (y/n) " response
    if [ "$response" != "y" ]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

echo ""
echo "[2/4] Installing hooks..."

# Copy hook scripts
HOOKS=("pre-commit.sh" "pre-push.sh" "post-checkout.sh" "post-merge.sh" "notifier.py")

for hook in "${HOOKS[@]}"; do
    source="$HOOKS_SOURCE/$hook"
    dest="$HOOKS_DIR/${hook%.sh}"

    if [ -f "$source" ]; then
        cp "$source" "$dest"
        echo "  ✓ Installed: $hook"

        # Make executable
        chmod +x "$dest"
    else
        echo "  ✗ Missing: $hook"
    fi
done

echo ""
echo "[3/4] Configuring permissions..."
echo "  ✓ Permissions configured"

echo ""
echo "[4/4] Verifying installation..."

# Count installed hooks
installed_count=$(ls -1 "$HOOKS_DIR"/{pre-commit,pre-push,post-checkout,post-merge} 2>/dev/null | wc -l)
if [ "$installed_count" -ge 3 ]; then
    echo "  ✓ Hooks installed successfully ($installed_count hooks)"
else
    echo "  ⚠ Some hooks may be missing"
fi

echo ""
echo "======================================"
echo " Installation Complete!"
echo "======================================"

echo ""
echo "Workflow rules now active:"
echo "  ⛔ BLOCK: Commits to main"
echo "  ⛔ BLOCK: Pushes to main"
echo "  💡 SUGGEST: Pull main after checkout"
echo "  💡 SUGGEST: Delete merged branches"

echo ""
echo "To bypass hooks (emergency only): git commit --no-verify"
