"""
Migration 010: Add Proactive Notifications Table

Creates table for tracking pending master notifications from proactive analysis:
- pending_master_notifications: Queue of proactive insights to present to master
"""

import sqlite3
from . import Migration


class Migration010(Migration):
    """Add pending_master_notifications table for proactive analysis"""

    def __init__(self):
        super().__init__()
        self.description = "Add pending_master_notifications table for proactive analysis and recommendations"
    
    def up(self, conn: sqlite3.Connection):
        """Create pending notifications table"""
        cursor = conn.cursor()
        
        # Pending master notifications table - queue of proactive insights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_master_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                category TEXT,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                presented_timestamp TEXT,
                master_response TEXT,
                dismissed INTEGER DEFAULT 0
            )
        ''')
        
        # Create indexes for efficient querying
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_status ON pending_master_notifications(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_priority ON pending_master_notifications(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON pending_master_notifications(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_type ON pending_master_notifications(type)')
    
    def down(self, conn: sqlite3.Connection):
        """Drop pending notifications table"""
        cursor = conn.cursor()
        cursor.execute('DROP INDEX IF EXISTS idx_notifications_type')
        cursor.execute('DROP INDEX IF EXISTS idx_notifications_timestamp')
        cursor.execute('DROP INDEX IF EXISTS idx_notifications_priority')
        cursor.execute('DROP INDEX IF EXISTS idx_notifications_status')
        cursor.execute('DROP TABLE IF EXISTS pending_master_notifications')
