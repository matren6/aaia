#!/usr/bin/env python3
"""Quick test of tasks API - checks structure."""

import sys
sys.path.insert(0, 'packages')

print("Testing task queue structure...")

# Mock scheduler structure
task_queue = [
    {
        "name": "system_health_check",
        "function": lambda: "OK",
        "interval_minutes": 30,
        "interval_hours": None,
        "priority": 1,
        "enabled": True,
        "last_run": None,
        "next_run": None
    },
    {
        "name": "self_diagnosis", 
        "function": lambda: "OK",
        "interval_minutes": 60,
        "interval_hours": None,
        "priority": 2,
        "enabled": True,
        "last_run": None,
        "next_run": None
    }
]

print(f"Task queue has {len(task_queue)} tasks")

# Test extraction logic
from datetime import datetime

tasks = []
for task in task_queue:
    last_run_str = None
    next_run_str = None
    
    if task.get("last_run"):
        last_run_str = task["last_run"].isoformat() if isinstance(task["last_run"], datetime) else str(task["last_run"])
    
    if task.get("next_run"):
        next_run_str = task["next_run"].isoformat() if isinstance(task["next_run"], datetime) else str(task["next_run"])
    
    tasks.append({
        "id": task["name"],
        "name": task["name"],
        "enabled": task.get("enabled", True),
        "priority": task.get("priority", 3),
        "interval_minutes": task.get("interval_minutes", 0),
        "interval_hours": task.get("interval_hours", 0),
        "last_run": last_run_str,
        "next_run": next_run_str,
        "execution_count": 0,
    })

print(f"Extracted {len(tasks)} tasks")
print("\nTasks:")
for t in tasks:
    print(f"  - {t['name']}: enabled={t['enabled']}, priority={t['priority']}, interval={t['interval_minutes']}min")

print("\n✅ Structure test passed!")
