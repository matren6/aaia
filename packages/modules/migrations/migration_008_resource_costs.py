"""
Migration 008: Add Resource Cost Tracking

Adds support for tracking CPU, memory, and electricity costs.
Includes resource_costs table and category indexes on economic_log.
"""

import sqlite3
from . import Migration


class Migration008(Migration):
    """Add resource cost tracking"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add resource cost tracking tables and indexes"
    
    def up(self, conn: sqlite3.Connection):
        """Add resource cost support"""
        cursor = conn.cursor()

        # Add category column to economic_log if it doesn't exist
        try:
            cursor.execute('''
                ALTER TABLE economic_log 
                ADD COLUMN category TEXT DEFAULT NULL
            ''')
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Add index on category for efficient filtering
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_economic_log_category 
            ON economic_log(category, timestamp DESC)
        ''')

        # Add resource_costs table for detailed tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                cost REAL NOT NULL,
                metadata TEXT
            )
        ''')

        conn.commit()
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_resource_costs_timestamp 
            ON resource_costs(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_resource_costs_type 
            ON resource_costs(resource_type)
        ''')
    
    def down(self, conn: sqlite3.Connection):
        """Remove resource cost support"""
        cursor = conn.cursor()
        cursor.execute('DROP INDEX IF EXISTS idx_economic_log_category')
        cursor.execute('DROP INDEX IF EXISTS idx_resource_costs_timestamp')
        cursor.execute('DROP INDEX IF EXISTS idx_resource_costs_type')
        cursor.execute('DROP TABLE IF EXISTS resource_costs')
