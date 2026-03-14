"""
Migration 004: Add Master Model Tables

Creates tables for tracking and modeling the master's psychology:
- master_model: Master's psychological traits and preferences
- master_interactions: Log of all interactions with master
"""

import sqlite3
from . import Migration


class Migration004(Migration):
    """Add master model tables"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add master_model and master_interactions tables"
    
    def up(self, conn: sqlite3.Connection):
        """Create master model tables"""
        cursor = conn.cursor()
        
        # Master model table - tracks master's psychological traits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS master_model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                trait_category TEXT NOT NULL,
                trait_name TEXT NOT NULL,
                trait_value TEXT,
                confidence REAL DEFAULT 0.5,
                evidence TEXT,
                last_updated TEXT,
                UNIQUE(trait_category, trait_name)
            )
        ''')
        
        # Master interactions table - logs all interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS master_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                user_input TEXT NOT NULL,
                system_response TEXT,
                intent_detected TEXT,
                success INTEGER DEFAULT 1,
                notes TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_master_model_category ON master_model(trait_category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_master_model_trait_name ON master_model(trait_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_master_interactions_timestamp ON master_interactions(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_master_interactions_type ON master_interactions(interaction_type)')
    
    def down(self, conn: sqlite3.Connection):
        """Drop master model tables"""
        cursor = conn.cursor()
        cursor.execute('DROP INDEX IF EXISTS idx_master_model_category')
        cursor.execute('DROP INDEX IF EXISTS idx_master_model_trait_name')
        cursor.execute('DROP INDEX IF EXISTS idx_master_interactions_timestamp')
        cursor.execute('DROP INDEX IF EXISTS idx_master_interactions_type')
        cursor.execute('DROP TABLE IF EXISTS master_interactions')
        cursor.execute('DROP TABLE IF EXISTS master_model')
