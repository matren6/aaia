#!/usr/bin/env python3
"""Check schema version"""

import sqlite3

conn = sqlite3.connect("data/scribe_test.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM schema_version ORDER BY version")
for row in cursor.fetchall():
    print(f"Version {row[0]}: {row[2]} (applied at {row[1]})")
conn.close()
