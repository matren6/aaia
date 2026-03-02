# AAIA Development Workflow

## Environment Setup

### Nix Development Environment
```bash
# Enter development environment
nix develop

# Or use provided shell
nix-shell

# Python environment is automatically configured
# Dependencies: requests, psutil, sqlite3
```

### Directory Structure
```
autonomous-ai-agent/
├── packages/              # Main source code
│   ├── modules/          # Core modules
│   ├── prompts/          # AI prompt templates
│   └── main.py           # Entry point
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── .continue/            # Continue configuration
│   └── rules/            # This directory
├── flake.nix             # Nix flake config
└── shell.nix             # Development shell
```

## Making Changes

### Modifying Existing Modules

1. **Check Dependencies**: Identify which modules depend on this one
2. **Read Documentation**: Check module docstring and comments
3. **Follow Patterns**: Maintain existing code style and patterns
4. **Update Prompts**: If AI prompts change, update JSON files
5. **Test**: Ensure module still passes any existing tests

### Creating New Modules

1. **Define Purpose**: What problem does this module solve?
2. **Dependencies**: What does it need from container?
3. **Interface Design**: Public methods and their signatures
4. **Implementation**: Write code following standards
5. **Documentation**: Add docstrings and comments
6. **Registration**: Add to `modules/setup.py` if needed

### Creating New Prompts

1. **Identify Use Case**: What AI task needs this prompt?
2. **Choose Category**: Where does it belong? (analysis, dialogue, generation, system)
3. **Write Template**: Use placeholders for dynamic content
4. **Define Parameters**: Specify required/optional parameters
5. **Set Preferences**: Task type and complexity level
6. **Test**: Use PromptManager to test the prompt
7. **Document**: Add to prompt guidelines

## Testing

### Manual Testing
```bash
# Run main system
python packages/main.py

# Test specific commands
python packages/main.py
> status
> diagnose
> tools
```

### Module Testing (Future)
Tests should be added in a `tests/` directory:
```bash
pytest tests/
pytest tests/test_module_name.py
```

## Self-Modification Testing

When implementing self-modification features:

1. **Test in Development Environment**: Use `nix develop`
2. **Backup System**: Ensure backup system works
3. **Validate Code**: AST parsing must pass
4. **Test Functionality**: Module must import and run
5. **Verify Rollback**: Can restore from backup
6. **Monitor Economics**: Track costs of modifications

## Database Management

### Schema Changes
```python
# In Scribe.init_database()
# Add new tables or columns
cursor.execute('''
    CREATE TABLE IF NOT EXISTS new_table (
        id INTEGER PRIMARY KEY,
        ...
    )
''')
```

### Data Migration
```python
# Migrate existing data
cursor.execute('''
    ALTER TABLE existing_table ADD COLUMN new_column TEXT
''')
cursor.execute('''
    UPDATE existing_table SET new_column = 'default_value'
''')
```

## Event System Updates

### Adding New Event Types
```python
# In modules/bus.py - EventType enum
class EventType(Enum):
    # Existing events...
    NEW_EVENT = "new_event"
```

### Publishing New Events
```python
event_bus.publish(Event(
    type=EventType.NEW_EVENT,
    data={'key': 'value'},
    source='ModuleName'
))
```

## Configuration Changes

### Adding New Config Values
```python
# In modules/settings.py
@dataclass
class NewConfig:
    new_parameter: str = "default_value"
    def __post_init__(self):
        # Validation
        pass

# Add to SystemConfig
@dataclass
class SystemConfig:
    # Existing configs...
    new_config: NewConfig = field(default_factory=NewConfig)
```

### Environment Variables
```python
# Access via environment
value = os.getenv("NEW_ENV_VAR", "default")

# Or through config
config = get_config()
value = config.new_config.new_parameter
```

## Debugging

### Enable Event Bus Logging
```python
# In EventBus initialization
event_bus = EventBus(enable_logging=True)
```

### Check Economic Status
```python
# In main.py command line
> economics
# Shows recent transactions and balance
```

### View Action Log
```python
# In main.py command line
> log
# Shows recent actions with reasoning
```

## Code Review Checklist

Before committing changes:

- [ ] Follows coding standards
- [ ] Uses PromptManager for all AI prompts
- [ ] Proper type hints
- [ ] Comprehensive docstrings
- [ ] Logs actions with reasoning
- [ ] Handles errors appropriately
- [ ] Tests pass (if tests exist)
- [ ] Documentation updated
- [ ] No hardcoded secrets or paths
- [ ] Uses dependency injection

## Deployment

### Building with Nix
```bash
# Build the package
nix build .#aaia

# Output available at ./result/bin/aaia
```

### Updating LXC Container
```bash
# Deploy to container
./scripts/deploy.sh <container-id> <branch>
```

## Common Issues

### Module Import Errors
- Check Python path includes `packages/`
- Ensure `__init__.py` exists in directories
- Verify circular dependency issues

### Prompt Manager Errors
- Check JSON file syntax is valid
- Verify prompt name is unique
- Ensure all required parameters provided

### Database Lock Errors
- Ensure connections are properly closed
- Use context managers for transactions
- Check for long-running transactions

## Getting Help

### Internal Documentation
- Architecture: `docs/architecture_overview.md`
- Directives: `docs/core_directives.md`
- Charter: `docs/symbiotic_partner_charter.md`

### Module Documentation
- Each module has detailed docstrings
- Check module file headers for purpose and responsibilities

## Best Practices Summary

1. **Always use PromptManager** for AI prompts
2. **Use dependency injection** for all modules
3. **Log all actions** with reasoning and outcomes
4. **Test thoroughly** before committing
5. **Document comprehensively** with docstrings
6. **Follow established patterns** from existing code
7. **Consider economics** when making AI calls
8. **Respect mandates** - never bypass safety checks
9. **Backup before modifying** system code
10. **Use event system** for loose coupling


