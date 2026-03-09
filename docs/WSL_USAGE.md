# WSL Usage Guide

## Running AAIA in WSL

There are **two different scripts** depending on where you're running from:

### 1. From Windows PowerShell → Use `wsl-run.sh`

Run from Windows to execute commands inside WSL:

```powershell
# From Windows PowerShell
.\wsl-run.sh build    # Build with Nix
.\wsl-run.sh python   # Run Python
.\wsl-run.sh test     # Run tests
```

### 2. From Inside WSL → Use `wsl-local.sh`

Run from inside WSL terminal:

```bash
# From WSL terminal
./wsl-local.sh build   # Build with Nix
./wsl-local.sh python  # Run Python
./wsl-local.sh test    # Run tests
./wsl-local.sh verify  # Run build verification
./wsl-local.sh pytest  # Run unit tests
```

---

## Quick Start (Inside WSL)

1. **Make script executable:**
   ```bash
   chmod +x wsl-local.sh
   ```

2. **Install Nix** (if not already installed):
   ```bash
   ./install.sh
   ```

3. **Enter development environment:**
   ```bash
   ./wsl-local.sh dev
   ```

4. **Run AAIA:**
   ```bash
   ./wsl-local.sh python
   ```

---

## Available Commands

### `wsl-local.sh` Commands (Inside WSL)

| Command | Description |
|---------|-------------|
| `build` | Build AAIA package with Nix |
| `run` | Run AAIA from build |
| `test` | Run wsl-test.sh script |
| `dev` | Enter Nix development shell |
| `python` | Run from Python (with Nix env) |
| `check` | Check Nix flake |
| `verify` | Run build verification script |
| `pytest` | Run pytest unit tests |

### `wsl-run.sh` Commands (From Windows)

Same commands, but run from Windows PowerShell:

```powershell
.\wsl-run.sh build
.\wsl-run.sh python
.\wsl-run.sh test
```

---

## Troubleshooting

### Error: "wsl: command not found"

**Problem**: You're running `wsl-run.sh` from inside WSL.

**Solution**: Use `wsl-local.sh` instead:
```bash
./wsl-local.sh <command>
```

### Error: "nix: command not found"

**Problem**: Nix is not installed in WSL.

**Solution**: Install Nix:
```bash
./install.sh
```

Then reload your shell or run:
```bash
source ~/.bashrc
```

### Error: "Permission denied"

**Problem**: Script is not executable.

**Solution**: Make it executable:
```bash
chmod +x wsl-local.sh
chmod +x wsl-run.sh
chmod +x wsl-test.sh
```

---

## Environment Setup

### Inside WSL Terminal:

1. Navigate to project:
   ```bash
   cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia
   ```

2. Make scripts executable:
   ```bash
   chmod +x wsl-local.sh wsl-run.sh wsl-test.sh install.sh
   ```

3. Install Nix (if needed):
   ```bash
   ./install.sh
   ```

4. Enter dev environment:
   ```bash
   ./wsl-local.sh dev
   ```

5. Run verification:
   ```bash
   ./wsl-local.sh verify
   ```

---

## Phase 2.5 Verification in WSL

```bash
# 1. Make script executable
chmod +x wsl-local.sh

# 2. Run build verification
./wsl-local.sh verify

# 3. Run unit tests
./wsl-local.sh pytest

# 4. Run main application
./wsl-local.sh python
```

---

## Which Script to Use?

**Use `wsl-local.sh` when:**
- You're in a WSL terminal (Ubuntu-24.04)
- You see a prompt like: `matren@DESKTOP-7AIBQM6:~$`
- You've already done `cd /mnt/c/Users/.../aaia`

**Use `wsl-run.sh` when:**
- You're in Windows PowerShell
- You see a prompt like: `PS C:\Users\...>`
- You want to run WSL commands from Windows

---

## Summary

| Where you are | Script to use | Example |
|---------------|---------------|---------|
| Inside WSL | `wsl-local.sh` | `./wsl-local.sh python` |
| Windows PowerShell | `wsl-run.sh` | `.\wsl-run.sh python` |

The key difference: `wsl-run.sh` calls `wsl -d Ubuntu-24.04` to enter WSL, while `wsl-local.sh` assumes you're already in WSL.
