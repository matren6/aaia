# WSL Testing Results

**Date:** 2026-03-14  
**Test Type:** Ollama connectivity from WSL

## Summary

✅ **OLLAMA REQUESTS WORK IN WSL** when using the proper Nix development environment.

## Root Cause

The issue was that `python-dotenv` package was not available when running Python directly in WSL, causing the `.env` file to not be loaded. The code in `packages/modules/settings.py` has a silent fallback:

```python
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Silently fails, uses hardcoded defaults
```

Without `python-dotenv`, the application uses hardcoded defaults:
- `OLLAMA_BASE_URL`: defaults to `http://localhost:11434` (instead of `http://192.168.178.104:11434`)
- `OLLAMA_MODEL`: defaults to `phi3` (instead of `phi4-mini:latest`)

## Test Results

### ❌ Test 1: Direct Python (No Nix)
```bash
wsl -d Ubuntu-24.04 -e bash -c "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && PYTHONPATH=packages python3 scripts/test_ollama_connection.py"
```
**Result:** Connection refused - tries to connect to `localhost:11434`

### ✅ Test 2: With Manual Environment Variables
```bash
wsl -d Ubuntu-24.04 -e bash -c "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && OLLAMA_BASE_URL=http://192.168.178.104:11434 OLLAMA_MODEL=phi4-mini:latest PYTHONPATH=packages python3 scripts/test_ollama_connection.py"
```
**Result:** ✅ Success! Connected and generated response

### ✅ Test 3: Using Nix Development Environment
```bash
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix develop --extra-experimental-features 'nix-command flakes' --command python3 scripts/test_ollama_connection.py"
```
**Result:** ✅ Success! `.env` file loaded correctly

**Output:**
```
Configuration:
  Enabled: True
  Base URL: http://192.168.178.104:11434
  Default Model: phi4-mini:latest
  Timeout: 300s

1. Testing /api/tags endpoint...
   ✅ Success! (200)
   Available Models: 2
     - phi4-mini:latest (2.32 GB)
     - qwen3:8b (4.87 GB)

3. Testing generate endpoint with a simple prompt...
   ✅ Success! (200)
   Response preview: Hello! How can I assist you today?...

✅ OLLAMA SERVER IS ACCESSIBLE
```

## Solution

**Always use Nix development environment in WSL:**

```bash
# From Windows PowerShell
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix develop --extra-experimental-features 'nix-command flakes' --command python3 packages/main.py"

# Or use the helper script
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && ./scripts/wsl_test.sh"

# With commands
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && ./scripts/wsl_test.sh -c status -e"
```

## Configuration Verified

From `.env` file:
- ✅ `OLLAMA_ENABLED=true`
- ✅ `OLLAMA_BASE_URL=http://192.168.178.104:11434` (remote Ollama server)
- ✅ `OLLAMA_MODEL=phi4-mini:latest`
- ✅ `OLLAMA_TIMEOUT=300`
- ✅ Available models: `phi4-mini:latest`, `qwen3:8b`

## Recommendations

1. **Update Copilot Instructions**: Add note about Nix requirement for WSL
2. **Consider**: Add warning if `python-dotenv` import fails (instead of silent fallback)
3. **WSL Quickstart**: Use `scripts/wsl_test.sh` for easier testing

## Dependencies in Nix

The `flake.nix` properly includes all required Python packages:
- ✅ `python-dotenv`
- ✅ `requests`
- ✅ `psutil`
- ✅ `pytest`

When using Nix, all dependencies are guaranteed to be available.
