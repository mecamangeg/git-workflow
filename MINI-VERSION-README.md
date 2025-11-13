# Mini Git Workflow - Claude Code Branch Sync

A **simplified, project-based** version of the Git Workflow Guardian. Perfect for quick setup and single-project workflows.

## 🎯 What It Does

**Automates the cloud-first development workflow in 3 simple steps:**

```
1. Detect Claude branches on remote
2. Auto-sync (git pull) the branch
3. Run tests → Start dev server
```

**That's it!** Simple, focused, project-local.

---

## ⚡ Quick Start

### 1. Copy to your project

```bash
# Copy mini_sync.py to your project
cp mini_sync.py /path/to/your/project/

# Optional: Copy example config
cp .sync.yaml.example /path/to/your/project/.sync.yaml
```

### 2. Run it

```bash
cd /path/to/your/project

# One-time sync (check once and sync if Claude branch found)
python mini_sync.py

# Watch mode (continuously check every 30s)
python mini_sync.py --watch

# Custom interval (check every 10s)
python mini_sync.py --watch --interval 10
```

**Done!** Your Claude branches will auto-sync, tests will run, and you'll be ready to test.

---

## 🎬 Example Usage

### Scenario: Code in Claude Code on the web

```bash
# Terminal 1: Start watch mode in your project
cd ~/Projects/my-app
python mini_sync.py --watch

# Output:
# ℹ Mini Git Workflow - Claude Code Sync
# ℹ Project: my-app
# ℹ Watch mode enabled (checking every 30s)
# ℹ Press Ctrl+C to stop
#
# ℹ Checking for Claude branches...
# ✓ Found 1 Claude branch(es): claude/add-feature-session_XXX
#
# Syncing branch: claude/add-feature-session_XXX
# ℹ Checking out claude/add-feature-session_XXX...
# ✓ Successfully synced claude/add-feature-session_XXX
#
# Running tests...
# ℹ Command: npm test
# ✓ Tests passed ✅
#
# Starting dev server...
# ✓ Run this command in a new terminal:
# npm run dev
```

### Terminal 2: Start dev server (or it shows you the command)

```bash
npm run dev
# Server running at http://localhost:3000
```

### Browser: Test your changes

```
http://localhost:3000
```

**Total time:** ~40 seconds from code to testing!

---

## 📋 Features

### ✅ What's Included

| Feature | Description |
|---------|-------------|
| **Claude Branch Detection** | Auto-detects branches matching `claude/*` pattern |
| **Auto-Sync** | Git fetch + checkout + pull automatically |
| **Test Runner** | Runs tests before dev server (configurable) |
| **Project Type Detection** | Auto-detects Next.js, React, Django, Flask, etc. |
| **Dev Server Hints** | Shows command to start dev server |
| **Watch Mode** | Continuously poll for new branches |
| **Zero Config** | Works out-of-the-box with sensible defaults |
| **Project-Local** | No global installation, no daemons |

### ❌ What's NOT Included

(Use full version if you need these)

| Feature | Why Not? |
|---------|----------|
| Background daemon | Keep it simple - run manually |
| Multiple repositories | Project-based only |
| Notification UI | Console output is enough |
| Webhooks | Polling is simpler |
| Terminal opener | Already in terminal |
| PR creator | Use `gh pr create` manually |
| Database | No state persistence needed |

---

## ⚙️ Configuration

### Default Behavior (No Config Needed)

The script works without any configuration:
- Detects `claude/*` branches
- Runs tests if found
- Shows dev server command

### Optional: Custom Config

Create `.sync.yaml` in your project root:

```yaml
# Claude branch patterns
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'

# Enable/disable tests
run_tests: true
test_timeout: 300  # 5 minutes

# Enable/disable dev server hints
start_dev_server: true

# Custom commands (optional)
test_commands:
  next: "npm test -- --coverage"
  python: "pytest --verbose"

dev_commands:
  next: "npm run dev -- --turbo"
```

---

## 🔧 Requirements

**Minimal:**
- Python 3.8+
- Git
- PyYAML (`pip install pyyaml`)

**That's it!** No databases, no services, no complex setup.

---

## 📖 Commands

### Basic Usage

```bash
# One-time sync
python mini_sync.py

# Watch mode (check every 30s)
python mini_sync.py --watch

# Custom interval (check every 10s)
python mini_sync.py --watch --interval 10

# Just check current branch
python mini_sync.py --check
```

### Typical Workflow

```bash
# 1. Start watch mode before coding in Claude Code web
python mini_sync.py --watch

# 2. Code in Claude Code on the web
# (Claude creates branch, pushes commits)

# 3. Script auto-detects and syncs
# (Happens automatically in watch mode)

# 4. Start dev server in new terminal
npm run dev  # or whatever command it shows

# 5. Test in browser
open http://localhost:3000
```

---

## 🎓 How It Works

### One-Time Sync Mode

```
1. git fetch --all --prune
2. Detect branches matching claude/* pattern
3. If found:
   → git checkout -b <branch> origin/<branch>
   → Run tests
   → Show dev server command
```

### Watch Mode

```
Loop every N seconds:
  1. git fetch --all --prune
  2. Detect Claude branches
  3. If new branch found:
     → Checkout and sync
     → Run tests
     → Show dev server command
```

**Simple polling**, no webhooks, no daemon complexity.

---

## 💡 When to Use Mini vs Full Version

### Use Mini Version If:
✅ Single project workflow
✅ Want simplicity over features
✅ Don't need background daemon
✅ Okay with manual dev server start
✅ Don't need notification UI

### Use Full Version If:
❌ Multiple repositories
❌ Want background daemon
❌ Want notification UI
❌ Need automatic dev server start
❌ Want webhook support
❌ Need terminal/PR integration

---

## 🚀 Tips & Tricks

### Tip 1: Run in tmux/screen

```bash
# Start watch mode in background session
tmux new -s sync
python mini_sync.py --watch

# Detach: Ctrl+b, d
# Reattach: tmux attach -t sync
```

### Tip 2: Add to project scripts

```json
// package.json
{
  "scripts": {
    "sync": "python mini_sync.py",
    "sync:watch": "python mini_sync.py --watch"
  }
}
```

Then:
```bash
npm run sync:watch
```

### Tip 3: Add to .gitignore

```
# .gitignore
mini_sync.py
.sync.yaml
```

This keeps the sync script project-local and not committed.

---

## 🐛 Troubleshooting

### "Not a git repository"
**Solution:** Run in a git repository directory

### "No Claude branches found"
**Solution:** Make sure Claude Code has pushed a branch to remote

### "Tests failed"
**Solution:** Fix tests or set `run_tests: false` in `.sync.yaml`

### "Command not found"
**Solution:** Install dependencies: `pip install pyyaml`

---

## 📊 Comparison: Mini vs Full

| Feature | Mini | Full |
|---------|------|------|
| Lines of Code | ~350 | ~5,000 |
| Files | 1 script | 12 services |
| Setup Time | 1 minute | 10-15 minutes |
| Dependencies | PyYAML | PyYAML, asyncio, aiohttp, tkinter |
| Background Daemon | ❌ | ✅ |
| Multi-Repository | ❌ | ✅ |
| Notification UI | ❌ Console | ✅ Popup |
| Auto Dev Server | ❌ Shows cmd | ✅ Starts |
| Webhooks | ❌ | ✅ |
| Terminal Opener | ❌ | ✅ |
| PR Creator | ❌ | ✅ |
| Test Runner | ✅ Basic | ✅ Advanced |
| Claude Detection | ✅ | ✅ |
| Git Sync | ✅ | ✅ |

**Mini = 7% the complexity, 80% the value** (for single-project use)

---

## 📝 Example Output

```
$ python mini_sync.py --watch

Mini Git Workflow - Claude Code Sync
ℹ Project: my-nextjs-app
ℹ Watch mode enabled (checking every 30s)
ℹ Press Ctrl+C to stop

ℹ Checking for Claude branches...
✓ Found 1 Claude branch(es): claude/add-user-auth-session_ABC123

Syncing branch: claude/add-user-auth-session_ABC123
ℹ Checking out claude/add-user-auth-session_ABC123...
✓ Successfully synced claude/add-user-auth-session_ABC123

Running tests...
ℹ Command: npm test
✓ Tests passed ✅

Starting dev server...
✓ Run this command in a new terminal:
npm run dev

Or press Ctrl+C and run it manually
```

---

## 🎉 Summary

**Mini Git Workflow gives you 80% of the value with 7% of the complexity.**

Perfect for:
- Quick project setup
- Single-project workflows
- Developers who prefer simplicity
- Projects that don't need all the bells and whistles

**350 lines of Python** vs 5,000 lines of services = **Simplicity wins!** 🚀

---

## 📦 Files

- `mini_sync.py` - Main script (~350 lines)
- `.sync.yaml.example` - Example configuration
- `MINI-VERSION-README.md` - This file

**Total:** 3 files, ready to use!

---

## 🔗 Related

- **Full Version:** See main repository for full-featured daemon
- **Official Docs:** [Claude Code Documentation](https://support.claude.com/en/articles/12618689-claude-code-on-the-web)

---

**License:** Same as main project
**Author:** Same as main project
**Version:** 1.0 (Mini)
