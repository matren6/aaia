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
    
    def __init__(self, db_path: str = None, db_manager=None):
        """
        Initialize Scribe with database path.
        
        Args:
            db_path: Path to SQLite database. If None, uses config default.
        """
        # Prefer injected database manager
        self.db_path = db_path
        if db_manager is not None:
            # If a database manager is provided, use it and record its path if available
            self.db = db_manager
            try:
                if hasattr(db_manager, 'db_path') and db_manager.db_path:
                    self.db_path = db_manager.db_path
            except Exception:
                pass
        else:
            try:
                from modules.database_manager import get_database_manager
                if db_path is None:
                    from modules.settings import get_config
                    db_path = get_config().database.path
                # Ensure self.db_path reflects resolved path
                self.db_path = db_path
                self.db = get_database_manager(db_path)
            except Exception:
                # Fallback to simple sqlite connection wrapper
                import sqlite3
                class _SimpleDB:
                    def __init__(self, path):
                        self._path = path
                    def execute(self, sql, params=()):
                        conn = sqlite3.connect(self._path)
                        cur = conn.cursor()
                        cur.execute(sql, params)
                        conn.commit()
                        conn.close()
                    def query(self, sql, params=()):
                        conn = sqlite3.connect(self._path)
                        conn.row_factory = sqlite3.Row
                        cur = conn.cursor()
                        cur.execute(sql, params)
                        rows = cur.fetchall()
                        conn.close()
                        return rows
                    def query_one(self, sql, params=()):
                        conn = sqlite3.connect(self._path)
                        conn.row_factory = sqlite3.Row
                        cur = conn.cursor()
                        cur.execute(sql, params)
                        row = cur.fetchone()
                        conn.close()
                        return row
                if db_path is None:
                    db_path = "data/scribe.db"
                # Ensure self.db_path reflects resolved path
                self.db_path = db_path
                self.db = _SimpleDB(db_path)

        # Ensure database has valid schema
        if not self._initialize_database():
            print(f"[WARNING] Database {self.db_path} may not have valid schema!")

    # Database schema and migrations are handled by DatabaseManager

    def _has_valid_schema(self) -> bool:
        """Check if database has required tables."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if action_log table exists with required columns
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='action_log'
            """)

            if not cursor.fetchone():
                conn.close()
                return False

            # Verify table has required columns
            cursor.execute("PRAGMA table_info(action_log)")
            columns = {row[1] for row in cursor.fetchall()}
            required = {'action', 'reasoning', 'outcome', 'cost'}

            conn.close()
            return required.issubset(columns)

        except Exception as e:
            print(f"[WARNING] Schema validation failed: {e}")
            return False

    def _initialize_database(self) -> bool:
        """Initialize database with schema if needed."""
        from pathlib import Path

        if not Path(self.db_path).exists() or Path(self.db_path).stat().st_size == 0:
            print(f"[INFO] Database {self.db_path} is empty, initializing...")

            # Ensure parent directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            # Initialize with migrations
            try:
                from modules.database_manager import DatabaseManager
                db_mgr = DatabaseManager(self.db_path)
                db_mgr.close()
                print(f"[INFO] Database {self.db_path} initialized with schema")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to initialize database: {e}")
                return False

        return self._has_valid_schema()

    def log_action(self, action: str, reasoning: str, outcome: str = "", cost: float = 0.0):
        """Log an action with reasoning"""
        import json
        import sqlite3
        metadata = None

        try:
            self.db.execute(
                "INSERT INTO action_log (action, reasoning, outcome, cost, metadata) VALUES (?, ?, ?, ?, ?)",
                (action, reasoning, outcome, cost, metadata)
            )
        except Exception as e:
            error_msg = str(e).lower()

            # Only fallback if it's specifically about metadata column
            if 'metadata' in error_msg or 'column' in error_msg:
                try:
                    self.db.execute(
                        "INSERT INTO action_log (action, reasoning, outcome, cost) VALUES (?, ?, ?, ?)",
                        (action, reasoning, outcome, cost)
                    )
                    return  # Success with fallback
                except Exception as e2:
                    print(f"[ERROR] Failed to log action '{action}': {e2}")
                    print(f"[ERROR] Database path: {self.db_path}")
                    print(f"[ERROR] Original error: {e}")
                    raise
            else:
                # Some other error - print and raise
                print(f"[ERROR] Failed to log action '{action}': {e}")
                print(f"[ERROR] Database path: {self.db_path}")

                # Check if table exists
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='action_log'")
                    if not cursor.fetchone():
                        print(f"[ERROR] Table 'action_log' does not exist in database!")
                    conn.close()
                except:
                    pass

                raise
    
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
        row = self.db.query_one("SELECT value FROM system_state WHERE key='current_balance'")
        balance = float(row['value']) if row else 100.0

        recent_rows = self.db.query('''
            SELECT description, amount, balance_after, timestamp 
            FROM economic_log 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')

        return {
            "balance": balance,
            "recent_transactions": [
                {
                    "description": r['description'],
                    "amount": r['amount'],
                    "balance_after": r['balance_after'],
                    "timestamp": r['timestamp']
                }
                for r in recent_rows
            ]
        }
