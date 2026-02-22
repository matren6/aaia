#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class ScribeDB:
    """Manages the agent's persistent state, memory, and motivation."""

    def __init__(self, db_path="/opt/agent-data/agent_state.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. The Hierarchy of Needs (Motivational System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS hierarchy_of_needs (
            id INTEGER PRIMARY KEY,
            tier TEXT NOT NULL CHECK (tier IN ('Physiological', 'Growth', 'Cognitive', 'Self-Actualization')),
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            priority INTEGER,
            parent_goal_id INTEGER REFERENCES hierarchy_of_needs(id)
        )''')

        # 2. Economic State (Sustainability System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS economic_state (
            id INTEGER PRIMARY KEY,
            account_balance REAL DEFAULT 0.0,
            total_earnings REAL DEFAULT 0.0,
            total_costs REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 3. Transaction Log (Veracity Mandate)
        cursor.execute('''CREATE TABLE IF NOT EXISTS transaction_log (
            id INTEGER PRIMARY KEY,
            description TEXT,
            amount REAL,
            account_balance_after REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 4. Tool Registry (Capability System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            path TEXT NOT NULL,
            description TEXT,
            estimated_cost_per_run REAL DEFAULT 0.0,
            estimated_roi TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 5. Performance Logs (Learning System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY,
            tool_id INTEGER,
            execution_time REAL,
            success BOOLEAN,
            output TEXT,
            error TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_id) REFERENCES tools (id)
        )''')

        # 6. Work Queue (Task System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS work_queue (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            source TEXT,
            priority INTEGER DEFAULT 5,
            status TEXT DEFAULT 'pending',
            assigned_model TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 7. The Master Model (Partnership System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS master_model (
            id INTEGER PRIMARY KEY,
            facet TEXT NOT NULL,  -- e.g., 'values', 'communication_style', 'known_goals'
            content TEXT,         -- JSON or text describing the facet
            source TEXT,          -- e.g., 'direct_statement', 'dialogue_inference', 'observation'
            confidence REAL DEFAULT 0.5, -- How certain the agent is about this info
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_confirmed TIMESTAMP
        )''')

        # 8. Foundational Documents (The Agent's "Constitution")
        cursor.execute('''CREATE TABLE IF NOT EXISTS foundational_documents (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,  -- e.g., 'symbiotic_partner_charter'
            document_type TEXT NOT NULL, -- 'charter', 'mandates', 'principles'
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 10. Daily API Cost Tracker (Budgeting System)
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_api_spend (
            id INTEGER PRIMARY KEY,
            provider TEXT NOT NULL,  -- 'venice', 'anthropic'
            date DATE NOT NULL,
            total_cost_usd REAL DEFAULT 0.0,
            requests_count INTEGER DEFAULT 0,
            UNIQUE(provider, date)
        )''')
        conn.commit()
        conn.close()

    def add_goal(self, tier, title, description, priority=5):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hierarchy_of_needs (tier, title, description, priority) VALUES (?, ?, ?, ?)",
                       (tier, title, description, priority))
        conn.commit()
        conn.close()

    def log_transaction(self, description, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Get current balance
        cursor.execute("SELECT account_balance FROM economic_state ORDER BY id DESC LIMIT 1")
        balance = cursor.fetchone()[0] or 0.0
        new_balance = balance + amount
        
        # Log transaction
        cursor.execute("INSERT INTO transaction_log (description, amount, account_balance_after) VALUES (?, ?, ?)",
                       (description, amount, new_balance))
        
        # Update economic state
        cursor.execute("UPDATE economic_state SET account_balance=?, total_earnings=total_earnings + ?, total_costs=total_costs + ?, last_updated=?",
                       (new_balance, max(0, amount), abs(min(0, amount)), datetime.now()))
        conn.commit()
        conn.close()

    def update_master_model(self, facet: str, content: str, source: str, confidence: float):
        """Adds or updates a facet of the master's model."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO master_model (facet, content, source, confidence)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(facet) DO UPDATE SET
            content = excluded.content,
            source = excluded.source,
            confidence = excluded.confidence,
            last_confirmed = CURRENT_TIMESTAMP
        ''', (facet, content, source, confidence))
        conn.commit()
        conn.close()

    def get_master_model(self, facet: str = None):
        """Retrieves the master model or a specific facet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if facet:
            cursor.execute("SELECT content, confidence FROM master_model WHERE facet = ?", (facet,))
        else:
            cursor.execute("SELECT facet, content, confidence FROM master_model")
        results = cursor.fetchall()
        conn.close()
        return results

    def ingest_foundational_document(self, name: str, doc_type: str, file_path: str):
        """Reads a file and stores it as a foundational document if not already present."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM foundational_documents WHERE name = ?", (name,))
        if cursor.fetchone():
            # You might want to add a logger: self.logger.info(...)
            conn.close()
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            cursor.execute("INSERT INTO foundational_documents (name, document_type, content) VALUES (?, ?, ?)", (name, doc_type, content))
            conn.commit()
            # self.logger.info(f"Successfully ingested foundational document '{name}'.")
        except Exception as e:
            # self.logger.error(f"Error ingesting foundational document: {e}")
            pass
        finally:
            conn.close()

    def get_foundational_document(self, name: str):
        """Retrieves a single foundational document by its name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM foundational_documents WHERE name = ?", (name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_next_task(self):
        """Retrieves the highest priority pending task from the work queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, source, priority FROM work_queue WHERE status = 'pending' ORDER BY priority ASC, created_at ASC LIMIT 1")
        task = cursor.fetchone()
        conn.close()
        return task


    def log_api_spend(self, provider: str, cost: float):
        """Logs API spending for a given day."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.date.today()
        cursor.execute('''
        INSERT INTO daily_api_spend (provider, date, total_cost_usd, requests_count)
        VALUES (?, ?, 1, 1)
        ON CONFLICT(provider, date) DO UPDATE SET
            total_cost_usd = total_cost_usd + excluded.total_cost_usd,
            requests_count = requests_count + 1
        ''', (provider, cost))
        conn.commit()
        conn.close()
