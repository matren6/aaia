#!/usr/bin/env python3
"""Check database schema."""

import sqlite3
import sys

def check_schema(db_path):
    """Check database schema."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Database: {db_path}")
        print("=" * 80)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\nTables found: {len(tables)}")
        for table in tables:
            print(f"\n  Table: {table}")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
            
            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    Rows: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    db = sys.argv[1] if len(sys.argv) > 1 else 'data/scribe.db'
    check_schema(db)
