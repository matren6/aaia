"""
Migration 009: Add Provider Performance Tracking

Creates table for tracking LLM provider performance metrics:
- provider_performance: Historical performance of each provider
  - Used for marginal cost-benefit analysis in Phase 2
  - Enables historical quality scoring
  - Supports ROI calculations for model selection
"""

import sqlite3
from . import Migration


class Migration009(Migration):
    """Add provider performance tracking"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add provider_performance table for marginal analysis"
    
    def up(self, conn: sqlite3.Connection):
        """Create provider performance tracking"""
        cursor = conn.cursor()
        
        # Provider performance table - historical tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS provider_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                task_type TEXT NOT NULL,
                complexity TEXT DEFAULT 'medium',
                quality_score REAL NOT NULL,
                response_time REAL NOT NULL,
                tokens_used INTEGER NOT NULL,
                cost REAL NOT NULL,
                success INTEGER DEFAULT 1,
                metadata TEXT
            )
        ''')
        
        # Indexes for efficient queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_provider_perf_provider_task 
            ON provider_performance(provider, task_type, timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_provider_perf_complexity 
            ON provider_performance(complexity, timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_provider_perf_success 
            ON provider_performance(success, timestamp DESC)
        ''')
        
        # Marginal analysis decisions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marginal_analysis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                task_type TEXT NOT NULL,
                complexity TEXT NOT NULL,
                selected_provider TEXT NOT NULL,
                quality_score REAL NOT NULL,
                estimated_cost REAL NOT NULL,
                utility_per_dollar REAL NOT NULL,
                opportunity_cost REAL NOT NULL,
                alternatives_evaluated INTEGER DEFAULT 0,
                reasoning TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_marginal_analysis_timestamp 
            ON marginal_analysis_log(timestamp DESC)
        ''')
    
    def down(self, conn: sqlite3.Connection):
        """Remove provider performance tracking"""
        cursor = conn.cursor()
        cursor.execute('DROP INDEX IF EXISTS idx_provider_perf_provider_task')
        cursor.execute('DROP INDEX IF EXISTS idx_provider_perf_complexity')
        cursor.execute('DROP INDEX IF EXISTS idx_provider_perf_success')
        cursor.execute('DROP INDEX IF EXISTS idx_marginal_analysis_timestamp')
        cursor.execute('DROP TABLE IF EXISTS marginal_analysis_log')
        cursor.execute('DROP TABLE IF EXISTS provider_performance')
