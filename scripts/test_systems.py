#!/usr/bin/env python3
"""Test if AAIA core systems are working."""

import sys
sys.path.insert(0, 'packages')

from pathlib import Path
from modules.settings import get_config, SystemConfig

print("=" * 80)
print("AAIA System Test")
print("=" * 80)

# 1. Check configuration
print("\n1. Configuration Check:")
config = get_config()
print(f"   Database path: {config.database.path}")
print(f"   DB exists: {Path(config.database.path).exists()}")
print(f"   DB size: {Path(config.database.path).stat().st_size if Path(config.database.path).exists() else 0} bytes")
print(f"   Scheduler enabled: {config.scheduler.enabled}")

# 2. Test Scribe
print("\n2. Scribe Test:")
try:
    from modules.scribe import Scribe
    scribe = Scribe(db_path=config.database.path)
    
    print("   Writing test action...")
    scribe.log(
        action="system_test",
        reasoning="Testing if Scribe writes to database",
        outcome="success",
        cost=0.0
    )
    
    print("   Reading back...")
    logs = scribe.get_recent_logs(limit=1)
    if logs:
        print(f"   ✅ Success! Found {len(logs)} log(s)")
        print(f"      Latest: {logs[0][1]} -> {logs[0][3]}")
    else:
        print("   ❌ FAIL: No logs found after write!")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# 3. Test EconomicManager
print("\n3. Economics Test:")
try:
    from modules.economics import EconomicManager
    from modules.scribe import Scribe
    
    scribe = Scribe(db_path=config.database.path)
    economics = EconomicManager(scribe=scribe, config=config.economics)
    
    balance = economics.get_current_balance()
    print(f"   Current balance: ${balance}")
    
    print("   Recording test transaction...")
    economics.record_income(amount=1.0, description="Test income")
    new_balance = economics.get_current_balance()
    print(f"   New balance: ${new_balance}")
    
    if new_balance > balance:
        print(f"   ✅ Success! Balance increased by ${new_balance - balance}")
    else:
        print(f"   ❌ FAIL: Balance did not increase!")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# 4. Check database tables
print("\n4. Database Tables Check:")
try:
    import sqlite3
    conn = sqlite3.connect(config.database.path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"   Tables: {len(tables)}")
    
    for table in ['action_log', 'economic_log', 'system_state', 'goals']:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} rows")
        else:
            print(f"   {table}: NOT FOUND!")
    
    conn.close()
    
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
