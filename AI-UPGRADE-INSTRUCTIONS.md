# AI Instructions: Upgrading to Version 2 (Latest Mode)

**Target Audience:** AI assistants (Claude Code) helping users upgrade their automation to version 2.

**Version 2 Key Feature:** "Latest Mode" - handles random branch names from Claude Code web by automatically switching to the branch with the newest commit.

---

## 🎯 When to Upgrade

**User says any of these:**
- "Upgrade my automation"
- "Update to version 2"
- "My automation is stuck on old branches"
- "Claude creates new branches but my server doesn't update"
- "I want the latest mode feature"
- "Replace my automation script"

---

## 🔍 Pre-Upgrade Check

### Step 1: Detect Current Setup

**Check if user already has automation:**

```bash
# Look for mini_sync.py
ls -la mini_sync.py

# Check if it's running
ps aux | grep mini_sync

# Check current version
head -20 mini_sync.py | grep "Latest Mode\|branch_tracking_mode"
```

**If found:**
- ✅ Version 2 detected: "You already have version 2 with Latest Mode!"
- ❌ Version 1 detected: Proceed with upgrade

**If not found:**
- This is a fresh install, not an upgrade
- Use regular installation instructions instead

### Step 2: Check Configuration

```bash
# Check if .sync.yaml exists
ls -la .sync.yaml

# Look for branch_tracking_mode setting
grep "branch_tracking_mode" .sync.yaml
```

**If `branch_tracking_mode` exists:**
- Already version 2
- No upgrade needed

**If not exists:**
- Version 1 config
- Needs upgrade

---

## 🚀 Upgrade Process (Step by Step)

### Step 1: Backup Current Setup

```bash
# Backup old script
cp mini_sync.py mini_sync.py.backup.$(date +%Y%m%d)

# Backup config
cp .sync.yaml .sync.yaml.backup.$(date +%Y%m%d)

# Confirm backups
ls -la *.backup.*
```

Tell user: "✅ Backed up your current setup to .backup files"

### Step 2: Stop Running Automation

```bash
# Find running process
PID=$(ps aux | grep "[m]ini_sync.py" | awk '{print $2}')

if [ -n "$PID" ]; then
    # Stop it gracefully
    kill $PID
    sleep 2

    # Confirm stopped
    if ps -p $PID > /dev/null; then
        kill -9 $PID
    fi

    echo "✅ Stopped automation (PID: $PID)"
else
    echo "ℹ No running automation detected"
fi
```

### Step 3: Download/Copy Version 2 Files

**Option A: If user has git-workflow repo:**

```bash
# Copy from git-workflow repo
cp /path/to/git-workflow/mini_sync.py ./
cp /path/to/git-workflow/.sync.yaml.example ./.sync.yaml.new

echo "✅ Copied version 2 files"
```

**Option B: If using install script:**

```bash
# Re-run install script (overwrites)
bash /path/to/git-workflow/install-to-project.sh $(pwd)

echo "✅ Installed version 2"
```

**Option C: Manual copy (provide files to user)**

If AI has access to the files, write them directly:
1. Write new mini_sync.py
2. Create .sync.yaml.new as template

### Step 4: Merge Configurations

**Important:** Don't lose user's custom settings!

```bash
# Extract user's custom settings from old config
OLD_PATTERNS=$(grep -A5 "claude_branch_patterns:" .sync.yaml.backup.* | tail -n +2 | grep "^  -")
OLD_TEST_CMD=$(grep -A10 "test_commands:" .sync.yaml.backup.* | tail -n +2)
OLD_DEV_CMD=$(grep -A10 "dev_commands:" .sync.yaml.backup.* | tail -n +2)
AUTO_START=$(grep "auto_start_server:" .sync.yaml.backup.* | awk '{print $2}')
RUN_TESTS=$(grep "run_tests:" .sync.yaml.backup.* | awk '{print $2}')

# Create new config with merged settings
cat > .sync.yaml << EOF
# Mini Git Workflow - Project Configuration
# Upgraded to Version 2 with Latest Mode

# Claude branch patterns to detect
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'

# Branch Tracking Mode (NEW in v2!)
# - 'latest': Always switch to branch with newest commit (RECOMMENDED)
# - 'sticky': Stay on current branch only (v1 behavior)
branch_tracking_mode: 'latest'

# Minimum seconds between branch switches (prevents thrashing)
min_branch_switch_interval: 30

# Run tests automatically after sync
run_tests: ${RUN_TESTS:-true}

# Test timeout in seconds
test_timeout: 300

# Start dev server after tests pass
start_dev_server: true

# Auto-start dev server
auto_start_server: ${AUTO_START:-false}

# Custom test commands (your existing commands preserved)
${OLD_TEST_CMD}

# Custom dev server commands (your existing commands preserved)
${OLD_DEV_CMD}
EOF

echo "✅ Created new config with your custom settings"
```

**Manual merge approach (safer for AI):**

```bash
# Show user what needs to be merged
echo "Your old custom settings:"
echo "========================"
grep -A20 "test_commands:\|dev_commands:" .sync.yaml.backup.*

echo ""
echo "New v2 config template created as .sync.yaml.new"
echo "Please review and merge your custom settings:"
echo "1. Open .sync.yaml.new"
echo "2. Add your custom test/dev commands"
echo "3. Set auto_start_server (true for Codespaces)"
echo "4. Save as .sync.yaml"
```

### Step 5: Verify Upgrade

```bash
# Check new version
head -25 mini_sync.py | grep "Latest Mode"

# Should see:
# - Two tracking modes: 'sticky' (stay on one branch) or 'latest' (follow newest commits)

# Check config
grep "branch_tracking_mode" .sync.yaml

# Should see:
# branch_tracking_mode: 'latest'

echo "✅ Version 2 verified"
```

### Step 6: Test New Version

```bash
# Test one-time sync
python mini_sync.py

# Should show:
# ℹ Checking for Claude branches...
# (no errors)

echo "✅ Basic functionality works"
```

### Step 7: Restart Automation

```bash
# Start watch mode with v2
python mini_sync.py --watch --interval 20 &

# Or if using tmux (for Codespaces)
tmux new-session -d -s claude-sync "python mini_sync.py --watch --interval 20"

# Verify running
sleep 2
ps aux | grep mini_sync

echo "✅ Automation restarted with version 2"
```

---

## 📋 Complete Upgrade Script

**For AI to execute (all steps combined):**

```bash
#!/bin/bash
# Automated upgrade to version 2

echo "🔄 Upgrading to Claude Code Automation v2..."
echo ""

# 1. Backup
echo "📦 Backing up current setup..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
cp mini_sync.py mini_sync.py.backup.$BACKUP_DATE 2>/dev/null || echo "No old script found"
cp .sync.yaml .sync.yaml.backup.$BACKUP_DATE 2>/dev/null || echo "No old config found"

# 2. Stop old automation
echo "⏸️  Stopping old automation..."
pkill -f "python.*mini_sync.py" || echo "No running automation"
sleep 2

# 3. Install v2
echo "📥 Installing version 2..."
if [ -f "/path/to/git-workflow/install-to-project.sh" ]; then
    bash /path/to/git-workflow/install-to-project.sh $(pwd)
else
    echo "⚠️  Please manually copy version 2 files"
    exit 1
fi

# 4. Merge config (if backup exists)
if [ -f ".sync.yaml.backup.$BACKUP_DATE" ]; then
    echo "🔧 Merging your custom settings..."

    # Preserve auto_start_server setting
    AUTO_START=$(grep "auto_start_server:" .sync.yaml.backup.$BACKUP_DATE | awk '{print $2}')
    if [ -n "$AUTO_START" ]; then
        sed -i "s/auto_start_server: false/auto_start_server: $AUTO_START/" .sync.yaml
    fi

    echo "⚠️  Please review .sync.yaml for any custom commands"
fi

# 5. Verify
echo "✅ Verifying installation..."
if grep -q "branch_tracking_mode" .sync.yaml; then
    echo "✅ Version 2 config detected"
else
    echo "❌ Config upgrade failed"
    exit 1
fi

if grep -q "Latest Mode" mini_sync.py; then
    echo "✅ Version 2 script detected"
else
    echo "❌ Script upgrade failed"
    exit 1
fi

# 6. Restart
echo "🚀 Starting version 2..."
python mini_sync.py --watch --interval 20 &
sleep 2

if ps aux | grep -q "[m]ini_sync.py"; then
    echo "✅ Version 2 running!"
else
    echo "⚠️  Please start manually: python mini_sync.py --watch --interval 20"
fi

echo ""
echo "🎉 Upgrade complete!"
echo ""
echo "New features in v2:"
echo "  • Latest Mode: Auto-switches to branch with newest commit"
echo "  • Works with random branch names"
echo "  • Auto-stashing for safe branch switches"
echo "  • Configurable throttling"
echo ""
echo "Your config: .sync.yaml"
echo "Backups: *.backup.$BACKUP_DATE"
echo ""
echo "To use sticky mode (v1 behavior): set branch_tracking_mode: 'sticky' in .sync.yaml"
```

---

## 🎓 User Education

After upgrade, explain to user:

### What Changed

```
Version 1 → Version 2 Changes:

1. NEW: Branch Tracking Mode
   - 'latest' mode: Auto-switches to newest branch (DEFAULT)
   - 'sticky' mode: Original v1 behavior (stay on one branch)

2. NEW: Smart Branch Detection
   - Uses commit timestamps, not branch names
   - Works with random branch names from Claude Code web
   - Always serves latest code automatically

3. NEW: Safety Features
   - Auto-stashes local changes before switching
   - Throttling to prevent rapid switches
   - Better error handling

4. Preserved: All Your Settings
   - Custom test commands
   - Custom dev commands
   - Auto-start settings
   - Port configurations
```

### How to Use

```bash
# Start automation (same as before)
python mini_sync.py --watch --interval 20

# New behavior in latest mode:
# - Checks ALL Claude branches
# - Switches to newest automatically
# - Server always shows latest code

# To use old behavior:
# Edit .sync.yaml:
# branch_tracking_mode: 'sticky'
```

### Configuration Options

```yaml
# NEW options in .sync.yaml:

# Set tracking mode
branch_tracking_mode: 'latest'  # or 'sticky' for v1 behavior

# Throttle branch switches
min_branch_switch_interval: 30  # seconds (only for 'latest' mode)
```

---

## 🐛 Troubleshooting Upgrade Issues

### Issue 1: Upgrade fails with "file not found"

```bash
# Manual upgrade steps:
# 1. Download v2 files to temp location
wget https://github.com/.../mini_sync.py -O /tmp/mini_sync_v2.py
wget https://github.com/.../.sync.yaml.example -O /tmp/.sync.yaml.example

# 2. Copy to project
cp /tmp/mini_sync_v2.py ./mini_sync.py
cp /tmp/.sync.yaml.example ./.sync.yaml.new

# 3. Merge config manually
vim .sync.yaml.new  # Add your custom settings
mv .sync.yaml.new .sync.yaml
```

### Issue 2: "branch_tracking_mode not recognized"

**Cause:** Old version still running or config not loaded

```bash
# 1. Confirm v2 installed
grep "branch_tracking_mode" mini_sync.py

# Should find the option in default config

# 2. Restart automation
pkill -f mini_sync
python mini_sync.py --watch --interval 20
```

### Issue 3: "Lost my custom settings"

```bash
# 1. Find backup
ls -la .sync.yaml.backup.*

# 2. Restore custom commands
vim .sync.yaml.backup.20250113  # View old settings
vim .sync.yaml                  # Add to new config

# 3. Restart
pkill -f mini_sync
python mini_sync.py --watch --interval 20
```

### Issue 4: Automation not switching branches

```bash
# 1. Check mode
grep "branch_tracking_mode" .sync.yaml

# Should be: 'latest'

# 2. Check logs
tail -f /tmp/sync-output.log

# Look for: "Branch tracking mode: latest"

# 3. Test manually
python mini_sync.py

# Should show branch detection and timestamps
```

### Issue 5: Switches too frequently

```bash
# Increase throttling
vim .sync.yaml

# Change:
min_branch_switch_interval: 60  # Increase to 60 seconds

# Restart
pkill -f mini_sync
python mini_sync.py --watch --interval 30
```

---

## ✅ Verification Checklist

After upgrade, verify:

```bash
# 1. Version 2 installed
grep "Latest Mode" mini_sync.py
# ✅ Should find "Latest Mode" in description

# 2. Config has new options
grep "branch_tracking_mode" .sync.yaml
# ✅ Should show: branch_tracking_mode: 'latest'

# 3. Automation running
ps aux | grep mini_sync
# ✅ Should show running process

# 4. Latest mode active
tail -20 /tmp/sync-output.log | grep "tracking mode"
# ✅ Should show: "Branch tracking mode: latest"

# 5. Backups exist
ls -la *.backup.*
# ✅ Should show backup files

# 6. Basic functionality works
python mini_sync.py --check
# ✅ Should show current branch, no errors
```

**If all checks pass:** "✅ Upgrade successful! Version 2 is running with Latest Mode."

---

## 📖 Quick Reference for AI

### Detect Version

```bash
# Version 1: No branch_tracking_mode
# Version 2: Has branch_tracking_mode

# Check script:
grep "branch_tracking_mode" mini_sync.py

# Check config:
grep "branch_tracking_mode" .sync.yaml
```

### Upgrade Command (One-liner)

```bash
# If install script available:
bash /path/to/git-workflow/install-to-project.sh $(pwd)

# Manual:
cp /path/to/git-workflow/mini_sync.py ./ && \
cp /path/to/git-workflow/.sync.yaml.example ./.sync.yaml.template && \
echo "Merge .sync.yaml.template with your .sync.yaml, then restart"
```

### Rollback (If needed)

```bash
# Restore backups
LATEST_BACKUP=$(ls -t *.backup.* | head -1)
cp mini_sync.py.backup.* mini_sync.py
cp .sync.yaml.backup.* .sync.yaml

# Restart
pkill -f mini_sync
python mini_sync.py --watch --interval 30
```

---

## 🎯 Success Criteria

Upgrade is successful when:

1. ✅ Version 2 script installed (has Latest Mode)
2. ✅ Config has `branch_tracking_mode` option
3. ✅ Custom settings preserved (test/dev commands)
4. ✅ Automation running with latest mode
5. ✅ User knows how to switch modes
6. ✅ Backups created for safety

---

## 💬 Sample AI Interaction

```
User: "Upgrade my automation to version 2"

AI: "I'll upgrade your Claude Code automation to version 2 with Latest Mode.
This will enable automatic switching to the newest branch, perfect for handling
random branch names from Claude Code web.

First, let me backup your current setup..."

[Executes backup]

AI: "✅ Backed up to .sync.yaml.backup.20250113

Now stopping current automation..."

[Stops old version]

AI: "✅ Stopped

Installing version 2..."

[Installs v2]

AI: "✅ Installed

Merging your custom settings..."

[Merges config]

AI: "✅ Config ready

Starting version 2 with Latest Mode..."

[Starts automation]

AI: "🎉 Upgrade complete!

Your automation now uses 'Latest Mode' which:
• Monitors ALL Claude branches
• Automatically switches to newest commit
• Works with random branch names
• Always serves latest code

Your config: .sync.yaml
Backups: .sync.yaml.backup.20250113

The automation is now running. Try making multiple requests to Claude Code web
and watch it automatically switch to the newest branches!"

User: "What if I want the old behavior?"

AI: "You can switch to 'sticky mode' which preserves the v1 behavior:

1. Edit .sync.yaml
2. Change: branch_tracking_mode: 'sticky'
3. Restart: pkill -f mini_sync && python mini_sync.py --watch --interval 20

In sticky mode, automation stays on current branch (original v1 behavior)."
```

---

## 🎉 Summary for AI

**When user asks to upgrade:**

1. ✅ Backup current setup
2. ✅ Stop running automation
3. ✅ Install version 2 files
4. ✅ Merge user's custom config
5. ✅ Verify installation
6. ✅ Restart with latest mode
7. ✅ Educate user on new features

**Key points to communicate:**
- Latest mode is now default (handles random branches)
- Sticky mode available (v1 behavior)
- Custom settings preserved
- Backups created for safety
- Can rollback if needed

**Version 2 = Latest Mode = Random branch name support ✅**
