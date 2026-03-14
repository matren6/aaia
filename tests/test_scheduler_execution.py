import os
import time
import sqlite3

# Ensure packages in path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from modules.scribe import Scribe
from modules.prompt_manager import PromptManager
from modules.scheduler import AutonomousScheduler

# Minimal stubs
class DummyRouter:
    pass

class DummyEconomics:
    def __init__(self):
        pass
    def get_balance(self):
        return 100.0

class DummyForge:
    pass


def run_minimal_scheduler_test():
    # Prepare test DB
    test_db = 'data/test_scribe.db'
    if os.path.exists(test_db):
        os.remove(test_db)

    scribe = Scribe(db_path=test_db)
    prompt_manager = PromptManager()  # uses prompts dir; safe

    router = DummyRouter()
    economics = DummyEconomics()
    forge = DummyForge()

    # Create scheduler
    scheduler = AutonomousScheduler(scribe, router, economics, forge, prompt_manager=prompt_manager)

    print('Initial registered tasks:', [t['name'] for t in scheduler.task_queue])

    # Register a simple task that logs an action
    executed = {'count': 0}

    def test_task():
        executed['count'] += 1
        scribe.log_action('test_task_executed', 'minimal test task ran', 'ok')
        return 'ok'

    # Register with immediate run
    scheduler.register_task(name='test_task', function=test_task, interval_minutes=1, priority=1)

    print('Tasks after registering test_task:', [t['name'] for t in scheduler.task_queue])

    # Start scheduler
    scheduler.start()

    # Wait enough time to allow first loop to run (default tasks may block briefly)
    time.sleep(15)

    # Stop scheduler
    scheduler.stop()

    # Check DB for action
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM action_log WHERE action = 'test_task_executed'")
    count = cursor.fetchone()[0]
    conn.close()

    print('Executed count variable:', executed['count'])
    print('Action log count:', count)

    assert executed['count'] >= 1, 'Task function not executed'
    assert count >= 1, 'Action not logged in DB'


if __name__ == '__main__':
    run_minimal_scheduler_test()
    print('Minimal scheduler execution test passed')
