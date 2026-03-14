# AAIA Copilot Instructions

## Core Architecture Rules (MANDATORY)

### 1. Dependency Injection Container
**ALL modules MUST use DI Container (`modules/container.py`)**

```python
# Register in modules/setup.py
container.register('ModuleName', ModuleClass, singleton=True)

# With dependencies - use factory function
container.register('Service', lambda c: Service(c.get('Dependency')))

# Retrieve services
service = container.get('ModuleName')
```

**Wire up ALL new modules in `modules/setup.py`** via `SystemBuilder.build()` method.

### 2. PromptManager (MANDATORY for AI)
**Use PromptManager for ALL AI/LLM prompts**

```python
from modules.prompt_manager import get_prompt_manager

pm = get_prompt_manager()
prompt = pm.get_prompt('category', 'prompt_name', variables={'key': 'value'})
```

Prompts stored in `packages/prompts/*.json` with templating support.

### 3. Event Bus Pattern
**Use for module communication:**

```python
from modules.bus import EventBus, EventType, Event

bus.emit(Event(EventType.SYSTEM_START, {'data': 'value'}))
bus.on(EventType.CUSTOM, handler_function)
```

## WSL Testing (Quick Reference)

**⚠️ IMPORTANT: Always use Nix in WSL**  
The Nix environment ensures `python-dotenv` and all dependencies are available, so `.env` configuration is properly loaded.

**From Windows PowerShell:**
```powershell
# Recommended: Use helper script with .env loading
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && ./scripts/wsl_test.sh -c status -e"

# Dev shell + test (ensures .env is loaded)
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix develop --extra-experimental-features 'nix-command flakes' --command python3 packages/main.py"

# Test Ollama connectivity
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix develop --extra-experimental-features 'nix-command flakes' --command python3 scripts/test_ollama_connection.py"

# Build and run
wsl -d Ubuntu-24.04 -e bash -lc "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix build --extra-experimental-features 'nix-command flakes' .#aaia && ./result/bin/aaia"
```

**From WSL:**
```bash
cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia

# Use helper script (recommended)
./scripts/wsl_test.sh -c "status" -e

# Or use Nix directly
nix develop --extra-experimental-features "nix-command flakes" --command python3 packages/main.py
```

**Why Nix is Required in WSL:**
- Without Nix: `python-dotenv` not available → `.env` file ignored → uses wrong defaults (`localhost:11434`)
- With Nix: All deps available → `.env` loaded → connects to `http://192.168.178.104:11434` ✅

## CLI Testing (Batch Mode & Automation)

**Non-Interactive Command Execution:**
```bash
# Execute single command and exit
PYTHONPATH=packages python3 packages/main.py -c "status" -e

# Execute multiple commands
PYTHONPATH=packages python3 packages/main.py -c "status" -c "tools" -c "config" -e

# Execute commands from file
PYTHONPATH=packages python3 packages/main.py --cmd-file scripts/commands.txt --autoexit

# With per-command timeout (for AI agent testing)
PYTHONPATH=packages python3 packages/main.py -c "status" -c "diagnose" -e -t 30
```

**Command File Format (scripts/commands.txt):**
```
# Lines starting with # are ignored
status
tools
config
# Empty lines are ignored

goals
```

**CLI Options:**
- `--cmd` / `-c` : Execute command (repeatable)
- `--cmd-file FILE` : Load commands from file (one per line, # for comments)
- `--autoexit` / `-e` : Exit immediately after executing commands
- `--timeout` / `-t SECONDS` : Kill command if it exceeds timeout (exit code 2)

**Testing Patterns:**

```bash
# Quick smoke test
PYTHONPATH=packages python3 packages/main.py -c "status" -e -t 5

# AI agent test suite
PYTHONPATH=packages python3 packages/main.py \
  -c "status" \
  -c "tools" \
  -c "diagnose" \
  -c "goals" \
  -e -t 60

# Config validation in CI/CD
PYTHONPATH=packages python3 packages/main.py -c "config validate" -e -t 10

# Integration test (WSL)
wsl -d Ubuntu-24.04 -e bash -lc \
  'cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && \
   PYTHONPATH=packages python3 packages/main.py -c "status" -e -t 5'
```

**Exit Codes:**
- `0` : Success
- `1` : General error
- `2` : Timeout exceeded

**Notes:**
- Timeout is per-command (each command must complete within timeout)
- Interactive commands (prompting for input) will be killed by timeout
- Use batch mode for automated testing, CI/CD, and AI agent validation
- If no commands provided, enters interactive mode

## File Structure

```
packages/
├── main.py                  # Entry point
├── modules/
│   ├── container.py         # DI Container (MANDATORY)
│   ├── setup.py            # SystemBuilder, wireup (MANDATORY)
│   ├── bus.py              # Event bus
│   ├── prompt_manager.py   # Prompt management (MANDATORY for AI)
│   └── *.py               # Other modules
└── prompts/
    └── *.json             # AI prompts (managed by PromptManager)
```

## Quick Patterns

### New Module Template
```python
class NewModule:
    def __init__(self, dependency_from_container):
        self.dep = dependency_from_container

# Wire in modules/setup.py -> SystemBuilder.build():
container.register('NewModule', 
    lambda c: NewModule(c.get('Dependency')), 
    singleton=True)
```

### Nix-Aware Self-Modification
```python
import subprocess
subprocess.run(['nix', 'build', '.#aaia'], check=True)
```

## Key Constraints
- ❌ **NO direct instantiation** - use DI Container
- ❌ **NO hardcoded prompts** - use PromptManager
- ✅ **Always register** new modules in `setup.py`
- ✅ **Test in WSL** before committing
- Make sure to only use LF as line ending to avoid issues in WSL and Nix environments.
- ⚠️ **No systemd in WSL** - full service testing needs NixOS
- 📍 **WSL Path**: `/mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia`
- 🤖 **Use batch mode** for automated testing and CI/CD pipelines
- ⚠️ **IMPORTANT: Per-implementation phase, create ONLY ONE final markdown summary file**
