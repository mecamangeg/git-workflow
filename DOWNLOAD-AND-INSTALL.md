# How to Download and Install to Your Projects

This guide shows how to get all the automation files and install them to your projects.

---

## 📦 Complete File List

You'll get these files:

### Core Files (Required)
- `mini_sync.py` - Main automation script
- `.sync.yaml.example` - Configuration template
- `sync-control.sh` - Control commands

### Devcontainer Files (For Codespaces)
- `.devcontainer/devcontainer.json` - Codespaces configuration
- `.devcontainer/start-sync.sh` - Auto-start script

### Documentation (Reference)
- `AI-SETUP-INSTRUCTIONS.md` - Guide for AI assistants
- `CODESPACES-SETUP.md` - Complete Codespaces guide
- `MINI-VERSION-README.md` - Full documentation
- `MINI-VERSION-SUMMARY.md` - Quick reference
- `CODESPACES-WORKFLOW-BRAINSTORM.md` - Design decisions

### Install Script (Helper)
- `install-to-project.sh` - Automated installation script

---

## 🚀 Quick Install Methods

### Method 1: One-Command Install (Recommended)

**From this repository:**

```bash
# Install to your project
bash install-to-project.sh /path/to/your/project

# Example:
bash install-to-project.sh ~/Projects/my-nextjs-app
```

This copies all files and sets up everything automatically.

---

### Method 2: Clone and Copy

**If you have git access to this repository:**

```bash
# Clone this repository
git clone <this-repo-url> claude-workflow
cd claude-workflow

# Install to your project
bash install-to-project.sh /path/to/your/project
```

---

### Method 3: Download via GitHub (If hosted on GitHub)

**Option A: Download ZIP**

1. Go to repository page
2. Click "Code" → "Download ZIP"
3. Extract ZIP file
4. Run install script:
   ```bash
   cd extracted-folder
   bash install-to-project.sh /path/to/your/project
   ```

**Option B: Download specific files**

Visit these URLs (replace `{owner}` and `{repo}` with actual values):

```
https://github.com/{owner}/{repo}/blob/main/mini_sync.py
https://github.com/{owner}/{repo}/blob/main/.sync.yaml.example
https://github.com/{owner}/{repo}/blob/main/sync-control.sh
https://github.com/{owner}/{repo}/blob/main/.devcontainer/devcontainer.json
https://github.com/{owner}/{repo}/blob/main/.devcontainer/start-sync.sh
```

Click "Raw" button on each file and save.

---

### Method 4: Manual Copy (If you have local access)

**Copy files manually:**

```bash
# Set source and destination
SOURCE=/home/user/git-workflow
DEST=/path/to/your/project

# Core files
cp $SOURCE/mini_sync.py $DEST/
cp $SOURCE/.sync.yaml.example $DEST/.sync.yaml
cp $SOURCE/sync-control.sh $DEST/
chmod +x $DEST/sync-control.sh

# Devcontainer (for Codespaces)
mkdir -p $DEST/.devcontainer
cp $SOURCE/.devcontainer/devcontainer.json $DEST/.devcontainer/
cp $SOURCE/.devcontainer/start-sync.sh $DEST/.devcontainer/
chmod +x $DEST/.devcontainer/start-sync.sh

# Documentation (optional)
cp $SOURCE/AI-SETUP-INSTRUCTIONS.md $DEST/
cp $SOURCE/CODESPACES-SETUP.md $DEST/
cp $SOURCE/MINI-VERSION-README.md $DEST/
cp $SOURCE/MINI-VERSION-SUMMARY.md $DEST/
cp $SOURCE/CODESPACES-WORKFLOW-BRAINSTORM.md $DEST/
```

---

## 📋 After Installation

Once files are copied to your project:

### Step 1: Install Dependencies

```bash
cd /path/to/your/project
pip install pyyaml
```

Or add to `requirements.txt`:
```
pyyaml>=6.0
```

### Step 2: Configure

Edit `.sync.yaml` for your project:

**For GitHub Codespaces:**
```yaml
auto_start_server: true  # Enable 100% automation
run_tests: true
start_dev_server: true
```

**For local development:**
```yaml
auto_start_server: false  # Manual server start
run_tests: true
start_dev_server: true
```

### Step 3: Test

**For Codespaces:**
```bash
# Commit devcontainer files
git add .devcontainer/ mini_sync.py .sync.yaml sync-control.sh
git commit -m "feat: add automation"
git push

# Open in Codespaces - automation starts automatically
```

**For local:**
```bash
# Test one-time sync
python mini_sync.py

# Start watch mode
python mini_sync.py --watch
```

---

## 🎯 Use in Multiple Projects

### Scenario: You have 5 projects

**Install to each project:**

```bash
# Clone once
git clone <this-repo-url> claude-workflow

# Install to all projects
cd claude-workflow
bash install-to-project.sh ~/Projects/project1
bash install-to-project.sh ~/Projects/project2
bash install-to-project.sh ~/Projects/project3
bash install-to-project.sh ~/Projects/project4
bash install-to-project.sh ~/Projects/project5
```

**Configure each project:**
- Edit `.sync.yaml` in each project
- Customize branch patterns if needed
- Adjust test/dev commands if needed

**Each project runs independently:**
- Separate `mini_sync.py` instance per project
- Separate configuration per project
- Separate dev server per project

---

## 🔄 Updating Files

If the automation scripts get updated:

**Option 1: Re-run install script**
```bash
cd claude-workflow
git pull  # Get latest changes
bash install-to-project.sh /path/to/your/project
```

**Option 2: Manual update**
```bash
cp claude-workflow/mini_sync.py /path/to/your/project/
# Restart automation
cd /path/to/your/project
bash sync-control.sh restart
```

---

## 📁 File Structure After Installation

Your project will have:

```
your-project/
├── mini_sync.py                    # Core automation
├── .sync.yaml                      # Your configuration
├── sync-control.sh                 # Control commands
├── .devcontainer/
│   ├── devcontainer.json          # Codespaces config
│   └── start-sync.sh              # Auto-start script
├── AI-SETUP-INSTRUCTIONS.md        # AI guide
├── CODESPACES-SETUP.md             # Codespaces guide
├── MINI-VERSION-README.md          # Full docs
├── MINI-VERSION-SUMMARY.md         # Quick reference
├── CODESPACES-WORKFLOW-BRAINSTORM.md  # Design decisions
└── .dev-server.log                 # (auto-created)
```

---

## 🧹 Clean Installation

If you want to remove the automation:

```bash
cd /path/to/your/project

# Remove core files
rm mini_sync.py .sync.yaml sync-control.sh

# Remove devcontainer
rm -rf .devcontainer/

# Remove documentation (optional)
rm AI-SETUP-INSTRUCTIONS.md
rm CODESPACES-SETUP.md
rm MINI-VERSION-README.md
rm MINI-VERSION-SUMMARY.md
rm CODESPACES-WORKFLOW-BRAINSTORM.md

# Remove generated files
rm .dev-server.log
```

---

## 💡 Tips

### Tip 1: Keep a Local Copy

Keep the `claude-workflow` repository for easy installation:

```bash
# Clone once to a permanent location
cd ~/Tools
git clone <this-repo-url> claude-workflow

# Use whenever needed
~/Tools/claude-workflow/install-to-project.sh /path/to/new/project
```

### Tip 2: Add to .gitignore (Optional)

If you don't want to commit automation files:

```bash
# Add to .gitignore
echo "mini_sync.py" >> .gitignore
echo ".sync.yaml" >> .gitignore
echo "sync-control.sh" >> .gitignore
echo ".dev-server.log" >> .gitignore
```

But for Codespaces, you MUST commit `.devcontainer/` files.

### Tip 3: Customize Per Project

Each project can have different settings:

**Project A (Next.js):**
```yaml
# .sync.yaml
auto_start_server: true
test_commands:
  next: "npm test -- --coverage"
```

**Project B (Django):**
```yaml
# .sync.yaml
auto_start_server: true
test_commands:
  django: "python manage.py test --parallel"
dev_commands:
  django: "python manage.py runserver 0.0.0.0:8000"
```

### Tip 4: Share with Team

Commit automation files to your project repo:

```bash
git add .devcontainer/ mini_sync.py .sync.yaml sync-control.sh *-*.md
git commit -m "feat: add Claude Code workflow automation"
git push
```

Now your whole team can use it!

---

## 🎉 Quick Start Summary

**For Codespaces (100% automation):**
```bash
# 1. Install
bash install-to-project.sh ~/Projects/my-app

# 2. Configure
cd ~/Projects/my-app
vim .sync.yaml  # Set auto_start_server: true

# 3. Commit and push
git add .devcontainer/ mini_sync.py .sync.yaml sync-control.sh
git commit -m "feat: add automation"
git push

# 4. Open in Codespaces - done!
```

**For local development:**
```bash
# 1. Install
bash install-to-project.sh ~/Projects/my-app

# 2. Configure
cd ~/Projects/my-app
vim .sync.yaml  # Set auto_start_server: false

# 3. Run
python mini_sync.py --watch

# 4. Code in Claude Code web - branches sync automatically!
```

---

## 📞 Need Help?

- **Quick start:** Read `MINI-VERSION-README.md`
- **Codespaces:** Read `CODESPACES-SETUP.md`
- **For AI assistants:** Read `AI-SETUP-INSTRUCTIONS.md`
- **Design decisions:** Read `CODESPACES-WORKFLOW-BRAINSTORM.md`

---

**Happy automating! 🚀**
