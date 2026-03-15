# AAIA Build & Script Standards

## Python Compilation (No Traditional Build Needed)

Python projects don't have traditional builds like C#, Java, or C++. When asked to "build", use **verification only**:

### Verification Commands:

```bash
# Verify individual files compile without syntax errors
python3 -m py_compile packages/modules/scribe.py
python3 -m py_compile packages/modules/database_manager.py

# Verify entire directory
find packages -name "*.py" -exec python3 -m py_compile {} +

# Quick check specific module
python3 -m py_compile packages/modules/*.py
```

### What This Does:
- Checks Python syntax
- Compiles to bytecode (.pyc)
- Reports syntax errors
- Does NOT create executable

### When to Use:
- After modifying Python files
- Before committing changes
- When asked to "build solution"
- To verify code is valid

---

## Bash Script Requirements (CRITICAL)

### Line Endings MUST Be LF Only

**ALL bash scripts MUST use LF line endings ONLY** (Unix standard).

**CRLF (Windows line endings) breaks bash in Linux/WSL with "bad interpreter" error**.

### Rules When Creating Bash Scripts:

1. **Set line endings to LF** (not CRLF) in your editor
2. **Verify with**: `file scripts/script.sh` 
   - ✅ Good: `shell script, ASCII text`
   - ❌ Bad: `shell script, ASCII text, with CRLF line terminators`
3. **Fix if broken**: `sed -i 's/\r$//' scripts/script.sh`
4. **Make executable**: `chmod +x scripts/script.sh`

### Example Script Template:

```bash
#!/bin/bash
# Script description
# Must use LF line endings (not CRLF)

set -e  # Exit on error

cd "$(dirname "$0")/.."  # Navigate to project root

echo "Script running..."
# Your code here
```

### How to Fix Broken Scripts:

If you see error: `/bin/bash^M: bad interpreter: No such file or directory`

**Fix with**:
```bash
# Convert CRLF to LF
sed -i 's/\r$//' scripts/script.sh

# Or using dos2unix (if available)
dos2unix scripts/script.sh
```

### Scripts in This Project:

All scripts must have LF line endings:
- `scripts/dry_run_test.sh` - ✅ LF verified
- `scripts/monitor_dry_run.sh` - ✅ LF verified
- `scripts/wsl_test.sh` - ✅ LF verified
- `scripts/verify_database.py` - Python (LF)
- Any new `scripts/*.sh` - **MUST be LF**

---

## Quick Reference

### Creating New Bash Script:
```bash
# 1. Create file
cat > scripts/my_script.sh << 'EOF'
#!/bin/bash
echo "Hello"
EOF

# 2. Fix line endings
sed -i 's/\r$//' scripts/my_script.sh

# 3. Make executable
chmod +x scripts/my_script.sh

# 4. Verify
file scripts/my_script.sh
# Should show: "shell script, ASCII text" (no CRLF warning)
```

### Verifying Python Files:
```bash
# Check if file compiles
python3 -m py_compile packages/modules/my_module.py

# Check all modified files
git diff --name-only | grep "\.py$" | xargs python3 -m py_compile
```

---

## Key Constraints

- ✅ **Bash scripts: LF line endings only** (not CRLF)
- ✅ **Python build: use `py_compile`** for verification
- ✅ **Always verify** scripts work in WSL
- ✅ **Fix line endings** before committing
- ⚠️ Make sure to only use LF as line ending to avoid issues in WSL and Nix environments
