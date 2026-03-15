#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('data/scribe.db')
count = conn.execute('SELECT COUNT(*) FROM action_log').fetchone()[0]
print(f'Total rows in action_log: {count}')

if count > 0:
    print('\nLast 5 actions:')
    rows = conn.execute('SELECT timestamp, action, outcome FROM action_log ORDER BY timestamp DESC LIMIT 5').fetchall()
    for row in rows:
        print(f'  [{row[0]}] {row[1]} -> {row[2][:50]}')
conn.close()
