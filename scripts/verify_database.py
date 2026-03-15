#!/usr/bin/env python3
"""Verify database has valid schema and initialize if needed."""

import sys
import sqlite3
from pathlib import Path

def verify_database(db_path):
    """Verify database exists and has required schema."""
    
    print(f"Checking database: {db_path}")
    
    # Check file exists
    if not Path(db_path).exists():
        print(f"  ❌ File does not exist")
        return False
    
    # Check file size
    size = Path(db_path).stat().st_size
    print(f"  File size: {size} bytes")
    
    if size == 0:
        print(f"  ❌ File is empty (0 bytes)")
        return False
    
    # Check tables
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"  Tables found: {len(tables)}")
        
        required_tables = ['action_log', 'economic_log', 'system_state', 'goals']
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            print(f"  ❌ Missing tables: {missing}")
            conn.close()
            return False
        
        # Check action_log structure
        cursor.execute("PRAGMA table_info(action_log)")
        columns = {row[1] for row in cursor.fetchall()}
        required_cols = {'action', 'reasoning', 'outcome', 'cost'}
        
        if not required_cols.issubset(columns):
            missing_cols = required_cols - columns
            print(f"  ❌ action_log missing columns: {missing_cols}")
            conn.close()
            return False
        
        print(f"  ✅ Schema valid")
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def initialize_database(db_path):
    """Initialize database with migrations."""
    
    print(f"\nInitializing database: {db_path}")
    
    # Add packages to path
    sys.path.insert(0, 'packages')
    
    try:
        from modules.database_manager import DatabaseManager
        
        # Create database manager (will run migrations)
        db_mgr = DatabaseManager(db_path)
        db_mgr.close()
        
        print(f"  ✅ Database initialized")
        return True
        
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/scribe_test.db'
    
    print("=" * 80)
    print("Database Verification Tool")
    print("=" * 80)
    
    if verify_database(db_path):
        print("\n✅ Database is valid")
        sys.exit(0)
    else:
        print("\n❌ Database is invalid or missing schema")
        
        response = input("\nInitialize database with schema? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            if initialize_database(db_path):
                # Verify again
                if verify_database(db_path):
                    print("\n✅ Database successfully initialized")
                    sys.exit(0)
                else:
                    print("\n❌ Initialization failed")
                    sys.exit(1)
            else:
                sys.exit(1)
        else:
            print("Skipping initialization")
            sys.exit(1)
