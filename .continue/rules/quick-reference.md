# Quick Reference - AAIA Codebase

## Common Imports

```python
from modules.bus import EventBus, EventType, Event, get_event_bus
from modules.container import get_container
from modules.scribe import Scribe
from prompts import get_prompt_manager
```

## Standard Patterns

### Get Module from Container
```python
container = get_container()
scribe = container.get('Scribe')
event_bus = container.get('EventBus')
```

### Use PromptManager
```python
pm = get_prompt_manager()
prompt_data = pm.get_prompt('prompt_name', param=value)
```

### Log Action
```python
scribe.log_action(
    action="description",
    reasoning="why",
    outcome="result"
)
```

### Publish Event
```python
event_bus.publish(Event(
    type=EventType.EVENT_TYPE,
    data={},
    source='ModuleName'
))
```

## Module Quick Reference

| Module | Purpose | Key Methods |
|--------|---------|-------------|
| Scribe | Logging & persistence | `log_action()`, `init_database()` |
| EventBus | Event communication | `publish()`, `subscribe()` |
| Container | Dependency injection | `get()`, `register()` |
| Router | Model routing | `route_request()`, `call_model()` |
| Forge | Tool creation | `create_tool()`, `list_tools()` |
| Economics | Cost tracking | `calculate_cost()`, `log_transaction()` |
| Mandates | Safety enforcement | `check_action()` |
| SelfDiagnosis | Health assessment | `perform_full_diagnosis()` |
| SelfModification | Code changes | `modify_module()`, `create_backup()` |

## Prompt Categories

- `analysis/`: Code analysis, system diagnosis
- `dialogue/`: Command understanding, risk analysis
- `generation/`: Code generation, tool creation
- `system/`: Reflection, health checks, strategy

## Event Types

System: `SYSTEM_STARTUP`, `SYSTEM_SHUTDOWN`, `SYSTEM_HEALTH_CHECK`
Economic: `ECONOMIC_TRANSACTION`, `BALANCE_LOW`, `INCOME_GENERATED`
Evolution: `EVOLUTION_STARTED`, `EVOLUTION_COMPLETED`, `EVOLUTION_FAILED`
Tool: `TOOL_CREATED`, `TOOL_LOADED`, `TOOL_ERROR`
Goal: `GOAL_CREATED`, `GOAL_COMPLETED`, `GOAL_FAILED`
Meta: `REFLECTION_STARTED`, `REFLECTION_COMPLETED`
Diagnosis: `DIAGNOSIS_COMPLETED`, `DIAGNOSIS_ACTION_REQUIRED`

## File Locations

- Modules: `packages/modules/`
- Prompts: `packages/prompts/`
- Main entry: `packages/main.py`
- Documentation: `docs/`
- Config: `packages/modules/settings.py`
- Setup: `packages/modules/setup.py`

## Golden Rules

1. ✅ Always use PromptManager for AI prompts
2. ✅ Use dependency injection for modules
3. ✅ Log all actions with reasoning
4. ✅ Publish events for important actions
5. ✅ Handle errors appropriately
6. ✅ Validate configuration before use
7. ✅ Backup before self-modification
8. ✅ Test after code changes
9. ✅ Document your code
10. ✅ Respect the prime mandates

## Common Commands (from main.py)

```
status              - Show system status
economics           - Show economic status
log                 - Show recent actions
tools               - List created tools
auto                - Toggle autonomous mode
tasks               - Show scheduled tasks
goals               - Show current goals
diagnose            - Run system self-diagnosis
evolve              - Run evolution pipeline
pipeline            - Run complete evolution
reflect             - Run meta-cognition reflection
discover            - Discover new capabilities
predict             - Predict master's next commands
explore             - Explore environment
orchestrate         - Run major evolution
strategy            - Optimize evolution strategy
```

## Quick Troubleshooting

**Import Error**: Check Python path includes `packages/`
**Prompt Error**: Verify JSON syntax and required parameters
**Database Error**: Check connection handling and query syntax
**Event Error**: Ensure proper Event structure and EventType
**Container Error**: Check service registration and dependencies

## Need More Help?

- Architecture: `docs/architecture_overview.md`
- Directives: `docs/core_directives.md`
- Standards: `.continue/rules/coding-standards.md`
- Workflow: `.continue/rules/development-workflow.md`
