#!/usr/bin/env python3
"""Analyze action logs from AAIA test database."""

import sqlite3
import sys
from collections import defaultdict

def analyze_logs(db_path='data/scribe_test.db'):
    """Analyze action logs and show statistics."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM action_log')
        total = cursor.fetchone()[0]
        print(f"Total actions logged: {total}")
        print("=" * 80)
        
        # By status
        print("\nActions by Status:")
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM action_log 
            GROUP BY status 
            ORDER BY count DESC
        ''')
        for row in cursor.fetchall():
            print(f"  {row['status']}: {row['count']}")
        
        # By action type
        print("\nTop 20 Actions by Frequency:")
        cursor.execute('''
            SELECT action, status, COUNT(*) as count 
            FROM action_log 
            GROUP BY action, status 
            ORDER BY count DESC 
            LIMIT 20
        ''')
        for row in cursor.fetchall():
            print(f"  {row['action']}: {row['status']} ({row['count']} times)")
        
        # Recent errors
        print("\nRecent Errors (last 20):")
        cursor.execute('''
            SELECT timestamp, action, details 
            FROM action_log 
            WHERE status = 'error' 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        errors = cursor.fetchall()
        if errors:
            for row in errors:
                print(f"\n  [{row['timestamp']}] {row['action']}")
                if row['details']:
                    details = row['details'][:200]
                    print(f"    {details}...")
        else:
            print("  No errors found")
        
        # Recent successful actions
        print("\nRecent Successful Actions (last 10):")
        cursor.execute('''
            SELECT timestamp, action, details 
            FROM action_log 
            WHERE status = 'success' 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        for row in cursor.fetchall():
            print(f"  [{row['timestamp']}] {row['action']}")
            if row['details']:
                details = row['details'][:100]
                print(f"    {details}...")
        
        # Actions with no result
        print("\nActions with 'pending' status:")
        cursor.execute('''
            SELECT COUNT(*) 
            FROM action_log 
            WHERE status = 'pending'
        ''')
        pending = cursor.fetchone()[0]
        print(f"  {pending} pending actions")
        
        conn.close()
        
    except Exception as e:
        print(f"Error analyzing logs: {e}")
        sys.exit(1)

if __name__ == '__main__':
    db = sys.argv[1] if len(sys.argv) > 1 else 'data/scribe_test.db'
    analyze_logs(db)
