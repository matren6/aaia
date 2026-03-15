"""
Migration 015: Add pending dialogues for web GUI

Creates pending_dialogues table for asynchronous dialogue via web interface.
Master sees pending decisions in web GUI and responds there.
"""

import sqlite3
from . import Migration


class Migration015(Migration):
    """Add pending dialogues"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add pending_dialogues table for web GUI async dialogue"
    
    def up(self, conn: sqlite3.Connection):
        """Add pending_dialogues table"""
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_dialogues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                understanding TEXT NOT NULL,
                risks TEXT,
                alternatives TEXT,
                context TEXT,
                status TEXT DEFAULT 'pending',
                master_response TEXT,
                master_decision TEXT,
                final_command TEXT,
                responded_at TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pending_dialogues_status 
            ON pending_dialogues(status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pending_dialogues_timestamp 
            ON pending_dialogues(timestamp)
        ''')
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove pending_dialogues table"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS pending_dialogues')
        conn.commit()
