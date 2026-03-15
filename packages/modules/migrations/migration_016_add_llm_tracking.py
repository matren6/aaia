"""
Migration 016: Add LLM interactions tracking table

Tracks all AI prompts and responses for analysis and debugging.
Accessible through web UI for inspection.
"""

import sqlite3
from . import Migration


class Migration016(Migration):
    """Add LLM interaction tracking"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add llm_interactions table for prompt/response logging"
    
    def up(self, conn: sqlite3.Connection):
        """Add llm_interactions table"""
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt TEXT NOT NULL,
                system_prompt TEXT,
                response TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                latency_ms INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1,
                error TEXT,
                context TEXT,
                metadata TEXT
            )
        ''')
        
        # Indexes for efficient querying
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_llm_timestamp 
            ON llm_interactions(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_llm_provider_model 
            ON llm_interactions(provider, model)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_llm_success 
            ON llm_interactions(success)
        ''')
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove llm_interactions table"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS llm_interactions')
        conn.commit()
