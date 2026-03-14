"""
Migration 005: Add Income Tracking Tables

Creates tables for tracking income and profitability:
- income: Income records from completed tasks and services
- income_opportunities: Identified opportunities for income generation
- profitability_reports: Regular profitability snapshots
"""

import sqlite3
from . import Migration


class Migration005(Migration):
    """Add income tracking tables"""
    
    def __init__(self):
        super().__init__()
        self.description = "Add income, income_opportunities, and profitability_reports tables"
    
    def up(self, conn: sqlite3.Connection):
        """Create income tracking tables"""
        cursor = conn.cursor()
        
        # Income table - tracks income records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                task_id TEXT,
                description TEXT,
                verification_status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Income opportunities table - tracks potential income opportunities
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS income_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                opportunity_type TEXT NOT NULL,
                description TEXT NOT NULL,
                estimated_value REAL,
                effort_estimate TEXT,
                status TEXT DEFAULT 'identified',
                notes TEXT
            )
        ''')
        
        # Profitability reports table - periodic snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profitability_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                total_income REAL DEFAULT 0.0,
                total_costs REAL DEFAULT 0.0,
                net_profit REAL DEFAULT 0.0,
                is_profitable INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_timestamp ON income(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_source ON income(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_opportunities_status ON income_opportunities(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_income_opportunities_timestamp ON income_opportunities(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profitability_reports_date ON profitability_reports(report_date DESC)')
    
    def down(self, conn: sqlite3.Connection):
        """Drop income tracking tables"""
        cursor = conn.cursor()
        cursor.execute('DROP INDEX IF EXISTS idx_income_timestamp')
        cursor.execute('DROP INDEX IF EXISTS idx_income_source')
        cursor.execute('DROP INDEX IF EXISTS idx_income_opportunities_status')
        cursor.execute('DROP INDEX IF EXISTS idx_income_opportunities_timestamp')
        cursor.execute('DROP INDEX IF EXISTS idx_profitability_reports_date')
        cursor.execute('DROP TABLE IF EXISTS profitability_reports')
        cursor.execute('DROP TABLE IF EXISTS income_opportunities')
        cursor.execute('DROP TABLE IF EXISTS income')
