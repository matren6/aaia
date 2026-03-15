#!/usr/bin/env python3
"""Test database migrations"""

import sys
import os

# Add packages to path
sys.path.insert(0, 'packages')

from modules.database_manager import DatabaseManager

print("Testing database migrations...")
print("=" * 80)

# Remove old test database
test_db = 'data/scribe_test.db'
if os.path.exists(test_db):
    print(f"Removing old test database: {test_db}")
    os.remove(test_db)

try:
    print(f"\nInitializing database: {test_db}")
    db = DatabaseManager(test_db)
    
    print("\n✅ Database initialized successfully!")
    
    # Check schema version
    result = db.query_one("SELECT MAX(version) as version FROM schema_version")
    version = result['version'] if result else 0
    print(f"✅ Current schema version: {version}")
    
    # List all migrations applied
    rows = db.query("SELECT version, description, applied_at FROM schema_version ORDER BY version")
    print(f"\n📋 Applied migrations ({len(rows)}):")
    for row in rows:
        print(f"   {row['version']:2d}. {row['description']} ({row['applied_at']})")
    
    # List all tables
    tables = db.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    print(f"\n📊 Tables created ({len(tables)}):")
    for table in tables:
        # Count rows
        count_result = db.query_one(f"SELECT COUNT(*) as count FROM {table['name']}")
        count = count_result['count'] if count_result else 0
        print(f"   - {table['name']}: {count} rows")
    
    print("\n" + "=" * 80)
    print("✅ All migrations completed successfully!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
