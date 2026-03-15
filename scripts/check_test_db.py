#!/usr/bin/env python3
"""Check test database structure and content"""

import sqlite3
import sys

db_path = "data/scribe_test.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Checking database: {db_path}")
    print("=" * 80)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\nTables found: {len(tables)}")
    for table in tables:
        table_name = table[0]
        print(f"\n  Table: {table_name}")
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"    Rows: {count}")
        
        # Get schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"    Columns:")
        for col in columns:
            print(f"      - {col[1]} ({col[2]})")
    
    # Check for master_interactions specifically
    print("\n" + "=" * 80)
    print("Master Interactions:")
    cursor.execute("SELECT COUNT(*) FROM master_interactions")
    count = cursor.fetchone()[0]
    print(f"  Total interactions: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM master_interactions ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        print("\n  Recent interactions:")
        for row in rows:
            print(f"    {row}")
    
    # Check action_log
    print("\n" + "=" * 80)
    print("Action Log:")
    cursor.execute("SELECT COUNT(*) FROM action_log")
    count = cursor.fetchone()[0]
    print(f"  Total actions: {count}")
    
    if count > 0:
        cursor.execute("SELECT timestamp, action, outcome FROM action_log ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        print("\n  Recent actions:")
        for row in rows:
            print(f"    {row[0]}: {row[1]} -> {row[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
