"""
Migration 014: Add subjective value assessment to economics

Implements Charter principle of Austrian economics with subjective value scoring.
"""

import sqlite3
from . import Migration


class Migration014(Migration):
    """Add subjective value tracking"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add value_to_master columns for Austrian economics"
    
    def up(self, conn: sqlite3.Connection):
        """Add value_to_master columns to economic_transactions table"""
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                ALTER TABLE economic_transactions 
                ADD COLUMN value_to_master REAL DEFAULT NULL
            ''')
        except:
            pass  # Column might already exist
        
        try:
            cursor.execute('''
                ALTER TABLE economic_transactions 
                ADD COLUMN master_goal TEXT DEFAULT NULL
            ''')
        except:
            pass  # Column might already exist
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove value assessment columns"""
        # SQLite doesn't support DROP COLUMN easily
        pass
