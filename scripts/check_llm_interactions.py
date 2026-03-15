#!/usr/bin/env python3
"""Check LLM interactions in database"""
import sqlite3
import os

db_path = os.path.expanduser('~/.local/share/aaia/scribe.db')
print(f"Checking: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llm_interactions'")
    if not cursor.fetchone():
        print("❌ llm_interactions table does NOT exist")
        conn.close()
        exit(1)
    
    # Count interactions
    cursor.execute("SELECT COUNT(*) FROM llm_interactions")
    count = cursor.fetchone()[0]
    print(f"✅ llm_interactions table exists")
    print(f"   Total interactions: {count}")
    
    if count > 0:
        cursor.execute("SELECT timestamp, provider, model, LEFT(prompt, 50) as prompt_preview FROM llm_interactions ORDER BY timestamp DESC LIMIT 5")
        print("\n   Recent interactions:")
        for row in cursor.fetchall():
            print(f"   - {row[0]} | {row[1]}/{row[2]} | {row[3]}...")
    else:
        print("   ⚠️  No interactions logged yet")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
