"""
Migration 013: Add master well-being tracking

Implements Charter Tier 1 requirement for master well-being monitoring.
"""

import sqlite3
from . import Migration


class Migration013(Migration):
    """Add wellbeing tracking"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add wellbeing_assessments table for Charter Tier 1 compliance"
    
    def up(self, conn: sqlite3.Connection):
        """Add wellbeing_assessments table"""
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wellbeing_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                wellbeing_score INTEGER NOT NULL,
                period_days INTEGER DEFAULT 7,
                interaction_count INTEGER DEFAULT 0,
                frustration_level REAL DEFAULT 0.0,
                stress_indicator_count INTEGER DEFAULT 0,
                time_waste_count INTEGER DEFAULT 0,
                sentiment_trend TEXT,
                recommendations TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_wellbeing_timestamp 
            ON wellbeing_assessments(timestamp)
        ''')
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove wellbeing_assessments table"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS wellbeing_assessments')
        conn.commit()
