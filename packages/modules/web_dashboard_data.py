"""
Dashboard Data Aggregation Module

Provides data aggregation from various AAIA modules for the web dashboard.
Centralizes data fetching logic used by REST API endpoints and WebSocket events.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class DashboardDataAggregator:
    """Aggregates data from multiple AAIA modules for dashboard display."""

    def __init__(self, scribe=None, economics=None, goals=None, scheduler=None,
                 hierarchy=None, master_model=None, container=None, config=None):
        """
        Initialize data aggregator.

        Args:
            scribe: Scribe module for database access
            economics: EconomicManager for balance/transaction data
            goals: GoalSystem for goal data
            scheduler: AutonomousScheduler for task data
            hierarchy: HierarchyManager for tier/focus data
            master_model: MasterModelManager for profile data
            container: DI Container for accessing other modules
            config: SystemConfig with database path
        """
        self.scribe = scribe
        self.economics = economics
        self.goals = goals
        self.scheduler = scheduler
        self.hierarchy = hierarchy
        self.master_model = master_model
        self.container = container
        self.config = config

        # Get database path
        if config:
            from modules.settings import get_config
            self.db_path = get_config().database.path
        else:
            self.db_path = "data/scribe.db"

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "status": "running",
            }

            # Get balance
            if self.economics:
                try:
                    status["balance"] = self.economics.get_current_balance()
                except Exception:
                    status["balance"] = 100.0
            else:
                status["balance"] = self._get_balance_from_db()

            # Get actions logged
            status["actions_logged"] = self._get_action_count()

            # Get tier/focus info
            if self.hierarchy:
                try:
                    tier_info = self.hierarchy.get_current_tier()
                    status["tier"] = tier_info
                except Exception:
                    status["tier"] = {"name": "Unknown", "tier": 0, "progress": 0}

            # Get scheduler status
            if self.scheduler:
                try:
                    status["scheduler_running"] = self.scheduler.running
                    status["active_tasks"] = len([t for t in self.scheduler.tasks if t.enabled])
                except Exception:
                    status["scheduler_running"] = False
                    status["active_tasks"] = 0

            return status
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_goals(self, status: Optional[str] = None, limit: int = 50, 
                  offset: int = 0) -> Dict[str, Any]:
        """Get goals with optional filtering."""
        try:
            if self.goals:
                try:
                    all_goals = self.goals.get_all_goals()
                    
                    # Filter by status
                    if status and status != "all":
                        all_goals = [g for g in all_goals if g.get("status") == status]
                    
                    # Count before pagination
                    total = len(all_goals)
                    
                    # Apply pagination
                    paginated = all_goals[offset:offset + limit]
                    
                    return {
                        "goals": paginated,
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                    }
                except Exception:
                    pass

            # Fallback to database
            return self._get_goals_from_db(status, limit, offset)
        except Exception as e:
            return {
                "error": str(e),
                "goals": [],
                "total": 0,
            }

    def get_economics(self, days: int = 30) -> Dict[str, Any]:
        """Get economics data for specified period."""
        try:
            if not self.economics:
                return self._get_economics_from_db(days)

            try:
                current_balance = self.economics.get_current_balance()
                transactions = self.economics.get_transactions(days=days)
                
                total_income = sum(t.amount for t in transactions if t.amount > 0)
                total_costs = sum(abs(t.amount) for t in transactions if t.amount < 0)
                net_profit = total_income - total_costs
                margin = (net_profit / total_income * 100) if total_income > 0 else 0
                
                return {
                    "balance": current_balance,
                    "total_income": total_income,
                    "total_costs": total_costs,
                    "net_profit": net_profit,
                    "profit_margin": margin,
                    "is_profitable": net_profit > 0,
                    "transaction_count": len(transactions),
                }
            except Exception:
                return self._get_economics_from_db(days)
        except Exception as e:
            return {
                "error": str(e),
                "balance": 0.0,
                "is_profitable": False,
            }

    def get_master_profile(self) -> Dict[str, Any]:
        """Get master psychological profile."""
        try:
            if self.master_model:
                try:
                    profile = self.master_model.get_profile()
                    interactions_count = self.master_model.get_interaction_count()
                    
                    return {
                        "profile": profile,
                        "interaction_count": interactions_count,
                        "last_reflection": self.master_model.get_last_reflection_time(),
                        "confidence": self.master_model.get_confidence_score(),
                    }
                except Exception:
                    pass

            # Fallback
            return {
                "profile": {},
                "interaction_count": 0,
                "last_reflection": None,
                "confidence": 0.0,
            }
        except Exception as e:
            return {
                "error": str(e),
                "profile": {},
            }

    def get_logs(self, filters: Optional[Dict] = None, limit: int = 50,
                 offset: int = 0) -> Dict[str, Any]:
        """Get action logs with optional filtering."""
        try:
            return self._get_logs_from_db(filters, limit, offset)
        except Exception as e:
            return {
                "error": str(e),
                "logs": [],
                "total": 0,
            }

    def get_tasks(self) -> Dict[str, Any]:
        """Get scheduler tasks."""
        try:
            if not self.scheduler:
                return {"tasks": [], "next_proposed_action": None, "error": "Scheduler not initialized"}

            # Scheduler uses task_queue (list of dicts), not tasks
            tasks = []
            for task in self.scheduler.task_queue:
                # Convert datetime to string if present
                last_run_str = None
                next_run_str = None

                if task.get("last_run"):
                    last_run_str = task["last_run"].isoformat() if isinstance(task["last_run"], datetime) else str(task["last_run"])

                if task.get("next_run"):
                    next_run_str = task["next_run"].isoformat() if isinstance(task["next_run"], datetime) else str(task["next_run"])

                tasks.append({
                    "id": task["name"],
                    "name": task["name"],
                    "enabled": task.get("enabled", True),
                    "priority": task.get("priority", 3),
                    "interval_minutes": task.get("interval_minutes", 0),
                    "interval_hours": task.get("interval_hours", 0),
                    "last_run": last_run_str,
                    "next_run": next_run_str,
                    "execution_count": 0,  # TODO: Track this
                })

            return {
                "tasks": tasks,
                "total": len(tasks),
                "next_proposed_action": None,  # TODO: Implement
            }
        except Exception as e:
            print(f"Error getting tasks: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "tasks": [],
                "total": 0,
            }

    def get_tools(self) -> Dict[str, Any]:
        """Get registered tools."""
        try:
            tools_dir = Path(self.config.tools.tools_dir) if self.config else Path("tools")
            
            if not tools_dir.exists():
                return {"tools": [], "total": 0}

            tools = []
            for tool_file in tools_dir.glob("*.py"):
                if tool_file.name.startswith("_"):
                    continue

                tools.append({
                    "name": tool_file.stem,
                    "description": "User-defined tool",
                    "created_at": datetime.fromtimestamp(tool_file.stat().st_ctime).isoformat(),
                    "usage_count": 0,  # TODO: Track from database
                    "last_used": None,
                })

            return {
                "tools": tools,
                "total": len(tools),
            }
        except Exception as e:
            return {
                "error": str(e),
                "tools": [],
                "total": 0,
            }

    def get_config(self) -> Dict[str, Any]:
        """Get complete current configuration with all settings."""
        try:
            if not self.config:
                from modules.settings import get_config
                self.config = get_config()

            from dataclasses import asdict
            import os

            # Get full configuration as dict
            config_dict = asdict(self.config)

            # Add environment variables that aren't in config
            env_vars = {
                "PYTHONPATH": os.getenv("PYTHONPATH", ""),
                "PATH": os.getenv("PATH", "")[:200] + "...",  # Truncate long paths
                "DB_PATH": os.getenv("DB_PATH", ""),
                "WEB_SERVER_ENABLED": os.getenv("WEB_SERVER_ENABLED", ""),
            }

            config_dict["environment"] = env_vars

            return config_dict
        except Exception as e:
            return {"error": str(e)}

    # Database helper methods

    def _get_balance_from_db(self) -> float:
        """Get current balance from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_state WHERE key='current_balance' LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            return float(row[0]) if row else 100.0
        except Exception:
            return 100.0

    def _get_action_count(self) -> int:
        """Get total action count from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM action_log")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0

    def _get_goals_from_db(self, status: Optional[str] = None, limit: int = 50,
                           offset: int = 0) -> Dict[str, Any]:
        """Get goals from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()

            # Get total count
            count_query = "SELECT COUNT(*) FROM goals WHERE 1=1"
            count_params = []
            if status and status != "all":
                count_query += " AND status = ?"
                count_params.append(status)

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]

            # Get paginated results
            query = "SELECT * FROM goals WHERE 1=1"
            params = []

            if status and status != "all":
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            goals = [dict(row) for row in rows]
            conn.close()

            # Count by status
            active = sum(1 for g in goals if g.get('status') == 'active')
            completed = sum(1 for g in goals if g.get('status') == 'completed')

            return {
                "goals": goals,
                "total": total,
                "limit": limit,
                "offset": offset,
                "active": active,
                "completed": completed,
            }
        except Exception as e:
            print(f"Error fetching goals: {e}")
            return {
                "goals": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "active": 0,
                "completed": 0,
            }

    def _get_economics_from_db(self, days: int = 30) -> Dict[str, Any]:
        """Get economics data from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get transactions from last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute(
                "SELECT amount, timestamp FROM action_log WHERE timestamp > ? AND action LIKE '%transaction%'",
                (cutoff_date.isoformat(),)
            )
            transactions = cursor.fetchall()
            conn.close()

            total_income = sum(t[0] for t in transactions if t[0] > 0)
            total_costs = sum(abs(t[0]) for t in transactions if t[0] < 0)
            net_profit = total_income - total_costs
            margin = (net_profit / total_income * 100) if total_income > 0 else 0

            return {
                "balance": self._get_balance_from_db(),
                "total_income": total_income,
                "total_costs": total_costs,
                "net_profit": net_profit,
                "profit_margin": margin,
                "is_profitable": net_profit > 0,
            }
        except Exception:
            return {
                "balance": 100.0,
                "total_income": 0,
                "total_costs": 0,
                "net_profit": 0,
                "profit_margin": 0,
                "is_profitable": False,
            }

    def _get_logs_from_db(self, filters: Optional[Dict] = None, limit: int = 50,
                          offset: int = 0) -> Dict[str, Any]:
        """Get logs from database with optional filtering."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()

            # Build query - note: action_log has 'outcome' not 'status', 'reasoning' not 'details'
            query = "SELECT id, timestamp, action, reasoning as details, outcome as status, cost FROM action_log WHERE 1=1"
            params = []

            if filters:
                if filters.get("action"):
                    query += " AND action LIKE ?"
                    params.append(f"%{filters['action']}%")
                if filters.get("status"):
                    query += " AND outcome = ?"
                    params.append(filters["status"])

            # Get total count first (without LIMIT)
            count_query = f"SELECT COUNT(*) FROM action_log WHERE 1=1"
            count_params = []
            if filters:
                if filters.get("action"):
                    count_query += " AND action LIKE ?"
                    count_params.append(f"%{filters['action']}%")
                if filters.get("status"):
                    count_query += " AND outcome = ?"
                    count_params.append(filters["status"])

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]

            # Get paginated results
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]
            conn.close()

            return {
                "logs": logs,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        except Exception as e:
            print(f"Error fetching logs: {e}")
            import traceback
            traceback.print_exc()
            return {"logs": [], "total": 0, "limit": limit, "offset": offset}
