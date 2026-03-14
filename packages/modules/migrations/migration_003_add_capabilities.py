"""
Migration 003: Add Capability Discovery

Adds tables for capability discovery and tracking:
- discovered_capabilities: Discovered system capabilities
- capability_validation: Validation results for capabilities
- reflection_log: Metacognition reflections
- effectiveness_metrics: Performance metrics over time
"""

import sqlite3
from . import Migration


class Migration003(Migration):
    """Add capability discovery and metacognition tables"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add capabilities, validation, reflection, and metrics tables"
    
    def up(self, conn: sqlite3.Connection):
        """Create capability and metacognition tables"""
        cursor = conn.cursor()
        
        # Discovered capabilities
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                capability_type TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                value_score REAL DEFAULT 0.0,
                complexity_score REAL DEFAULT 0.0,
                dependencies TEXT,
                status TEXT DEFAULT 'discovered'
            )
        ''')
        
        # Capability validation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capability_validation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capability_id INTEGER NOT NULL,
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validation_result TEXT,
                confidence REAL DEFAULT 0.0,
                notes TEXT,
                FOREIGN KEY (capability_id) REFERENCES discovered_capabilities(id)
            )
        ''')
        
        # Reflection log (metacognition)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reflection_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reflection_type TEXT NOT NULL,
                insights TEXT,
                improvements TEXT,
                regressions TEXT,
                effectiveness_score REAL DEFAULT 0.0
            )
        ''')
        
        # Effectiveness metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS effectiveness_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                context TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_capabilities_status ON discovered_capabilities(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_capabilities_type ON discovered_capabilities(capability_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_validation_capability ON capability_validation(capability_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reflection_timestamp ON reflection_log(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON effectiveness_metrics(metric_name, timestamp DESC)')
    
    def down(self, conn: sqlite3.Connection):
        """Drop capability and metacognition tables"""
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS effectiveness_metrics')
        cursor.execute('DROP TABLE IF EXISTS reflection_log')
        cursor.execute('DROP TABLE IF EXISTS capability_validation')
        cursor.execute('DROP TABLE IF EXISTS discovered_capabilities')
