# scribe.py
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List

class Scribe:
    def __init__(self, db_path: str = "data/scribe.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Directives table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS directives (
                id INTEGER PRIMARY KEY,
                type TEXT,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Hierarchy of needs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hierarchy_of_needs (
                id INTEGER PRIMARY KEY,
                tier INTEGER,
                name TEXT,
                description TEXT,
                current_focus BOOLEAN DEFAULT 0,
                progress REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Economic log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economic_log (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                amount REAL,
                balance_after REAL,
                category TEXT
            )
        ''')
        
        # Action log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_log (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT,
                reasoning TEXT,
                outcome TEXT,
                cost REAL DEFAULT 0.0
            )
        ''')
        
        # Dialogue log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialogue_log (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                phase TEXT,
                content TEXT,
                master_command TEXT,
                reasoning TEXT
            )
        ''')
        
        # Master model table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS master_model (
                id INTEGER PRIMARY KEY,
                trait TEXT,
                value TEXT,
                confidence REAL DEFAULT 0.5,
                evidence_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tools registry
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # System state
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def log_action(self, action: str, reasoning: str, outcome: str = "", cost: float = 0.0):
        """Log an action with reasoning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO action_log (action, reasoning, outcome, cost) VALUES (?, ?, ?, ?)",
            (action, reasoning, outcome, cost)
        )
        conn.commit()
        conn.close()