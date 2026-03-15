#!/usr/bin/env python3
import sqlite3
import sys

db = sys.argv[1] if len(sys.argv) > 1 else 'data/scribe_test.db'
conn = sqlite3.connect(db)
count = conn.execute('SELECT COUNT(*) FROM action_log').fetchone()[0]
print(f'Rows in {db}: {count}')

if count > 0:
    print('\nLast 10 actions:')
    rows = conn.execute('SELECT timestamp, action, outcome FROM action_log ORDER BY timestamp DESC LIMIT 10').fetchall()
    for row in rows:
        print(f'  [{row[0]}] {row[1]} -> {row[2][:80]}')
conn.close()
