"""
Migration 009: Add Safety Lockout Tracking

Creates table for tracking catastrophic risk safety lockouts:
- safety_lockouts: Log of safety lockout situations requiring explicit master acknowledgment
"""

import sqlite3
from . import Migration


class Migration009(Migration):
    """Add safety_lockouts table for catastrophic risk management"""

    def __init__(self):
        super().__init__()
        self.description = "Add safety_lockouts table for catastrophic risk acknowledgment"
    
    def up(self, conn: sqlite3.Connection):
        """Create safety lockout tracking table"""
        cursor = conn.cursor()
        
        # Safety lockouts table - tracks catastrophic risks requiring explicit acknowledgment
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS safety_lockouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                violations TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                acknowledge_timestamp TEXT,
                master_response TEXT
            )
        ''')
        
        # Create indexes for efficient querying
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_safety_lockouts_timestamp ON safety_lockouts(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_safety_lockouts_acknowledged ON safety_lockouts(acknowledged)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_safety_lockouts_active ON safety_lockouts(acknowledged) WHERE acknowledged = 0')
    
    def down(self, conn: sqlite3.Connection):
        """Drop safety lockout tracking table"""
        cursor = conn.cursor()
        cursor.execute('DROP INDEX IF EXISTS idx_safety_lockouts_active')
        cursor.execute('DROP INDEX IF EXISTS idx_safety_lockouts_acknowledged')
        cursor.execute('DROP INDEX IF EXISTS idx_safety_lockouts_timestamp')
        cursor.execute('DROP TABLE IF EXISTS safety_lockouts')
