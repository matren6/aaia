"""
Migration 011: Add dialogue outcomes tracking table

Tracks effectiveness of structured dialogue protocol.
"""

import sqlite3
from . import Migration


class Migration011(Migration):
    """Add dialogue outcomes tracking"""

    def __init__(self):
        super().__init__()
        self.description = "Add dialogue_outcomes table for effectiveness tracking"

    def up(self, conn: sqlite3.Connection):
        """Add dialogue_outcomes table"""
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialogue_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                risks_count INTEGER DEFAULT 0,
                alternatives_count INTEGER DEFAULT 0,
                master_decision TEXT,
                outcome_success INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dialogue_timestamp 
            ON dialogue_outcomes(timestamp)
        ''')

        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove dialogue_outcomes table"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS dialogue_outcomes')
        conn.commit()
