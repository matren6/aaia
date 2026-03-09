# WSL Setup & Troubleshooting Guide

## The Issue You're Seeing

```
ModuleNotFoundError: No module named 'psutil'
```

**This is EXPECTED!** The system Python in WSL doesn't have AAIA's dependencies.

## ✅ Solution: Use Nix Environment

All Python commands **must** run through the Nix environment:

```bash
# ❌ WRONG - Uses system Python (missing dependencies)
python packages/main.py

# ✅ CORRECT - Uses Nix Python (has all dependencies)
./wsl-local.sh python
```

---

## Quick Start (Step-by-Step)

### 1. Configure Nix (One-Time Setup)

```bash
chmod +x configure-nix.sh
./configure-nix.sh
```

### 2. Test Nix Environment

```bash
# Check if dependencies are available
./wsl-local.sh deps
```

Expected output:
```
✓ All dependencies available
```

### 3. Run Build Verification

```bash
./wsl-local.sh verify
```

Expected output:
```
*** BUILD VERIFICATION: PASSED ***
```

### 4. Run Unit Tests

```bash
./wsl-local.sh pytest
```

### 5. Run Main Application

```bash
./wsl-local.sh python
```

---

## Available Commands

| Command | What It Does | Uses Nix Env? |
|---------|--------------|---------------|
| `./wsl-local.sh deps` | Check dependencies | ✅ Yes |
| `./wsl-local.sh quick-test` | Quick import test | ✅ Yes |
| `./wsl-local.sh verify` | Full verification | ✅ Yes |
| `./wsl-local.sh pytest` | Unit tests | ✅ Yes |
| `./wsl-local.sh python` | Run main app | ✅ Yes |
| `./wsl-local.sh shell` | Enter Nix shell | ✅ Yes |
| `./wsl-local.sh build` | Build package | ✅ Yes |

---

## Why Use Nix?

**Problem**: WSL's system Python is missing:
- psutil
- requests
- python-dotenv
- Other AAIA dependencies

**Solution**: Nix provides:
- Isolated environment
- All dependencies pre-installed
- Reproducible builds
- No conflicts with system packages

---

## Common Workflows

### Workflow 1: Quick Verification

```bash
./wsl-local.sh deps        # Check dependencies
./wsl-local.sh quick-test  # Quick import test
./wsl-local.sh verify      # Full verification
```

### Workflow 2: Development

```bash
./wsl-local.sh shell  # Enter Nix shell
# Now you're in a shell with all dependencies
python packages/main.py
pytest tests/ -v
exit  # Leave Nix shell
```

### Workflow 3: Run Tests

```bash
./wsl-local.sh pytest  # Run unit tests
./wsl-local.sh verify  # Run verification script
```

---

## Troubleshooting

### Error: "No module named 'psutil'"

**Cause**: Running Python directly instead of through Nix

**Solution**:
```bash
# Don't run:
python packages/main.py

# Instead run:
./wsl-local.sh python
```

### Error: "experimental Nix feature 'nix-command' is disabled"

**Cause**: Nix not configured

**Solution**:
```bash
./configure-nix.sh
```

Or manually:
```bash
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" > ~/.config/nix/nix.conf
```

### Error: "nix: command not found"

**Cause**: Nix not installed

**Solution**:
```bash
./install.sh
source ~/.bashrc
```

---

## Understanding the Environment

### System Python (Don't Use)
```bash
$ python3 --version
Python 3.12.3

$ python3 -c "import psutil"
ModuleNotFoundError: No module named 'psutil'
```

### Nix Python (Use This)
```bash
$ nix develop -c python --version
Python 3.11.x

$ nix develop -c python -c "import psutil; print('✓ Works!')"
✓ Works!
```

---

## Phase 2.5 Verification in WSL

Complete verification workflow:

```bash
# 1. Configure Nix (if not done)
./configure-nix.sh

# 2. Check dependencies
./wsl-local.sh deps

# 3. Run quick test
./wsl-local.sh quick-test

# 4. Run full verification
./wsl-local.sh verify

# 5. Run unit tests
./wsl-local.sh pytest

# 6. Try running the application
./wsl-local.sh python
```

All should pass! ✅

---

## Key Takeaway

**Always use `./wsl-local.sh <command>` in WSL**

This ensures you're running in the Nix environment with all dependencies.

Never run Python directly - always through Nix!
