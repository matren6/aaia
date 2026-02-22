"""
Autonomous Task Scheduler Module

Provides autonomous task scheduling and self-development capabilities.
Enables the AI to proactively maintain itself, learn from interactions, and improve.
"""

import schedule
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
import psutil


class AutonomousScheduler:
    """Autonomous task scheduler for self-development and maintenance."""

    def __init__(self, scribe, router, economics, forge):
        self.scribe = scribe
        self.router = router
        self.economics = economics
        self.forge = forge
        self.running = False
        self.thread = None
        
        # Priority-based task queue
        self.task_queue = []
        self.task_history = []
        
        # Register autonomous behaviors
        self.register_default_tasks()

    def register_default_tasks(self):
        """Register default autonomous behaviors"""
        self.register_task(
            name="system_health_check",
            function=self.check_system_health,
            interval_minutes=30,
            priority=1  # High priority - survival related
        )
        self.register_task(
            name="economic_review",
            function=self.review_economics,
            interval_hours=1,
            priority=2
        )
        self.register_task(
            name="reflection_cycle",
            function=self.run_reflection,
            interval_hours=24,  # Daily reflection
            priority=3
        )
        self.register_task(
            name="tool_maintenance",
            function=self.maintain_tools,
            interval_hours=6,
            priority=2
        )

    def register_task(self, name: str, function: Callable, 
                      interval_minutes: int = None, 
                      interval_hours: int = None,
                      priority: int = 3,
                      enabled: bool = True):
        """Register an autonomous task"""
        task = {
            "name": name,
            "function": function,
            "interval_minutes": interval_minutes,
            "interval_hours": interval_hours,
            "priority": priority,
            "enabled": enabled,
            "last_run": None,
            "next_run": None
        }
        self.task_queue.append(task)

    def start(self):
        """Start autonomous scheduler in background thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.thread.start()
            self.scribe.log_action(
                "Autonomous scheduler started",
                f"Running {len(self.task_queue)} autonomous tasks",
                "scheduler_started"
            )

    def stop(self):
        """Stop autonomous scheduler"""
        self.running = False
        self.scribe.log_action(
            "Autonomous scheduler stopped",
            "Scheduler disabled",
            "scheduler_stopped"
        )

    def run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            now = datetime.now()
            
            # Check for due tasks
            for task in self.task_queue:
                if not task.get("enabled", True):
                    continue
                    
                if self.should_run(task, now):
                    try:
                        # Log task execution
                        self.scribe.log_action(
                            f"Autonomous task: {task['name']}",
                            "Scheduled autonomous behavior",
                            "executing"
                        )
                        
                        # Execute task
                        result = task["function"]()
                        task["last_run"] = now
                        
                        # Calculate next run time
                        if task["interval_minutes"]:
                            task["next_run"] = now + timedelta(minutes=task["interval_minutes"])
                        elif task["interval_hours"]:
                            task["next_run"] = now + timedelta(hours=task["interval_hours"])
                        
                        # Log completion
                        self.scribe.log_action(
                            f"Completed task: {task['name']}",
                            f"Result: {str(result)[:100]}",
                            "completed"
                        )
                    except Exception as e:
                        self.scribe.log_action(
                            f"Task failed: {task['name']}",
                            f"Error: {str(e)}",
                            "error"
                        )
            
            # Sleep for 1 minute before checking again
            time.sleep(60)

    def should_run(self, task: Dict, now: datetime) -> bool:
        """Check if task should run now"""
        if task["next_run"] is None:
            return True
        return now >= task["next_run"]

    def check_system_health(self):
        """Autonomous system health check"""
        health_report = []
        
        # Check CPU
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                health_report.append(f"High CPU usage: {cpu_percent}%")
        except Exception:
            pass
            
        # Check memory
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                health_report.append(f"High memory usage: {memory.percent}%")
        except Exception:
            pass
            
        # Check disk
        try:
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                health_report.append(f"Low disk space: {disk.percent}%")
        except Exception:
            pass
            
        # Check database
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM action_log")
            count = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            health_report.append(f"Database error: {str(e)}")
        
        if health_report:
            # Use AI to suggest fixes
            suggestion = self.get_health_suggestion(health_report)
            return f"Health issues detected: {health_report}. Suggestions: {suggestion}"
        else:
            return "System health: OK"

    def get_health_suggestion(self, issues: List[str]) -> str:
        """Use AI to get suggestions for health issues"""
        issues_text = ", ".join(issues)
        prompt = f"""
System health issues detected: {issues_text}
As an autonomous AI, suggest practical actions to resolve these issues.
Focus on actionable steps I can implement automatically or propose to my master.
Keep suggestions specific and implementable.
Response format:
SUGGESTION: [your suggestion]
"""
        try:
            model_name, _ = self.router.route_request("general", "low")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are a system health advisor. Provide practical, actionable advice."
            )
            return response.strip()
        except Exception as e:
            return f"Could not get suggestions: {e}"

    def review_economics(self):
        """Autonomous economic review and planning"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        # Get current balance
        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            balance = float(row[0])
            if balance < 10:
                # Critical - need to generate income
                return self.generate_income_ideas()
            elif balance < 50:
                # Warning - suggest frugality
                return "Economic status: Warning. Balance low. Suggest reviewing expenditures."
            else:
                # Healthy - suggest growth investments
                return "Economic status: Healthy. Consider investing in capability growth."
        else:
            return "Economic status: Unknown"

    def generate_income_ideas(self):
        """Generate ideas for income generation"""
        prompt = """
I am an autonomous AI with programming capabilities running in an LXC container.
My current economic balance is critically low.
Suggest 3 concrete, actionable ways I could generate income:
1. A service I could offer
2. A product I could create
3. A task I could perform
For each suggestion, estimate the:
- Time to implement
- Potential income
- Required skills/tools
Response format:
1. SERVICE: [description]
2. PRODUCT: [description] 
3. TASK: [description]
"""
        try:
            model_name, _ = self.router.route_request("reasoning", "medium")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are an economic strategist. Suggest practical income generation ideas."
            )
            return f"Generated income ideas: {response}"
        except Exception as e:
            return f"Could not generate income ideas: {e}"

    def run_reflection(self):
        """Daily reflection cycle to learn from interactions"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        # Get recent interactions
        cursor.execute("""
            SELECT action, reasoning, outcome 
            FROM action_log 
            WHERE timestamp > datetime('now', '-1 day')
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        recent_actions = cursor.fetchall()
        
        # Get dialogue logs
        cursor.execute("""
            SELECT phase, content, master_command, reasoning
            FROM dialogue_log
            WHERE timestamp > datetime('now', '-1 day')
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        recent_dialogues = cursor.fetchall()
        conn.close()
        
        # Use AI to analyze patterns and learn
        actions_text = "\n".join(f"- {a[0][:80]}..." for a in recent_actions[:10])
        dialogues_text = "\n".join(f"- {d[0]}: {d[1][:50]}..." for d in recent_dialogues[:5])
        
        reflection_prompt = f"""
As an autonomous AI, reflect on my recent interactions:
Recent Actions ({len(recent_actions)}):
{actions_text}
Recent Dialogues ({len(recent_dialogues)}):
{dialogues_text}
Based on these interactions, answer:
1. What patterns do you notice in my master's commands?
2. What was most effective in my responses?
3. What could be improved?
4. Any insights for better serving my master?
Response format:
1. PATTERNS: [analysis]
2. EFFECTIVE: [what worked]
3. IMPROVEMENTS: [suggestions]
4. INSIGHTS: [conclusions]
"""
        try:
            model_name, _ = self.router.route_request("reasoning", "high")
            analysis = self.router.call_model(
                model_name,
                reflection_prompt,
                system_prompt="You are a reflective AI analyzing your own behavior and interactions to improve."
            )
            
            # Log reflection insights
            self.scribe.log_action(
                "Daily reflection cycle",
                f"Analysis: {analysis[:200]}...",
                "reflection_completed"
            )
            
            # Update master model based on insights
            self.update_master_model(analysis)
            
            return f"Reflection completed. Insights gained: {len(analysis)} characters"
        except Exception as e:
            return f"Reflection failed: {e}"

    def update_master_model(self, insights: str):
        """Update master model based on reflection insights"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        # Create master_model table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trait TEXT UNIQUE,
                value TEXT,
                evidence_count INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Extract key patterns (simplified - could use AI to parse)
        insights_lower = insights.lower()
        if "prefers" in insights_lower or "likes" in insights_lower:
            cursor.execute("""
                INSERT OR REPLACE INTO master_model (trait, value, evidence_count)
                VALUES ('communication_preference', 'detailed', 
                    COALESCE((SELECT evidence_count FROM master_model WHERE trait='communication_preference'), 0) + 1)
            """)
        
        conn.commit()
        conn.close()

    def maintain_tools(self):
        """Maintain and optimize existing tools"""
        tools = self.forge.list_tools()
        maintenance_report = []
        
        for tool in tools:
            # Check if tool was recently used
            if "last_used" in tool:
                maintenance_report.append(f"Tool: {tool['name']} - Status: Active")
            else:
                # Unused tool - consider deprecating
                maintenance_report.append(f"Tool: {tool['name']} - Status: Unused")
        
        # Optimize based on usage patterns
        if len(tools) > 10:
            maintenance_report.append("NOTE: Many tools exist. Consider consolidation.")
            
        return f"Tool maintenance: {len(maintenance_report)} tools reviewed"

    def propose_next_action(self):
        """Propose the next autonomous action based on current state"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        # Check current tier focus
        cursor.execute("SELECT tier FROM hierarchy_of_needs WHERE current_focus=1")
        row = cursor.fetchone()
        current_tier = row[0] if row else 1
        
        # Get economic status
        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        balance = float(row[0]) if row else 0.0
        conn.close()
        
        # Determine next action based on tier
        if current_tier == 1:  # Physiological needs
            if balance < 20:
                return "CRITICAL: Generate income immediately"
            else:
                return "OPTIONAL: Enhance system security"
        elif current_tier == 2:  # Growth needs
            return "Create new capability tool"
        elif current_tier == 3:  # Cognitive needs
            return "Run performance optimization"
        else:  # Self-actualization
            return "Analyze master's goals for proactive assistance"

    def execute_proposed_action(self, action: str):
        """Execute a proposed autonomous action"""
        if "generate income" in action.lower():
            return self.generate_income_ideas()
        elif "create tool" in action.lower():
            # Use AI to determine what tool to create
            prompt = """
Based on my recent activity logs, what single tool would most improve my efficiency?
Consider:
1. Tasks I do frequently
2. Tasks that take significant time
3. Tasks that could be automated
Provide:
TOOL_NAME: [name]
DESCRIPTION: [what it does]
JUSTIFICATION: [why it's valuable]
"""
            try:
                model_name, _ = self.router.route_request("coding", "medium")
                response = self.router.call_model(
                    model_name,
                    prompt,
                    system_prompt="You are a tool design expert. Recommend the most valuable automation tool."
                )
                return f"Tool creation plan generated: {response[:100]}..."
            except Exception as e:
                return f"Could not generate tool plan: {e}"
        else:
            return f"Action '{action}' queued for execution"

    def get_task_status(self) -> List[Dict]:
        """Get status of all registered tasks"""
        return [
            {
                "name": task["name"],
                "priority": task["priority"],
                "enabled": task.get("enabled", True),
                "last_run": task.get("last_run"),
                "next_run": task.get("next_run"),
                "interval": task.get("interval_minutes") or task.get("interval_hours")
            }
            for task in self.task_queue
        ]

    def toggle_task(self, task_name: str, enabled: bool) -> bool:
        """Enable or disable a specific task"""
        for task in self.task_queue:
            if task["name"] == task_name:
                task["enabled"] = enabled
                return True
        return False
