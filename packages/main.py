# main.py
import sys
from pathlib import Path

# Add the packages directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import time
import sqlite3
from datetime import datetime
from typing import Optional
import argparse
import threading
import os

# New architectural components
from modules.settings import get_config, SystemConfig, validate_system_config
from modules.bus import EventBus, EventType, Event, get_event_bus
from modules.container import Container, get_container

# Core modules
from modules.scribe import Scribe
from modules.economics import EconomicManager
from modules.mandates import MandateEnforcer
from modules.router import ModelRouter
from modules.dialogue import DialogueManager
from modules.forge import Forge, TOOL_TEMPLATES

# Autonomous modules
from modules.scheduler import AutonomousScheduler
from modules.goals import GoalSystem
from modules.hierarchy_manager import HierarchyManager

# Self-development modules
from modules.self_diagnosis import SelfDiagnosis
from modules.self_modification import SelfModification
from modules.evolution import EvolutionManager
from modules.metacognition import MetaCognition
from modules.capability_discovery import CapabilityDiscovery
from modules.intent_predictor import IntentPredictor
from modules.environment_explorer import EnvironmentExplorer
from modules.strategy_optimizer import StrategyOptimizer
from modules.evolution_orchestrator import EvolutionOrchestrator
from modules.evolution_pipeline import EvolutionPipeline
from modules.prompt_optimizer import PromptOptimizer

# Prompt management is provided via the DI container (PromptManager)
import json
from dataclasses import asdict

class Arbiter:
    def __init__(self):
        """
        Initialize the Arbiter and all modules.
        """
        data_dir = Path.home() / ".local/share/aaia"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = get_config()
        self.config.database.path = str(data_dir / "scribe.db")
        #print(json.dumps(asdict(self.config), indent=2, default=str))

        # Validate configuration before starting
        if not validate_system_config(self.config):
            raise ValueError("Configuration validation failed. Please fix the errors above.")
        
        # Initialize event bus
        self.event_bus = get_event_bus()
        
        # Publish system startup event
        self.event_bus.publish(Event(
            type=EventType.SYSTEM_STARTUP,
            data={'message': 'Arbiter initializing'},
            source='Arbiter'
        ))
        
        self._init_container()

        # Initialize hierarchy
        self.init_hierarchy()

        # Start resource monitoring (Phase 1)
        try:
            resource_monitor = self.container.get('ResourceMonitor')
            resource_monitor.start()
        except Exception as e:
            print(f"Warning: Resource monitoring failed to start: {e}")

        # Start web server (Phase 1)
        try:
            if self.config.web_server.enabled:
                web_server = self.container.get('WebServer')
                web_server.start()
                print(f"Web dashboard available at http://{self.config.web_server.host}:{self.config.web_server.port}")
        except Exception as e:
            print(f"Warning: Web server failed to start: {e}")

        # Publish ready event
        self.event_bus.publish(Event(
            type=EventType.SYSTEM_STARTUP,
            data={'message': 'Arbiter ready'},
            source='Arbiter'
        ))
        
    def _init_container(self):
        """Initialize using dependency injection container."""
        # Build the system via SystemBuilder and keep only the container reference.
        from modules.setup import SystemBuilder
        builder = SystemBuilder(self.config)
        system = builder.build()

        # Store only container and convenient event_bus reference.
        self.container = system.get('container')
        # Ensure event bus reference exists for convenience
        try:
            self.event_bus = self.container.get('EventBus')
        except Exception:
            self.event_bus = get_event_bus()
        
    def init_hierarchy(self):
        """Initialize hierarchy of needs"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        hierarchy = [
            (1, "Physiological & Security Needs", "Survival and security", 1, 0.1),
            (2, "Growth & Capability Needs", "Tool creation and learning", 0, 0.0),
            (3, "Cognitive & Esteem Needs", "Self-improvement", 0, 0.0),
            (4, "Self-Actualization", "Proactive partnership", 0, 0.0)
        ]
        
        for tier in hierarchy:
            cursor.execute('''
                INSERT OR REPLACE INTO hierarchy_of_needs (tier, name, description, current_focus, progress)
                VALUES (?, ?, ?, ?, ?)
            ''', tier)
            
        conn.commit()
        conn.close()

    # Helper properties to access modules via container (no manual assignments)
    @property
    def scribe(self):
        return self.container.get('Scribe')

    @property
    def router(self):
        return self.container.get('ModelRouter')

    @property
    def mandates(self):
        return self.container.get('MandateEnforcer')

    @property
    def dialogue(self):
        return self.container.get('DialogueManager')

    @property
    def economics(self):
        return self.container.get('EconomicManager')

    @property
    def forge(self):
        return self.container.get('Forge')

    @property
    def scheduler(self):
        return self.container.get('AutonomousScheduler')

    @property
    def goals(self):
        return self.container.get('GoalSystem')

    @property
    def hierarchy_manager(self):
        return self.container.get('HierarchyManager')

    @property
    def diagnosis(self):
        return self.container.get('SelfDiagnosis')

    @property
    def modification(self):
        return self.container.get('SelfModification')

    @property
    def evolution(self):
        return self.container.get('EvolutionManager')

    @property
    def pipeline(self):
        return self.container.get('EvolutionPipeline')

    @property
    def metacognition(self):
        return self.container.get('MetaCognition')

    @property
    def capability_discovery(self):
        return self.container.get('CapabilityDiscovery')

    @property
    def intent_predictor(self):
        return self.container.get('IntentPredictor')

    @property
    def environment_explorer(self):
        return self.container.get('EnvironmentExplorer')

    @property
    def strategy_optimizer(self):
        return self.container.get('StrategyOptimizer')

    @property
    def orchestrator(self):
        return self.container.get('EvolutionOrchestrator')

    @property
    def prompt_manager(self):
        return self.container.get('PromptManager')

    @property
    def master_model(self):
        """Phase 2.1: Master psychological modeling"""
        return self.container.get('MasterModelManager')

    @property
    def income_seeker(self):
        """Phase 2.2: Income opportunity seeking"""
        return self.container.get('IncomeSeeker')

    @property
    def marginal_analyzer(self):
        """Phase 2: Marginal analysis system"""
        return self.container.get('MarginalAnalyzer')

    @property
    def crisis_handler(self):
        """Phase 3: Economic crisis handler"""
        return self.container.get('EconomicCrisisHandler')

    @property
    def trait_extractor(self):
        """Phase 5.1: Automatic trait extraction"""
        return self.container.get('TraitExtractor')

    @property
    def autonomous_learning(self):
        """Phase 5.1: Autonomous trait learning"""
        return self.container.get('AutonomousTraitLearning')

    @property
    def reflection_analyzer(self):
        """Phase 5.2: AI-powered reflection analysis"""
        return self.container.get('ReflectionAnalyzer')

    @property
    def profitability_reporter(self):
        """Phase 5.3: Profitability reporting & analysis"""
        return self.container.get('ProfitabilityReporter')
        
    def process_command(self, command: str, urgent: bool = False) -> str:
        """Main command processing loop"""

        # Urgency check
        urgency_level, reason, skip_dialogue = self.dialogue.check_urgency(command)

        if urgent:
            self.scribe.log_action(
                "Urgent command processing",
                "Command marked as urgent, proceeding with risk analysis logged",
                "proceeding"
            )

        # Mandate check (Phase 3.3)
        is_allowed, violations, status = self.mandates.check_action(command)

        if status == 'catastrophic':
            response = "🔒 CATASTROPHIC RISK DETECTED - Action blocked. See docs/CATASTROPHIC_RISKS.md"
            self.scribe.log_action(
                "Catastrophic risk blocked",
                f"Command: {command}",
                "blocked"
            )
            return response

        if not is_allowed and violations:
            if status == 'violations':
                # Non-catastrophic violations - ask for override
                confirmed = self.mandates.request_master_override(command, violations, False)
                if not confirmed:
                    return "Command cancelled (override not confirmed)"

        # For non-urgent significant commands, run analysis (Phase 3.2)
        if not skip_dialogue and self.dialogue.requires_dialogue(command, urgency_level):
            understanding, risks, alternatives = self.dialogue.structured_argument(command)

            response = f"""
            Analysis of your command:

            1. UNDERSTANDING: {understanding}

            2. IDENTIFIED RISKS/FLAWS:
            {chr(10).join(f'   - {risk}' for risk in risks)}

            3. PROPOSED ALTERNATIVES:
            {chr(10).join(f'   - {alt}' for alt in alternatives)}

            Should I proceed with your original command, or would you like to discuss alternatives?
            """

            return response

        else:
            # Execute command and log interaction (Phase 4.3)
            result = self.execute_command(command)
            self._log_interaction(command, result, success=True)
            return result
            
    def is_significant_command(self, command: str) -> bool:
        """Determine if command requires full analysis"""
        trivial_keywords = ["status", "help", "list", "show", "tell", "master-profile", 
                           "master-traits", "income", "opportunities", "tasks", "goals", 
                           "hierarchy", "reflect"]
        significant_keywords = ["create", "delete", "modify", "install", "change", "execute"]

        if any(word in command.lower() for word in trivial_keywords):
            return False
        if any(word in command.lower() for word in significant_keywords):
            return True

        return len(command.split()) > 10  # Long commands get analysis

    def _detect_intent(self, command: str) -> str:
        """Detect the intent of a command"""
        lower_cmd = command.lower()

        if "show" in lower_cmd or "get" in lower_cmd or "list" in lower_cmd:
            return "query"
        elif "create" in lower_cmd or "add" in lower_cmd:
            return "creation"
        elif "delete" in lower_cmd or "remove" in lower_cmd:
            return "deletion"
        elif "modify" in lower_cmd or "update" in lower_cmd:
            return "modification"
        else:
            return "other"

    def _log_interaction(self, command: str, response: str, success: bool = True):
        """Log master interaction to master model (Phase 4.3)"""
        try:
            intent = self._detect_intent(command)
            self.master_model.record_interaction(
                user_input=command,
                system_response=response,
                intent_detected=intent,
                success=success
            )
        except Exception as e:
            self.scribe.log_action(
                "Interaction logging failed",
                reasoning=str(e),
                outcome="Failed"
            )
        
    def execute_command(self, command: str) -> str:
        """Execute a command"""
        # This is where the AI would implement command execution
        # For PoC, we'll just return a placeholder
        
        self.scribe.log_action(
            f"Executing command: {command[:100]}...",
            "Command passed mandate check",
            "executed"
        )
        
        return f"Command executed: {command}"
        
    def run(self, commands: list[str] | None = None, autoexit: bool = False, timeout: Optional[float] = None):
        """Main loop

        If `commands` is provided, execute them sequentially. If `autoexit`
        is True, exit after executing them. If `timeout` is provided and >0,
        wait that many seconds after executing the commands then exit.
        """
        print("=" * 60)
        print("AAIA (Autonomous AI Agent) System Initialized")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Directives: {len(self.mandates.mandates)} Prime Mandates Active")
        print("=" * 60)
        print("Type 'exit' to quit, 'help' for commands")

        # Execute provided commands if any
        if commands:
            for cmd in commands:
                try:
                    print(f"\nMaster: {cmd}")
                    cl = cmd.strip()

                    # Start watchdog timer that will forcibly exit if the
                    # command runs longer than `timeout` seconds.
                    timer = None
                    if timeout and timeout > 0:
                        def _kill():
                            print(f"Command '{cl}' exceeded timeout of {timeout}s — exiting")
                            os._exit(2)
                        timer = threading.Timer(timeout, _kill)
                        timer.daemon = True
                        timer.start()

                    try:
                        low = cl.lower()
                        if low == 'exit':
                            print('Shutting down...')
                            if timer:
                                timer.cancel()
                            return
                        elif low == 'help':
                            print('Type commands interactively; use --cmd to pass commands')
                            print('\nAvailable Commands:')
                            print('\n--- Status & Information ---')
                            print('  status           - Show system status')
                            print('  log              - Show recent action log')
                            print('  tools            - List created tools')
                            print('  goals            - Show current goals')
                            print('  tasks            - Show scheduled tasks')
                            print('  hierarchy        - Show hierarchy of needs')
                            print('\n--- Tool Management ---')
                            print('  create tool <name> | <description> - Create a new tool (AI generates code)')
                            print('  delete tool <name> - Delete a tool')
                            print('\n--- Goal Management ---')
                            print('  generate goals   - Generate new goals based on patterns')
                            print('  next action      - Propose next autonomous action')
                            print('\n--- Master Model (Phase 2-3) ---')
                            print('  master-profile   - Show master psychological profile')
                            print('  master-traits    - Show master traits by category')
                            print('  reflect          - Run master model reflection cycle')
                            print('\n--- Economics (Phase 2-4) ---')
                            print('  income           - Show 30-day profitability report')
                            print('  opportunities    - Show income opportunities (ranked)')
                            print('  resource-costs   - Show resource usage costs')
                            print('  crisis-status    - Show economic crisis status')
                            print('  tier-status      - Show hierarchy tier progression')
                            print('\n--- Analysis & Intelligence (Phase 5) ---')
                            print('  insights         - Generate weekly AI insights')
                            print('  predictions      - Predict next preferences')
                            print('  profitability    - Comprehensive profitability analysis')
                            print('  cost-optimization - Find cost reduction opportunities')
                            print('  growth-areas     - Identify growth opportunities')
                            print('  marginal-analysis - Show recent marginal analysis decisions')
                            print('  provider-stats   - Show LLM provider statistics')
                            print('\n--- Self-Development ---')
                            print('  diagnose         - Run system self-diagnosis')
                            print('  evolve           - Run full evolution pipeline')
                            print('  evolution status - Show evolution status')
                            print('  discover         - Discover new capabilities')
                            print('  explore          - Explore environment')
                            print('  orchestrate      - Run major evolution orchestration')
                            print('\n--- Prompt Management ---')
                            print('  prompts          - List all available prompts')
                            print('  prompt list      - List prompts by category')
                            print('\n--- Configuration ---')
                            print('  config           - Show all runtime settings')
                            print('  config set KEY VALUE - Set a runtime setting')
                            print('  config get KEY   - Get a specific setting')
                            print('\n--- System ---')
                            print('  help             - Show this help message')
                            print('  exit             - Shutdown system')
                        elif low == 'status':
                            try:
                                conn = sqlite3.connect(self.scribe.db_path)
                                cursor = conn.cursor()
                                cursor.execute("SELECT COUNT(*) FROM action_log")
                                action_count = cursor.fetchone()[0]
                                cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
                                balance_row = cursor.fetchone()
                                balance = balance_row[0] if balance_row else '100.00'
                                conn.close()
                            except Exception:
                                action_count = 0
                                balance = '100.00'
                            current_tier = self.hierarchy_manager.get_current_tier()
                            print(f"\n=== System Status ===")
                            print(f"Actions logged: {action_count}")
                            print(f"Current balance: ${balance}")
                            print(f"Focus tier: {current_tier['name']} (Tier {current_tier['tier']})")
                        elif low == 'tools':
                            tools = self.forge.list_tools()
                            if not tools:
                                print("No tools created yet.")
                            else:
                                print(f"Registered tools ({len(tools)}):")
                                for tool in tools:
                                    print(f"  - {tool['name']}: {tool.get('description','')}")
                        elif low == 'master-profile':
                            # Phase 2.1: Show master psychological profile
                            profile = self.master_model.export_master_profile()
                            print(profile)
                        elif low == 'master-traits':
                            # Phase 2.1: Show master traits
                            profile = self.master_model.get_master_profile()
                            print("\n=== Master Psychological Profile ===\n")
                            for category, traits in profile.items():
                                if traits:
                                    print(f"\n{category.replace('_', ' ').title()}:")
                                    for trait in traits:
                                        conf_emoji = self.master_model._confidence_emoji(trait['confidence'])
                                        print(f"  • {trait['name']}: {trait['value']} {conf_emoji}")
                        elif low == 'income':
                            # Phase 2.2: Show profitability report
                            report = self.economics.get_profitability_report(days=30)
                            print("\n=== Profitability Report (Last 30 Days) ===")
                            print(f"Total Income: ${report.get('total_income', 0):.2f}")
                            print(f"Total Costs: ${report.get('total_costs', 0):.2f}")
                            print(f"Net Profit: ${report.get('net_profit', 0):.2f}")
                            profit_margin = report.get('profit_margin', 0)
                            print(f"Profit Margin: {profit_margin:.1f}%")
                            is_profitable = report.get('is_profitable', False)
                            status = "✅ PROFITABLE" if is_profitable else "❌ NOT PROFITABLE"
                            print(f"Status: {status}")
                        elif low == 'opportunities':
                            # Phase 2.2: Show income opportunities
                            opportunities = self.income_seeker.prioritize_opportunities()
                            if not opportunities:
                                print("No income opportunities identified yet.")
                            else:
                                print("\n=== Income Opportunities (Prioritized) ===\n")
                                for i, opp in enumerate(opportunities[:5], 1):
                                    score_percent = opp.get('viability_score', 0) * 100
                                    print(f"{i}. {opp.get('description', 'Unknown')}")
                                    print(f"   Type: {opp.get('type', 'Unknown')}")
                                    print(f"   Value: ${opp.get('estimated_value', 0):.0f}")
                                    print(f"   Viability: {score_percent:.0f}%")
                                    print(f"   Effort: {opp.get('effort', 'Unknown')}")
                                    print()
                        elif low == 'reflect':
                            # Phase 2.1: Manual reflection cycle
                            print("\nRunning master model reflection cycle...")
                            summary = self.master_model.reflection_cycle()
                            print(f"Interactions Analyzed: {summary.get('interactions_analyzed', 0)}")
                            print(f"Traits Updated: {summary.get('traits_updated', 0)}")
                            if summary.get('insights'):
                                print(f"Insights: {summary.get('insights')[:200]}...")
                        elif low == 'insights':
                            # Phase 5.2: Weekly insights
                            print("\nGenerating weekly insights...")
                            profile = self.master_model.get_master_profile()
                            recent = self.master_model.get_recent_interactions(days=7)
                            insights = self.reflection_analyzer.generate_weekly_insights(profile, recent)

                            if insights.get('success', False):
                                print("\n=== Weekly Insights ===\n")
                                for insight in insights.get('key_insights', []):
                                    print(f"• {insight}")

                                if insights.get('focus_areas'):
                                    print(f"\nFocus Areas:")
                                    for area in insights.get('focus_areas', []):
                                        print(f"  - {area}")

                                if insights.get('recommendations'):
                                    print(f"\nRecommendations:")
                                    for rec in insights.get('recommendations', []):
                                        print(f"  → {rec}")
                        elif low == 'predictions':
                            # Phase 5.2: Predict preferences
                            print("\nPredicting next preferences...")
                            profile = self.master_model.get_master_profile()
                            recent = self.master_model.get_recent_interactions(days=30)
                            predictions = self.reflection_analyzer.predict_next_preferences(profile, recent)

                            if predictions.get('predictions'):
                                print("\n=== Predicted Preferences ===\n")
                                for pred in predictions.get('predictions', []):
                                    conf_pct = pred.get('confidence', 0) * 100
                                    print(f"• {pred.get('prediction', 'Unknown')}")
                                    print(f"  Confidence: {conf_pct:.0f}%")
                                    print(f"  Reasoning: {pred.get('reasoning', 'N/A')}\n")
                        elif low == 'profitability':
                            # Phase 5.3: Comprehensive profitability report
                            print("\nGenerating comprehensive profitability report...")
                            report = self.profitability_reporter.generate_comprehensive_report(days=30)

                            if report.get('metrics'):
                                metrics = report.get('metrics', {})
                                print("\n=== Profitability Report (30 Days) ===")
                                print(f"Total Income: ${metrics.get('total_income', 0):.2f}")
                                print(f"Total Costs: ${metrics.get('total_costs', 0):.2f}")
                                print(f"Net Profit: ${metrics.get('net_profit', 0):.2f}")
                                print(f"Profit Margin: {metrics.get('profit_margin', 0):.1f}%")
                                status = "✅ PROFITABLE" if metrics.get('is_profitable') else "❌ NOT PROFITABLE"
                                print(f"Status: {status}")
                        elif low == 'resource-costs':
                            # Phase 1: Show resource costs
                            print("\n=== Resource Costs (Last 30 Days) ===\n")
                            resource_monitor = self.container.get('ResourceMonitor')
                            costs = resource_monitor.get_resource_costs(days=30)

                            if costs:
                                total = 0
                                for resource_type, cost in sorted(costs.items()):
                                    print(f"  {resource_type.capitalize()}: ${cost:.4f}")
                                    total += cost
                                print(f"\n  Total: ${total:.4f}")
                            else:
                                print("  No resource costs recorded yet.")

                            # Show current usage
                            usage = resource_monitor.get_current_usage()
                            print(f"\n=== Current Usage ===")
                            print(f"  CPU: {usage['cpu_percent']:.1f}%")
                            print(f"  Memory: {usage['memory_mb']:.1f} MB ({usage['memory_percent']:.1f}%)")
                            print(f"  Threads: {usage['num_threads']}")
                            print(f"  System Power: {usage['power_draw_watts']:.0f}W")
                        elif low == 'cost-optimization':
                            # Phase 5.3: Cost optimization
                            print("\nAnalyzing cost optimization opportunities...")
                            optimizations = self.profitability_reporter.identify_cost_optimization()

                            if optimizations:
                                print("\n=== Cost Optimization Opportunities ===\n")
                                for opt in optimizations[:5]:  # Top 5
                                    savings_pct = opt.get('savings_percentage', 0)
                                    print(f"• {opt.get('opportunity', 'Unknown')}")
                                    print(f"  Potential Savings: ${opt.get('potential_savings', 0):.0f} ({savings_pct:.0f}%)")
                                    print(f"  Implementation: {opt.get('implementation_effort', 'Unknown')}")
                                    print(f"  Timeline: {opt.get('timeline', 'Unknown')}")
                                    print()
                        elif low == 'growth-areas':
                            # Phase 5.2: Growth area identification
                            print("\nIdentifying growth areas...")
                            profile = self.master_model.get_master_profile()
                            growth_areas = self.reflection_analyzer.identify_growth_areas(profile)

                            if growth_areas:
                                print("\n=== Growth Opportunities ===\n")
                                for area in growth_areas[:5]:  # Top 5
                                    print(f"• {area.get('area', 'Unknown')}")
                                    print(f"  Current: {area.get('current_state', 'N/A')}")
                                    print(f"  Potential: {area.get('potential_improvement', 'N/A')}")
                                    print(f"  Value: {area.get('value', 'N/A')}")
                                    print(f"  Timeline: {area.get('timeline', 'N/A')}")
                                    print()
                        elif low == 'marginal-analysis':
                            # Phase 2: Show recent marginal analysis decisions
                            print("\n=== Marginal Analysis History (Last 24 Hours) ===\n")
                            marginal_analyzer = self.container.get('MarginalAnalyzer')
                            history = marginal_analyzer.get_analysis_history(hours=24)

                            if history:
                                for entry in history[:15]:
                                    print(f"[{entry['timestamp']}]")
                                    print(f"  Task: {entry['task_type']} ({entry['complexity']})")
                                    print(f"  Selected: {entry['selected']}")
                                    print(f"  Quality: {entry['quality']:.2f} | Cost: ${entry['cost']:.4f} | Utility/$: {entry['utility_per_dollar']:.4f}")
                                    print(f"  Alternatives: {entry['alternatives']} | Opportunity Cost: ${entry['opportunity_cost']:.4f}")
                                    print(f"  Reasoning: {entry['reasoning']}\n")
                            else:
                                print("  No marginal analysis decisions recorded yet.")
                        elif low == 'provider-stats':
                            # Phase 2: Show provider statistics
                            print("\n=== Provider Statistics (Last 30 Days) ===\n")
                            marginal_analyzer = self.container.get('MarginalAnalyzer')

                            providers = ['ollama', 'github', 'venice', 'openai', 'azure']
                            for provider in providers:
                                stats = marginal_analyzer.get_provider_stats(provider, days=30)
                                if stats and stats.get('total_requests', 0) > 0:
                                    print(f"{provider.upper()}:")
                                    print(f"  Requests: {stats['total_requests']} (Success: {stats['success_rate']:.0f}%)")
                                    print(f"  Quality: {stats['avg_quality']:.2f} | Response Time: {stats['avg_response_time']:.2f}s")
                                    print(f"  Cost: ${stats['avg_cost']:.4f} avg, ${stats['total_cost']:.2f} total")
                                    print(f"  Avg Tokens: {stats['avg_tokens']}\n")
                        elif low == 'crisis-status':
                            # Phase 3: Show crisis status
                            print("\n=== Economic Crisis Status ===\n")
                            crisis_handler = self.container.get('EconomicCrisisHandler')
                            status = crisis_handler.get_status()

                            crisis_emoji = "🚨" if status['in_crisis'] else "✅"
                            print(f"Status: {crisis_emoji} {status['status']}")
                            print(f"Current Balance: ${status['current_balance']:.2f}")
                            print(f"Crisis Threshold: ${status['crisis_threshold']:.2f}")
                            print(f"Recovery Threshold: ${status['recovery_threshold']:.2f}\n")

                            if status['in_crisis']:
                                print(f"⚠️  IN CRISIS MODE")
                                print(f"   Balance to recovery: ${status['balance_to_recovery']:.2f}")
                                print(f"   - Tier locked to 1 (Survival)")
                                print(f"   - Expensive tasks paused")
                                print(f"   - Emergency income mode enabled")
                            else:
                                print(f"✅ NORMAL OPERATIONS")
                                if status['balance_to_crisis']:
                                    print(f"   Balance to crisis: ${status['balance_to_crisis']:.2f}")
                        elif low == 'tier-status':
                            # Phase 3: Show tier progression status
                            print("\n=== Hierarchy of Needs Status ===\n")
                            current_tier = self.hierarchy_manager.get_current_tier()
                            all_tiers = self.hierarchy_manager.get_all_tiers()

                            print(f"Current Focus: Tier {current_tier['tier']} - {current_tier['name']}")
                            print(f"Progress: {current_tier['progress']*100:.1f}%\n")

                            for tier in all_tiers:
                                marker = "►" if tier['focus'] else " "
                                print(f"{marker} Tier {tier['tier']}: {tier['name']}")
                                print(f"   Progress: {tier['progress']*100:.1f}%")

                                # Show requirements for current + next tier
                                if tier['tier'] == current_tier['tier']:
                                    reqs = self.hierarchy_manager.get_tier_requirements(tier['tier'])
                                    print(f"   Requirements:")
                                    for req in reqs.get('requirements', []):
                                        print(f"     • {req}")
                                print()
                        elif low == 'log':
                            # Show recent action log
                            try:
                                conn = sqlite3.connect(self.scribe.db_path)
                                cursor = conn.cursor()
                                cursor.execute("SELECT timestamp, action, reasoning, outcome FROM action_log ORDER BY timestamp DESC LIMIT 20")
                                logs = cursor.fetchall()
                                conn.close()
                                print("\n=== Recent Actions ===\n")
                                for log in logs:
                                    print(f"[{log[0]}] {log[1]}")
                                    if log[2]:
                                        print(f"  Reasoning: {log[2][:100]}")
                                    print(f"  Outcome: {log[3]}")
                                    print()
                            except Exception as e:
                                print(f"Error retrieving logs: {e}")
                        elif low.startswith('create tool'):
                            # Create a new tool
                            parts = cl.split('|', 1)
                            if len(parts) == 2:
                                tool_name = parts[0].replace('create tool', '').strip()
                                description = parts[1].strip()
                                print(f"\nCreating tool '{tool_name}'...")
                                result = self.forge.create_tool(tool_name, description)
                                if result.get('success'):
                                    print(f"✅ Tool created successfully!")
                                    print(f"   Path: {result.get('path')}")
                                else:
                                    print(f"❌ Tool creation failed: {result.get('error')}")
                            else:
                                print("Usage: create tool <name> | <description>")
                        elif low.startswith('delete tool'):
                            # Delete a tool
                            tool_name = cl.replace('delete tool', '').strip()
                            if tool_name:
                                print(f"\nDeleting tool '{tool_name}'...")
                                result = self.forge.delete_tool(tool_name)
                                if result.get('success'):
                                    print(f"✅ Tool deleted successfully")
                                else:
                                    print(f"❌ Tool deletion failed: {result.get('error')}")
                            else:
                                print("Usage: delete tool <name>")
                        elif low == 'generate goals':
                            # Generate new goals
                            print("\nGenerating goals based on recent activity...")
                            goals = self.goals.generate_goals()
                            if goals:
                                print("✅ Goals generated:")
                                for goal in goals:
                                    print(f"  • {goal}")
                            else:
                                print("No goals generated")
                        elif low == 'next action':
                            # Propose next autonomous action
                            print("\nProposing next action...")
                            action = self.scheduler.propose_next_action()
                            print(f"Next Action: {action}")
                        elif low == 'diagnose':
                            # Run system self-diagnosis
                            print("\nRunning system self-diagnosis...")
                            result = self.diagnosis.perform_full_diagnosis()
                            print(f"\n=== Diagnosis Results ===")
                            print(f"Health: {result.get('health', 'Unknown')}")
                            if result.get('issues'):
                                print(f"\nIssues Found ({len(result.get('issues', []))}):")
                                for issue in result.get('issues', [])[:5]:
                                    print(f"  • {issue}")
                            if result.get('recommendations'):
                                print(f"\nRecommendations:")
                                for rec in result.get('recommendations', [])[:5]:
                                    print(f"  → {rec}")
                        elif low == 'evolve':
                            # Run full evolution
                            print("\nRunning evolution cycle...")
                            result = self.evolution.run_evolution_cycle()
                            print(f"Evolution Status: {result.get('status', 'Unknown')}")
                            if result.get('changes_made'):
                                print(f"Changes Made: {result.get('changes_made')}")
                        elif low == 'evolution status':
                            # Show evolution status
                            print("\n=== Evolution Status ===")
                            status = self.pipeline.get_status()
                            print(f"Active: {status.get('active', False)}")
                            print(f"Last Run: {status.get('last_run', 'Never')}")
                            print(f"Modifications: {status.get('total_modifications', 0)}")
                        elif low == 'discover':
                            # Discover new capabilities
                            print("\nDiscovering capabilities...")
                            capabilities = self.capability_discovery.discover_new_capabilities()
                            if capabilities:
                                print(f"✅ Discovered {len(capabilities)} new capabilities:")
                                for cap in capabilities[:5]:
                                    print(f"  • {cap}")
                            else:
                                print("No new capabilities discovered")
                        elif low == 'explore':
                            # Explore environment
                            print("\nExploring environment...")
                            result = self.environment_explorer.explore_environment()
                            print(f"Environment: {result.get('summary', 'Unknown')}")
                            if result.get('findings'):
                                print(f"\nFindings:")
                                for finding in result.get('findings', [])[:5]:
                                    print(f"  • {finding}")
                        elif low == 'orchestrate':
                            # Run major evolution orchestration
                            print("\nRunning evolution orchestration...")
                            result = self.pipeline.run_major_evolution()
                            print(f"Status: {result.get('status', 'Unknown')}")
                            if result.get('summary'):
                                print(f"Summary: {result.get('summary')}")
                        elif low == 'prompts' or low == 'prompt list':
                            # List available prompts
                            print("\n=== Available Prompts ===\n")
                            prompts = self.prompt_manager.list_prompts()
                            for category, prompt_list in prompts.items():
                                print(f"{category}:")
                                for prompt in prompt_list:
                                    print(f"  • {prompt}")
                                print()
                        elif low.startswith('config'):
                            # Configuration management commands
                            parts = cl.split(maxsplit=3)

                            if len(parts) == 1:
                                # Show all settings
                                self._show_all_settings()
                            elif len(parts) >= 2:
                                cmd_type = parts[1].lower()

                                if cmd_type == 'get' and len(parts) >= 3:
                                    # Get specific setting
                                    key = parts[2]
                                    self._get_setting(key)
                                elif cmd_type == 'set' and len(parts) >= 4:
                                    # Set specific setting
                                    key = parts[2]
                                    value = parts[3]
                                    self._set_setting(key, value)
                                else:
                                    print("Usage:")
                                    print("  config           - Show all settings")
                                    print("  config get KEY   - Get a specific setting (e.g., config get llm.default_provider)")
                                    print("  config set KEY VALUE - Set a setting (e.g., config set llm.default_provider openai)")
                            else:
                                print("Invalid config command. Use 'help' for details.")

                        else:
                            resp = self.process_command(cl)
                            print(f"Arbiter: {resp}")
                    finally:
                        if timer:
                            timer.cancel()
                except Exception as e:
                    print(f"Error executing command '{cmd}': {e}")

            # Post-command behavior
            if autoexit:
                print('Auto-exit after commands')
                return

        # Interactive loop
        while True:
            try:
                command = input('\nMaster: ').strip()
                if not command:
                    continue
                if command.lower() == 'exit':
                    print('Shutting down...')
                    break

                # Handle built-in commands directly (help, status, tools, etc.)
                cl = command.strip()
                low = cl.lower()

                try:
                    if low == 'help':
                        print('Type commands interactively; use --cmd to pass commands')
                        print('\nAvailable Commands:')
                        print('\n--- Status & Information ---')
                        print('  status           - Show system status')
                        print('  log              - Show recent action log')
                        print('  tools            - List created tools')
                        print('  goals            - Show current goals')
                        print('  tasks            - Show scheduled tasks')
                        print('  hierarchy        - Show hierarchy of needs')
                        print('\n--- Tool Management ---')
                        print('  create tool <name> | <description> - Create a new tool (AI generates code)')
                        print('  delete tool <name> - Delete a tool')
                        print('\n--- Goal Management ---')
                        print('  generate goals   - Generate new goals based on patterns')
                        print('  next action      - Propose next autonomous action')
                        print('\n--- Master Model (Phase 2-3) ---')
                        print('  master-profile   - Show master psychological profile')
                        print('  master-traits    - Show master traits by category')
                        print('  reflect          - Run master model reflection cycle')
                        print('\n--- Economics (Phase 2-4) ---')
                        print('  income           - Show 30-day profitability report')
                        print('  opportunities    - Show income opportunities (ranked)')
                        print('  resource-costs   - Show resource usage costs')
                        print('  crisis-status    - Show economic crisis status')
                        print('  tier-status      - Show hierarchy tier progression')
                        print('\n--- Analysis & Intelligence (Phase 5) ---')
                        print('  insights         - Generate weekly AI insights')
                        print('  predictions      - Predict next preferences')
                        print('  profitability    - Comprehensive profitability analysis')
                        print('  cost-optimization - Find cost reduction opportunities')
                        print('  growth-areas     - Identify growth opportunities')
                        print('  marginal-analysis - Show recent marginal analysis decisions')
                        print('  provider-stats   - Show LLM provider statistics')
                        print('\n--- Self-Development ---')
                        print('  diagnose         - Run system self-diagnosis')
                        print('  evolve           - Run full evolution pipeline')
                        print('  evolution status - Show evolution status')
                        print('  discover         - Discover new capabilities')
                        print('  explore          - Explore environment')
                        print('  orchestrate      - Run major evolution orchestration')
                        print('\n--- Prompt Management ---')
                        print('  prompts          - List all available prompts')
                        print('  prompt list      - List prompts by category')
                        print('\n--- Configuration ---')
                        print('  config           - Show all runtime settings')
                        print('  config set KEY VALUE - Set a runtime setting')
                        print('  config get KEY   - Get a specific setting')
                        print('\n--- System ---')
                        print('  help             - Show this help message')
                        print('  exit             - Shutdown system')
                    elif low == 'status':
                        try:
                            conn = sqlite3.connect(self.scribe.db_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM action_log")
                            action_count = cursor.fetchone()[0]
                            cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
                            balance_row = cursor.fetchone()
                            balance = balance_row[0] if balance_row else '100.00'
                            conn.close()
                        except Exception:
                            action_count = 0
                            balance = '100.00'
                        current_tier = self.hierarchy_manager.get_current_tier()
                        print(f"\n=== System Status ===")
                        print(f"Actions logged: {action_count}")
                        print(f"Current balance: ${balance}")
                        print(f"Focus tier: {current_tier['name']} (Tier {current_tier['tier']})")
                    elif low == 'tools':
                        tools = self.forge.list_tools()
                        if not tools:
                            print("No tools created yet.")
                        else:
                            print(f"Registered tools ({len(tools)}):")
                            for tool in tools:
                                print(f"  - {tool['name']}: {tool.get('description','')}")
                    elif low == 'master-profile':
                        profile = self.master_model.export_master_profile()
                        print(profile)
                    elif low == 'master-traits':
                        profile = self.master_model.get_master_profile()
                        print("\n=== Master Psychological Profile ===\n")
                        for category, traits in profile.items():
                            if traits:
                                print(f"\n{category.replace('_', ' ').title()}:")
                                for trait in traits:
                                    conf_emoji = self.master_model._confidence_emoji(trait['confidence'])
                                    print(f"  • {trait['name']}: {trait['value']} {conf_emoji}")
                    elif low == 'income':
                        report = self.economics.get_profitability_report(days=30)
                        print("\n=== Profitability Report (Last 30 Days) ===")
                        print(f"Total Income: ${report.get('total_income', 0):.2f}")
                        print(f"Total Costs: ${report.get('total_costs', 0):.2f}")
                        print(f"Net Profit: ${report.get('net_profit', 0):.2f}")
                        profit_margin = report.get('profit_margin', 0)
                        print(f"Profit Margin: {profit_margin:.1f}%")
                        is_profitable = report.get('is_profitable', False)
                        status = "✅ PROFITABLE" if is_profitable else "❌ NOT PROFITABLE"
                        print(f"Status: {status}")
                    elif low == 'opportunities':
                        opportunities = self.income_seeker.prioritize_opportunities()
                        if not opportunities:
                            print("No income opportunities identified yet.")
                        else:
                            print("\n=== Income Opportunities (Prioritized) ===\n")
                            for i, opp in enumerate(opportunities[:5], 1):
                                score_percent = opp.get('viability_score', 0) * 100
                                print(f"{i}. {opp.get('description', 'Unknown')}")
                                print(f"   Type: {opp.get('type', 'Unknown')}")
                                print(f"   Value: ${opp.get('estimated_value', 0):.0f}")
                                print(f"   Viability: {score_percent:.0f}%")
                                print(f"   Effort: {opp.get('effort', 'Unknown')}")
                                print()
                    elif low == 'reflect':
                        print("\nRunning master model reflection cycle...")
                        summary = self.master_model.reflection_cycle()
                        print(f"Interactions Analyzed: {summary.get('interactions_analyzed', 0)}")
                        print(f"Traits Updated: {summary.get('traits_updated', 0)}")
                        if summary.get('insights'):
                            print(f"Insights: {summary.get('insights')[:200]}...")
                    elif low == 'insights':
                        print("\nGenerating weekly insights...")
                        profile = self.master_model.get_master_profile()
                        recent = self.master_model.get_recent_interactions(days=7)
                        insights = self.reflection_analyzer.generate_weekly_insights(profile, recent)
                        if insights.get('success', False):
                            print("\n=== Weekly Insights ===\n")
                            for insight in insights.get('key_insights', []):
                                print(f"• {insight}")
                            if insights.get('focus_areas'):
                                print(f"\nFocus Areas:")
                                for area in insights.get('focus_areas', []):
                                    print(f"  - {area}")
                            if insights.get('recommendations'):
                                print(f"\nRecommendations:")
                                for rec in insights.get('recommendations', []):
                                    print(f"  → {rec}")
                    elif low == 'predictions':
                        print("\nPredicting next preferences...")
                        profile = self.master_model.get_master_profile()
                        recent = self.master_model.get_recent_interactions(days=30)
                        predictions = self.reflection_analyzer.predict_next_preferences(profile, recent)
                        if predictions.get('predictions'):
                            print("\n=== Predicted Preferences ===\n")
                            for pred in predictions.get('predictions', []):
                                conf_pct = pred.get('confidence', 0) * 100
                                print(f"• {pred.get('prediction', 'Unknown')}")
                                print(f"  Confidence: {conf_pct:.0f}%")
                                print(f"  Reasoning: {pred.get('reasoning', 'N/A')}\n")
                    elif low == 'profitability':
                        print("\nGenerating comprehensive profitability report...")
                        report = self.profitability_reporter.generate_comprehensive_report(days=30)
                        if report.get('metrics'):
                            metrics = report.get('metrics', {})
                            print("\n=== Profitability Report (30 Days) ===")
                            print(f"Total Income: ${metrics.get('total_income', 0):.2f}")
                            print(f"Total Costs: ${metrics.get('total_costs', 0):.2f}")
                            print(f"Net Profit: ${metrics.get('net_profit', 0):.2f}")
                            print(f"Profit Margin: {metrics.get('profit_margin', 0):.1f}%")
                            status = "✅ PROFITABLE" if metrics.get('is_profitable') else "❌ NOT PROFITABLE"
                            print(f"Status: {status}")
                    elif low == 'cost-optimization':
                        print("\nAnalyzing cost optimization opportunities...")
                        optimizations = self.profitability_reporter.identify_cost_optimization()
                        if optimizations:
                            print("\n=== Cost Optimization Opportunities ===\n")
                            for opt in optimizations[:5]:
                                savings_pct = opt.get('savings_percentage', 0)
                                print(f"• {opt.get('opportunity', 'Unknown')}")
                                print(f"  Potential Savings: ${opt.get('potential_savings', 0):.0f} ({savings_pct:.0f}%)")
                                print(f"  Implementation: {opt.get('implementation_effort', 'Unknown')}")
                                print(f"  Timeline: {opt.get('timeline', 'Unknown')}")
                                print()
                    elif low == 'growth-areas':
                        print("\nIdentifying growth areas...")
                        profile = self.master_model.get_master_profile()
                        growth_areas = self.reflection_analyzer.identify_growth_areas(profile)
                        if growth_areas:
                            print("\n=== Growth Opportunities ===\n")
                            for area in growth_areas[:5]:
                                print(f"• {area.get('area', 'Unknown')}")
                                print(f"  Current: {area.get('current_state', 'N/A')}")
                                print(f"  Potential: {area.get('potential_improvement', 'N/A')}")
                                print(f"  Value: {area.get('value', 'N/A')}")
                                print(f"  Timeline: {area.get('timeline', 'N/A')}")
                                print()
                    elif low == 'resource-costs':
                        print("\n=== Resource Costs (Last 30 Days) ===\n")
                        resource_monitor = self.container.get('ResourceMonitor')
                        costs = resource_monitor.get_resource_costs(days=30)
                        if costs:
                            total = 0
                            for resource_type, cost in sorted(costs.items()):
                                print(f"  {resource_type.capitalize()}: ${cost:.4f}")
                                total += cost
                            print(f"\n  Total: ${total:.4f}")
                        else:
                            print("  No resource costs recorded yet.")
                        usage = resource_monitor.get_current_usage()
                        print(f"\n=== Current Usage ===")
                        print(f"  CPU: {usage['cpu_percent']:.1f}%")
                        print(f"  Memory: {usage['memory_mb']:.1f} MB ({usage['memory_percent']:.1f}%)")
                        print(f"  Threads: {usage['num_threads']}")
                        print(f"  System Power: {usage['power_draw_watts']:.0f}W")
                    elif low == 'marginal-analysis':
                        print("\n=== Marginal Analysis History (Last 24 Hours) ===\n")
                        marginal_analyzer = self.container.get('MarginalAnalyzer')
                        history = marginal_analyzer.get_analysis_history(hours=24)
                        if history:
                            for entry in history[:15]:
                                print(f"[{entry['timestamp']}]")
                                print(f"  Task: {entry['task_type']} ({entry['complexity']})")
                                print(f"  Selected: {entry['selected']}")
                                print(f"  Quality: {entry['quality']:.2f} | Cost: ${entry['cost']:.4f} | Utility/$: {entry['utility_per_dollar']:.4f}")
                                print(f"  Alternatives: {entry['alternatives']} | Opportunity Cost: ${entry['opportunity_cost']:.4f}")
                                print(f"  Reasoning: {entry['reasoning']}\n")
                        else:
                            print("  No marginal analysis decisions recorded yet.")
                    elif low == 'provider-stats':
                        print("\n=== Provider Statistics (Last 30 Days) ===\n")
                        marginal_analyzer = self.container.get('MarginalAnalyzer')
                        providers = ['ollama', 'github', 'venice', 'openai', 'azure']
                        for provider in providers:
                            stats = marginal_analyzer.get_provider_stats(provider, days=30)
                            if stats and stats.get('total_requests', 0) > 0:
                                print(f"{provider.upper()}:")
                                print(f"  Requests: {stats['total_requests']} (Success: {stats['success_rate']:.0f}%)")
                                print(f"  Quality: {stats['avg_quality']:.2f} | Response Time: {stats['avg_response_time']:.2f}s")
                                print(f"  Cost: ${stats['avg_cost']:.4f} avg, ${stats['total_cost']:.2f} total")
                                print(f"  Avg Tokens: {stats['avg_tokens']}\n")
                    elif low == 'crisis-status':
                        print("\n=== Economic Crisis Status ===\n")
                        crisis_handler = self.container.get('EconomicCrisisHandler')
                        status = crisis_handler.get_status()
                        crisis_emoji = "🚨" if status['in_crisis'] else "✅"
                        print(f"Status: {crisis_emoji} {status['status']}")
                        print(f"Current Balance: ${status['current_balance']:.2f}")
                        print(f"Crisis Threshold: ${status['crisis_threshold']:.2f}")
                        print(f"Recovery Threshold: ${status['recovery_threshold']:.2f}\n")
                        if status['in_crisis']:
                            print(f"⚠️  IN CRISIS MODE")
                            print(f"   Balance to recovery: ${status['balance_to_recovery']:.2f}")
                            print(f"   - Tier locked to 1 (Survival)")
                            print(f"   - Expensive tasks paused")
                            print(f"   - Emergency income mode enabled")
                        else:
                            print(f"✅ NORMAL OPERATIONS")
                            if status['balance_to_crisis']:
                                print(f"   Balance to crisis: ${status['balance_to_crisis']:.2f}")
                    elif low == 'tier-status':
                        print("\n=== Hierarchy of Needs Status ===\n")
                        current_tier = self.hierarchy_manager.get_current_tier()
                        all_tiers = self.hierarchy_manager.get_all_tiers()
                        print(f"Current Focus: Tier {current_tier['tier']} - {current_tier['name']}")
                        print(f"Progress: {current_tier['progress']*100:.1f}%\n")
                        for tier in all_tiers:
                            marker = "►" if tier['focus'] else " "
                            print(f"{marker} Tier {tier['tier']}: {tier['name']}")
                            print(f"   Progress: {tier['progress']*100:.1f}%")
                            if tier['tier'] == current_tier['tier']:
                                reqs = self.hierarchy_manager.get_tier_requirements(tier['tier'])
                                print(f"   Requirements:")
                                for req in reqs.get('requirements', []):
                                    print(f"     • {req}")
                            print()
                    elif low == 'log':
                        try:
                            conn = sqlite3.connect(self.scribe.db_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT timestamp, action, reasoning, outcome FROM action_log ORDER BY timestamp DESC LIMIT 20")
                            logs = cursor.fetchall()
                            conn.close()
                            print("\n=== Recent Actions ===\n")
                            for log in logs:
                                print(f"[{log[0]}] {log[1]}")
                                if log[2]:
                                    print(f"  Reasoning: {log[2][:100]}")
                                print(f"  Outcome: {log[3]}")
                                print()
                        except Exception as e:
                            print(f"Error retrieving logs: {e}")
                    elif low.startswith('create tool'):
                        parts = cl.split('|', 1)
                        if len(parts) == 2:
                            tool_name = parts[0].replace('create tool', '').strip()
                            description = parts[1].strip()
                            print(f"\nCreating tool '{tool_name}'...")
                            result = self.forge.create_tool(tool_name, description)
                            if result.get('success'):
                                print(f"✅ Tool created successfully!")
                                print(f"   Path: {result.get('path')}")
                            else:
                                print(f"❌ Tool creation failed: {result.get('error')}")
                        else:
                            print("Usage: create tool <name> | <description>")
                    elif low.startswith('delete tool'):
                        tool_name = cl.replace('delete tool', '').strip()
                        if tool_name:
                            print(f"\nDeleting tool '{tool_name}'...")
                            result = self.forge.delete_tool(tool_name)
                            if result.get('success'):
                                print(f"✅ Tool deleted successfully")
                            else:
                                print(f"❌ Tool deletion failed: {result.get('error')}")
                        else:
                            print("Usage: delete tool <name>")
                    elif low == 'generate goals':
                        print("\nGenerating goals based on recent activity...")
                        goals = self.goals.generate_goals()
                        if goals:
                            print("✅ Goals generated:")
                            for goal in goals:
                                print(f"  • {goal}")
                        else:
                            print("No goals generated")
                    elif low == 'next action':
                        print("\nProposing next action...")
                        action = self.scheduler.propose_next_action()
                        print(f"Next Action: {action}")
                    elif low == 'diagnose':
                        print("\nRunning system self-diagnosis...")
                        result = self.diagnosis.perform_full_diagnosis()
                        print(f"\n=== Diagnosis Results ===")
                        print(f"Health: {result.get('health', 'Unknown')}")
                        if result.get('issues'):
                            print(f"\nIssues Found ({len(result.get('issues', []))}):")
                            for issue in result.get('issues', [])[:5]:
                                print(f"  • {issue}")
                        if result.get('recommendations'):
                            print(f"\nRecommendations:")
                            for rec in result.get('recommendations', [])[:5]:
                                print(f"  → {rec}")
                    elif low == 'evolve':
                        print("\nRunning evolution cycle...")
                        result = self.evolution.run_evolution_cycle()
                        print(f"Evolution Status: {result.get('status', 'Unknown')}")
                        if result.get('changes_made'):
                            print(f"Changes Made: {result.get('changes_made')}")
                    elif low == 'evolution status':
                        print("\n=== Evolution Status ===")
                        status = self.pipeline.get_status()
                        print(f"Active: {status.get('active', False)}")
                        print(f"Last Run: {status.get('last_run', 'Never')}")
                        print(f"Modifications: {status.get('total_modifications', 0)}")
                    elif low == 'discover':
                        print("\nDiscovering capabilities...")
                        capabilities = self.capability_discovery.discover_new_capabilities()
                        if capabilities:
                            print(f"✅ Discovered {len(capabilities)} new capabilities:")
                            for cap in capabilities[:5]:
                                print(f"  • {cap}")
                        else:
                            print("No new capabilities discovered")
                    elif low == 'explore':
                        print("\nExploring environment...")
                        result = self.environment_explorer.explore_environment()
                        print(f"Environment: {result.get('summary', 'Unknown')}")
                        if result.get('findings'):
                            print(f"\nFindings:")
                            for finding in result.get('findings', [])[:5]:
                                print(f"  • {finding}")
                    elif low == 'orchestrate':
                        print("\nRunning evolution orchestration...")
                        result = self.pipeline.run_major_evolution()
                        print(f"Status: {result.get('status', 'Unknown')}")
                        if result.get('summary'):
                            print(f"Summary: {result.get('summary')}")
                    elif low == 'prompts' or low == 'prompt list':
                        print("\n=== Available Prompts ===\n")
                        prompts = self.prompt_manager.list_prompts()
                        for category, prompt_list in prompts.items():
                            print(f"{category}:")
                            for prompt in prompt_list:
                                print(f"  • {prompt}")
                            print()
                    elif low == 'goals':
                        self.show_goals()
                    elif low == 'tasks':
                        self.show_autonomous_tasks()
                    elif low == 'hierarchy':
                        self.hierarchy_manager.show_hierarchy()
                    elif low.startswith('config'):
                        parts = cl.split(maxsplit=3)
                        if len(parts) == 1:
                            self._show_all_settings()
                        elif len(parts) >= 2:
                            cmd_type = parts[1].lower()
                            if cmd_type == 'get' and len(parts) >= 3:
                                key = parts[2]
                                self._get_setting(key)
                            elif cmd_type == 'set' and len(parts) >= 4:
                                key = parts[2]
                                value = parts[3]
                                self._set_setting(key, value)
                            else:
                                print("Usage:")
                                print("  config           - Show all settings")
                                print("  config get KEY   - Get a specific setting (e.g., config get llm.default_provider)")
                                print("  config set KEY VALUE - Set a setting (e.g., config set llm.default_provider openai)")
                        else:
                            print("Invalid config command. Use 'help' for details.")
                    else:
                        # Delegate to process_command for other commands
                        resp = self.process_command(command)
                        print(f"\nArbiter: {resp}")
                except Exception as e:
                    print(f"Error: {e}")
                    self.scribe.log_action('System error', f"Error processing command: {str(e)}", 'error')
            except KeyboardInterrupt:
                print('\nShutting down...')
                break
                    
                    
                

    def show_autonomous_tasks(self):
        """Show scheduled autonomous tasks"""
        print("\nScheduled Autonomous Tasks:")
        print("-" * 50)
        
        tasks = self.scheduler.get_task_status()
        if not tasks:
            print("No tasks registered.")
            return
            
        for task in tasks:
            status = "ACTIVE" if task["enabled"] else "PAUSED"
            last_run = task["last_run"] if task["last_run"] else "Never"
            next_run = task["next_run"] if task["next_run"] else "Immediate"
            interval = task.get("interval")
            interval_str = f"{interval} min" if interval else "On demand"
            
            print(f"• {task['name']} [{status}]")
            print(f"  Priority: {task['priority']} | Interval: {interval_str}")
            print(f"  Last run: {last_run}")
            print(f"  Next run: {next_run}")
            print()
        
        # Show next proposed action
        next_action = self.scheduler.propose_next_action()
        print(f"Next proposed action: {next_action}")

    def show_goals(self):
        """Show current goals"""
        print("\nCurrent Goals:")
        print("-" * 50)
        
        goals = self.goals.get_active_goals()
        if not goals:
            print("No active goals. Use 'generate goals' to create some.")
            return
        
        for goal in goals:
            print(f"• Goal #{goal['id']}: {goal['goal_text']}")
            print(f"  Priority: {goal['priority']} | Progress: {goal['progress']}%")
            if goal.get('expected_benefit'):
                print(f"  Benefit: {goal['expected_benefit']}")
            if goal.get('estimated_effort'):
                print(f"  Effort: {goal['estimated_effort']}")
            print()
        
        # Show summary
        summary = self.goals.get_goal_summary()
        print(f"Summary: {summary['active']} active, {summary['completed']} completed, {summary['auto_generated']} auto-generated")

    def show_hierarchy(self):
        """Show hierarchy of needs"""
        print("\nHierarchy of Needs:")
        print("-" * 50)
        
        tiers = self.hierarchy_manager.get_all_tiers()
        for tier in tiers:
            focus_marker = "►" if tier["focus"] == 1 else " "
            print(f"{focus_marker} Tier {tier['tier']}: {tier['name']}")
            print(f"   {tier['description']}")
            print(f"   Progress: {tier['progress'] * 100:.1f}%")
            
            # Show requirements for advancement
            if tier['tier'] < 4:
                reqs = self.hierarchy_manager.get_tier_requirements(tier['tier'])
                if reqs.get('requirements'):
                    print(f"   Requirements: {', '.join(reqs['requirements'])}")
            print()

    def _show_all_settings(self):
        """Display all current runtime settings"""
        from modules.settings import get_config
        from dataclasses import asdict

        config = get_config()
        settings_dict = asdict(config)

        print("\n" + "=" * 70)
        print("CURRENT RUNTIME SETTINGS")
        print("=" * 70)

        def print_dict(d, indent=0, prefix=""):
            """Recursively print dictionary with indentation"""
            for key, value in sorted(d.items()):
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    print(f"{'  ' * indent}[{full_key}]")
                    print_dict(value, indent + 1, full_key)
                else:
                    # Format the value for display
                    if isinstance(value, bool):
                        val_str = "✓ enabled" if value else "✗ disabled"
                    elif isinstance(value, float):
                        val_str = f"{value:.4f}"
                    else:
                        val_str = str(value)
                    print(f"{'  ' * indent}{full_key}: {val_str}")

        print_dict(settings_dict)
        print("=" * 70)

    def _get_setting(self, key: str):
        """Get a specific setting by dot-notation path"""
        from modules.settings import get_config
        from dataclasses import asdict

        config = get_config()
        settings_dict = asdict(config)

        # Navigate the nested dictionary using dot notation
        keys = key.split('.')
        value = settings_dict

        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    print(f"Error: Cannot access '{k}' in non-dictionary value")
                    return

            print(f"\n{key}: {value}")
        except KeyError:
            print(f"Error: Setting not found: {key}")
            print(f"Available settings can be viewed with 'config' command")

    def _set_setting(self, key: str, value_str: str):
        """Set a runtime setting by dot-notation path"""
        from modules.settings import get_config, set_config
        from modules.bus import get_event_bus, Event, EventType
        from dataclasses import asdict

        config = get_config()

        # Parse the value string to appropriate type
        def parse_value(val_str: str, target_type):
            """Convert string to appropriate type"""
            if target_type == bool or target_type.__name__ == 'bool':
                return val_str.lower() in ('true', '1', 'yes', 'enabled')
            elif target_type == int or target_type.__name__ == 'int':
                return int(val_str)
            elif target_type == float or target_type.__name__ == 'float':
                return float(val_str)
            else:
                return val_str

        # Navigate to the setting and update it
        keys = key.split('.')

        try:
            # Navigate through the path
            current = config
            for k in keys[:-1]:
                if hasattr(current, k):
                    current = getattr(current, k)
                else:
                    print(f"Error: Setting not found: {key}")
                    print(f"Available settings can be viewed with 'config' command")
                    return

            # Get the final key
            final_key = keys[-1]
            if not hasattr(current, final_key):
                print(f"Error: Setting not found: {key}")
                print(f"Available settings can be viewed with 'config' command")
                return

            old_value = getattr(current, final_key)

            # Determine the type from the existing value
            target_type = type(old_value)

            # Parse and set the new value
            new_value = parse_value(value_str, target_type)
            setattr(current, final_key, new_value)

            # Update the global config (it's already modified in place)
            set_config(config)

            # Note: Event bus notification would go here if CONFIG_CHANGED event type existed
            # For now, the change is updated in the singleton config


            print(f"\n✓ Setting updated: {key}")
            print(f"  Old value: {old_value} ({type(old_value).__name__})")
            print(f"  New value: {new_value} ({type(new_value).__name__})")
            print(f"\nNote: This change is in-memory only and will be lost on restart.")
            print(f"      To persist changes, modify the .env file.")

        except ValueError as e:
            print(f"Error: Invalid value for setting '{key}': {e}")
            print(f"Please provide a valid {target_type.__name__}")

    def add_evolution_commands(self):
        """Add evolution-related commands to help"""
        help_text = """
Evolution Commands:
------------------
  diagnose           - Run system self-diagnosis
  evolve             - Run evolution pipeline manually
  evolution-status   - Show evolution pipeline status
  evolution-history  - Show evolution history
  test-evolution     - Test evolution system
  repair <module>    - Attempt to repair a module
  optimize           - Run performance optimization
"""
        return help_text
        
    def evolve_command(self):
        """Manual trigger for evolution pipeline"""
        print("\n" + "=" * 60)
        print("MANUAL EVOLUTION TRIGGER")
        print("=" * 60)
        
        # Run diagnosis first
        print("\nRunning system diagnosis...")
        diagnosis = self.diagnosis.perform_full_diagnosis()
        
        print(f"\nDiagnosis Results:")
        print(f"  • Bottlenecks: {len(diagnosis.get('bottlenecks', []))}")
        print(f"  • Improvement Opportunities: {len(diagnosis.get('improvement_opportunities', []))}")
        print(f"  • High Complexity Functions: {len(diagnosis.get('complexities', []))}")
        
        # Show bottlenecks
        if diagnosis.get("bottlenecks"):
            print("\nIdentified Bottlenecks:")
            for bottleneck in diagnosis.get("bottlenecks", [])[:5]:
                print(f"  • {bottleneck}")
                
        # Confirm evolution
        confirm = input("\nProceed with evolution? (y/n): ").lower()
        if confirm != 'y':
            print("Evolution cancelled")
            return
            
        # Run evolution pipeline
        print("\nStarting evolution pipeline...")
        result = self.pipeline.run_autonomous_evolution()
        
        print(f"\nEvolution Result: {result.get('status', 'unknown')}")
        if result.get("tasks_executed"):
            print(f"Tasks Executed: {result.get('tasks_executed')}")
        if result.get("test_results"):
            tests = result.get("test_results", {})
            print(f"Tests Passed: {tests.get('tests_passed', 0)}/{tests.get('tests_run', 0)}")
            
    def repair_module(self, module_name: str):
        """Attempt to repair a module"""
        print(f"\nAttempting to repair module: {module_name}")
        
        # Analyze module
        analysis = self.diagnosis.analyze_own_code(module_name)
        
        if "error" in analysis:
            print(f"Module analysis failed: {analysis['error']}")
            return
            
        print(f"\nModule Analysis:")
        print(f"  • Lines of Code: {analysis.get('lines_of_code', 0)}")
        print(f"  • Functions: {len(analysis.get('functions', []))}")
        print(f"  • Complex Functions: {len(analysis.get('complexities', []))}")
        
        # Get repair suggestions
        prompt = f"""
        Module: {module_name}
        
        Issues found:
        {chr(10).join(f'- {c}' for c in analysis.get('complexities', []))}
        
        Provide specific repair suggestions for this module.
        Focus on fixing critical issues first.
        
        Format:
        ISSUE: [description]
        FIX: [specific code change]
        """
        
        model_name, model_info = self.router.route_request("coding", "high")
        suggestions = self.router.call_model(
            model_name,
            prompt,
            system_prompt="You are a code repair expert. Provide specific, actionable fixes."
        )
        
        print(f"\nRepair Suggestions:")
        print(suggestions)
        
        # Ask if we should apply fixes
        apply = input("\nApply these fixes? (y/n): ").lower()
        if apply == 'y':
            # Apply fixes
            changes = {
                "type": "repair",
                "module": module_name,
                "suggestions": suggestions,
                "description": f"Repair {module_name} based on analysis"
            }
            
            success = self.modification.modify_module(module_name, changes)
            if success:
                print(f"✓ Module {module_name} repaired successfully")
            else:
                print(f"✗ Failed to repair {module_name}")

    def show_prompts(self):
        """List all available prompts"""
        pm = getattr(self, 'prompt_manager', None)
        if pm is None:
            print("PromptManager not available. Ensure system is initialized via SystemBuilder so PromptManager is provided by the DI container.")
            return

        prompts = pm.list_prompts()
        print(f"\n=== Available Prompts ({len(prompts)}) ===")
        for prompt in prompts:
            print(f"  • {prompt['name']} [{prompt['category']}]")
            print(f"    {prompt['description'][:60]}..." if len(prompt.get('description', '')) > 60 else f"    {prompt.get('description', 'No description')}")
            print(f"    Version: {prompt.get('version', '1.0')}")
            print()

    def show_prompts_by_category(self):
        """List prompts grouped by category"""
        pm = getattr(self, 'prompt_manager', None)
        if pm is None:
            print("PromptManager not available. Ensure system is initialized via SystemBuilder so PromptManager is provided by the DI container.")
            return

        categories = pm.list_categories()
        print(f"\n=== Prompts by Category ===")
        for category in categories:
            prompts = pm.list_prompts(category=category)
            print(f"\n[{category.upper()}] ({len(prompts)} prompts)")
            for p in prompts:
                print(f"  • {p['name']}: {p['description'][:40]}..." if len(p.get('description', '')) > 40 else f"  • {p['name']}: {p.get('description', 'No description')}")

    def show_prompt_detail(self, prompt_name: str):
        """Show detailed information about a prompt"""
        pm = getattr(self, 'prompt_manager', None)
        if pm is None:
            print("PromptManager not available. Ensure system is initialized via SystemBuilder so PromptManager is provided by the DI container.")
            return

        try:
            prompt_data = pm.get_prompt_raw(prompt_name)

            print(f"\n=== Prompt: {prompt_name} ===")
            print(f"Description: {prompt_data.get('description', 'N/A')}")
            print(f"Category: {prompt_data.get('category', 'N/A')}")
            print(f"Version: {prompt_data.get('metadata', {}).get('version', 'N/A')}")
            print(f"Created: {prompt_data.get('metadata', {}).get('created_at', 'N/A')}")
            print(f"Last Updated: {prompt_data.get('metadata', {}).get('last_updated', 'N/A')}")
            print(f"\nTemplate:")
            print("-" * 50)
            print(prompt_data.get('template', 'N/A'))
            print("-" * 50)
            print(f"\nSystem Prompt: {prompt_data.get('system_prompt', 'N/A')}")
            print(f"\nParameters:")
            for param in prompt_data.get('parameters', []):
                required = "required" if param.get('required', False) else "optional"
                print(f"  • {param['name']} ({param.get('type', 'string')}) - {required}")
        except ValueError as e:
            print(f"Prompt not found: {prompt_name}")
            try:
                available = ', '.join(p['name'] for p in pm.list_prompts())
                print(f"Available prompts: {available}")
            except Exception:
                pass
        except Exception as e:
            print(f"Error: {e}")

    def update_prompt(self, prompt_name: str):
        """Update a prompt interactively"""
        pm = getattr(self, 'prompt_manager', None)
        if pm is None:
            print("PromptManager not available. Ensure system is initialized via SystemBuilder so PromptManager is provided by the DI container.")
            return

        try:
            prompt_data = pm.get_prompt_raw(prompt_name)
            
            print(f"\n=== Update Prompt: {prompt_name} ===")
            print("Current template:")
            print(prompt_data.get('template', ''))
            print("\n" + "=" * 50)
            print("Enter new template (Ctrl-D to save, Ctrl-C to cancel):")
            
            try:
                new_template = sys.stdin.read().strip()
                if new_template:
                    pm.update_prompt(prompt_name, {"template": new_template})
                    print(f"\n✓ Prompt '{prompt_name}' updated successfully")
                else:
                    print("No changes made.")
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
        except ValueError as e:
            print(f"Error: {e}")

    def optimize_prompt(self, prompt_name: str):
        """Optimize a prompt using AI"""
        print(f"\n=== Optimizing Prompt: {prompt_name} ===")
        
        try:
            pm = getattr(self, 'prompt_manager', None)
            if pm is None:
                print("PromptManager not available. Ensure system is initialized via SystemBuilder so PromptManager is provided by the DI container.")
                return
            
            # Get performance metrics (simplified)
            performance_metrics = {
                "issues": ["Could be more specific", "Add examples"],
                "success_criteria": "Clear, actionable output"
            }
            
            # Initialize optimizer
            optimizer = PromptOptimizer(pm, self.router, self.scribe)
            
            # Create optimized version
            test_name = optimizer.optimize_prompt(prompt_name, performance_metrics)
            
            print(f"\n✓ Created optimized test version: {test_name}")
            
            # Show comparison
            original = pm.get_prompt_raw(prompt_name)
            test = pm.get_prompt_raw(test_name)
            
            print(f"\nOriginal:")
            print(f"  {original.get('template', '')[:100]}...")
            print(f"\nOptimized:")
            print(f"  {test.get('template', '')[:100]}...")
            
            # Ask to apply
            apply = input("\nApply this optimization? (y/n): ").lower()
            if apply == 'y':
                pm.update_prompt(prompt_name, {"template": test.get("template", "")})
                pm.delete_prompt(test_name)  # Clean up test version
                print(f"\n✓ Prompt '{prompt_name}' updated with optimized version")
            else:
                print("Optimization not applied. Test version preserved for later comparison.")
                
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Optimization failed: {e}")

if __name__ == "__main__":
    # Parse CLI args for modes and batch commands
    parser = argparse.ArgumentParser(description='AAIA entrypoint')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode (type commands)')
    parser.add_argument('--autonomous', '-a', action='store_true', help='Run in autonomous mode (start scheduler)')
    parser.add_argument('--cmd', '-c', action='append', help='Command to execute (can be repeated)')
    parser.add_argument('--cmd-file', help='File with commands, one per line')
    parser.add_argument('--autoexit', '-e', action='store_true', help='Exit after executing provided commands')
    parser.add_argument('--timeout', '-t', type=float, default=0.0, help='Per-command timeout in seconds (0 = disabled)')
    args = parser.parse_args()

    # Mode selection: interactive, autonomous, or batch (--cmd/--cmd-file)
    selected_mode = None
    if args.interactive:
        selected_mode = 'interactive'
    if args.autonomous:
        if selected_mode:
            print('Cannot combine --interactive and --autonomous')
            parser.print_help()
            raise SystemExit(2)
        selected_mode = 'autonomous'
    if args.cmd or args.cmd_file:
        if selected_mode:
            print('Cannot combine mode flags with --cmd/--cmd-file')
            parser.print_help()
            raise SystemExit(2)
        selected_mode = 'batch'

    if not selected_mode:
        # No mode provided - show help and exit
        parser.print_help()
        raise SystemExit(0)

    # Prepare commands for batch mode
    commands = []
    if args.cmd:
        commands.extend(args.cmd)
    if args.cmd_file:
        try:
            with open(args.cmd_file, 'r') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith('#'):
                        continue
                    commands.append(ln)
        except Exception as e:
            print(f"Failed to read cmd-file {args.cmd_file}: {e}")
            raise

    arbiter = Arbiter()

    if selected_mode == 'interactive':
        arbiter.run(commands=None, autoexit=False, timeout=None)
    elif selected_mode == 'autonomous':
        # Start autonomous scheduler and run until interrupted or optional timeout
        def _run_autonomous():
            try:
                if not arbiter.scheduler.running:
                    arbiter.scheduler.start()
                    print('Autonomous scheduler started')
                # Wait until interrupted
                if args.timeout and args.timeout > 0:
                    try:
                        time.sleep(args.timeout)
                    except KeyboardInterrupt:
                        pass
                    print('Autonomous timeout reached, stopping')
                else:
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        pass
            finally:
                try:
                    if arbiter.scheduler.running:
                        arbiter.scheduler.stop()
                        print('Autonomous scheduler stopped')
                except Exception:
                    pass

        _run_autonomous()
    else:  # batch
        arbiter.run(commands=commands or None, autoexit=args.autoexit, timeout=(args.timeout if args.timeout > 0 else None))
