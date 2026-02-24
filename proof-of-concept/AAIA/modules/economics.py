# economics.py
"""
Economics Module - Resource Management and Cost Tracking

PURPOSE:
The Economics module manages the AI's virtual economy, tracking expenditures,
maintaining balance, and implementing budget management. This gives the AI
a sense of resource constraints that drives efficient behavior.

PROBLEM SOLVED:
Without economic constraints, an AI might:
- Use unlimited API calls without regard for cost
- Be inefficient in token usage
- Not optimize for cost-effectiveness
- Have no concept of "budget" or resource limits

The economics module creates:
1. Budget awareness: Track current balance
2. Cost tracking: Every operation has a cost
3. Transaction logging: Full audit trail of expenditures
4. Balance management: Update balance after each transaction
5. Budget warnings: Alert when balance is low
6. Income generation: Ability to earn more credits

KEY RESPONSIBILITIES:
1. Calculate costs for model usage (per-token pricing)
2. Log all transactions (inference, tools, operations)
3. Maintain current balance in system state
4. Provide budget status and warnings
5. Support income generation suggestions
6. Generate economic reports

COST MODEL:
- Local models (Ollama): ~$0.001 per 1K tokens
- External APIs: Variable rates
- Tool creation: One-time cost
- System operations: Minimal cost

DEPENDENCIES: Scribe (for database access)
OUTPUTS: Cost calculations, balance updates, transaction logs
"""

import sqlite3
from decimal import Decimal
from .scribe import Scribe

class EconomicManager:
    def __init__(self, scribe: Scribe):
        self.scribe = scribe
        self.local_model_cost_per_token = Decimal('0.000001')  # $0.001 per 1000 tokens
        
    def calculate_cost(self, model_name: str, token_count: int) -> Decimal:
        """Calculate cost for model usage"""
        # For now, only track monetary costs
        if "local" in model_name.lower():
            return self.local_model_cost_per_token * token_count
        else:
            # External APIs would have different costs
            return Decimal('0.01')  # Placeholder for API costs
            
    def log_transaction(self, description: str, amount: Decimal, category: str = "inference"):
        """Log a monetary transaction"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        # Get current balance
        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        current_balance = Decimal(row[0]) if row else Decimal('100.00')  # Starting balance
        
        new_balance = current_balance + amount
        
        # Update balance
        cursor.execute(
            "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
            ('current_balance', str(new_balance))
        )
        
        # Log transaction
        cursor.execute(
            "INSERT INTO economic_log (description, amount, balance_after, category) VALUES (?, ?, ?, ?)",
            (description, float(amount), float(new_balance), category)
        )
        
        conn.commit()
        conn.close()
        
        return new_balance