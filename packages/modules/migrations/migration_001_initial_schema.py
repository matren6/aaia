"""
Migration 001: Initial Schema

Creates the base tables for the system:
- action_log: All system actions
- economic_log: Economic transactions
- system_state: Key-value state storage
- hierarchy_of_needs: Tier progression
"""

import sqlite3
from . import Migration


class Migration001(Migration):
    """Initial schema setup"""
    
    def __init__(self):
        super().__init__()
        self.description = "Initial schema: action_log, economic_log, system_state, hierarchy_of_needs"
    
    def up(self, conn: sqlite3.Connection):
        """Create initial tables"""
        cursor = conn.cursor()
        
        # Action log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                reasoning TEXT,
                outcome TEXT,
                cost REAL DEFAULT 0.0,
                metadata TEXT
            )
        ''')
        
        # Economic log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economic_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                transaction_type TEXT
            )
        ''')
        
        # System state table (key-value store)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Hierarchy of needs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hierarchy_of_needs (
                tier INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                current_focus INTEGER DEFAULT 0,
                progress REAL DEFAULT 0.0,
                unlocked_at TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_action_log_timestamp ON action_log(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_economic_log_timestamp ON economic_log(timestamp DESC)')
    
    def down(self, conn: sqlite3.Connection):
        """Drop initial tables"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS action_log')
        cursor.execute('DROP TABLE IF EXISTS economic_log')
        cursor.execute('DROP TABLE IF EXISTS system_state')
        cursor.execute('DROP TABLE IF EXISTS hierarchy_of_needs')
