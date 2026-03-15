#!/usr/bin/env python3
import sys
sys.path.insert(0, 'packages')
from pathlib import Path

# Test with new database
test_db = 'data/test_scribe_new.db'
if Path(test_db).exists():
    Path(test_db).unlink()

print(f'Creating Scribe with new database: {test_db}')
from modules.scribe import Scribe
scribe = Scribe(test_db)

print(f'Logging test action...')
scribe.log_action('test_init', 'Testing initialization', 'SUCCESS', 0.0)

print(f'Verifying write...')
import sqlite3
conn = sqlite3.connect(test_db)
count = conn.execute('SELECT COUNT(*) FROM action_log').fetchone()[0]
conn.close()

print(f'Rows in database: {count}')
if count == 1:
    print('✅ Test passed!')
else:
    print(f'❌ Test failed - expected 1 row, got {count}')
