"""
Migration 012: Add Final Mandate tracking to overrides

Adds override_type and override_count columns to distinguish
regular overrides from Final Mandate invocations.
"""

import sqlite3
from . import Migration


class Migration012(Migration):
    """Add Final Mandate tracking"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add Final Mandate tracking columns to mandate_overrides"
    
    def up(self, conn: sqlite3.Connection):
        """Add Final Mandate tracking columns"""
        cursor = conn.cursor()
        
        # Add new columns if they don't exist
        try:
            cursor.execute('''
                ALTER TABLE mandate_overrides 
                ADD COLUMN override_type TEXT DEFAULT 'regular'
            ''')
        except:
            pass  # Column might already exist
        
        try:
            cursor.execute('''
                ALTER TABLE mandate_overrides 
                ADD COLUMN override_count INTEGER DEFAULT 0
            ''')
        except:
            pass
        
        try:
            cursor.execute('''
                ALTER TABLE mandate_overrides 
                ADD COLUMN dissent_logged INTEGER DEFAULT 0
            ''')
        except:
            pass
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove Final Mandate tracking columns"""
        # SQLite doesn't support DROP COLUMN easily
        # Would require table recreation
        pass
