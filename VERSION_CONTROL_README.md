# 🎯 Version Control Guide for OptionsTrading_App

## 📋 **What to Version Control**

### ✅ **INCLUDE in Git (Source Code & Configuration)**
- `cursorstrategies/*.py` - All your trading strategies
- `app/*.py` - Web application code
- `strategies/*.py` - Base strategy classes
- `run_strategy_cli.py` - CLI runner
- `requirements*.txt` - Python dependencies
- `*.md` - Documentation files
- `.gitignore` - Git ignore rules
- `env.example` - Environment template (NO real credentials)

### ❌ **EXCLUDE from Git (Sensitive & Generated)**
- `.env` - Real environment variables with API keys
- `strategies.db` - Database files
- `*.log` - Log files
- `__pycache__/` - Python cache
- `venv/` - Virtual environment
- Any files with real IBKR credentials

## 🚀 **Git Setup Commands**

### **First Time Setup (after installing Git):**
```bash
# Initialize Git repository
git init

# Add all source code files
git add .

# Create initial commit
git commit -m "🎯 Initial commit: Trading strategy system with MNQ futures strategy

- Complete trading strategy framework
- MNQ futures strategy with real market data
- Web application with FastAPI
- CLI runner for strategy execution
- Connection manager for IBKR
- No fallback price system - real market data only"

# Add remote repository (if using GitHub/GitLab)
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

### **Daily Development Workflow:**
```bash
# Check what files have changed
git status

# See detailed changes
git diff

# Add specific files
git add cursorstrategies/futures_mnq_strategy.py
git add app/connection_manager.py

# Or add all changes
git add .

# Commit with descriptive message
git commit -m "✨ Enhance MNQ strategy with improved stop loss logic

- Add dynamic stop loss calculation
- Improve position monitoring
- Fix event loop handling in CLI mode
- Add comprehensive error handling"

# Push to remote
git push origin main
```

## 📝 **Commit Message Conventions**

### **Format:**
```
<emoji> <type>: <description>

<detailed explanation if needed>
```

### **Emojis by Type:**
- 🎯 **New Feature**: `🎯 feat: Add new trading strategy`
- ✨ **Enhancement**: `✨ enhance: Improve stop loss logic`
- 🐛 **Bug Fix**: `🐛 fix: Resolve event loop conflict`
- 🔧 **Refactor**: `🔧 refactor: Clean up connection manager`
- 📚 **Documentation**: `📚 docs: Update strategy parameters`
- 🧪 **Test**: `🧪 test: Add strategy unit tests`
- 🚀 **Performance**: `🚀 perf: Optimize market data handling`
- 🔒 **Security**: `🔒 security: Remove hardcoded credentials`

### **Examples:**
```bash
git commit -m "🎯 feat: Add ES futures strategy

- Implement ES December 2025 futures trading
- Add volatility-based entry signals
- Include comprehensive risk management
- Support both paper and live trading modes"

git commit -m "✨ enhance: Improve MNQ strategy execution

- Add real-time position monitoring
- Implement dynamic stop loss adjustment
- Add take profit logic with configurable multiplier
- Improve order fill detection and handling"

git commit -m "🐛 fix: Resolve CLI event loop conflicts

- Fix 'Cannot run event loop while another loop is running'
- Implement proper async/await handling in CLI mode
- Add event loop isolation for strategy execution
- Maintain real-time market data functionality"
```

## 🔄 **Branching Strategy**

### **Main Branches:**
- `main` - Production-ready code
- `develop` - Development and testing
- `feature/*` - New features (e.g., `feature/es-strategy`)
- `bugfix/*` - Bug fixes (e.g., `bugfix/event-loop`)
- `hotfix/*` - Critical production fixes

### **Branch Workflow:**
```bash
# Create feature branch
git checkout -b feature/es-strategy

# Make changes and commit
git add .
git commit -m "🎯 feat: Add ES futures strategy"

# Push feature branch
git push origin feature/es-strategy

# Merge back to develop (via Pull Request)
git checkout develop
git merge feature/es-strategy

# Clean up feature branch
git branch -d feature/es-strategy
```

## 📊 **File Organization for Version Control**

### **Strategy Files:**
```
cursorstrategies/
├── futures_mnq_strategy.py     # ✅ Version controlled
├── es_futures_strategy.py      # ✅ Version controlled
├── breakout_strategy.py        # ✅ Version controlled
└── __init__.py                 # ✅ Version controlled
```

### **Application Files:**
```
app/
├── __init__.py                 # ✅ Version controlled
├── main.py                     # ✅ Version controlled
├── connection_manager.py       # ✅ Version controlled
├── routers/                    # ✅ Version controlled
│   ├── strategies.py
│   └── connection.py
└── models/                     # ✅ Version controlled
    └── strategy.py
```

### **Configuration Files:**
```
├── .gitignore                  # ✅ Version controlled
├── requirements.txt            # ✅ Version controlled
├── requirements_runner.txt     # ✅ Version controlled
├── env.example                 # ✅ Version controlled (template only)
└── README.md                   # ✅ Version controlled
```

## 🚨 **Security Best Practices**

### **Never Commit:**
- Real API keys or credentials
- Database files with sensitive data
- Log files with account information
- Environment files with real values

### **Always Use:**
- `.env.example` for templates
- Placeholder values in code
- Environment variables for secrets
- `.gitignore` to exclude sensitive files

## 📈 **Version Control Benefits**

1. **Code History**: Track all changes and who made them
2. **Rollback**: Revert to previous working versions
3. **Collaboration**: Multiple developers can work safely
4. **Testing**: Test new features without affecting production
5. **Documentation**: Commit messages serve as change log
6. **Backup**: Code is safely stored in remote repository

## 🔍 **Useful Git Commands**

```bash
# View commit history
git log --oneline --graph

# See changes in a specific commit
git show <commit-hash>

# Compare branches
git diff main..develop

# Stash changes temporarily
git stash
git stash pop

# View file history
git log --follow -- cursorstrategies/futures_mnq_strategy.py

# Create tags for releases
git tag -a v1.0.0 -m "First production release"
git push origin v1.0.0
```

## 🎯 **Next Steps**

1. **Install Git** from https://git-scm.com/download/win
2. **Initialize repository** with the commands above
3. **Create first commit** with your current working system
4. **Set up remote repository** on GitHub/GitLab if desired
5. **Follow daily workflow** for all future changes

This will ensure your trading strategy system is perfectly version controlled and safe! 🚀
