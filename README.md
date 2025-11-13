# Git Workflow Guardian

> A proactive tool that helps developers maintain Git workflow best practices through intelligent notifications and enforcement.

[![Tests](https://github.com/yourusername/git-workflow-guardian/workflows/CI/badge.svg)](https://github.com/yourusername/git-workflow-guardian/actions)
[![Coverage](https://img.shields.io/codecov/c/github/yourusername/git-workflow-guardian)](https://codecov.io/gh/yourusername/git-workflow-guardian)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Problem

Developers often forget to follow Git workflow best practices:
- Accidentally committing to `main` branch
- Pushing directly to protected branches
- Forgetting to pull latest changes before starting work
- Leaving stale merged branches
- Not testing locally before committing

## ✨ Solution

Git Workflow Guardian provides a **hybrid approach**:

1. **Git Hooks** (Critical Enforcement) - Blocks violations before they happen
2. **Background Service** (Proactive Guidance) - Suggests best practices via notifications

## 🚀 Quick Start

```powershell
# 1. Clone and install
git clone https://github.com/yourusername/git-workflow-guardian.git
cd git-workflow-guardian

# 2. Install hooks in your repository
.\scripts\install_hooks.ps1 -RepoPath "C:\Your\Project"

# 3. Install background monitoring service
.\scripts\install_service.ps1

# 4. Done! You're protected ✅
```

## 📋 Features

### Critical Enforcement (Git Hooks)
- ⛔ **Block commits to main** - Prevents accidental commits to protected branches
- ⛔ **Block pushes to main** - Stops direct pushes, enforces PR workflow
- 💡 **Smart overrides** - Session-level overrides when you really need them

### Proactive Guidance (Background Service)
- 💡 **Pull reminders** - Suggests pulling main when out of sync
- 💡 **Branch cleanup** - Notifies about merged branches ready for deletion
- 💡 **Local testing** - Reminds to run dev server before committing
- 💡 **Branch naming** - Validates branch names follow conventions

### Advanced Features (Phase 3)
- 📊 **Compliance Dashboard** - Real-time view of workflow compliance
- 📈 **Analytics** - Track violations and improvement trends
- 🎨 **Customizable Rules** - Configure notifications and enforcement levels

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         GIT WORKFLOW GUARDIAN           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────┐         ┌──────────────┐  │
│  │  HOOKS  │         │   SERVICE    │  │
│  │ (Block) │◄───────►│  (Suggest)   │  │
│  └─────────┘         └──────────────┘  │
│       │                     │           │
│       └──────────┬──────────┘           │
│                  │                      │
│           ┌──────▼──────┐               │
│           │  NOTIFIER   │               │
│           └──────┬──────┘               │
│                  │                      │
│           ┌──────▼──────┐               │
│           │  STATE DB   │               │
│           └─────────────┘               │
└─────────────────────────────────────────┘
```

## 📖 Documentation

- [User Guide](docs/USER_GUIDE.md) - Installation and usage
- [Developer Guide](docs/DEVELOPER.md) - Architecture and contributing
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

## 🎨 Workflow Rules

| Rule | Type | Description |
|------|------|-------------|
| Commit to Main | **CRITICAL** | Blocks commits to main/master branches |
| Push to Main | **CRITICAL** | Blocks pushes to main/master branches |
| Branch Naming | **WARNING** | Validates branch name conventions |
| Pull Before Work | **SUGGESTION** | Reminds to pull latest main |
| Test Locally | **SUGGESTION** | Checks if dev server is running |
| Delete Merged Branch | **SUGGESTION** | Suggests cleaning up merged branches |

## ⚙️ Configuration

Create `config/config.yaml`:

```yaml
rules:
  commit_to_main:
    severity: critical
    enabled: true
    blocking: true

  branch_naming:
    pattern: "^claude/[a-z0-9-]+-[A-Za-z0-9]{24}$"

monitoring:
  poll_interval: 30
  repos:
    auto_discover: true
    search_paths:
      - "D:/Projects"
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=service --cov-report=html

# Specific test
pytest tests/test_hooks.py -v
```

## 🤝 Contributing

Contributions are welcome! Please read [DEVELOPER.md](docs/DEVELOPER.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Success Metrics

- **95%+** workflow compliance after 2 weeks
- **<5** false positive notifications per day
- **100%** critical violations prevented (zero commits to main)
- **>4.0/5.0** user satisfaction score

## 📅 Roadmap

- [x] Phase 0: Project setup
- [ ] Phase 1: Git hooks implementation
- [ ] Phase 2: Background monitoring service
- [ ] Phase 3: Compliance dashboard and analytics
- [ ] Phase 4: VSCode extension, machine learning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python, Git hooks, and love ❤️
- Inspired by developer productivity and workflow optimization
- Community feedback and contributions

---

**Status:** 🚧 In Development
**Version:** 1.0.0
**Maintainer:** Git Workflow Guardian Team

---

Made with [Claude Code](https://claude.com/claude-code) 🤖
