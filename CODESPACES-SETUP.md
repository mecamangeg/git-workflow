# GitHub Codespaces - 100% Automation Setup

**Perfect balance: Fully automated + Visible + Easy to control**

## 🎯 What This Setup Does

When you open your project in GitHub Codespaces:

1. **Auto-installs** dependencies (pyyaml)
2. **Auto-starts** sync watcher in visible tmux session
3. **Auto-detects** Claude branches every 10 seconds
4. **Auto-syncs** branches (git fetch + checkout + pull)
5. **Auto-runs** tests
6. **Auto-starts** dev server with preview URL
7. **Shows** everything in real-time logs

**And you can:**
- ✅ See logs in real-time (attach to tmux)
- ✅ Restart easily (Ctrl+C or control script)
- ✅ Modify script and restart instantly
- ✅ Control everything with simple commands

**Smart Features:**
- 🎯 **Single port per project type** - Next.js always on 3000, Django on 8000, etc.
- 🧹 **Auto-cleanup** - Kills old servers on same port (no more port conflicts!)
- 🧠 **Smart detection** - Skips server for libraries/CLI tools (only starts when needed)

---

## ⚡ Quick Setup (5 minutes)

### 1. Copy Files to Your Project

```bash
# Core files
cp mini_sync.py /path/to/your/project/
cp .sync.yaml.example /path/to/your/project/.sync.yaml

# Codespaces automation
mkdir -p /path/to/your/project/.devcontainer
cp .devcontainer/devcontainer.json /path/to/your/project/.devcontainer/
cp .devcontainer/start-sync.sh /path/to/your/project/.devcontainer/

# Control script
cp sync-control.sh /path/to/your/project/
```

### 2. Customize Config (Optional)

Edit `.sync.yaml` if needed:

```yaml
# Auto-start dev server in Codespaces
auto_start_server: true  # Change to true for Codespaces

# Adjust polling interval if needed
# (configured in start-sync.sh)
```

### 3. Commit and Push

```bash
git add .devcontainer/ mini_sync.py .sync.yaml sync-control.sh
git commit -m "feat: add Codespaces auto-sync setup"
git push
```

### 4. Open in Codespaces

```bash
# From GitHub UI:
# Code → Codespaces → Create codespace on main
```

**Done!** Sync watcher starts automatically on launch.

---

## 🚀 Your New Workflow

### Before (Manual - 9 steps, 3-5 minutes)

```
1. Code in Claude Code web
2. Manually open terminal in Codespaces
3. Manually cd to project
4. Manually git fetch
5. Manually git checkout branch
6. Manually git pull
7. Manually run tests
8. Manually start dev server
9. Test in browser
```

### After (Automated - 2 steps, 20 seconds)

```
1. Code in Claude Code web
   └─→ [AUTOMATIC] Branch detected (10s)
   └─→ [AUTOMATIC] Synced
   └─→ [AUTOMATIC] Tests run
   └─→ [AUTOMATIC] Dev server started
   └─→ [AUTOMATIC] Preview URL shown

2. Click preview URL → Test
```

**Time saved: 80%+**

---

## 📊 How It Works

### On Codespaces Startup

```
1. Codespaces opens
2. .devcontainer/devcontainer.json runs:
   └─→ postCreateCommand: pip install pyyaml
   └─→ postStartCommand: bash .devcontainer/start-sync.sh

3. start-sync.sh creates tmux session:
   └─→ tmux new-session -d -s claude-sync
   └─→ Runs: python mini_sync.py --watch --interval 10

4. mini_sync.py starts watching:
   └─→ Polls remote every 10 seconds
   └─→ Detects claude/* branches
   └─→ Auto-syncs when found
   └─→ Runs tests
   └─→ Starts dev server
   └─→ Shows preview URL
```

### When Claude Creates a Branch

```
Claude Code web → pushes branch → GitHub
                                     ↓
                    (10s polling interval)
                                     ↓
              mini_sync.py detects new branch
                                     ↓
                    git fetch + checkout + pull
                                     ↓
                            Run tests (npm test)
                                     ↓
                    Start dev server (npm run dev)
                                     ↓
             Show preview URL in terminal logs
                                     ↓
                      You: Click URL → Test!
```

---

## 🎯 Smart Port Management

### Single Consistent Port Per Project Type

The system ensures **only one server runs per project type** using consistent ports:

| Project Type | Port | Example URL |
|-------------|------|-------------|
| Next.js | 3000 | `https://codespace-3000.app.github.dev` |
| React | 3000 | `https://codespace-3000.app.github.dev` |
| Vue | 8080 | `https://codespace-8080.app.github.dev` |
| Django | 8000 | `https://codespace-8000.app.github.dev` |
| Flask | 5000 | `https://codespace-5000.app.github.dev` |

**What this means:**
- ✅ **No confusion** - Always the same preview URL for your project type
- ✅ **No conflicts** - Old servers automatically killed before starting new ones
- ✅ **Bookmark-friendly** - Save the URL once, use forever (just refresh)

### Example Scenario

**Problem (before):**
```
1. You sync branch A → Next.js starts on port 3000
2. You sync branch B → Next.js starts on port 3001 (conflict!)
3. Which URL to test? 🤔 Port 3000 or 3001?
```

**Solution (now):**
```
1. You sync branch A → Next.js starts on port 3000
2. You sync branch B → Old server killed, new one starts on port 3000
3. Same URL! Just refresh your browser ✅
```

### Auto-Cleanup in Action

When starting a new dev server:
```
ℹ Killing existing process on port 3000 (PID: 1234)...
✓ Cleared port 3000
ℹ Starting dev server: npm run dev
✓ Dev server started (PID: 5678)
🚀 Preview URL: https://mycodespace-3000.app.github.dev
```

---

## 🧠 Smart Server Detection

### Only Starts Servers When Needed

The system intelligently detects if your project needs a dev server:

**✅ Projects that GET a server:**
- Next.js, React, Vue apps (web frameworks)
- Django, Flask apps (web backends)
- Node.js projects with `dev` or `start` scripts
- Python projects with FastAPI/Flask/Django imports

**❌ Projects that DON'T get a server:**
- Node.js libraries (no dev/start scripts in package.json)
- Python libraries (setup.py/pyproject.toml without web frameworks)
- CLI tools
- Documentation projects

### Example: Node.js Library

```json
{
  "name": "my-utility-library",
  "scripts": {
    "test": "jest",
    "build": "tsc"
  }
}
```

**Result:**
```
ℹ Project type 'node' doesn't need a dev server (library/CLI tool)
✓ Sync complete, no server started
```

### Example: Next.js App

```json
{
  "name": "my-nextjs-app",
  "scripts": {
    "dev": "next dev",
    "build": "next build"
  }
}
```

**Result:**
```
ℹ Starting dev server: npm run dev
✓ Dev server started (PID: 1234)
🚀 Preview URL: https://mycodespace-3000.app.github.dev
```

---

## 🎮 Control Commands

All automation is controlled via `sync-control.sh`:

### Check Status

```bash
bash sync-control.sh status
```

Output:
```
Claude Code Workflow - Status
✓ Auto-sync is running

📊 Session Info:
claude-sync: 1 windows (created Thu Jan 15 10:30:00 2025)

🔗 Commands:
   - View logs:  bash sync-control.sh logs
   - Stop:       bash sync-control.sh stop
   - Restart:    bash sync-control.sh restart
```

### View Logs (Real-time)

```bash
bash sync-control.sh logs
```

This **attaches** you to the tmux session where you can see:
- Branch detection messages
- Git sync operations
- Test results
- Dev server startup
- Preview URLs

**To detach (leave running):** Press `Ctrl+b`, then `d`

### Stop Auto-Sync

```bash
bash sync-control.sh stop
```

### Restart Auto-Sync

```bash
bash sync-control.sh restart
```

### View Dev Server Logs

```bash
bash sync-control.sh dev-logs
```

Shows dev server output from `.dev-server.log`

### Get Help

```bash
bash sync-control.sh help
```

---

## 🎨 Visibility Features

### Feature 1: Visible Terminal

The sync watcher runs in a **tmux session**, not hidden in background:

```bash
# Attach to see what's happening
tmux attach -t claude-sync

# Or use control script
bash sync-control.sh logs
```

### Feature 2: Real-time Logs

You see everything as it happens:

```
ℹ Checking for Claude branches...
✓ Found 1 Claude branch(es): claude/add-feature-session_ABC
✓ Successfully synced claude/add-feature-session_ABC
✓ Tests passed ✅
✓ Dev server started (PID: 1234)

🚀 Preview URL:
https://mycodespace-3000.app.github.dev
```

### Feature 3: Easy Restart

**Method 1: Via control script**
```bash
bash sync-control.sh restart
```

**Method 2: From attached tmux**
```bash
# Attach to session
tmux attach -t claude-sync

# Press Ctrl+C to stop
# Then re-run
python mini_sync.py --watch --interval 10
```

### Feature 4: Easy Modification

```bash
# 1. Edit the script
vim mini_sync.py

# 2. Restart via control script
bash sync-control.sh restart

# Or attach and Ctrl+C, then re-run
tmux attach -t claude-sync
# Ctrl+C
# python mini_sync.py --watch --interval 10
```

---

## 🔧 Configuration

### Adjust Polling Interval

Edit `.devcontainer/start-sync.sh`:

```bash
# Default: check every 10 seconds
python mini_sync.py --watch --interval 10

# Faster: check every 5 seconds
python mini_sync.py --watch --interval 5

# Slower: check every 30 seconds (save CPU)
python mini_sync.py --watch --interval 30
```

### Customize Branch Patterns

Edit `.sync.yaml`:

```yaml
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'
  - '^assistant/.*'  # Add more patterns
```

### Disable Auto-Start (Manual Mode)

Edit `.sync.yaml`:

```yaml
auto_start_server: false
```

Then mini_sync.py will just show the command instead of starting the server.

### Customize Ports

Edit `.devcontainer/devcontainer.json`:

```json
{
  "forwardPorts": [3000, 5000, 8000, 8080],
  "portsAttributes": {
    "3000": {
      "label": "Next.js",
      "onAutoForward": "notify"
    },
    "8000": {
      "label": "Django",
      "onAutoForward": "notify"
    }
  }
}
```

---

## 🐛 Troubleshooting

### Sync Not Starting on Launch

**Check:** Is `.devcontainer/devcontainer.json` in your repo?

```bash
ls .devcontainer/devcontainer.json
```

**Fix:** Commit and push devcontainer files, then rebuild Codespaces.

### Can't See Logs

**Check:** Is tmux session running?

```bash
tmux list-sessions
```

**Fix:** Start manually:

```bash
bash sync-control.sh start
```

### Dev Server Not Starting

**Check:** Is `auto_start_server: true` in `.sync.yaml`?

**Check:** Are ports forwarded in devcontainer.json?

**Fix:** Edit config and restart:

```bash
bash sync-control.sh restart
```

### Preview URL Not Working

**Check:** Is the port correct? Check with:

```bash
# See what ports your dev server uses
cat .dev-server.log
```

**Fix:** Update port in devcontainer.json and reload Codespaces.

### Sync Detection Too Slow/Fast

**Adjust interval** in `.devcontainer/start-sync.sh`:

```bash
# Faster (5s)
python mini_sync.py --watch --interval 5

# Slower (30s)
python mini_sync.py --watch --interval 30
```

Then restart:

```bash
bash sync-control.sh restart
```

---

## 📖 Usage Examples

### Example 1: Normal Development

```bash
# 1. Open Codespaces (auto-starts sync)
# 2. Code in Claude Code web
# 3. Wait ~10 seconds
# 4. See in terminal:
#    ✓ Branch synced
#    ✓ Tests passed
#    ✓ Dev server started
#    🚀 Preview URL: https://...
# 5. Click URL → test
# 6. Merge or iterate
```

### Example 2: Checking Logs

```bash
# View sync activity
bash sync-control.sh logs

# See output:
# ℹ Checking for Claude branches...
# ✓ Found claude/new-feature
# ✓ Synced successfully
# ✓ Tests passed
#
# Press Ctrl+b, d to detach
```

### Example 3: Manual Restart

```bash
# Stop sync
bash sync-control.sh stop

# Make changes to mini_sync.py
vim mini_sync.py

# Start again
bash sync-control.sh start

# Or restart in one command
bash sync-control.sh restart
```

### Example 4: Debugging Dev Server

```bash
# Check if dev server is running
bash sync-control.sh status

# View dev server logs
bash sync-control.sh dev-logs

# Restart if needed
bash sync-control.sh restart
```

---

## 💡 Pro Tips

### Tip 1: Bookmark Preview URL

Your preview URL format:
```
https://[codespace-name]-[port].app.github.dev
```

Save it and just refresh when new branches sync!

### Tip 2: Use Multiple Terminals

```
Terminal 1: tmux attach -t claude-sync  (watch sync activity)
Terminal 2: bash sync-control.sh dev-logs (watch dev server)
Terminal 3: <free for other commands>
```

### Tip 3: Keep Codespaces Alive

Codespaces timeout after inactivity. To prevent:

```bash
# Add to your shell profile
while true; do echo "keepalive" > /dev/null; sleep 300; done &
```

### Tip 4: Quick Status Check

Add alias to your shell:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias sync-status='bash sync-control.sh status'
alias sync-logs='bash sync-control.sh logs'
alias sync-restart='bash sync-control.sh restart'
```

Then just:
```bash
sync-status
sync-logs
sync-restart
```

### Tip 5: Notification When Ready

Add to `mini_sync.py` in the dev server start section:

```python
# Terminal bell to notify
import os
os.system('echo -e "\\a"')
```

Your terminal will beep when dev server is ready!

---

## 🎉 Summary

**This setup gives you:**

✅ **100% automation** - Everything happens automatically
✅ **Visible terminal** - See what's happening in real-time
✅ **Easy restart** - Ctrl+C or one command
✅ **Easy modify** - Edit script, restart
✅ **Full control** - Simple control commands
✅ **Background friendly** - Runs in tmux, detachable
✅ **No manual steps** - Just code and test

**Your workflow becomes:**
```
1. Code in Claude Code web
2. Click preview URL
3. Test
4. Merge

That's it! 🚀
```

**Setup time:** 5 minutes
**Time saved per iteration:** 80%+
**Automation level:** 100%
**Control level:** 100%

---

## 📋 File Checklist

Make sure you have these files:

```
your-project/
├── mini_sync.py                    ✓ Core sync script
├── .sync.yaml                      ✓ Configuration
├── sync-control.sh                 ✓ Control commands
├── .devcontainer/
│   ├── devcontainer.json          ✓ Codespaces config
│   └── start-sync.sh              ✓ Auto-start script
└── .dev-server.log                 (auto-created)
```

---

## 🚀 Next Steps

1. **Copy files** to your project
2. **Customize config** if needed
3. **Commit and push**
4. **Open in Codespaces**
5. **Code in Claude Code web**
6. **Watch it work!**

---

**Questions?** Check:
- `bash sync-control.sh help` - Quick command reference
- `MINI-VERSION-README.md` - Detailed mini_sync.py docs
- `CODESPACES-WORKFLOW-BRAINSTORM.md` - Design decisions

**Enjoy 100% automated, fully visible, easily controllable cloud-first development!** 🎉
