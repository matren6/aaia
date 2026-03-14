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
        self.register_task(
            name="master_model_reflection",
            function=self.run_master_model_reflection,
            interval_minutes=max(60, 10080),  # Weekly with minimum 1 hour for testing
            priority=2
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
                        result = task["function"]()
                        task["last_run"] = now

                        # Calculate next run time
                        if task.get("interval_minutes"):
                            task["next_run"] = now + timedelta(minutes=task["interval_minutes"])
                        elif task.get("interval_hours"):
                            task["next_run"] = now + timedelta(hours=task["interval_hours"])

                        # Log completion
                        try:
                            self.scribe.log_action(
                                f"Completed task: {task['name']}",
                                f"Result: {str(result)[:100]}",
                                "completed"
                            )
                        except Exception as e:
                            print(f"[DEBUG] scribe.log_action failed after executing {task.get('name')}: {e}")

                    except Exception as e:
                        try:
                            self.scribe.log_action(
                                f"Task failed: {task['name']}",
                                f"Error: {str(e)}",
                                "error"
                            )
                        except Exception:
                            print(f"[ERROR] Task {task.get('name')} failed and logging also failed: {e}")

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
        model_name, _ = self.router.route_request("general", "low")
        response = self.router.call_model(
            model_name,
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

        model_name, _ = self.router.route_request("reasoning", "medium")
        response = self.router.call_model(
            model_name,
            prompt_data["prompt"],
            prompt_data.get("system_prompt", "")
        )

        # Parse response into list of ideas
        ideas = []
        if response:
            for line in response.split('\n'):
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                    ideas.append(line.strip())

        return ideas if ideas else [response] if response else []

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
            # Try PromptManager first for tool creation
            prompt_data = self.prompt_manager.get_prompt("tool_creation_plan")
            model_name, _ = self.router.route_request("coding", "medium")
            response = self.router.call_model(
                model_name,
                prompt_data["prompt"],
                prompt_data["system_prompt"]
            )

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
