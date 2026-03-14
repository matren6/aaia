"""
Migration 002: Add Goals System

Adds tables for goal management:
- goals: Active and completed goals
- goal_history: History of goal changes
"""

import sqlite3
from . import Migration


class Migration002(Migration):
    """Add goals system tables"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add goals and goal_history tables"
    
    def up(self, conn: sqlite3.Connection):
        """Create goals tables"""
        cursor = conn.cursor()
        
        # Goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_text TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                progress INTEGER DEFAULT 0,
                auto_generated INTEGER DEFAULT 0,
                tier INTEGER,
                expected_benefit TEXT,
                estimated_effort TEXT,
                parent_goal_id INTEGER,
                FOREIGN KEY (parent_goal_id) REFERENCES goals(id)
            )
        ''')
        
        # Goal history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goal_history_goal_id ON goal_history(goal_id)')
    
    def down(self, conn: sqlite3.Connection):
        """Drop goals tables"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS goal_history')
        cursor.execute('DROP TABLE IF EXISTS goals')
