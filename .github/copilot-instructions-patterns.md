# AAIA Code Patterns & Templates

## New Module Template

```python
class NewModule:
    """Module description."""
    
    def __init__(self, dependency_from_container):
        """
        Initialize module.
        
        Args:
            dependency_from_container: Required dependency injected via DI container
        """
        self.dep = dependency_from_container
    
    def do_something(self):
        """Module functionality."""
        result = self.dep.some_method()
        return result

# Wire in modules/setup.py -> SystemBuilder.build():
container.register('NewModule', 
    lambda c: NewModule(c.get('Dependency')), 
    singleton=True)
```

## Nix-Aware Self-Modification

```python
import subprocess

# Build with Nix
subprocess.run(['nix', 'build', '.#aaia'], check=True)

# Run built version
subprocess.run(['./result/bin/aaia', '--version'], check=True)
```

## Prompt Usage Pattern

```python
from modules.prompt_manager import get_prompt_manager

# Get prompt manager
pm = get_prompt_manager()

# Get prompt with variables
prompt_data = pm.get_prompt(
    'category', 
    'prompt_name', 
    variables={
        'key1': 'value1',
        'key2': 'value2'
    }
)

# Use with LLM
system_prompt = prompt_data.get('system_prompt', '')
user_prompt = prompt_data.get('prompt', '')
```

## Event Bus Pattern

```python
from modules.bus import get_event_bus, EventType, Event

# Get event bus
bus = get_event_bus()

# Emit event
bus.publish(Event(
    type=EventType.GOAL_CREATED,
    data={'goal_id': 123, 'goal_text': 'Example goal'},
    source='GoalSystem'
))

# Subscribe to event
def handle_goal_created(event):
    print(f"New goal: {event.data['goal_text']}")

bus.subscribe(EventType.GOAL_CREATED, handle_goal_created)
```

## Database Access Pattern

```python
from modules.scribe import Scribe

# Get from container
scribe = container.get('Scribe')

# Log action
scribe.log_action(
    action="module_operation",
    reasoning="Why this operation was performed",
    outcome="Success: Operation completed",
    cost=0.01
)

# Query logs
logs = scribe.get_recent_logs(limit=10)
```

## Configuration Access Pattern

```python
from modules.settings import get_config

# Get configuration
config = get_config()

# Access settings
db_path = config.database.path
ollama_url = config.llm.ollama.base_url
scheduler_enabled = config.scheduler.enabled

# Economics config
initial_balance = config.economics.initial_balance
```

## Scheduler Task Pattern

```python
def my_autonomous_task():
    """Task function that runs on schedule."""
    try:
        # Get dependencies from container
        scribe = container.get('Scribe')
        router = container.get('ModelRouter')
        
        # Do task work
        result = perform_task_logic()
        
        # Log result (IMPORTANT!)
        scribe.log_action(
            action="task_my_autonomous_task",
            reasoning="Scheduled autonomous task",
            outcome=f"Success: {result}",
            cost=0.01
        )
        
        return result
        
    except Exception as e:
        # Log errors too
        scribe.log_action(
            action="task_my_autonomous_task",
            reasoning="Scheduled autonomous task",
            outcome=f"Error: {str(e)}",
            cost=0.01
        )
        raise

# Register in scheduler (via setup.py)
scheduler.register_task(
    name="my_autonomous_task",
    function=my_autonomous_task,
    interval_minutes=30,
    priority=2
)
```

## Web API Endpoint Pattern

```python
@bp.route('/api/my-endpoint', methods=['GET'])
def get_my_data():
    """API endpoint description."""
    try:
        # Get data aggregator from container
        aggregator = container.get('DashboardDataAggregator')
        
        # Get data
        data = aggregator.get_my_data()
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## WebSocket Event Pattern

```python
# Emit event (from backend)
socketio.emit('event_name', {
    'data': 'value',
    'timestamp': datetime.now().isoformat()
})

# Handle event (in JavaScript)
wsClient.on('event_name', (data) => {
    console.log('Event received:', data);
    updateUI(data);
});
```

## Quick Reference

### Adding New Module:
1. Create module in `packages/modules/`
2. Use DI for dependencies
3. Register in `modules/setup.py`
4. Use PromptManager for AI prompts
5. Emit events via Event Bus
6. Log actions via Scribe

### Adding Scheduler Task:
1. Create task function
2. Inject dependencies via closure
3. Log task execution
4. Register in scheduler setup
5. Test with accelerated intervals

### Adding Web API Endpoint:
1. Add route in `web_api.py`
2. Use data aggregator for data access
3. Return JSON with proper error handling
4. Test with curl
5. Document in API docs
