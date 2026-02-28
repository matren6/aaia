# scribe.py
"""
Scribe Module - Core Logging and Persistence System

PURPOSE:
The Scribe serves as the central memory and logging system for the entire
autonomous AI agent. It provides persistent storage of all system actions,
dialogues, economic transactions, and state information.

PROBLEM SOLVED:
Without persistent memory, each conversation would start fresh with no context.
The Scribe solves this by maintaining a SQLite database that records:
- Every action the system takes and why
- Dialogue history with the master
- Economic transactions and balance
- Tool registry and usage
- Master model traits and patterns
- Hierarchy of needs state

KEY RESPONSIBILITIES:
1. Initialize and manage SQLite database with all required tables
2. Log actions with reasoning and outcomes (action_log)
3. Track economic transactions and balance (economic_log)
4. Record dialogue interactions (dialogue_log)
5. Maintain the master model - learned traits about the user
6. Register and track tools/capabilities
7. Store system state information
8. Manage hierarchy of needs progression
9. Provide query methods for analyzing past behavior

DEPENDENCIES: None ( foundational module)
OUTPUTS: All other modules use Scribe for persistence
"""

import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List

class Scribe:
    """
    Core logging and persistence module.
    
    Provides centralized SQLite-based storage for all system data.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize Scribe with database path.
        
        Args:
            db_path: Path to SQLite database. If None, uses config default.
        """
        if db_path is None:
            # Try to get from config
            try:
                from modules.settings import get_config
                db_path = get_config().database.path
            except Exception:
                db_path = "data/scribe.db"
        
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
    
    def validate_mandates(self, action_data: Dict) -> bool:
        """
        Validate action data against mandate requirements.
        
        This is a convenience method for external modules to check
        if an action passes mandate validation.
        
        Args:
            action_data: Dictionary containing action information to validate
            
        Returns:
            True if the action data is valid for mandate processing
        """
        # Basic validation - action_data should be a non-empty dict
        if not isinstance(action_data, dict):
            return False
        if not action_data:
            return False
        return True
        
    def get_economic_status(self) -> Dict[str, Any]:
        """
        Get current economic status.
        
        Returns:
            Dictionary with balance and recent transactions
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        balance = float(row[0]) if row else 100.0
        
        cursor.execute('''
            SELECT description, amount, balance_after, timestamp 
            FROM economic_log 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        recent = cursor.fetchall()
        
        conn.close()
        
        return {
            "balance": balance,
            "recent_transactions": [
                {
                    "description": r[0],
                    "amount": r[1],
                    "balance_after": r[2],
                    "timestamp": r[3]
                }
                for r in recent
            ]
        }
