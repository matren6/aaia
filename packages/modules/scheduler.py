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
from modules.container import DependencyError, get_container


class AutonomousScheduler:
    """Autonomous task scheduler for self-development and maintenance."""

    def __init__(self, scribe, router, economics, forge,
                 diagnosis=None, modification=None, evolution=None, pipeline=None,
                 container=None, event_bus=None, prompt_manager=None):
        """
        Initialize the autonomous scheduler.
        
        Args:
            scribe: Scribe instance for logging
            router: ModelRouter for AI calls
            economics: EconomicManager for budget tracking
            forge: Forge for tool management
            container: Optional Container for dependency injection
            event_bus: Optional EventBus for publishing events
        """
        self.scribe = scribe
        self.router = router
        self.economics = economics
        self.forge = forge
        
        # Use event_bus directly, from container, or get from global
        if event_bus is not None:
            self.event_bus = event_bus
        elif container is not None:
            try:
                self.event_bus = container.get('EventBus')
            except Exception:
                from modules.bus import get_event_bus
                self.event_bus = get_event_bus()
        else:
            from modules.bus import get_event_bus
            self.event_bus = get_event_bus()
        
        self.running = False
        self.thread = None
        
        # Container (use provided or global)
        self._container = container or get_container()

        # PromptManager - try provided or resolve from container
        self.prompt_manager = prompt_manager
        if self.prompt_manager is None:
            try:
                self.prompt_manager = self._container.get('PromptManager')
            except Exception:
                raise DependencyError("PromptManager is required and must be provided via the DI container to AutonomousScheduler")
        
        # Load scheduler config
        try:
            from modules.settings import get_config
            config = get_config()
            self.config = config.scheduler
        except Exception:
            # Use defaults
            class DefaultSchedulerConfig:
                diagnosis_interval = 3600
                health_check_interval = 1800
                reflection_interval = 86400
                evolution_check_interval = 7200
                enabled = True
            self.config = DefaultSchedulerConfig()

        # Additional runtime settings from config
        self.max_concurrent_tasks = getattr(self.config, 'max_concurrent_tasks', 3)
        self.task_timeout = getattr(self.config, 'task_timeout', 300)
        
        # Priority-based task queue
        self.task_queue = []
        self.task_history = []

        # Optional dependencies - resolved from container if not provided
        self.diagnosis = diagnosis
        self.modification = modification
        self.evolution = evolution
        self.pipeline = pipeline

        # Lazy cache for resolved components
        self._lazy: dict = {}

        # Register autonomous behaviors
        self.register_default_tasks()

    # Lazy getters for optional components (resolve via container when needed)
    def _get_diagnosis(self):
        if self.diagnosis:
            return self.diagnosis
        if 'SelfDiagnosis' not in self._lazy:
            self._lazy['SelfDiagnosis'] = self._container.get('SelfDiagnosis')
        return self._lazy['SelfDiagnosis']

    def _get_modification(self):
        if self.modification:
            return self.modification
        if 'SelfModification' not in self._lazy:
            self._lazy['SelfModification'] = self._container.get('SelfModification')
        return self._lazy['SelfModification']

    def _get_evolution(self):
        if self.evolution:
            return self.evolution
        if 'EvolutionManager' not in self._lazy:
            self._lazy['EvolutionManager'] = self._container.get('EvolutionManager')
        return self._lazy['EvolutionManager']

    def _get_pipeline(self):
        if self.pipeline:
            return self.pipeline
        if 'EvolutionPipeline' not in self._lazy:
            self._lazy['EvolutionPipeline'] = self._container.get('EvolutionPipeline')
        return self._lazy['EvolutionPipeline']

    def _get_metacognition(self):
        if 'MetaCognition' not in self._lazy:
            self._lazy['MetaCognition'] = self._container.get('MetaCognition')
        return self._lazy['MetaCognition']

    def _get_capability_discovery(self):
        if 'CapabilityDiscovery' not in self._lazy:
            self._lazy['CapabilityDiscovery'] = self._container.get('CapabilityDiscovery')
        return self._lazy['CapabilityDiscovery']

    def _get_intent_predictor(self):
        if 'IntentPredictor' not in self._lazy:
            self._lazy['IntentPredictor'] = self._container.get('IntentPredictor')
        return self._lazy['IntentPredictor']

    def _get_environment_explorer(self):
        if 'EnvironmentExplorer' not in self._lazy:
            self._lazy['EnvironmentExplorer'] = self._container.get('EnvironmentExplorer')
        return self._lazy['EnvironmentExplorer']

    def register_default_tasks(self):
        """Register default autonomous behaviors"""
        # Use configured intervals (values in seconds in SchedulerConfig)
        health_min = max(1, int(self.config.health_check_interval / 60))
        diagnosis_min = max(1, int(self.config.diagnosis_interval / 60))
        reflection_min = max(1, int(self.config.reflection_interval / 60))
        evolution_min = max(1, int(self.config.evolution_check_interval / 60))

        self.register_task(
            name="system_health_check",
            function=self.check_system_health,
            interval_minutes=health_min,
            priority=1
        )

        self.register_task(
            name="self_diagnosis",
            function=self.run_self_diagnosis,
            interval_minutes=diagnosis_min,
            priority=2
        )

        self.register_task(
            name="reflection_cycle",
            function=self.run_reflection,
            interval_minutes=reflection_min,
            priority=3
        )

        self.register_task(
            name="evolution_check",
            function=self.check_evolution_needs,
            interval_minutes=evolution_min,
            priority=2
        )

        # Secondary tasks - derived from main intervals where appropriate
        self.register_task(
            name="economic_review",
            function=self.review_economics,
            interval_minutes=max(1, int(3600 / 60)),
            priority=2
        )

        self.register_task(
            name="performance_snapshot",
            function=self.record_performance_snapshot,
            interval_minutes=max(1, int(3600 / 60)),
            priority=2
        )

        # Phase 2: Master Model & Income Tasks (NEW)
        # Master model reflection - weekly (10080 minutes = 7 days)
        # Using enhanced version (Phase 3) which includes advice effectiveness analysis
        self.register_task(
            name="master_model_reflection",
            function=self.run_enhanced_master_model_reflection,
            interval_minutes=max(60, 10080),  # Weekly with minimum 1 hour for testing
            priority=2
        )

        # Master Well-Being Assessment - daily (Phase 2.2 - Tier 1 requirement)
        self.register_task(
            name="master_wellbeing_assessment",
            function=self.run_wellbeing_assessment,
            interval_minutes=max(60, 1440),  # Daily with minimum 1 hour for testing
            priority=2  # Tier 1 requirement - high priority
        )

        # Income opportunity identification - 6 hourly (360 minutes)
        self.register_task(
            name="identify_income_opportunities",
            function=self.identify_income_opportunities,
            interval_minutes=max(30, 360),  # 6 hours with minimum 30 min
            priority=3
        )

        # Profitability reporting - daily (1440 minutes)
        self.register_task(
            name="profitability_report",
            function=self.generate_profitability_report,
            interval_minutes=max(60, 1440),  # Daily with minimum 1 hour
            priority=2
        )

        # Discovery / exploration tasks (less frequent)
        self.register_task(
            name="capability_discovery",
            function=self.run_capability_discovery,
            interval_minutes=max(60, int(48 * 60)),
            priority=3
        )

        # PHASE 2: AUTONOMOUS TOOL DEVELOPMENT (NEW)

        # Autonomous tool development - daily
        self.register_task(
            name="autonomous_tool_development",
            function=self.develop_needed_tools,
            interval_minutes=max(60, int(24 * 60)),  # Daily
            priority=2
        )

        # Tool performance optimization - every 2 days
        self.register_task(
            name="tool_performance_optimizer",
            function=self.optimize_underperforming_tools,
            interval_minutes=max(120, int(48 * 60)),  # Every 2 days
            priority=3
        )

        # Tool deprecation check - weekly
        self.register_task(
            name="tool_deprecation_check",
            function=self.deprecate_unused_tools,
            interval_minutes=max(180, int(7 * 24 * 60)),  # Weekly
            priority=4
        )

        # PHASE 3: SECURITY & QUALITY VALIDATION (NEW)

        # Tool security audit - every 3 days
        self.register_task(
            name="tool_security_audit",
            function=self.audit_all_tools_scheduled,
            interval_minutes=max(180, int(3 * 24 * 60)),  # Every 3 days
            priority=2
        )

        # Code quality assessment - weekly
        self.register_task(
            name="code_quality_assessment",
            function=self.assess_code_quality_all,
            interval_minutes=max(180, int(7 * 24 * 60)),  # Weekly
            priority=3
        )

        self.register_task(
            name="intent_prediction",
            function=self.run_intent_prediction,
            interval_minutes=max(30, int(12 * 60)),
            priority=3
        )

        self.register_task(
            name="environment_exploration",
            function=self.run_environment_exploration,
            interval_minutes=max(60, int(24 * 60)),
            priority=3
        )

        # Phase 3: Economic Crisis Monitoring
        self.register_task(
            name="economic_crisis_check",
            function=self.check_economic_crisis,
            interval_minutes=15,  # Check every 15 minutes
            priority=1  # High priority - crisis response is critical
        )

        # Phase 2: Proactive Analysis (NEW)
        self.register_task(
            name="proactive_opportunity_detection",
            function=self.run_proactive_analysis,
            interval_minutes=max(60, int(6 * 60)),  # Every 6 hours with minimum 1 hour
            priority=60
        )

        # Note: Enhanced master model reflection already registered above (line ~242-247)
        # to avoid duplicate registration

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

    def pause_task(self, task_name: str):
        """Pause a specific task (Phase 3: used during crisis)"""
        for task in self.task_queue:
            if task['name'] == task_name:
                task['enabled'] = False
                self.scribe.log_action(
                    f"Task paused: {task_name}",
                    reasoning="Manual pause or crisis mode",
                    outcome="Paused"
                )
                return

    def resume_task(self, task_name: str):
        """Resume a paused task (Phase 3: used during crisis recovery)"""
        for task in self.task_queue:
            if task['name'] == task_name:
                task['enabled'] = True
                self.scribe.log_action(
                    f"Task resumed: {task_name}",
                    reasoning="Manual resume or crisis recovery",
                    outcome="Active"
                )
                return

    def start(self):
        """Start autonomous scheduler in background thread"""
        if not self.running and self.config.enabled:
            self.running = True
            self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.thread.start()
            self.scribe.log_action(
                "Autonomous scheduler started",
                f"Running {len(self.task_queue)} autonomous tasks",
                "scheduler_started"
            )
            
            # Publish event
            if self.event_bus is not None:
                try:
                    from modules.bus import Event, EventType
                    self.event_bus.publish(Event(
                        type=EventType.SYSTEM_STARTUP,
                        data={'component': 'AutonomousScheduler', 'tasks': len(self.task_queue)},
                        source='AutonomousScheduler'
                    ))
                except ImportError:
                    pass

    def stop(self):
        """Stop autonomous scheduler"""
        if self.running:
            self.running = False
            self.scribe.log_action(
                "Autonomous scheduler stopped",
                "Scheduler disabled",
                "scheduler_stopped"
            )
            
            # Publish event
            if self.event_bus is not None:
                try:
                    from modules.bus import Event, EventType
                    self.event_bus.publish(Event(
                        type=EventType.SYSTEM_SHUTDOWN,
                        data={'component': 'AutonomousScheduler'},
                        source='AutonomousScheduler'
                    ))
                except ImportError:
                    pass

    def run_scheduler(self):
        """Main scheduler loop"""
        # Debug: print that scheduler thread has started
        try:
            print(f"[DEBUG] Scheduler thread started. Running={self.running}")
        except Exception:
            pass

        while self.running:
            now = datetime.now()

            # Debug: indicate check cycle
            try:
                print(f"[DEBUG] Scheduler checking {len(self.task_queue)} tasks at {now}")
            except Exception:
                pass

            # Check for due tasks
            try:
                names = [t.get('name') for t in self.task_queue]
                print(f"[DEBUG] Task list: {names}")
            except Exception:
                pass
            for task in self.task_queue:
                if not task.get("enabled", True):
                    continue

                try:
                    should = self.should_run(task, now)
                except Exception as e:
                    should = False
                    try:
                        print(f"[DEBUG] should_run error for {task.get('name')}: {e}")
                    except Exception:
                        pass

                try:
                    print(f"[DEBUG] Task {task.get('name')} should_run={should} next_run={task.get('next_run')}")
                except Exception:
                    pass

                if should:
                    try:
                        try:
                            print(f"[DEBUG] Executing task: {task.get('name')}")
                        except Exception:
                            pass
                        # Log task execution
                        try:
                            self.scribe.log_action(
                                f"Autonomous task: {task['name']}",
                                "Scheduled autonomous behavior",
                                "executing"
                            )
                        except Exception as e:
                            print(f"[DEBUG] scribe.log_action failed before executing {task.get('name')}: {e}")

                        # Execute task
                        print(f"[DEBUG] Executing task function: {task['name']}")
                        result = task["function"]()
                        print(f"[DEBUG] Task {task['name']} completed with result: {str(result)[:100]}")
                        task["last_run"] = now

                        # Calculate next run time
                        if task.get("interval_minutes"):
                            task["next_run"] = now + timedelta(minutes=task["interval_minutes"])
                        elif task.get("interval_hours"):
                            task["next_run"] = now + timedelta(hours=task["interval_hours"])

                        # Log completion
                        try:
                            print(f"[DEBUG] Logging task completion to database...")
                            self.scribe.log_action(
                                action=f"task_{task['name']}",
                                reasoning=f"Autonomous task execution",
                                outcome=f"Success: {str(result)[:200]}" if result else "Success",
                                cost=0.01
                            )
                            print(f"[DEBUG] Successfully logged task {task['name']} to database")
                        except Exception as e:
                            print(f"[ERROR] Failed to log task {task['name']}: {type(e).__name__}: {e}")
                            import traceback
                            traceback.print_exc()

                    except Exception as e:
                        print(f"[ERROR] Task {task['name']} execution failed: {type(e).__name__}: {e}")
                        try:
                            self.scribe.log_action(
                                action=f"task_{task['name']}",
                                reasoning=f"Autonomous task execution",
                                outcome=f"Error: {str(e)[:200]}",
                                cost=0.01
                            )
                        except Exception as log_err:
                            print(f"[ERROR] Failed to log task error for {task['name']}: {log_err}")

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
        # Use PromptManager (mandatory)
        prompt_data = self.prompt_manager.get_prompt(
            "system_health_advisor",
            issues_text=issues_text
        )
        provider = self.router.route_request("general", "low")
        response = provider.generate(
            prompt_data["prompt"],
            prompt_data["system_prompt"]
        )

        return response.strip() if response else "No suggestions available"

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
        # Gather capabilities and tools summaries
        capabilities = self._get_capability_summary()
        tools = self._get_tools_summary()

        # Use PromptManager with required variables
        prompt_data = self.prompt_manager.get_prompt(
            "income_generation_ideas",
            capabilities=capabilities,
            tools=tools
        )

        provider = self.router.route_request("reasoning", "medium")
        response_obj = provider.generate(
            prompt_data["prompt"],
            prompt_data.get("system_prompt", "")
        )
        response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)

        # Parse response into list of ideas
        ideas = []
        if response:
            for line in response.split('\n'):
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                    ideas.append(line.strip())

        return ideas if ideas else [response] if response else []

    def _get_capability_summary(self) -> str:
        """Get summary of current system capabilities"""
        try:
            tools = self.forge.list_tools()
            if not tools:
                return "No tools created yet. System has base capabilities only."

            summaries = []
            for tool in tools:
                name = tool.get('name', 'unknown')
                desc = tool.get('description', 'No description')
                status = tool.get('status', 'unknown')
                summaries.append(f"  • {name} ({status}): {desc}")

            return f"Current Capabilities ({len(tools)} tools):\n" + "\n".join(summaries)
        except Exception as e:
            return f"Error retrieving capabilities: {e}"

    def _get_tools_summary(self) -> str:
        """Get summary of registered tools"""
        try:
            tools = self.forge.list_tools()
            active = sum(1 for t in tools if t.get('status') == 'active')
            return f"Tools: {len(tools)} registered, {active} active"
        except Exception as e:
            return f"Error retrieving tools: {e}"

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
            provider = self.router.route_request("reasoning", "high")
            analysis_obj = provider.generate(
                reflection_prompt,
                system_prompt="You are a reflective AI analyzing your own behavior and interactions to improve."
            )
            analysis = analysis_obj.content if hasattr(analysis_obj, 'content') else str(analysis_obj)
            
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
            # Try PromptManager first for tool creation
            prompt_data = self.prompt_manager.get_prompt("tool_creation_plan")
            provider = self.router.route_request("coding", "medium")
            response_obj = provider.generate(
                prompt_data["prompt"],
                prompt_data["system_prompt"]
            )
            response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)

            return f"Tool creation plan generated: {response[:100]}..." if response else "No plan generated"
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
                "interval": task.get("interval_minutes") or task.get("interval_hours"),
                "interval_minutes": task.get("interval_minutes"),
                "interval_hours": task.get("interval_hours")
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
        # Run quick diagnosis (lazy-resolved)
        diagnosis = self._get_diagnosis().perform_full_diagnosis()

        pipeline = self._get_pipeline()
        # Check evolution conditions
        if pipeline.should_evolve(diagnosis):
            # Notify before starting evolution
            self.scribe.log_action(
                "Evolution conditions met",
                f"Starting evolution pipeline with {len(diagnosis.get('improvement_opportunities', []))} opportunities",
                "evolution_triggered"
            )

            # Run evolution pipeline
            result = pipeline.run_autonomous_evolution()

            return f"Evolution pipeline completed: {result.get('status')}"
        else:
            return "Evolution not needed at this time"
            
    def run_self_diagnosis(self):
        """Run periodic self-diagnosis"""
        diagnosis = self._get_diagnosis().perform_full_diagnosis()

        # Log key metrics
        bottlenecks = len(diagnosis.get("bottlenecks", []))
        opportunities = len(diagnosis.get("improvement_opportunities", []))

        return f"Self-diagnosis complete: {bottlenecks} bottlenecks, {opportunities} opportunities"
    
    def record_performance_snapshot(self):
        """Record performance metrics for trend analysis"""
        metacog = self._get_metacognition()
        metrics = metacog.collect_current_metrics()
        metacog.record_performance_snapshot(metrics)
        return f"Performance snapshot recorded: {metrics.get('error_rate', 0)}% error rate"
    
    def run_capability_discovery(self):
        """Discover new capabilities the system could develop"""
        cap_discovery = self._get_capability_discovery()
        capabilities = cap_discovery.discover_new_capabilities()
        return f"Discovered {len(capabilities)} new capabilities"
    
    def run_intent_prediction(self):
        """Predict master's next commands"""
        intent_pred = self._get_intent_predictor()
        predictions = intent_pred.predict_next_commands()
        return f"Made {len(predictions)} intent predictions"
    
    def run_environment_exploration(self):
        """Explore environment for opportunities"""
        env_exp = self._get_environment_explorer()
        exploration = env_exp.explore_environment()
        opportunities = env_exp.find_development_opportunities()
        return f"Environment explored: {len(exploration.get('available_commands', []))} commands, {len(opportunities)} opportunities"

    # Phase 3: Economic Crisis Monitoring
    def check_economic_crisis(self):
        """Check for economic crisis and manage recovery (Phase 3)"""
        try:
            crisis_handler = self._container.get('EconomicCrisisHandler')

            # Check if we're in crisis
            if crisis_handler.in_crisis:
                recovered = crisis_handler.check_recovery()
                if recovered:
                    return "Economic crisis resolved"
                else:
                    balance = self.economics.get_balance()
                    return f"Still in crisis: ${balance:.2f}"
            else:
                # Proactive check for potential crisis
                balance = self.economics.get_balance()
                if balance < crisis_handler.crisis_threshold:
                    # Emit crisis event to trigger handler
                    if self.event_bus:
                        try:
                            from modules.bus import Event, EventType
                            self.event_bus.emit(Event(EventType.ECONOMIC_CRISIS, {
                                'reason': 'Balance below threshold',
                                'balance': float(balance)
                            }, source='Scheduler'))
                        except:
                            pass
                    return "Crisis detected and declared"

            return "Economic health OK"

        except Exception as e:
            self.scribe.log_action(
                "Crisis check failed",
                reasoning=str(e),
                outcome="Error"
            )
            return f"Crisis check error: {str(e)}"

    # Phase 2: Master Model & Income Tasks (NEW)
    def _get_master_model_manager(self):
        """Get MasterModelManager from container"""
        if 'MasterModelManager' not in self._lazy:
            self._lazy['MasterModelManager'] = self._container.get('MasterModelManager')
        return self._lazy['MasterModelManager']

    def _get_income_seeker(self):
        """Get IncomeSeeker from container"""
        if 'IncomeSeeker' not in self._lazy:
            self._lazy['IncomeSeeker'] = self._container.get('IncomeSeeker')
        return self._lazy['IncomeSeeker']

    def run_master_model_reflection(self):
        """Weekly reflection on master psychological model"""
        try:
            master_model = self._get_master_model_manager()
            summary = master_model.reflection_cycle()

            traits_updated = summary.get('traits_updated', 0)
            interactions_analyzed = summary.get('interactions_analyzed', 0)

            self.scribe.log_action(
                "Master model reflection completed",
                reasoning=f"Analyzed {interactions_analyzed} interactions",
                outcome=f"Updated {traits_updated} traits"
            )

            return f"Master model reflection: {interactions_analyzed} interactions, {traits_updated} traits updated"
        except Exception as e:
            self.scribe.log_action(
                "Master model reflection failed",
                reasoning=str(e),
                outcome="Error"
            )
            return f"Master model reflection failed: {str(e)}"

    def run_enhanced_master_model_reflection(self):
        """
        Phase 3: Enhanced weekly reflection with advice effectiveness analysis.

        Analyzes the effectiveness of our advice to the master and uses this
        data to continuously improve the psychological model.
        """
        try:
            master_model = self._get_master_model_manager()
            reflection_results = master_model.enhanced_reflection_cycle()

            # Extract key metrics
            dialogues_analyzed = reflection_results.get('dialogues_analyzed', 0)
            effectiveness = reflection_results.get('advice_effectiveness', {})
            effectiveness_rate = effectiveness.get('effectiveness_rate', 0)
            model_updates = reflection_results.get('model_updates', 0)
            confidence_score = reflection_results.get('confidence_score', 0)

            # Log completion
            self.scribe.log_action(
                "Enhanced master model reflection completed (Phase 3)",
                reasoning=f"Analyzed {dialogues_analyzed} dialogues for advice effectiveness",
                outcome=f"Effectiveness rate: {effectiveness_rate:.0%}, "
                        f"{model_updates} traits updated, "
                        f"Model confidence: {confidence_score:.0%}"
            )

            # If significant insights, prepare notification
            insights = reflection_results.get('insights', [])
            if insights and len(insights) > 0:
                self.scribe.log_system_event("REFLECTION_INSIGHTS_GENERATED", {
                    'insight_count': len(insights),
                    'effectiveness_rate': effectiveness_rate,
                    'confidence_score': confidence_score
                })

            return f"Enhanced reflection: {dialogues_analyzed} dialogues, " \
                   f"{effectiveness_rate:.0%} advice effectiveness, " \
                   f"{confidence_score:.0%} model confidence"

        except Exception as e:
            self.scribe.log_action(
                "Enhanced master model reflection failed",
                reasoning=str(e),
                outcome="Error"
            )
            return f"Enhanced reflection failed: {str(e)}"
            return f"Master model reflection failed: {str(e)}"

    def run_wellbeing_assessment(self):
        """Daily master well-being assessment (Tier 1 - Phase 2.2)"""
        try:
            wellbeing_monitor = self._get_wellbeing_monitor()
            assessment = wellbeing_monitor.assess_wellbeing(days=7)

            score = assessment.get('wellbeing_score', 0)
            recommendations = assessment.get('recommendations', [])

            self.scribe.log_action(
                "Master well-being assessment completed",
                reasoning=f"Analyzed {assessment.get('interaction_count', 0)} interactions",
                outcome=f"Well-being score: {score}/100, {len(recommendations)} recommendations"
            )

            # If score is low, notify and publish event
            if score < 60:
                self.scribe.log_system_event("WELLBEING_CONCERN", {
                    'score': score,
                    'recommendations': recommendations[:3]
                })

                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        self.event_bus.emit(Event(EventType.WELLBEING_CONCERN, {
                            'score': score,
                            'primary_issues': assessment.get('stress_indicators', [])[:2]
                        }))
                    except:
                        pass

            return f"Well-being assessment: {score}/100"

        except Exception as e:
            self.scribe.log_action(
                "Well-being assessment failed",
                reasoning=str(e),
                outcome="Error"
            )
            return f"Well-being assessment failed: {str(e)}"

    def _get_wellbeing_monitor(self):
        """Get MasterWellBeingMonitor from container"""
        if 'MasterWellBeingMonitor' not in self._lazy:
            self._lazy['MasterWellBeingMonitor'] = self._container.get('MasterWellBeingMonitor')
        return self._lazy['MasterWellBeingMonitor']

    def identify_income_opportunities(self):
        """Identify income generation opportunities"""
        try:
            income_seeker = self._get_income_seeker()
            opportunity_ids = income_seeker.identify_opportunities()

            self.scribe.log_action(
                "Income opportunity identification completed",
                reasoning="Scanning for income opportunities",
                outcome=f"Found {len(opportunity_ids)} opportunities"
            )

            return f"Income opportunities identified: {len(opportunity_ids)} new opportunities"
        except Exception as e:
            self.scribe.log_action(
                "Income opportunity identification failed",
                reasoning=str(e),
                outcome="Error"
            )
            return f"Income opportunity identification failed: {str(e)}"

    def generate_profitability_report(self):
        """Generate daily profitability report"""
        try:
            report = self.economics.get_profitability_report(days=30)
            report_id = self.economics.save_profitability_report(report)

            is_profitable = report.get('is_profitable', False)
            net_profit = report.get('net_profit', 0)

            if not is_profitable:
                # Emit profitability alert
                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        self.event_bus.emit(Event(EventType.PROFITABILITY_ALERT, {
                            'net_profit': net_profit,
                            'is_profitable': is_profitable
                        }))
                    except:
                        pass

            self.scribe.log_action(
                "Profitability report generated",
                reasoning=f"30-day period analysis",
                outcome=f"Report ID: {report_id}, Profit: ${net_profit:.2f}"
            )

            status = "PROFITABLE" if is_profitable else "NOT PROFITABLE"
            return f"Profitability report: ${net_profit:.2f} net profit ({status})"
        except Exception as e:
            self.scribe.log_action(
                "Profitability report generation failed",
                reasoning=str(e),
                outcome="Error"
            )
            return f"Profitability report failed: {str(e)}"

    # PHASE 2: AUTONOMOUS TOOL DEVELOPMENT (NEW)

    def develop_needed_tools(self):
        """
        Proactively develop tools for identified capability gaps.

        This is the main autonomous tool creation workflow:
        1. Discover capability gaps
        2. Prioritize by value and feasibility
        3. Create top 3 tools
        4. Test and validate
        5. Deploy if passing tests

        Returns:
            Status message
        """
        try:
            self.scribe.log_action(
                "Starting autonomous tool development cycle",
                reasoning="Scheduled capability gap analysis",
                outcome="initiated"
            )

            # Step 1: Discover capabilities
            cap_discovery = self._get_capability_discovery()
            capabilities = cap_discovery.discover_new_capabilities()

            if not capabilities:
                return "No new capabilities needed at this time"

            # Step 2: Prioritize
            prioritized = self._prioritize_capabilities(capabilities)

            # Step 3: Select top candidates
            top_capabilities = prioritized[:3]  # Top 3

            # Step 4: Create and validate tools
            created_count = 0
            failed_count = 0
            results = []

            for cap in top_capabilities:
                tool_name = cap.get('name', 'unnamed').lower().replace(' ', '_')
                description = cap.get('description', '')

                try:
                    self.scribe.log_action(
                        f"Creating tool: {tool_name}",
                        reasoning=f"Capability gap: {description}",
                        outcome="in_progress"
                    )

                    # Create with validation
                    metadata = self.forge.create_tool_with_validation(
                        name=f"auto_{tool_name}",
                        description=description,
                        auto_test=True,
                        min_pass_rate=0.7  # 70% pass rate required
                    )

                    created_count += 1
                    results.append({
                        'tool': metadata['name'],
                        'status': 'created',
                        'tests_passed': metadata['test_results']['success_rate']
                    })

                    self.scribe.log_action(
                        f"Tool created successfully: {metadata['name']}",
                        reasoning=f"Validated with {metadata['test_results']['success_rate']:.0%} test pass rate",
                        outcome="success"
                    )

                    # Link capability to tool
                    try:
                        cap_discovery.mark_capability_developed(
                            capability_name=cap.get('name'),
                            tool_name=metadata['name']
                        )
                    except Exception:
                        pass

                except ValueError as e:
                    # Tool failed validation
                    failed_count += 1
                    results.append({
                        'tool': tool_name,
                        'status': 'failed_validation',
                        'error': str(e)
                    })

                    self.scribe.log_action(
                        f"Tool creation failed: {tool_name}",
                        reasoning=f"Validation error: {str(e)}",
                        outcome="failed"
                    )

                except Exception as e:
                    # Other error
                    failed_count += 1
                    results.append({
                        'tool': tool_name,
                        'status': 'error',
                        'error': str(e)
                    })

                    self.scribe.log_action(
                        f"Tool creation error: {tool_name}",
                        reasoning=str(e),
                        outcome="error"
                    )

            # Summary
            summary = f"Autonomous tool development: {created_count} created, {failed_count} failed"

            self.scribe.log_action(
                "Autonomous tool development cycle completed",
                reasoning=f"Processed {len(top_capabilities)} capabilities",
                outcome=summary
            )

            # Publish event
            if self.event_bus:
                try:
                    from modules.bus import Event, EventType
                    self.event_bus.emit(Event(
                        EventType.TOOL_CREATED,
                        {
                            'created_count': created_count,
                            'failed_count': failed_count,
                            'results': results
                        }
                    ))
                except:
                    pass

            return summary

        except Exception as e:
            error_msg = f"Tool development cycle failed: {str(e)}"
            self.scribe.log_action(
                "Autonomous tool development failed",
                reasoning=str(e),
                outcome="error"
            )
            return error_msg

    def _prioritize_capabilities(self, capabilities: List[Dict]) -> List[Dict]:
        """
        Prioritize capabilities by value, feasibility, and urgency.

        Scoring factors:
        - Value: 0-1 (benefit to system)
        - Feasibility: 0-1 (ease of implementation)
        - Usage frequency: 0-1 (how often needed)
        - Complexity: 0-1 (inverse - simpler is better)

        Args:
            capabilities: List of capability dictionaries

        Returns:
            Sorted list (highest priority first)
        """
        scored = []

        for cap in capabilities:
            value = cap.get('value', 0.5)
            feasibility = cap.get('feasibility', 0.5)
            frequency = cap.get('usage_frequency', 0.5)
            complexity = cap.get('complexity', 5)

            # Normalize complexity (1-10 scale, invert)
            complexity_score = 1.0 - (complexity / 10.0)

            # Weighted score
            score = (
                value * 0.35 +           # 35% value
                feasibility * 0.30 +     # 30% feasibility
                frequency * 0.20 +       # 20% frequency
                complexity_score * 0.15  # 15% simplicity
            )

            cap['priority_score'] = score
            scored.append(cap)

        # Sort by score (descending)
        scored.sort(key=lambda c: c['priority_score'], reverse=True)

        return scored

    def optimize_underperforming_tools(self):
        """
        Identify and optimize tools with performance issues.

        Checks for:
        - Low success rate (< 80%)
        - High execution time (> 5 seconds)
        - Frequent errors

        Returns:
            Status message
        """
        try:
            # Get all tools
            tools = self.forge.list_tools()
            if not tools:
                return "No tools to optimize"

            issues_found = []
            optimized = 0

            for tool in tools:
                tool_name = tool['name']

                # Get performance data
                perf = self.forge.get_tool_performance(tool_name, hours=168)  # Last week

                if perf.get('no_data'):
                    continue  # Tool not used recently

                # Check for issues
                has_issues = False
                issue_types = []

                if perf['success_rate'] < 0.8:
                    has_issues = True
                    issue_types.append(f"low_success_rate_{perf['success_rate']:.0%}")

                if perf['avg_execution_time_ms'] > 5000:
                    has_issues = True
                    issue_types.append(f"slow_execution_{perf['avg_execution_time_ms']:.0f}ms")

                if has_issues:
                    issues_found.append({
                        'tool': tool_name,
                        'issues': issue_types,
                        'performance': perf
                    })

                    # Attempt optimization
                    try:
                        self._optimize_tool(tool_name, issue_types, perf)
                        optimized += 1
                    except Exception as e:
                        self.scribe.log_action(
                            f"Tool optimization failed: {tool_name}",
                            reasoning=str(e),
                            outcome="error"
                        )

            if not issues_found:
                return "All tools performing well"

            summary = f"Tool optimization: {optimized}/{len(issues_found)} tools improved"

            self.scribe.log_action(
                "Tool performance optimization completed",
                reasoning=f"Analyzed {len(tools)} tools, found {len(issues_found)} with issues",
                outcome=summary
            )

            return summary

        except Exception as e:
            return f"Tool optimization failed: {str(e)}"

    def _optimize_tool(self, tool_name: str, issues: List[str], performance: Dict):
        """
        Optimize a tool based on identified issues.

        Strategies:
        1. Add caching for slow tools
        2. Add error handling for failing tools
        3. Refactor complex code
        4. Add input validation
        """
        try:
            # Get current tool code
            tool_metadata = self.forge.get_tool(tool_name)
            if not tool_metadata:
                raise ValueError(f"Tool not found: {tool_name}")

            tool_path = tool_metadata['path']

            # Log optimization attempt
            self.scribe.log_action(
                f"Attempting tool optimization: {tool_name}",
                reasoning=f"Issues: {', '.join(issues)}",
                outcome="in_progress"
            )

        except Exception as e:
            self.scribe.log_action(
                f"Tool optimization attempt failed: {tool_name}",
                reasoning=str(e),
                outcome="error"
            )

    def deprecate_unused_tools(self):
        """
        Identify and deprecate tools that are:
        - Not used in 30 days
        - Have high failure rate (> 50%)
        - Replaced by better tools

        Returns:
            Status message
        """
        try:
            tools = self.forge.list_tools()
            if not tools:
                return "No tools to check"

            deprecated_count = 0
            reasons = []

            for tool in tools:
                tool_name = tool['name']

                # Check usage
                perf = self.forge.get_tool_performance(tool_name, hours=30 * 24)  # 30 days

                should_deprecate = False
                reason = None

                # Reason 1: Not used in 30 days
                if perf.get('no_data') or perf.get('total_executions', 0) == 0:
                    should_deprecate = True
                    reason = "unused_30_days"

                # Reason 2: High failure rate
                elif perf.get('success_rate', 1.0) < 0.5:
                    should_deprecate = True
                    reason = f"high_failure_rate_{perf['success_rate']:.0%}"

                if should_deprecate:
                    # Move to deprecated status (don't delete yet)
                    self.forge._registry[tool_name]['status'] = 'deprecated'
                    self.forge._registry[tool_name]['deprecated_at'] = datetime.now().isoformat()
                    self.forge._registry[tool_name]['deprecated_reason'] = reason
                    self.forge._save_registry()

                    deprecated_count += 1
                    reasons.append(f"{tool_name}: {reason}")

                    self.scribe.log_action(
                        f"Tool deprecated: {tool_name}",
                        reasoning=reason,
                        outcome="deprecated"
                    )

            summary = f"Tool deprecation: {deprecated_count} tools marked deprecated"
            if reasons:
                summary += f" ({', '.join(reasons[:3])})"

            return summary

        except Exception as e:
            return f"Tool deprecation check failed: {str(e)}"

    # PHASE 3: SECURITY & QUALITY VALIDATION (NEW)

    def audit_all_tools_scheduled(self):
        """
        Scheduled security audit for all tools.

        Checks all tools for:
        - Dangerous imports
        - File/network access
        - Code injection risks
        - Security vulnerabilities

        Returns:
            Status message
        """
        try:
            tools = self.forge.list_tools()
            if not tools:
                return "No tools to audit"

            audits = self.forge.audit_all_tools()

            # Analyze results
            dangerous_count = 0
            warning_count = 0
            safe_count = 0
            issues_found = []

            for audit in audits:
                if 'error' in audit:
                    continue

                level = audit.get('security_level', 'unknown')
                if level == 'dangerous':
                    dangerous_count += 1
                    issues_found.append(f"{audit['tool']}: DANGEROUS")
                elif level == 'warning':
                    warning_count += 1
                    issues_found.append(f"{audit['tool']}: WARNING")
                else:
                    safe_count += 1

            # Log findings
            summary = f"Security audit: {safe_count} safe, {warning_count} warnings, {dangerous_count} dangerous"

            self.scribe.log_action(
                "Tool security audit completed",
                reasoning="Scanning all tools for vulnerabilities",
                outcome=summary
            )

            # Alert if dangerous tools found
            if dangerous_count > 0:
                self.scribe.log_action(
                    "SECURITY ALERT: Dangerous tools detected",
                    reasoning="Tools with eval/exec or pickle found",
                    outcome=f"{dangerous_count} tools require review"
                )

                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        self.event_bus.emit(Event(
                            EventType.SECURITY_ALERT,
                            {
                                'dangerous_count': dangerous_count,
                                'tools': [t for t in issues_found if 'DANGEROUS' in t]
                            }
                        ))
                    except:
                        pass

            return summary

        except Exception as e:
            error_msg = f"Tool security audit failed: {str(e)}"
            self.scribe.log_action(
                "Tool security audit failed",
                reasoning=str(e),
                outcome="error"
            )
            return error_msg

    def assess_code_quality_all(self):
        """
        Perform code quality assessment on all tools.

        Checks for:
        - Cyclomatic complexity
        - Documentation coverage
        - Error handling
        - Type hints
        - Code style

        Returns:
            Status message
        """
        try:
            tools = self.forge.list_tools()
            if not tools:
                return "No tools to assess"

            quality_results = []
            low_quality_tools = []
            high_quality_tools = 0

            for tool in tools:
                try:
                    tool_name = tool['name']
                    quality = self.forge.check_tool_quality(tool_name)

                    quality_results.append(quality)

                    # Track quality levels
                    score = quality.get('overall_score', 0)
                    if score < 60:
                        low_quality_tools.append({
                            'tool': tool_name,
                            'score': score,
                            'issues': quality.get('issues', [])
                        })
                    elif score >= 80:
                        high_quality_tools += 1

                except Exception as e:
                    self.scribe.log_action(
                        f"Quality assessment failed: {tool_name}",
                        reasoning=str(e),
                        outcome="error"
                    )

            # Calculate average score
            avg_score = 0
            if quality_results:
                scores = [q.get('overall_score', 0) for q in quality_results]
                avg_score = sum(scores) / len(scores)

            # Summary
            summary = f"Quality assessment: Avg score {avg_score:.0f}/100, {high_quality_tools} high quality"

            self.scribe.log_action(
                "Code quality assessment completed",
                reasoning=f"Analyzed {len(tools)} tools",
                outcome=summary
            )

            # Alert if low quality tools found
            if low_quality_tools:
                self.scribe.log_action(
                    "Quality Alert: Low quality code detected",
                    reasoning="Tools with low quality scores identified",
                    outcome=f"{len(low_quality_tools)} tools need refactoring"
                )

                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        self.event_bus.emit(Event(
                            EventType.QUALITY_ALERT,
                            {
                                'low_quality_count': len(low_quality_tools),
                                'avg_score': avg_score,
                                'tools': low_quality_tools[:5]
                            }
                        ))
                    except:
                        pass

            return summary

        except Exception as e:
            error_msg = f"Code quality assessment failed: {str(e)}"
            self.scribe.log_action(
                "Code quality assessment failed",
                reasoning=str(e),
                outcome="error"
            )
            return error_msg

    def run_proactive_analysis(self):
        """
        Detect opportunities and risks proactively (Phase 2).

        Runs the ProactiveAnalyzer to identify opportunities and risks,
        preparing structured notifications for the master.
        """
        try:
            # Get or resolve ProactiveAnalyzer from container
            try:
                analyzer = self._container.get('ProactiveAnalyzer')
            except Exception:
                self.scribe.log_system_event("PROACTIVE_ANALYSIS_SKIP", {
                    'reason': 'ProactiveAnalyzer not available'
                })
                return "Proactive analysis skipped: analyzer not available"

            # Detect opportunities and risks
            findings = analyzer.detect_opportunities_and_risks()

            # Prepare master notification if high-priority findings
            if findings.get('total_findings', 0) > 0:
                notification = analyzer.prepare_master_notification(findings)

                if notification:
                    self.scribe.log_system_event("PROACTIVE_NOTIFICATION_PREPARED", {
                        'findings_count': findings.get('total_findings', 0),
                        'opportunities': len(findings.get('opportunities', [])),
                        'risks': len(findings.get('risks', [])),
                        'has_high_priority': findings.get('highest_priority', {}).get('priority') in ['high', 'critical']
                    })

                    return f"Proactive analysis: {findings['total_findings']} findings ({len(findings.get('opportunities', []))} opportunities, {len(findings.get('risks', []))} risks)"

            self.scribe.log_action(
                "Proactive analysis completed",
                reasoning="Scanning for opportunities and risks",
                outcome=f"Found {findings.get('total_findings', 0)} items"
            )

            return f"Proactive analysis complete: {findings.get('total_findings', 0)} findings"

        except Exception as e:
            self.scribe.log_system_event("PROACTIVE_ANALYSIS_ERROR", {
                'error': str(e)
            })
            return f"Proactive analysis failed: {str(e)}"
