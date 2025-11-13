# Instructions for AI: Setting Up Claude Code Workflow Automation

**Target Audience:** AI assistants (Claude Code) helping users set up automated Git workflow for cloud-first development.

---

## 🎯 What This Automation Does

This system automates the workflow between Claude Code on the web and local/Codespaces development:

1. **Auto-detects** branches created by Claude Code web (matching `claude/*` pattern)
2. **Auto-syncs** those branches locally (git fetch + checkout + pull)
3. **Auto-runs** tests to verify the changes
4. **Auto-starts** dev servers (when needed) with consistent ports
5. **Shows** preview URLs (in Codespaces) for immediate testing

**Key benefit:** Eliminates manual git commands, reduces context switching, speeds up dev by 80%+.

---

## 📋 Setup Steps for AI Assistant

When a user asks you to set up this automation, follow these steps:

### Step 1: Copy Core Files

Copy these files from the git-workflow repository to the user's project:

```bash
# Core sync script
cp /path/to/git-workflow/mini_sync.py ./

# Example configuration
cp /path/to/git-workflow/.sync.yaml.example ./.sync.yaml

# Control script (optional but recommended)
cp /path/to/git-workflow/sync-control.sh ./
chmod +x sync-control.sh
```

### Step 2: For GitHub Codespaces (Recommended)

If the user is using GitHub Codespaces, also copy:

```bash
# Create devcontainer directory
mkdir -p .devcontainer

# Copy Codespaces configuration
cp /path/to/git-workflow/.devcontainer/devcontainer.json ./.devcontainer/
cp /path/to/git-workflow/.devcontainer/start-sync.sh ./.devcontainer/
chmod +x .devcontainer/start-sync.sh
```

### Step 3: Install Dependencies

```bash
pip install pyyaml
```

Or add to requirements.txt:
```
pyyaml>=6.0
```

### Step 4: Configure for the Project

Edit `.sync.yaml` based on project type:

**For Codespaces (100% automation):**
```yaml
# Enable auto-start for Codespaces
auto_start_server: true

# Keep these enabled
run_tests: true
start_dev_server: true

# Adjust polling interval in .devcontainer/start-sync.sh if needed
```

**For local development (manual server start):**
```yaml
# Manual mode - shows command instead of auto-starting
auto_start_server: false

run_tests: true
start_dev_server: true
```

### Step 5: Customize (Optional)

Adjust configuration based on project needs:

**Custom branch patterns:**
```yaml
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'
  - '^assistant/.*'
```

**Custom test commands:**
```yaml
test_commands:
  next: "npm test -- --coverage"
  python: "pytest --verbose"
```

**Custom dev commands:**
```yaml
dev_commands:
  next: "npm run dev -- --turbo"
  django: "python manage.py runserver 0.0.0.0:8000"
```

### Step 6: Test the Setup

**For Codespaces:**
```bash
# Already runs automatically on startup
# Check status:
bash sync-control.sh status

# View logs:
bash sync-control.sh logs
```

**For local development:**
```bash
# Test one-time sync
python mini_sync.py

# Start watch mode
python mini_sync.py --watch
```

---

## 🔧 Configuration Reference

### Project Detection

The system automatically detects project types:

| File/Indicator | Detected As | Default Port |
|----------------|-------------|--------------|
| `package.json` with Next.js | `next` | 3000 |
| `package.json` with React | `react` | 3000 |
| `package.json` with Vue | `vue` | 8080 |
| `manage.py` | `django` | 8000 |
| `app.py` or `wsgi.py` | `flask` | 5000 |
| Generic Node.js | `node` | 3000 |
| Generic Python | `python` | 8000 |

### Server Detection Logic

**Servers are started for:**
- ✅ Next.js, React, Vue, Django, Flask projects (always)
- ✅ Node.js projects with `dev` or `start` scripts
- ✅ Python projects with web framework imports

**Servers are skipped for:**
- ❌ Node.js libraries (no dev/start scripts)
- ❌ Python libraries (no web framework detected)
- ❌ CLI tools
- ❌ Documentation projects

### Port Management

**Single port per project type:**
- Next.js/React → **Always port 3000**
- Vue → **Always port 8080**
- Django → **Always port 8000**
- Flask → **Always port 5000**

**Before starting a new server:**
1. Check if any process is using the target port
2. Kill existing process (SIGTERM → SIGKILL)
3. Start new server on the same port
4. **Result:** Consistent preview URL, no conflicts

---

## 💡 Usage Patterns

### Pattern 1: Codespaces (100% Automation)

**User workflow:**
1. Opens project in GitHub Codespaces
2. Automation starts automatically (via devcontainer.json)
3. User codes in Claude Code web
4. Branch auto-syncs within 10 seconds
5. Tests run, server starts, preview URL shown
6. User clicks URL to test

**AI assistance needed:**
- Help with initial setup (copy files)
- Customize config if needed
- Debug if issues occur

**Commands to teach user:**
```bash
bash sync-control.sh status    # Check if running
bash sync-control.sh logs      # View activity
bash sync-control.sh restart   # Restart if needed
```

### Pattern 2: Local Development (Manual)

**User workflow:**
1. Runs `python mini_sync.py --watch` in terminal
2. Codes in Claude Code web
3. Branch auto-syncs within 30 seconds (default)
4. Tests run, server command shown
5. User manually starts server in another terminal
6. User tests at localhost:PORT

**AI assistance needed:**
- Help start watch mode
- Explain manual server start
- Adjust polling interval if needed

**Commands to teach user:**
```bash
python mini_sync.py --watch              # Start watching
python mini_sync.py --watch --interval 10  # Faster polling
```

### Pattern 3: One-Time Sync

**User workflow:**
1. User says "sync the latest Claude branch"
2. AI runs: `python mini_sync.py`
3. Latest branch synced, tests run
4. User manually starts server if needed

**AI assistance:**
```bash
python mini_sync.py  # Sync latest Claude branch once
```

---

## 🐛 Common Issues and Solutions

### Issue 1: "No Claude branches found"

**Cause:** Claude Code web hasn't pushed a branch yet, or branch pattern doesn't match.

**Solution:**
```bash
# Check remote branches
git fetch --all
git branch -r | grep claude

# If branches exist but don't match, update pattern in .sync.yaml:
claude_branch_patterns:
  - '^claude/.*'
  - '^ai/.*'  # Add alternative patterns
```

### Issue 2: "Port already in use"

**Cause:** Another process is using the port, and kill failed (insufficient permissions).

**Solution:**
```bash
# Manually kill process on port (example: 3000)
lsof -ti :3000 | xargs kill -9

# Or restart automation
bash sync-control.sh restart
```

### Issue 3: "Tests failed"

**Cause:** Actual test failures in the code, or test command incorrect.

**Solution:**
```bash
# Check test output
cat .dev-server.log

# Fix tests or temporarily disable
# Edit .sync.yaml:
run_tests: false  # Disable tests temporarily
```

### Issue 4: "Dev server not starting"

**Cause:** Project is a library (no server needed), or command is wrong.

**Solution:**
```bash
# Check if project needs server
cat package.json  # Look for "dev" or "start" script

# If it's a library, this is expected:
# ℹ Project type 'node' doesn't need a dev server (library/CLI tool)

# If it should have a server, check/customize command:
# Edit .sync.yaml:
dev_commands:
  next: "npm run dev"  # Or whatever your command is
```

### Issue 5: "Automation not starting in Codespaces"

**Cause:** devcontainer.json not committed, or Codespaces not rebuilt.

**Solution:**
```bash
# Ensure files are committed
git add .devcontainer/ mini_sync.py .sync.yaml sync-control.sh
git commit -m "feat: add automation"
git push

# Rebuild Codespaces
# From Codespaces UI: Command Palette → "Rebuild Container"
```

---

## 📝 AI Assistant Guidelines

### When User Says: "Set up automation for Claude Code workflow"

**Do this:**
1. Confirm they're using Claude Code on the web
2. Ask: "Are you using GitHub Codespaces or local development?"
3. Copy appropriate files based on their answer
4. Configure .sync.yaml based on their environment
5. Test the setup
6. Explain the control commands
7. Create a .gitignore entry if they want (optional)

**Example interaction:**
```
User: "Set up automation for Claude Code workflow"

AI: "I'll set up the automation for cloud-first development with Claude Code.
Are you using GitHub Codespaces or local development?"

User: "Codespaces"

AI: "Great! I'll set up 100% automation for Codespaces. This will:
- Auto-start sync watcher on Codespaces launch
- Auto-detect Claude branches every 10 seconds
- Auto-sync, test, and start dev server
- Show preview URLs automatically

Setting up now..."

[Copy files, configure, test]

AI: "✅ Setup complete! Your automation will start automatically when you
open Codespaces. Here are the control commands:

- Check status: bash sync-control.sh status
- View logs: bash sync-control.sh logs
- Restart: bash sync-control.sh restart

Next steps:
1. Commit these files: git add . && git commit -m 'feat: add automation'
2. Push: git push
3. Open in Codespaces - automation starts automatically
4. Code in Claude Code web - branches sync automatically
5. Click preview URL to test"
```

### When User Says: "This is too slow, make it faster"

**Options to offer:**
1. Reduce polling interval: `--interval 5` (check every 5 seconds)
2. Switch to webhook mode (if they want to implement Phase 5)
3. Check network latency between Codespaces and GitHub

**Example:**
```bash
# Edit .devcontainer/start-sync.sh
# Change from:
python mini_sync.py --watch --interval 10

# To:
python mini_sync.py --watch --interval 5  # Check every 5 seconds
```

### When User Says: "I want to customize branch patterns"

**Do this:**
```yaml
# Edit .sync.yaml
claude_branch_patterns:
  - '^claude/.*'      # Default: claude/*
  - '^ai/.*'          # Add: ai/*
  - '^feature/.*'     # Add: feature/*
  - '^username-.*'    # Add: username-*
```

### When User Says: "Can it work with multiple projects?"

**Answer:**
"The mini version is project-based - one script per project. Each project needs:
- Its own mini_sync.py
- Its own .sync.yaml
- Its own Codespaces config (if using)

This keeps things simple. If you need to monitor multiple repositories from
one place, you'd need the full version (Phase 0 implementation) with daemon
support and repository management."

### When User Says: "How do I debug issues?"

**Guide them:**
```bash
# 1. Check if sync is running
bash sync-control.sh status

# 2. View live logs
bash sync-control.sh logs
# Press Ctrl+b, then d to detach

# 3. Check dev server logs
bash sync-control.sh dev-logs
# Or: cat .dev-server.log

# 4. Test sync manually
python mini_sync.py --check  # Check current branch
python mini_sync.py          # One-time sync

# 5. Check git status
git status
git branch -r | grep claude  # See remote Claude branches
```

---

## 🎯 Quick Reference for AI

**Files to copy:**
- ✅ Always: `mini_sync.py`, `.sync.yaml.example` → `.sync.yaml`
- ✅ Recommended: `sync-control.sh`
- ✅ For Codespaces: `.devcontainer/devcontainer.json`, `.devcontainer/start-sync.sh`

**Configuration:**
- Codespaces: `auto_start_server: true`
- Local: `auto_start_server: false`

**Commands to teach:**
- Start watch: `python mini_sync.py --watch`
- Control: `bash sync-control.sh status|logs|restart`
- One-time: `python mini_sync.py`

**Common customizations:**
- Branch patterns: Edit `claude_branch_patterns` in `.sync.yaml`
- Polling interval: Change `--interval 10` in start-sync.sh
- Test/dev commands: Edit `test_commands` and `dev_commands` in `.sync.yaml`

---

## 📚 Additional Resources

Point users to:
- `CODESPACES-SETUP.md` - Complete Codespaces setup guide
- `MINI-VERSION-README.md` - Full mini version documentation
- `MINI-VERSION-SUMMARY.md` - Capabilities overview
- `CODESPACES-WORKFLOW-BRAINSTORM.md` - Design decisions and alternatives

---

## 🎉 Success Criteria

Setup is successful when:
1. ✅ Files are in place and executable
2. ✅ Configuration matches user's environment
3. ✅ Sync watcher starts (automatically in Codespaces, manually local)
4. ✅ User can see logs (via control script or direct view)
5. ✅ Claude branch is detected and synced
6. ✅ Tests run successfully
7. ✅ Dev server starts (if project needs it)
8. ✅ User can access preview URL or localhost
9. ✅ User knows control commands
10. ✅ User understands the workflow

**When all criteria are met, the user's workflow becomes:**
1. Code in Claude Code web
2. Click preview URL
3. Test
4. Merge

**That's it! Everything else is automated.** 🚀
