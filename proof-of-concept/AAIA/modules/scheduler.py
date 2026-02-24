"""
Autonomous Task Scheduler Module - Self-Directed Background Operations

PURPOSE:
The Scheduler enables the AI to operate autonomously by running background tasks
at specified intervals. It provides the "heartbeat" of self-development, regularly
performing maintenance, reflection, and improvement activities without requiring
external triggers.

PROBLEM SOLVED:
A truly autonomous AI shouldn't wait for commands to improve itself:
- System health needs continuous monitoring
- Regular reflection improves understanding of master
- Capabilities should be discovered and developed proactively
- Evolution should happen on a schedule, not just on demand
- Self-diagnosis should run periodically

KEY RESPONSIBILITIES:
1. Run background tasks at specified intervals
2. Priority-based task queue management
3. System health checks (CPU, memory, disk)
4. Economic review and budget management
5. Daily reflection cycles
6. Tool maintenance
7. Evolution checks
8. Self-diagnosis execution
9. Performance snapshot recording
10. Capability discovery
11. Intent prediction
12. Environment exploration

SCHEDULED TASKS:
- system_health_check: Every 30 minutes
- economic_review: Every hour
- reflection_cycle: Every 24 hours
- tool_maintenance: Every 6 hours
- evolution_check: Every 24 hours
- self_diagnosis: Every 6 hours
- performance_snapshot: Every hour
- capability_discovery: Every 48 hours
- intent_prediction: Every 12 hours
- environment_exploration: Every 24 hours

DEPENDENCIES: Scribe, Router, Economics, Forge, SelfDiagnosis, SelfModification, Evolution
OUTPUTS: Background execution of autonomous tasks, scheduler status
"""
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
import psutil
from modules.self_diagnosis import SelfDiagnosis
from modules.self_modification import SelfModification
from modules.evolution import EvolutionManager
from modules.evolution_pipeline import EvolutionPipeline


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

        # Add evolution pipeline
        self.diagnosis = SelfDiagnosis(scribe, router, forge)
        self.modification = SelfModification(scribe, router, forge)
        self.evolution = EvolutionManager(scribe, router, forge, self.diagnosis, self.modification)
        self.pipeline = EvolutionPipeline(scribe, router, forge, self.diagnosis, self.modification, self.evolution)

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
        self.register_task(
            name="evolution_check",
            function=self.check_evolution_needs,
            interval_hours=24,  # Daily check
            priority=2
        )
        
        self.register_task(
            name="self_diagnosis",
            function=self.run_self_diagnosis,
            interval_hours=6,  # Every 6 hours
            priority=3
        )
        
        # Advanced self-development tasks
        self.register_task(
            name="performance_snapshot",
            function=self.record_performance_snapshot,
            interval_hours=1,
            priority=2
        )
        self.register_task(
            name="capability_discovery",
            function=self.run_capability_discovery,
            interval_hours=48,  # Every 2 days
            priority=3
        )
        self.register_task(
            name="intent_prediction",
            function=self.run_intent_prediction,
            interval_hours=12,
            priority=3
        )
        self.register_task(
            name="environment_exploration",
            function=self.run_environment_exploration,
            interval_hours=24,
            priority=3
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

    def check_evolution_needs(self):
        """Check if evolution is needed and run if necessary"""
        # Run quick diagnosis
        diagnosis = self.diagnosis.perform_full_diagnosis()
        
        # Check evolution conditions
        if self.pipeline.should_evolve(diagnosis):
            # Notify before starting evolution
            self.scribe.log_action(
                "Evolution conditions met",
                f"Starting evolution pipeline with {len(diagnosis.get('improvement_opportunities', []))} opportunities",
                "evolution_triggered"
            )
            
            # Run evolution pipeline
            result = self.pipeline.run_autonomous_evolution()
            
            return f"Evolution pipeline completed: {result.get('status')}"
        else:
            return "Evolution not needed at this time"
            
    def run_self_diagnosis(self):
        """Run periodic self-diagnosis"""
        diagnosis = self.diagnosis.perform_full_diagnosis()
        
        # Log key metrics
        bottlenecks = len(diagnosis.get("bottlenecks", []))
        opportunities = len(diagnosis.get("improvement_opportunities", []))
        
        return f"Self-diagnosis complete: {bottlenecks} bottlenecks, {opportunities} opportunities"
    
    def record_performance_snapshot(self):
        """Record performance metrics for trend analysis"""
        from modules.metacognition import MetaCognition
        metacog = MetaCognition(self.scribe, self.router, self.diagnosis)
        metrics = metacog.collect_current_metrics()
        metacog.record_performance_snapshot(metrics)
        return f"Performance snapshot recorded: {metrics.get('error_rate', 0)}% error rate"
    
    def run_capability_discovery(self):
        """Discover new capabilities the system could develop"""
        from modules.capability_discovery import CapabilityDiscovery
        cap_discovery = CapabilityDiscovery(self.scribe, self.router, self.forge)
        capabilities = cap_discovery.discover_new_capabilities()
        return f"Discovered {len(capabilities)} new capabilities"
    
    def run_intent_prediction(self):
        """Predict master's next commands"""
        from modules.intent_predictor import IntentPredictor
        intent_pred = IntentPredictor(self.scribe, self.router)
        predictions = intent_pred.predict_next_commands()
        return f"Made {len(predictions)} intent predictions"
    
    def run_environment_exploration(self):
        """Explore environment for opportunities"""
        from modules.environment_explorer import EnvironmentExplorer
        env_exp = EnvironmentExplorer(self.scribe, self.router)
        exploration = env_exp.explore_environment()
        opportunities = env_exp.find_development_opportunities()
        return f"Environment explored: {len(exploration.get('available_commands', []))} commands, {len(opportunities)} opportunities"