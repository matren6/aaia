#!/usr/bin/env python3
"""Update production database to latest schema"""

import sys
import os

sys.path.insert(0, 'packages')

from modules.database_manager import DatabaseManager

# Production database path
PROD_DB = os.path.expanduser('~/.local/share/aaia/scribe.db')

print(f"Updating production database: {PROD_DB}")
print("=" * 80)

if not os.path.exists(PROD_DB):
    print(f"Database doesn't exist yet at {PROD_DB}")
    print("It will be created with latest schema on first run.")
    sys.exit(0)

try:
    # Initialize database manager - this will run migrations
    db = DatabaseManager(PROD_DB)
    
    # Check current version
    result = db.query_one("SELECT MAX(version) as version FROM schema_version")
    version = result['version'] if result else 0
    
    print(f"✅ Database updated successfully!")
    print(f"✅ Current schema version: {version}")
    
    # List applied migrations
    rows = db.query("SELECT version, description FROM schema_version ORDER BY version")
    print(f"\n📋 Applied migrations ({len(rows)}):")
    for row in rows:
        print(f"   {row['version']:2d}. {row['description']}")
    
    print("\n" + "=" * 80)
    print("✅ Production database is up to date!")
    
except Exception as e:
    print(f"❌ Error updating database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
