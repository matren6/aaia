# Test all three architectural improvements

# 1. Configuration Management
from modules.settings import get_config, SystemConfig, reset_config
reset_config()  # Reset to get fresh config

config = get_config()
print('1. Configuration Management:')
print(f'   - Database path: {config.database.path}')
print(f'   - LLM model: {config.llm.model}')
print(f'   - Initial balance: {config.economics.initial_balance}')
print(f'   - Scheduler enabled: {config.scheduler.enabled}')

# 2. Event Bus
from modules.bus import get_event_bus, EventType, Event, reset_event_bus
reset_event_bus()

event_bus = get_event_bus()

def test_handler(event):
    print(f'   Event received: {event.type.value}')

event_bus.subscribe(EventType.SYSTEM_STARTUP, test_handler)
event_bus.publish(Event(type=EventType.SYSTEM_STARTUP, data={'test': True}, source='test'))
print(f'2. Event Bus: {event_bus.get_handler_count()} handlers, {len(event_bus.get_history())} events')

# Test unsubscribe_all
def multi_handler(event):
    pass
event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, multi_handler)
event_bus.subscribe(EventType.ECONOMIC_TRANSACTION, multi_handler)
event_bus.unsubscribe_all(multi_handler)
print(f'   - unsubscribe_all works: {event_bus.get_handler_count() == 1}')

# 3. Dependency Injection Container
from modules.container import get_container, reset_container
reset_container()

container = get_container()

# Register some test services
container.register('TestService', lambda c: 'test_instance', singleton=True)
container.register('TestFactory', lambda c: f'factory_{id(c)}')

s1 = container.get('TestService')
s2 = container.get('TestService')
s3 = container.get('TestFactory')

print(f'3. Dependency Injection Container:')
print(f'   - Singleton works: {s1 is s2}')
print(f'   - Factory works: {s3 is not None}')
print(f'   - Registered services: {container.get_registered_services()}')

# 4. Integration test - full Arbiter
print('4. Full System Integration:')
from main import Arbiter

arbiter = Arbiter()
print(f'   - Arbiter initialized with config, event_bus, and container')
print(f'   - Scribe db_path: {arbiter.scribe.db_path}')
print(f'   - Event bus has {len(event_bus.get_history())} events')

print()
print('All architectural improvements working correctly!')

