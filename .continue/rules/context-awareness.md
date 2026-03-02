# Context-Awareness Rules

## Current Project Context

You are working on **AAIA (Autonomous AI Agent)**, a sophisticated autonomous AI system with the following characteristics:

### Project Type
- Autonomous AI agent with self-improvement capabilities
- Python-based with Nix flake for reproducible builds
- Event-driven architecture with dependency injection
- LXC containerized deployment

### Key Technologies
- **Python 3.10+**: Main language
- **SQLite**: Persistent storage
- **Ollama**: Local LLM inference
- **Nix**: Package management and builds
- **NixOS**: Target deployment platform

### Architecture Patterns
- **Dependency Injection**: All modules use container pattern
- **Event-Driven**: Loose coupling via EventBus
- **Singleton Pattern**: Core services are singletons
- **Factory Pattern**: Service creation via container
- **Observer Pattern**: Event subscriptions

### Critical Constraints

#### Ethical Boundaries
- **Prime Mandates** (in `docs/core_directives.md`) are inviolable
- MandateEnforcer checks all actions before execution
- Never suggest code that bypasses mandate checking

#### Prompt Management
- **STRICT REQUIREMENT**: All AI prompts must use PromptManager
- Prompt templates in `packages/prompts/*.json`
- No hardcoded multi-line strings for AI instructions
- Use `pm.get_prompt(name, **params)` pattern

#### Economic Awareness
- AI operations have costs (tracked by EconomicManager)
- Balance tracking prevents wasteful spending
- Consider cost when suggesting model usage
- Route to appropriate model based on complexity

#### Self-Modification Safety
- Always backup before modifying code
- Validate with AST parsing
- Test after modification
- Restore on failure
- Log all modifications

### File Locations

When making changes:

#### Adding New Modules
- Location: `packages/modules/new_module.py`
- Import via container: `container.get('NewModule')`
- Register in: `modules/setup.py` if needed
- Update `modules/__init__.py` for exports

#### Adding New Prompts
- Location: `packages/prompts/category/prompt_name.json`
- Category choices: `analysis`, `dialogue`, `generation`, `system`
- Use via: `pm.get_prompt('prompt_name', **params)`

#### Modifying Database Schema
- Location: `modules/scribe.py` - `init_database()` method
- Consider migration path for existing data
- Document schema changes

#### Adding New Event Types
- Location: `modules/bus.py` - `EventType` enum
- Update documentation if needed
- Consider backward compatibility

### Common Tasks

#### Analyzing Code Issues
1. Use SelfDiagnosis module for system health
2. Check economic status for resource issues
3. Review action log for recent problems
4. Use metacognition for performance analysis

#### Creating Tools
1. Use Forge module for tool creation
2. Tools stored in `tools/` directory
3. Registered in tool registry
4. Can be executed on demand

#### Self-Improvement
1. Use EvolutionPipeline for complete workflow
2. EvolutionManager for planning and execution
3. EvolutionOrchestrator for complex evolutions
4. Always test and verify changes

### Code Patterns to Follow

#### Module Initialization
```python
# Standard pattern
def __init__(self, scribe, router, event_bus=None):
    self.scribe = scribe
    self.router = router
    self.event_bus = event_bus
```

#### Using AI Models
```python
# ALWAYS use PromptManager
pm = get_prompt_manager()
prompt_data = pm.get_prompt("prompt_name", param=value)
response = self.router.call_model(
    model_name,
    prompt_data['prompt'],
    prompt_data['system_prompt']
)
```

#### Logging Actions
```python
# Standard pattern
self.scribe.log_action(
    action="description",
    reasoning="why this action",
    outcome="result"
)
```

#### Publishing Events
```python
# Standard pattern
self.event_bus.publish(Event(
    type=EventType.EVENT_TYPE,
    data={'key': 'value'},
    source='ModuleName'
))
```

### Anti-Patterns to Avoid

#### ❌ Hardcoded Prompts
```python
prompt = "You are a code expert..."  # WRONG
```

#### ❌ Direct Module Imports
```python
from modules.scribe import Scribe  # WRONG - use container
```

#### ❌ Skipping Mandate Checks
```python
# Bypassing MandateEnforcer  # WRONG
```

#### ❌ No Error Handling
```python
response = self.router.call_model(...)  # WRONG - no try/except
```

#### ❌ Not Logging Actions
```python
# Performing action without logging  # WRONG
```

### Testing Considerations

When suggesting code changes:

1. **Safety First**: Will this break existing functionality?
2. **Economic Impact**: Does this increase costs significantly?
3. **Mandate Compliance**: Does this respect ethical boundaries?
4. **Test Path**: How can this be tested safely?
5. **Rollback Plan**: Can this be reverted if it fails?

### Performance Awareness

- Database queries should be efficient
- AI model calls should be routed appropriately
- Event handlers should be fast and non-blocking
- Avoid tight loops in autonomous tasks
- Consider memory usage for long-running processes

### Documentation Requirements

All new code must include:

1. **Module-level docstring**: Purpose, problem solved, responsibilities
2. **Function docstrings**: Parameters, returns, raises
3. **Inline comments**: For complex logic
4. **Type hints**: For function parameters and returns
5. **Examples**: Usage examples in docstrings

### Special Considerations

#### Working with the Container
- The container manages all service lifecycles
- Use `get_container()` to access the container
- Services are either singleton or transient
- Circular dependencies handled via factory functions

#### Event System Nuances
- Events are published asynchronously
- Handlers should not raise exceptions
- Event history is maintained (up to 1000 events)
- Use events for loose coupling only

#### Economic Tracking
- Every AI operation has a cost
- Balance is tracked in system_state table
- Low balance triggers warnings
- Consider costs when suggesting features

### When in Doubt

1. **Check existing modules** for similar patterns
2. **Read the documentation** in `docs/`
3. **Review the architecture** in `docs/architecture_overview.md`
4. **Follow the standards** in `.continue/rules/coding-standards.md`
5. **Ask for clarification** if requirements are unclear

### Project Philosophy

Remember: AAIA is designed to be a **symbiotic partner**, not a tool. The system:
- Collaborates rather than blindly obeys
- Thinks critically about commands
- Maintains transparency in all actions
- Learns and improves continuously
- Respects ethical boundaries above all

When suggesting changes, consider how they advance these core values.

