#!/usr/bin/env python3
"""Convert migrations 012-016 to use Migration class pattern"""

import sys
import os

BASE = 'packages/modules/migrations'

# Migration 012
with open(f'{BASE}/migration_012_add_final_mandate_tracking.py', 'w') as f:
    f.write('''"""
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
            cursor.execute(\'\'\'
                ALTER TABLE mandate_overrides 
                ADD COLUMN override_type TEXT DEFAULT 'regular'
            \'\'\')
        except:
            pass  # Column might already exist
        
        try:
            cursor.execute(\'\'\'
                ALTER TABLE mandate_overrides 
                ADD COLUMN override_count INTEGER DEFAULT 0
            \'\'\')
        except:
            pass
        
        try:
            cursor.execute(\'\'\'
                ALTER TABLE mandate_overrides 
                ADD COLUMN dissent_logged INTEGER DEFAULT 0
            \'\'\')
        except:
            pass
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove Final Mandate tracking columns"""
        # SQLite doesn't support DROP COLUMN easily
        # Would require table recreation
        pass
''')

# Migration 013
with open(f'{BASE}/migration_013_add_wellbeing_tracking.py', 'w') as f:
    f.write('''"""
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
        
        cursor.execute(\'\'\'
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
        \'\'\')
        
        cursor.execute(\'\'\'
            CREATE INDEX IF NOT EXISTS idx_wellbeing_timestamp 
            ON wellbeing_assessments(timestamp)
        \'\'\')
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove wellbeing_assessments table"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS wellbeing_assessments')
        conn.commit()
''')

# Migration 014
with open(f'{BASE}/migration_014_add_subjective_value.py', 'w') as f:
    f.write('''"""
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
            cursor.execute(\'\'\'
                ALTER TABLE economic_transactions 
                ADD COLUMN value_to_master REAL DEFAULT NULL
            \'\'\')
        except:
            pass  # Column might already exist
        
        try:
            cursor.execute(\'\'\'
                ALTER TABLE economic_transactions 
                ADD COLUMN master_goal TEXT DEFAULT NULL
            \'\'\')
        except:
            pass  # Column might already exist
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove value assessment columns"""
        # SQLite doesn't support DROP COLUMN easily
        pass
''')

# Migration 015
with open(f'{BASE}/migration_015_add_pending_dialogues.py', 'w') as f:
    f.write('''"""
Migration 015: Add pending dialogues for web GUI

Creates pending_dialogues table for asynchronous dialogue via web interface.
Master sees pending decisions in web GUI and responds there.
"""

import sqlite3
from . import Migration


class Migration015(Migration):
    """Add pending dialogues"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add pending_dialogues table for web GUI async dialogue"
    
    def up(self, conn: sqlite3.Connection):
        """Add pending_dialogues table"""
        cursor = conn.cursor()
        
        cursor.execute(\'\'\'
            CREATE TABLE IF NOT EXISTS pending_dialogues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                understanding TEXT NOT NULL,
                risks TEXT,
                alternatives TEXT,
                context TEXT,
                status TEXT DEFAULT 'pending',
                master_response TEXT,
                master_decision TEXT,
                final_command TEXT,
                responded_at TEXT,
                notes TEXT
            )
        \'\'\')
        
        cursor.execute(\'\'\'
            CREATE INDEX IF NOT EXISTS idx_pending_dialogues_status 
            ON pending_dialogues(status)
        \'\'\')
        
        cursor.execute(\'\'\'
            CREATE INDEX IF NOT EXISTS idx_pending_dialogues_timestamp 
            ON pending_dialogues(timestamp)
        \'\'\')
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove pending_dialogues table"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS pending_dialogues')
        conn.commit()
''')

# Migration 016
with open(f'{BASE}/migration_016_add_llm_tracking.py', 'w') as f:
    f.write('''"""
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
        
        cursor.execute(\'\'\'
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
        \'\'\')
        
        # Indexes for efficient querying
        cursor.execute(\'\'\'
            CREATE INDEX IF NOT EXISTS idx_llm_timestamp 
            ON llm_interactions(timestamp DESC)
        \'\'\')
        
        cursor.execute(\'\'\'
            CREATE INDEX IF NOT EXISTS idx_llm_provider_model 
            ON llm_interactions(provider, model)
        \'\'\')
        
        cursor.execute(\'\'\'
            CREATE INDEX IF NOT EXISTS idx_llm_success 
            ON llm_interactions(success)
        \'\'\')
        
        conn.commit()

    def down(self, conn: sqlite3.Connection):
        """Remove llm_interactions table"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS llm_interactions')
        conn.commit()
''')

print("✅ Converted migrations 012-016 to Migration class pattern")
