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

**From Windows PowerShell:**
```powershell
# Build and run
wsl -d Ubuntu-24.04 -e bash -c "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix build .#aaia && ./result/bin/aaia"

# Dev shell + test
wsl -d Ubuntu-24.04 -e bash -c "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix develop -c python packages/main.py"

# Validate imports
wsl -d Ubuntu-24.04 -e bash -c "cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia && nix develop -c python -c 'from modules.bus import EventBus; print(\"OK\")'"
```

**From WSL:**
```bash
cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia
nix build .#aaia && ./result/bin/aaia
```

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
