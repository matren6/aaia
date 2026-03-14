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
import time
from decimal import Decimal
from typing import Optional
from .scribe import Scribe


class EconomicManager:
    """
    Manages the virtual economy for the AI agent.
    
    Tracks expenditures, maintains balance, and publishes events
    for decoupled communication with other modules.
    """
    
    def __init__(self, scribe: Scribe, event_bus = None):
        """
        Initialize EconomicManager.

        Args:
            scribe: Scribe instance for persistence
            event_bus: Optional EventBus for publishing economic events
        """
        self.scribe = scribe
        self.event_bus = event_bus

        # Load config or use defaults
        try:
            from modules.settings import get_config
            config = get_config()
            self.inference_cost = Decimal(str(config.economics.inference_cost))
            self.tool_creation_cost = Decimal(str(config.economics.tool_creation_cost))
            self.low_balance_threshold = Decimal(str(config.economics.low_balance_threshold))
            self.initial_balance = Decimal(str(config.economics.initial_balance))
        except Exception:
            self.inference_cost = Decimal('0.01')
            self.tool_creation_cost = Decimal('1.0')
            self.low_balance_threshold = Decimal('10.0')
            self.initial_balance = Decimal('100.00')

        self.local_model_cost_per_token = Decimal('0.000001')  # $0.001 per 1000 tokens

        # Track provider costs separately
        self.provider_costs = {}  # {provider_name: total_cost}

        # Subscribe to relevant events
        if self.event_bus:
            try:
                from modules.bus import EventType
                # Track LLM response costs automatically
                self.event_bus.subscribe(EventType.LLM_RESPONSE, self._on_llm_response)
                # Track tool creation costs if published
                self.event_bus.subscribe(EventType.TOOL_CREATED, self._on_tool_created)
            except Exception:
                pass

    def _on_llm_response(self, event):
        """Handle LLM_RESPONSE events to record costs automatically."""
        try:
            data = getattr(event, 'data', {})
            cost = data.get('cost', 0.0)
            model = data.get('model', 'unknown')
            if cost and float(cost) > 0:
                # Record as spending
                from decimal import Decimal as _D
                self.log_transaction(f"LLM call to {model}", -_D(str(cost)), category='llm', metadata={'model': model})
        except Exception:
            pass

    def _on_tool_created(self, event):
        """Handle TOOL_CREATED events to record tool creation costs if provided."""
        try:
            data = getattr(event, 'data', {})
            cost = data.get('cost', 0.0)
            tool_name = data.get('tool_name', 'unknown')
            if cost and float(cost) > 0:
                from decimal import Decimal as _D
                self.log_transaction(f"Tool creation: {tool_name}", -_D(str(cost)), category='tool_creation', metadata={'tool_name': tool_name})
        except Exception:
            pass
        
    def calculate_cost(self, model_name: str, token_count: int) -> Decimal:
        """Calculate cost for model usage"""
        # For now, only track monetary costs
        if "local" in model_name.lower():
            return self.local_model_cost_per_token * token_count
        else:
            # External APIs would have different costs
            return Decimal('0.01')  # Placeholder for API costs
            
    def log_transaction(self, description: str, amount: Decimal, category: str = "inference", metadata: dict = None):
        """
        Log a monetary transaction and publish event.

        Args:
            description: Description of the transaction
            amount: Amount (negative for spending, positive for income)
            category: Transaction category (inference, tool_creation, etc.)
            metadata: Optional dict with additional info (provider, model, tokens, etc.)

        Returns:
            New balance after transaction
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Get current balance
        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        current_balance = Decimal(row[0]) if row else self.initial_balance

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

        # Track provider costs if metadata available
        if metadata and 'provider' in metadata:
            provider = metadata['provider']
            if provider not in self.provider_costs:
                self.provider_costs[provider] = Decimal('0')
            self.provider_costs[provider] += abs(amount)

        # Publish event if event bus is available
        if self.event_bus is not None:
            try:
                from modules.bus import Event, EventType

                # Economic transaction event
                try:
                    self.event_bus.publish(Event(
                        type=EventType.ECONOMIC_TRANSACTION,
                        data={
                            'description': description,
                            'amount': float(amount),
                            'balance_after': float(new_balance),
                            'transaction_type': category,
                            'metadata': metadata or {}
                        },
                        source='EconomicManager'
                    ))
                except Exception:
                    # Don't let publishing break flow
                    pass

                # Check for low balance and publish warning
                if new_balance < self.low_balance_threshold:
                    try:
                        self.event_bus.publish(Event(
                            type=EventType.BALANCE_LOW,
                            data={
                                'balance': float(new_balance),
                                'threshold': float(self.low_balance_threshold)
                            },
                            source='EconomicManager'
                        ))
                    except Exception:
                        pass
            except Exception:
                pass  # Bus import or publish error

        return new_balance

    def get_provider_costs(self, provider_name: Optional[str] = None) -> dict:
        """Get cost breakdown by provider

        Args:
            provider_name: Specific provider or None for all

        Returns:
            Dict with provider costs
        """
        if provider_name:
            return {provider_name: self.provider_costs.get(provider_name, Decimal('0'))}
        return {k: v for k, v in self.provider_costs.items()}

    def get_balance(self) -> Decimal:
        """Get current balance

        Returns:
            Current balance as Decimal
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        conn.close()

        return Decimal(row[0]) if row else self.initial_balance

    def record_income(self, amount: float, source: str, task_id: str = None, description: str = ""):
        """
        Record income from completed task or service.

        Args:
            amount: Income amount (must be > 0)
            source: Source type (task_completion, service, optimization_savings, other)
            task_id: Optional task identifier
            description: Optional description
        """
        if amount <= 0:
            raise ValueError("Income amount must be positive")

        valid_sources = ['task_completion', 'service', 'optimization_savings', 'other']
        if source not in valid_sources:
            raise ValueError(f"Invalid source. Must be one of: {valid_sources}")

        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        from datetime import datetime
        cursor.execute('''
            INSERT INTO income (timestamp, amount, source, task_id, description, verification_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), amount, source, task_id, description[:200], 'pending'))

        conn.commit()
        conn.close()

        # Also log as transaction (positive)
        self.log_transaction(
            f"Income: {description or source}",
            Decimal(str(amount)),
            category='income',
            metadata={'source': source, 'task_id': task_id}
        )

        # Emit event
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.INCOME_RECORDED, {
                    'amount': amount,
                    'source': source,
                    'task_id': task_id
                }))
            except:
                pass

        self.scribe.log_action(f"Income recorded: {source}", outcome=f"Amount: {amount}")

    def get_total_income(self, start_date: str = None, end_date: str = None) -> float:
        """
        Get total income for period.

        Args:
            start_date: ISO format start date
            end_date: ISO format end date

        Returns:
            Total income
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM income
                WHERE timestamp >= ? AND timestamp <= ?
            ''', (start_date, end_date))
        else:
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM income')

        result = cursor.fetchone()[0]
        conn.close()
        return float(result)

    def get_income_by_source(self, start_date: str = None, end_date: str = None) -> dict:
        """
        Get income breakdown by source.

        Args:
            start_date: ISO format start date
            end_date: ISO format end date

        Returns:
            Dict with income per source
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute('''
                SELECT source, COALESCE(SUM(amount), 0) FROM income
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY source
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT source, COALESCE(SUM(amount), 0) FROM income
                GROUP BY source
            ''')

        breakdown = {}
        for row in cursor.fetchall():
            breakdown[row[0]] = float(row[1])

        conn.close()
        return breakdown

    def get_total_costs(self, start_date: str = None, end_date: str = None) -> float:
        """
        Get total costs for period.

        Args:
            start_date: ISO format start date
            end_date: ISO format end date

        Returns:
            Total costs
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute('''
                SELECT COALESCE(SUM(ABS(amount)), 0) FROM economic_log
                WHERE timestamp >= ? AND timestamp <= ? AND amount < 0
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT COALESCE(SUM(ABS(amount)), 0) FROM economic_log
                WHERE amount < 0
            ''')

        result = cursor.fetchone()[0]
        conn.close()
        return float(result)

    def get_profitability_report(self, days: int = 30) -> dict:
        """
        Generate profitability report for period.

        Args:
            days: Number of days to analyze

        Returns:
            Report dict with profitability metrics
        """
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        total_income = self.get_total_income(start_iso, end_iso)
        total_costs = self.get_total_costs(start_iso, end_iso)
        net_profit = total_income - total_costs

        return {
            'period_days': days,
            'period_start': start_iso,
            'period_end': end_iso,
            'total_income': total_income,
            'total_costs': total_costs,
            'net_profit': net_profit,
            'is_profitable': net_profit > 0,
            'profit_margin': (net_profit / total_income * 100) if total_income > 0 else 0
        }

    def save_profitability_report(self, report: dict) -> int:
        """
        Save profitability report to database.

        Args:
            report: Report dictionary

        Returns:
            Report ID
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        from datetime import datetime
        cursor.execute('''
            INSERT INTO profitability_reports
            (report_date, period_start, period_end, total_income, total_costs, net_profit, is_profitable, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            report.get('period_start'),
            report.get('period_end'),
            report.get('total_income', 0),
            report.get('total_costs', 0),
            report.get('net_profit', 0),
            1 if report.get('is_profitable') else 0,
            f"Margin: {report.get('profit_margin', 0):.1f}%"
        ))

        conn.commit()
        report_id = cursor.lastrowid
        conn.close()

        return report_id

    def get_latest_profitability_report(self) -> dict:
        """
        Get most recent profitability report.

        Returns:
            Report dict or None
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM profitability_reports
            ORDER BY report_date DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'id': row[0],
            'report_date': row[1],
            'period_start': row[2],
            'period_end': row[3],
            'total_income': row[4],
            'total_costs': row[5],
            'net_profit': row[6],
            'is_profitable': bool(row[7]),
            'notes': row[8]
        }

    def record_income_opportunity(self, opportunity_type: str, description: str, 
                                 estimated_value: float = 0, effort_estimate: str = "") -> int:
        """
        Record identified income opportunity.

        Args:
            opportunity_type: Type of opportunity
            description: Detailed description
            estimated_value: Estimated value
            effort_estimate: Effort estimate (low/medium/high)

        Returns:
            Opportunity ID
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        from datetime import datetime
        cursor.execute('''
            INSERT INTO income_opportunities
            (timestamp, opportunity_type, description, estimated_value, effort_estimate, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            opportunity_type,
            description[:500],
            estimated_value,
            effort_estimate,
            'identified'
        ))

        conn.commit()
        opp_id = cursor.lastrowid
        conn.close()

        return opp_id

    def get_pending_opportunities(self) -> list:
        """
        Get pending income opportunities.

        Returns:
            List of opportunity dicts
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM income_opportunities
            WHERE status IN ('identified', 'in_progress')
            ORDER BY estimated_value DESC
        ''')

        opportunities = []
        for row in cursor.fetchall():
            opportunities.append({
                'id': row[0],
                'timestamp': row[1],
                'type': row[2],
                'description': row[3],
                'estimated_value': row[4],
                'effort': row[5],
                'status': row[6],
                'notes': row[7]
            })

        conn.close()
        return opportunities

    def update_opportunity_status(self, opportunity_id: int, status: str, notes: str = ""):
        """
        Update opportunity status.

        Args:
            opportunity_id: ID of opportunity
            status: New status (identified, in_progress, completed, rejected)
            notes: Optional notes
        """
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE income_opportunities
            SET status = ?, notes = ?
            WHERE id = ?
        ''', (status, notes[:200], opportunity_id))

        conn.commit()
        conn.close()

        self.scribe.log_action(f"Opportunity {opportunity_id} status updated", outcome=f"New status: {status}")