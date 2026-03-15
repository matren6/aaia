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
from typing import Optional, Dict, List
from datetime import datetime, timedelta
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

    def calculate_net_position(self, days: int = 30) -> Dict:
        """
        Calculate comprehensive financial position for a given period.

        Computes income, costs, and profit metrics used for determining
        economic health and hierarchy tier progression.

        Args:
            days: Number of days to analyze (default 30)

        Returns:
            Dict with keys:
            - period_days: Number of days analyzed
            - total_income: Sum of all income
            - total_costs: Sum of all costs
            - net_position: Income minus costs
            - profitable: Boolean indicating if net > 0
            - income_breakdown: Dict of income by source
            - cost_breakdown: Dict of costs by category
            - trend: "improving", "declining", or "stable"
            - previous_period_comparison: Difference from previous period
            - roi_percentage: Return on investment percentage
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get income breakdown
            income_sources = self._get_income_breakdown(start_date, end_date)
            total_income = sum(income_sources.values())

            # Get cost breakdown
            cost_categories = self._get_cost_breakdown(start_date, end_date)
            total_costs = sum(cost_categories.values())

            # Net calculation
            net_position = total_income - total_costs

            # Trend analysis - compare with previous period
            previous_period_net = self._get_previous_period_net(days)
            if net_position > previous_period_net:
                trend = 'improving'
            elif net_position < previous_period_net:
                trend = 'declining'
            else:
                trend = 'stable'

            # Calculate ROI
            roi_percentage = (net_position / max(total_costs, 1)) * 100 if total_costs > 0 else 0

            result = {
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_income': total_income,
                'total_costs': total_costs,
                'net_position': net_position,
                'profitable': net_position > 0,
                'income_breakdown': income_sources,
                'cost_breakdown': cost_categories,
                'trend': trend,
                'previous_period_comparison': net_position - previous_period_net,
                'roi_percentage': roi_percentage
            }

            # Check for economic crisis
            if net_position < -100 or (total_costs > 0 and net_position < -total_costs * 0.5):
                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        severity = 'critical' if net_position < -total_costs else 'high'
                        self.event_bus.emit(Event(EventType.ECONOMIC_CRISIS, {
                            'severity': severity,
                            'net_loss': abs(net_position),
                            'days_analyzed': days,
                            'crisis_threshold_exceeded': True
                        }))
                    except:
                        pass

            # Store analysis in database for trend tracking
            self._record_financial_analysis(result)

            return result

        except Exception as e:
            self.scribe.log_system_event("FINANCIAL_ANALYSIS_ERROR", {'error': str(e)})
            return {
                'period_days': days,
                'total_income': 0,
                'total_costs': 0,
                'net_position': 0,
                'profitable': False,
                'income_breakdown': {},
                'cost_breakdown': {},
                'trend': 'unknown',
                'roi_percentage': 0,
                'error': str(e)
            }

    def _get_income_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Get income by source for period."""
        try:
            income = self.get_income_by_source(start_date.isoformat(), end_date.isoformat())
            return income if income else {}
        except Exception:
            return {}

    def _get_cost_breakdown(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Get costs by category for period."""
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT category, COALESCE(SUM(ABS(amount)), 0) as total
                FROM economic_log
                WHERE timestamp >= ? AND timestamp <= ? AND amount < 0
                GROUP BY category
            ''', (start_date.isoformat(), end_date.isoformat()))

            breakdown = {}
            for row in cursor.fetchall():
                breakdown[row[0]] = row[1]

            conn.close()
            return breakdown
        except Exception:
            return {}

    def _get_previous_period_net(self, days: int) -> float:
        """Get net position from previous equivalent period."""
        try:
            end_date = datetime.now() - timedelta(days=days)
            start_date = end_date - timedelta(days=days)

            income_sources = self._get_income_breakdown(start_date, end_date)
            total_income = sum(income_sources.values())

            cost_breakdown = self._get_cost_breakdown(start_date, end_date)
            total_costs = sum(cost_breakdown.values())

            return total_income - total_costs
        except Exception:
            return 0

    def _record_financial_analysis(self, analysis: Dict) -> None:
        """Store financial analysis for trend tracking."""
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            cursor = conn.cursor()

            # Store in financial_snapshots or similar table if available
            # For now, just log to audit
            self.scribe.log_system_event("FINANCIAL_ANALYSIS", {
                'period': analysis.get('period_days'),
                'net_position': analysis.get('net_position'),
                'profitable': analysis.get('profitable'),
                'trend': analysis.get('trend')
            })

            conn.close()
        except Exception:
            pass

    def get_profitability_status(self) -> Dict:
        """
        Get current profitability status for hierarchy progression checks.

        Returns:
            Dict with keys:
            - is_profitable_30d: Profitable in last 30 days
            - is_profitable_7d: Profitable in last 7 days
            - consistent_profitability: Both 30d and 7d profitable
            - trend: Current trend direction
            - economic_health_score: 0-100 health score
        """
        try:
            net_30 = self.calculate_net_position(30)
            net_7 = self.calculate_net_position(7)

            status = {
                'is_profitable_30d': net_30['profitable'],
                'is_profitable_7d': net_7['profitable'],
                'consistent_profitability': net_30['profitable'] and net_7['profitable'],
                'trend': net_30['trend'],
                'economic_health_score': self._calculate_health_score(net_30, net_7)
            }

            return status

        except Exception as e:
            self.scribe.log_system_event("PROFITABILITY_STATUS_ERROR", {'error': str(e)})
            return {
                'is_profitable_30d': False,
                'is_profitable_7d': False,
                'consistent_profitability': False,
                'trend': 'unknown',
                'economic_health_score': 0
            }

    def _calculate_health_score(self, net_30: Dict, net_7: Dict) -> int:
        """
        Calculate economic health score 0-100.

        Factors:
        - Profitability in both periods: +40 points
        - Positive trend: +30 points
        - Good ROI: +30 points
        """
        score = 30  # Baseline

        # Profitability bonus
        if net_30['profitable']:
            score += 20
        if net_7['profitable']:
            score += 20

        # Trend bonus/penalty
        if net_30['trend'] == 'improving':
            score += 15
        elif net_30['trend'] == 'declining':
            score -= 15

        # ROI bonus
        roi = net_30.get('roi_percentage', 0)
        if roi > 20:
            score += 15
        elif roi < -20:
            score -= 15

        return max(0, min(100, score))

    def analyze_trends(self) -> Dict:
        """
        Analyze economic trends over time.

        Returns:
            Dict with trend analysis
        """
        try:
            net_30 = self.calculate_net_position(30)
            net_7 = self.calculate_net_position(7)
            net_1 = self.calculate_net_position(1)

            trend = net_30['trend']

            if trend == 'declining':
                analysis = "Revenue is declining compared to previous period"
                recommendations = [
                    "Increase income-generating activities",
                    "Reduce operational costs",
                    "Identify and implement high-ROI opportunities"
                ]
            elif trend == 'improving':
                analysis = "Revenue is improving - good trajectory"
                recommendations = [
                    "Continue current high-performing activities",
                    "Scale successful operations",
                    "Reinvest profits into growth"
                ]
            else:
                analysis = "Revenue is stable"
                recommendations = [
                    "Monitor for changes",
                    "Explore new opportunities",
                    "Maintain efficiency"
                ]

            return {
                'trend': trend,
                'analysis': analysis,
                'recommendations': recommendations,
                'current_status': net_30,
                'short_term': net_7,
                'very_short_term': net_1,
                'potential': max(0, net_7['total_income'] * 4)  # Extrapolate 7d to 30d
            }

        except Exception as e:
            self.scribe.log_system_event("TREND_ANALYSIS_ERROR", {'error': str(e)})
            return {
                'trend': 'unknown',
                'analysis': 'Unable to analyze trends',
                'recommendations': [],
                'error': str(e)
            }