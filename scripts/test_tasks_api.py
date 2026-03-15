#!/usr/bin/env python3
"""Test tasks API endpoint."""

import sys
import time
sys.path.insert(0, 'packages')

from modules.settings import get_config
from modules.setup import SystemBuilder

print("=" * 80)
print("Testing Tasks API")
print("=" * 80)

# Build system
config = get_config()
builder = SystemBuilder(config)
system = builder.build()
container = system.get('container')

# Get components
scheduler = container.get('AutonomousScheduler')
data_aggregator = container.get('DashboardDataAggregator')

print(f"\n1. Scheduler initialized: {scheduler is not None}")
print(f"   Task queue size: {len(scheduler.task_queue)}")
print(f"   Tasks: {[t['name'] for t in scheduler.task_queue[:5]]}...")

print(f"\n2. Data aggregator initialized: {data_aggregator is not None}")

print(f"\n3. Testing get_tasks()...")
try:
    result = data_aggregator.get_tasks()
    print(f"   Success!")
    print(f"   Total tasks: {result.get('total', 0)}")
    print(f"   Error: {result.get('error', 'None')}")
    
    if result.get('tasks'):
        print(f"\n   First 5 tasks:")
        for task in result['tasks'][:5]:
            print(f"   - {task['name']}: enabled={task['enabled']}, priority={task['priority']}")
    else:
        print(f"   No tasks returned!")
        
except Exception as e:
    print(f"   FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
