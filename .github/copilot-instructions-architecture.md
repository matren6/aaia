# AAIA Architecture Instructions

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

## Module Registration Example

```python
# In modules/setup.py -> SystemBuilder.build()
def _register_core_services(self):
    """Register all core services in DI container."""
    
    # Simple singleton
    self.container.register('Scribe', Scribe, singleton=True)
    
    # With dependencies
    self.container.register(
        'EconomicManager',
        lambda c: EconomicManager(
            scribe=c.get('Scribe'),
            config=self.config.economics
        ),
        singleton=True
    )
```

## Key Constraints

- ❌ **NEVER** instantiate modules directly
- ❌ **NEVER** hardcode AI prompts in code
- ✅ **ALWAYS** use DI Container for dependencies
- ✅ **ALWAYS** use PromptManager for AI prompts
- ✅ **ALWAYS** register in `modules/setup.py`
