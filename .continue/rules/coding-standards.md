# AAIA Coding Standards

## Language and Style

### Python Standards
- **Python 3.10+**: Use type hints extensively
- **PEP 8**: Follow PEP 8 style guidelines
- **Docstrings**: All public functions must have docstrings
- **Type Annotations**: Use `typing` module for complex types

### Module Structure
```python
"""
Module purpose description.

PROBLEM SOLVED:
What problem does this module solve?

KEY RESPONSIBILITIES:
1. responsibility_1
2. responsibility_2

DEPENDENCIES: List of dependencies
OUTPUTS: What this module produces
"""

from typing import Dict, List, Optional
from .base_module import BaseModule

class MyModule:
    """Brief description."""
    
    def __init__(self, dependency: BaseModule):
        """Initialize with dependency injection."""
        self.dependency = dependency
```

## Prompt Management Rules

### NEVER Hardcode Prompts
❌ BAD:
```python
prompt = """
You are a code expert. Analyze this code:
{code}
"""
response = router.call_model(model_name, prompt)
```

✅ GOOD:
```python
from prompts import get_prompt_manager

pm = get_prompt_manager()
prompt_data = pm.get_prompt(
    "code_analysis",
    code=code_snippet,
    complexity="high"
)
response = router.call_model(
    model_name,
    prompt_data['prompt'],
    prompt_data['system_prompt']
)
```

### Creating New Prompts
1. Create JSON file in `packages/prompts/` or subdirectory
2. Follow prompt structure:
```json
{
  "name": "prompt_name",
  "description": "What this prompt does",
  "template": "Template with {placeholders}",
  "parameters": [
    {"name": "placeholder", "type": "string", "required": true}
  ],
  "system_prompt": "You are a [role]...",
  "model_preferences": {
    "task_type": "coding",
    "complexity": "high"
  }
}
```
3. Register in appropriate category subdirectory

## Event System Usage

### Publishing Events
```python
from modules.bus import Event, EventType

event_bus.publish(Event(
    type=EventType.SYSTEM_STARTUP,
    data={'key': 'value'},
    source='ModuleName'
))
```

### Subscribing to Events
```python
def my_handler(event: Event):
    # Handle event
    pass

event_bus.subscribe(EventType.ECONOMIC_TRANSACTION, my_handler)
```

## Error Handling

### Database Operations
```python
try:
    conn = sqlite3.connect(self.scribe.db_path)
    cursor = conn.cursor()
    cursor.execute("...")
    conn.commit()
except sqlite3.Error as e:
    self.scribe.log_action("Operation failed", str(e), "error")
    raise
finally:
    conn.close()
```

### AI Model Calls
```python
try:
    model_name, _ = self.router.route_request(task_type, complexity)
    response = self.router.call_model(model_name, prompt, system_prompt)
except Exception as e:
    self.scribe.log_action("AI call failed", str(e), "error")
    # Handle failure appropriately
```

## Testing

### Module Testing
- Each module should have corresponding test file
- Test directory: `tests/` (to be created)
- Use pytest framework
- Mock external dependencies (router, database)

### Self-Modification Testing
```python
# Always test after self-modification
if self.test_module(module_name):
    # Success
    pass
else:
    # Restore backup
    self.restore_backup(module_name)
```

## Safety Practices

### Self-Modification Checklist
1. ✅ Create backup before modification
2. ✅ Validate code syntax with AST parsing
3. ✅ Test module functionality
4. ✅ Restore on failure
5. ✅ Log all modifications

### Economic Awareness
```python
# Check balance before expensive operations
balance = self.economics.get_current_balance()
if balance < threshold:
    # Use cheaper model or defer operation
    pass
```

## Code Organization

### File Naming
- Use snake_case: `my_module.py`
- Test files: `test_my_module.py`
- Configuration: `settings.py`, `setup.py`

### Import Order
1. Standard library
2. Third-party imports
3. Local imports (from modules...)
4. Relative imports (from .)

### Class Design
- Single Responsibility Principle
- Dependency injection over hard dependencies
- Clear separation of concerns
- Comprehensive docstrings

## Performance Considerations

### Database Queries
- Use parameterized queries to prevent SQL injection
- Index frequently queried columns
- Batch operations when possible
- Close connections properly

### AI Model Usage
- Route requests based on complexity
- Use cheaper models for simple tasks
- Cache responses when appropriate
- Track costs for all calls

## Documentation

### Module Documentation
Each module file should start with:
- Purpose statement
- Problem solved
- Key responsibilities
- Dependencies
- Outputs

### Function Documentation
```python
def function_name(param1: str, param2: int) -> Dict:
    """
    Brief description.
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Dictionary with keys...
        
    Raises:
        ValueError: When...
    """
    pass
```
