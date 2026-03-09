# Quick WSL Commands Reference

## You are INSIDE WSL - Use These Commands:

```bash
# First-time setup
chmod +x configure-nix.sh wsl-local.sh
./configure-nix.sh

# Check if Nix environment has dependencies
./wsl-local.sh deps

# Quick import test
./wsl-local.sh quick-test

# Run build verification (10 tests)
./wsl-local.sh verify

# Run unit tests (4 tests)
./wsl-local.sh pytest

# Run main application
./wsl-local.sh python

# Enter Nix shell (interactive)
./wsl-local.sh shell

# Build with Nix
./wsl-local.sh build

# Show help
./wsl-local.sh help
```

---

## ⚠️ IMPORTANT: Always Use Nix Environment!

**DON'T run Python directly:**
```bash
# ❌ WRONG - Missing dependencies (psutil, etc.)
python packages/main.py
python verify_build.py
```

**DO run through wsl-local.sh:**
```bash
# ✅ CORRECT - Has all dependencies
./wsl-local.sh python
./wsl-local.sh verify
```

---

## Common Issues & Solutions

### ❌ Error: "No module named 'psutil'"

**Cause:** You're using system Python instead of Nix Python

✅ **Solution:** Always use `./wsl-local.sh <command>`

```bash
# System Python (missing deps)
python -c "import psutil"  # ❌ Fails

# Nix Python (has deps)
./wsl-local.sh deps  # ✅ Works
```

---

### ❌ Error: "experimental Nix feature disabled"

✅ **Solution:** Configure Nix

```bash
./configure-nix.sh
```

---

### ❌ Error: "wsl: command not found"
**You're using the wrong script!**

✅ **Solution:** Use `wsl-local.sh` instead of `wsl-run.sh`

```bash
# Wrong (from inside WSL):
./wsl-run.sh test

# Correct (from inside WSL):
./wsl-local.sh test
```

---

### ❌ Error: "nix: command not found"

✅ **Solution:** Install Nix first

```bash
./install.sh
source ~/.bashrc
```

---

### ❌ Error: "Permission denied"

✅ **Solution:** Make executable

```bash
chmod +x wsl-local.sh configure-nix.sh
```

---

## Phase 2.5 Verification Checklist

From inside WSL:

```bash
# 1. One-time setup
chmod +x configure-nix.sh wsl-local.sh
./configure-nix.sh

# 2. Check dependencies available
./wsl-local.sh deps
# Expected: "✓ All dependencies available"

# 3. Quick import test
./wsl-local.sh quick-test
# Expected: "✓ ModelInfo imported successfully"

# 4. Full verification (10 tests)
./wsl-local.sh verify
# Expected: "*** BUILD VERIFICATION: PASSED ***"

# 5. Unit tests (4 tests)
./wsl-local.sh pytest
# Expected: "4 passed"

# 6. Try running the application
./wsl-local.sh python
# Expected: "AAIA (Autonomous AI Agent) System Initialized"
```

---

## New Commands Added

| Command | Description |
|---------|-------------|
| `./wsl-local.sh deps` | Check if dependencies available |
| `./wsl-local.sh quick-test` | Quick import test |
| `./wsl-local.sh shell` | Enter interactive Nix shell |

---

## Remember:

- **Inside WSL** → Use `./wsl-local.sh`
- **Windows PowerShell** → Use `.\wsl-run.sh`
- **Always use Nix environment** for Python commands!

You are currently: **INSIDE WSL** ✓
