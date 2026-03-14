"""
Migration 006: Add Mandate Override Tracking

Creates table for tracking mandate overrides:
- mandate_overrides: Log of master override approvals
"""

import sqlite3
from . import Migration


class Migration006(Migration):
    """Add mandate override tracking table"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add mandate_overrides table for tracking master overrides"
    
    def up(self, conn: sqlite3.Connection):
        """Create mandate override tracking table"""
        cursor = conn.cursor()
        
        # Mandate overrides table - audit trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mandate_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                violations TEXT NOT NULL,
                master_confirmed INTEGER DEFAULT 1,
                outcome TEXT,
                notes TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mandate_overrides_timestamp ON mandate_overrides(timestamp DESC)')
    
    def down(self, conn: sqlite3.Connection):
        """Drop mandate override tracking table"""
        cursor = conn.cursor()
        cursor.execute('DROP INDEX IF EXISTS idx_mandate_overrides_timestamp')
        cursor.execute('DROP TABLE IF EXISTS mandate_overrides')
