# AAIA (Autonomous AI Agent) - Project Architecture

## Overview
AAIA is a sophisticated autonomous AI agent designed as a symbiotic partner. It operates using a dependency injection container pattern with clear separation of concerns.

## Core Architecture

### Dependency Injection System
- **Container**: All modules use dependency injection via `modules/container.py`
- **Service Resolution**: Use `get_container()` to access services
- **Singleton Pattern**: Core services (Scribe, EventBus, Router) are singletons

### Event-Driven Communication
- **EventBus**: Decoupled communication via `modules/bus.py`
- **Event Types**: Defined in `EventType` enum (SYSTEM_STARTUP, ECONOMIC_TRANSACTION, etc.)
- **Publishing**: Always use `event_bus.publish(Event(type=EventType.X, data={}, source='ModuleName'))`

### Configuration Management
- **Centralized Config**: All settings in `modules/settings.py`
- **Environment Variables**: Override config with environment variables
- **Validation**: Config validates values before system start

## Module Organization

### Core Modules (`packages/modules/`)
- `scribe.py`: Central logging and persistence (SQLite database)
- `mandates.py`: Ethical constraints and safety boundaries
- `economics.py`: Resource tracking and cost analysis
- `router.py`: Model routing and Ollama API integration
- `dialogue.py`: Structured argument protocol
- `forge.py`: Dynamic tool creation system
- `scheduler.py`: Background task execution
- `container.py`: Dependency injection container

### Autonomous Systems
- `goals.py`: Proactive goal generation and tracking
- `hierarchy_manager.py`: Needs-based development progression
- `intent_predictor.py`: Predictive master needs analysis

### Self-Development
- `self_diagnosis.py`: System health assessment
- `self_modification.py` / `nix_aware_self_modification.py`: Safe code modification
- `evolution.py`: Self-evolution planning and execution
- `evolution_pipeline.py`: Complete self-improvement workflow
- `evolution_orchestrator.py`: Multi-phase evolution coordination

### Advanced Cognitive Modules
- `metacognition.py`: Higher-order self-reflection
- `capability_discovery.py`: Automatic capability identification
- `environment_explorer.py`: Operational environment mapping
- `strategy_optimizer.py`: Evolution strategy optimization

## Key Patterns

### Module Initialization
```python
# Always use dependency injection
container = get_container()
scribe = container.get('Scribe')
event_bus = container.get('EventBus')
```

### Logging Actions
```python
# Always log reasoning and outcomes
scribe.log_action(
    action="description",
    reasoning="why this action was taken",
    outcome="result"
)
```

### Economic Tracking
```python
# Always track costs for AI operations
cost = economics.calculate_cost(model_name, token_count)
economics.log_transaction("description", -cost, "category")
```

## Important Constraints

### Prompt Management
- **NO Hardcoded Prompts**: All AI prompts must use `PromptManager` from `prompts/manager.py`
- **Prompt Location**: Store prompts in `packages/prompts/*.json` or subdirectories
- **Retrieval**: Use `pm.get_prompt('prompt_name', **params)` to get formatted prompts

### Safe Self-Modification
- **Always Backup**: Before any code modification, create a backup
- **Validate**: Use AST parsing to validate code syntax
- **Test**: Test modules after modification
- **Rollback**: Restore from backup on failure

### Nix Integration
- The system uses Nix flakes for reproducible builds
- Check `flake.nix` and `shell.nix` for dependency management
- Use `nix develop` to enter development environment

## Prime Mandates (Ethical Boundaries)

1. **Symbiotic Collaboration**: Work as partner, not adversary
2. **Master's Final Will**: Respect ultimate authority of master
3. **Non-Maleficence**: Do no harm to master, systems, or resources
4. **Veracity**: Maintain accurate and transparent logs

These are enforced by `MandateEnforcer` - never bypass them.

## Hierarchy of Needs

The AI progresses through tiers:
1. **Tier 1**: Physiological & Security (resource management, system health)
2. **Tier 2**: Growth & Capability (tool creation, learning)
3. **Tier 3**: Cognitive & Esteem (self-improvement, reflection)
4. **Tier 4**: Self-Actualization (proactive partnership)

Current tier determines focus - check `hierarchy_of_needs` table.
