# main.py
import sys
from pathlib import Path

# Add the packages directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import time
import sqlite3
from datetime import datetime
from typing import Optional

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

class Arbiter:
    def __init__(self):
        """
        Initialize the Arbiter and all modules.
        
        Args:
            use_container: If True, use dependency injection container
        """
        data_dir = Path.home() / ".local/share/aaia"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = get_config()
        self.config.database.path = str(data_dir / "scribe.db")
        
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
        
        # Publish ready event
        self.event_bus.publish(Event(
            type=EventType.SYSTEM_STARTUP,
            data={'message': 'Arbiter ready'},
            source='Arbiter'
        ))
        
    def _init_container(self):
        """Initialize using dependency injection container."""
        container = get_container()
        
        # Register services
        from modules.setup import SystemBuilder
        builder = SystemBuilder(self.config)
        
        # Build and get modules
        system = builder.build()
        modules = system['modules']
        
        # Assign to self
        self.scribe = modules.get('Scribe')
        self.economics = modules.get('EconomicManager')
        self.mandates = modules.get('MandateEnforcer')
        self.router = modules.get('ModelRouter')
        self.dialogue = modules.get('DialogueManager')
        self.forge = modules.get('Forge')
        self.scheduler = modules.get('AutonomousScheduler')
        self.goals = modules.get('GoalSystem')
        self.hierarchy_manager = modules.get('HierarchyManager')
        self.diagnosis = modules.get('SelfDiagnosis')
        self.modification = modules.get('SelfModification')
        self.evolution = modules.get('EvolutionManager')
        self.pipeline = modules.get('EvolutionPipeline')
        self.metacognition = modules.get('MetaCognition')
        self.capability_discovery = modules.get('CapabilityDiscovery')
        self.intent_predictor = modules.get('IntentPredictor')
        self.environment_explorer = modules.get('EnvironmentExplorer')
        self.strategy_optimizer = modules.get('StrategyOptimizer')
        self.orchestrator = modules.get('EvolutionOrchestrator')
        
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
        
    def process_command(self, command: str, urgent: bool = False) -> str:
        """Main command processing loop"""
        
        # Urgency check
        if urgent:
            self.scribe.log_action(
                "Urgent command processing",
                "Command marked as urgent, proceeding with risk analysis logged",
                "proceeding"
            )
            
        # Mandate check
        is_allowed, violations = self.mandates.check_action(command)
        
        if not is_allowed:
            return f"Command violates mandates: {', '.join(violations)}"
            
        # For non-urgent significant commands, run analysis
        if not urgent and self.is_significant_command(command):
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
            # Execute directly for trivial commands
            return self.execute_command(command)
            
    def is_significant_command(self, command: str) -> bool:
        """Determine if command requires full analysis"""
        trivial_keywords = ["status", "help", "list", "show", "tell"]
        significant_keywords = ["create", "delete", "modify", "install", "change"]
        
        if any(word in command.lower() for word in trivial_keywords):
            return False
        if any(word in command.lower() for word in significant_keywords):
            return True
            
        return len(command.split()) > 10  # Long commands get analysis
        
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
        
    def run(self):
        """Main loop"""
        print("=" * 60)
        print("AAIA (Autonomous AI Agent) System Initialized")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Directives: {len(self.mandates.mandates)} Prime Mandates Active")
        print("=" * 60)
        print("Type 'exit' to quit, 'help' for commands")
        
        while True:
            try:
                command = input("\nMaster: ").strip()
                
                if command.lower() == "exit":
                    print("Shutting down...")
                    break
                elif command.lower() == "help":
                    print("Available commands:")
                    print("  help - Show this help")
                    print("  status - Show system status")
                    print("  economics - Show economic status")
                    print("  log - Show recent actions")
                    print("  tools - List all created tools")
                    print("  create tool <name> | <description> - Create tool (AI generates code)")
                    print("  delete tool <name> - Delete a tool")
                    print("-" * 40)
                    print("Autonomous Control:")
                    print("  auto / autonomous - Toggle autonomous mode")
                    print("  tasks / scheduler - Show autonomous tasks")
                    print("  goals - Show current goals")
                    print("  generate goals - Generate new goals")
                    print("  hierarchy - Show hierarchy of needs")
                    print("  next action - Propose next autonomous action")
                    print("-" * 40)
                    print("Self-Development:")
                    print("  diagnose - Run system self-diagnosis")
                    print("  evolve - Run full evolution pipeline")
                    print("  evolution status - Show evolution status")
                    print("  analyze <module> - Analyze a module for improvements")
                    print("  repair <module> - Attempt to repair a module")
                    print("  pipeline - Run complete evolution pipeline")
                    print("-" * 40)
                    print("Advanced Self-Development:")
                    print("  reflect - Run meta-cognition reflection")
                    print("  discover - Discover new capabilities")
                    print("  predict - Predict master's next commands")
                    print("  explore - Explore environment")
                    print("  orchestrate - Run major evolution orchestration")
                    print("  strategy - Optimize evolution strategy")
                    print("  master profile - Show master behavior model")
                    print("  [any other command] - Process command")
                    continue
                elif command.lower() == "status":
                    # Show system status
                    conn = sqlite3.connect(self.scribe.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM action_log")
                    action_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
                    balance_row = cursor.fetchone()
                    balance = balance_row[0] if balance_row else "100.00"
                    
                    conn.close()
                    
                    # Get hierarchy info
                    current_tier = self.hierarchy_manager.get_current_tier()
                    
                    print(f"\n=== System Status ===")
                    print(f"Actions logged: {action_count}")
                    print(f"Current balance: ${balance}")
                    print(f"Focus tier: {current_tier['name']} (Tier {current_tier['tier']})")
                    print(f"Tier progress: {current_tier['progress'] * 100:.1f}%")
                    print()
                    print(f"=== Autonomy ===")
                    print(f"Autonomous mode: {'ENABLED' if self.scheduler.running else 'DISABLED'}")
                    print(f"Active tasks: {len([t for t in self.scheduler.task_queue if t.get('enabled', True)])}")
                    print(f"Tools created: {len(self.forge.list_tools())}")
                    
                    # Show next proposed action
                    next_action = self.scheduler.propose_next_action()
                    print(f"Next proposed action: {next_action}")
                    
                    # Show evolution status
                    evolution_status = self.evolution.get_evolution_status()
                    print(f"\n=== Evolution ===")
                    print(f"Status: {evolution_status['state']}")
                    print(f"Last cycle: {evolution_status['last_cycle']}")
                    print(f"Progress: {evolution_status['progress']}")
                    continue
                elif command.lower() == "economics":
                    # Show economic status
                    conn = sqlite3.connect(self.scribe.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT description, amount, balance_after FROM economic_log ORDER BY timestamp DESC LIMIT 10")
                    transactions = cursor.fetchall()
                    
                    print("Recent transactions:")
                    for desc, amount, balance in transactions:
                        print(f"  {desc}: ${amount:.6f} (Balance: ${balance:.2f})")
                    continue
                elif command.lower() == "log":
                    # Show recent actions
                    conn = sqlite3.connect(self.scribe.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT action, reasoning, outcome FROM action_log ORDER BY timestamp DESC LIMIT 5")
                    actions = cursor.fetchall()
                    
                    print("Recent actions:")
                    for action, reasoning, outcome in actions:
                        print(f"  Action: {action[:50]}...")
                        print(f"  Reasoning: {reasoning[:50]}...")
                        print(f"  Outcome: {outcome}")
                        print()
                    continue
                elif command.lower() == "tools":
                    # List all available tools
                    tools = self.forge.list_tools()
                    if not tools:
                        print("No tools created yet. Use 'create tool <name> | <description>' to create one.")
                    else:
                        print(f"Registered tools ({len(tools)}):")
                        for tool in tools:
                            print(f"  - {tool['name']}: {tool['description']}")
                    continue
                elif command.lower().startswith("create tool "):
                    # Create a new tool (AI generates code if not provided)
                    parts = command[11:].split("|")
                    if len(parts) < 2:
                        print("Usage: create tool <name> | <description> [| <code>]")
                        print("Example: create tool my_tool | This does something useful")
                        print("Note: If no code is provided, the AI will generate it automatically.")
                        continue
                    tool_name = parts[0].strip()
                    tool_desc = parts[1].strip()
                    
                    # Get code if provided (optional)
                    tool_code = None
                    if len(parts) > 2 and parts[2].strip():
                        tool_code = parts[2].strip()
                    
                    print(f"Creating tool '{tool_name}'...", flush=True)
                    if tool_code is None:
                        print("  Using AI to generate code from description...")
                    
                    try:
                        metadata = self.forge.create_tool(tool_name, tool_desc, tool_code)
                        print(f"Tool created successfully: {metadata['name']}")
                    except Exception as e:
                        print(f"Failed to create tool: {e}")
                    continue
                elif command.lower().startswith("delete tool "):
                    # Delete a tool
                    tool_name = command[12:].strip()
                    if self.forge.delete_tool(tool_name):
                        print(f"Tool deleted: {tool_name}")
                    else:
                        print(f"Tool not found: {tool_name}")
                    continue
                elif command.lower() in ["auto", "autonomous", "autonomy"]:
                    # Toggle autonomous mode
                    if self.scheduler.running:
                        self.scheduler.stop()
                        print("Autonomous mode DISABLED")
                    else:
                        self.scheduler.start()
                        print("Autonomous mode ENABLED")
                    continue
                elif command.lower() in ["tasks", "scheduler"]:
                    # Show autonomous tasks
                    self.show_autonomous_tasks()
                    continue
                elif command.lower() == "goals":
                    # Show current goals
                    self.show_goals()
                    continue
                elif command.lower() == "generate goals":
                    # Generate new goals
                    print("Generating autonomous goals...")
                    goals = self.goals.generate_goals()
                    for goal in goals:
                        print(goal)
                    print(f"Generated {len(goals)} goals")
                    continue
                elif command.lower() == "hierarchy":
                    # Show hierarchy of needs
                    self.show_hierarchy()
                    continue
                elif command.lower() == "next action":
                    # Propose next autonomous action
                    action = self.scheduler.propose_next_action()
                    print(f"Proposed next action: {action}")
                    continue
                elif command.lower() == "diagnose":
                    # Run self-diagnosis
                    print("Running system self-diagnosis...")
                    diagnosis = self.diagnosis.perform_full_diagnosis()
                    print(self.diagnosis.get_diagnosis_summary())
                    continue
                elif command.lower() == "evolve":
                    # Plan and execute evolution cycle
                    print("Planning evolution cycle...")
                    plan = self.evolution.plan_evolution_cycle()
                    print(f"\n=== Evolution Plan ({plan['cycle_id']}) ===")
                    print(f"Focus Tier: {plan['focus_tier_name']} (Tier {plan['focus_tier']})")
                    print(f"\nGoals:")
                    for goal in plan['goals']:
                        print(f"  • {goal}")
                    print(f"\nTasks ({len(plan['tasks'])}):")
                    for i, task in enumerate(plan['tasks'][:5], 1):
                        print(f"  {i}. {task.get('task', 'Unnamed')} [{task.get('priority', 'medium')}]")
                    if len(plan['tasks']) > 5:
                        print(f"  ... and {len(plan['tasks']) - 5} more")
                    
                    # Ask to execute
                    execute = input("\nExecute evolution tasks? (y/n): ").lower()
                    if execute == 'y':
                        print("\nExecuting tasks...")
                        for i, task in enumerate(plan['tasks'][:3]):
                            print(f"  • {task.get('task', 'Unnamed')}...")
                            result = self.evolution.execute_evolution_task(task)
                            if result['success']:
                                print(f"    ✓ {result['output'][:60]}...")
                            else:
                                print(f"    ✗ {result.get('errors', ['Unknown'])[0]}")
                        print("\nEvolution cycle complete!")
                    continue
                elif command.lower() == "evolution status":
                    # Show evolution status
                    status = self.evolution.get_evolution_status()
                    print("\n=== Evolution Status ===")
                    print(f"State: {status['state']}")
                    print(f"Last Cycle: {status['last_cycle']}")
                    print(f"Focus Tier: {status['focus_tier']}")
                    print(f"Goals: {status['goals']}")
                    print(f"Tasks: {status['tasks']}")
                    print(f"Completed: {status['completed_tasks']}")
                    print(f"Progress: {status['progress']}")
                    continue
                elif command.lower().startswith("analyze "):
                    # Analyze a specific module
                    module_name = command[8:].strip()
                    if not module_name:
                        print("Usage: analyze <module_name>")
                        print("Example: analyze router")
                        continue
                    print(f"Analyzing module: {module_name}...")
                    analysis = self.diagnosis.analyze_own_code(module_name)
                    
                    if "error" in analysis:
                        print(f"Error analyzing module: {analysis['error']}")
                    else:
                        print(f"\n=== Module Analysis: {module_name} ===")
                        print(f"Lines of code: {analysis['lines_of_code']}")
                        print(f"Functions: {len(analysis['functions'])}")
                        if analysis.get('complexities'):
                            print(f"\nHigh complexity functions:")
                            for c in analysis['complexities']:
                                print(f"  • {c['function']}: {c['score']} ({c['suggestion']})")
                        if analysis.get('improvements'):
                            print(f"\nAI Suggestions:")
                            for imp in analysis['improvements'][:5]:
                                print(f"  {imp}")
                    continue
                elif command.lower() == "pipeline":
                    # Run complete evolution pipeline
                    print("Running complete evolution pipeline...")
                    result = self.pipeline.run_autonomous_evolution()
                    print(f"\nPipeline Result: {result.get('status', 'unknown')}")
                    if result.get('tasks_executed'):
                        print(f"Tasks executed: {result.get('tasks_executed')}")
                    if result.get('test_results'):
                        tests = result.get('test_results')
                        print(f"Tests: {tests.get('tests_passed', 0)}/{tests.get('tests_run', 0)} passed")
                    continue
                elif command.lower().startswith("repair "):
                    # Repair a module
                    module_name = command[7:].strip()
                    if not module_name:
                        print("Usage: repair <module_name>")
                        print("Example: repair router")
                        continue
                    self.repair_module(module_name)
                    continue
                elif command.lower() == "reflect":
                    # Run meta-cognition reflection
                    print("Running meta-cognition reflection...")
                    reflection = self.metacognition.reflect_on_effectiveness()
                    print("\n=== Meta-Cognition Reflection ===")
                    print(f"Timestamp: {reflection.get('timestamp', 'N/A')}")
                    print("\nImprovements:")
                    for imp in reflection.get('improvements', []):
                        print(f"  ✓ {imp}")
                    print("\nRegressions:")
                    for reg in reflection.get('regressions', []):
                        print(f"  ! {reg}")
                    print("\nInsights:")
                    for insight in reflection.get('insights', []):
                        print(f"  • {insight}")
                    print(f"\nEffectiveness Score: {self.metacognition.get_effectiveness_score()}")
                    continue
                elif command.lower() == "discover":
                    # Discover new capabilities
                    print("Discovering new capabilities...")
                    capabilities = self.capability_discovery.discover_new_capabilities()
                    print(f"\n=== Discovered Capabilities ({len(capabilities)}) ===")
                    for cap in capabilities[:5]:
                        if isinstance(cap, dict) and 'name' in cap:
                            print(f"\n• {cap.get('name', 'Unknown')}")
                            print(f"  Description: {cap.get('description', 'N/A')}")
                            print(f"  Value: {cap.get('value', 'N/A')}/10 | Complexity: {cap.get('complexity', 'N/A')}/10")
                            print(f"  Dependencies: {', '.join(cap.get('dependencies', [])) or 'None'}")
                    continue
                elif command.lower() == "predict":
                    # Predict master's next commands
                    print("Predicting master's next commands...")
                    predictions = self.intent_predictor.predict_next_commands()
                    print("\n=== Command Predictions ===")
                    for i, pred in enumerate(predictions[:3], 1):
                        if isinstance(pred, dict):
                            print(f"\n{i}. {pred.get('command', 'Unknown')}")
                            print(f"   Confidence: {pred.get('confidence', 0):.2f}")
                            print(f"   Rationale: {pred.get('rationale', 'N/A')}")
                    continue
                elif command.lower() == "explore":
                    # Explore environment
                    print("Exploring environment...")
                    exploration = self.environment_explorer.explore_environment()
                    print("\n=== Environment Exploration ===")
                    print(f"Platform: {exploration.get('system_info', {}).get('platform', 'Unknown')}")
                    print(f"Containerized: {exploration.get('system_info', {}).get('containerized', False)}")
                    print(f"Available Commands: {len(exploration.get('available_commands', []))}")
                    resources = exploration.get('resource_availability', {})
                    print(f"Memory Available: {resources.get('memory_available_gb', 'N/A')} GB")
                    print(f"Disk Free: {resources.get('disk_free_gb', 'N/A')} GB")
                    print(f"Network: {'Available' if exploration.get('network_capabilities', {}).get('external_http') else 'Limited'}")
                    
                    # Show opportunities
                    opportunities = self.environment_explorer.find_development_opportunities()
                    if opportunities:
                        print("\n=== Development Opportunities ===")
                        for opp in opportunities[:3]:
                            print(f"• {opp.get('type', 'Unknown')}: {opp.get('value', '')}")
                    continue
                elif command.lower() == "orchestrate":
                    # Run major evolution orchestration
                    print("Running major evolution orchestration...")
                    result = self.orchestrator.orchestrate_major_evolution()
                    print(f"\n=== Evolution Complete ===")
                    print(f"Overall Status: {result.get('overall_status', 'unknown')}")
                    print(f"Phases Completed: {len(result.get('phases', {}))}")
                    continue
                elif command.lower() == "strategy":
                    # Optimize evolution strategy
                    print("Optimizing evolution strategy...")
                    optimization = self.strategy_optimizer.optimize_evolution_strategy()
                    print("\n=== Strategy Optimization ===")
                    print("Adopt:")
                    for item in optimization.get('adopt', [])[:3]:
                        print(f"  ✓ {item.get('element', 'N/A')}: {item.get('value', 'N/A')}")
                    print("Avoid:")
                    for item in optimization.get('avoid', [])[:3]:
                        print(f"  ✗ {item.get('element', 'N/A')}")
                    print("\nExperiment with:")
                    for exp in optimization.get('experiment_with', [])[:3]:
                        print(f"  • {exp}")
                    print(f"\nRecommended: {optimization.get('recommended_approach', 'N/A')}")
                    continue
                elif command.lower() == "master profile":
                    # Show master behavior model
                    profile = self.intent_predictor.get_master_profile()
                    print("\n=== Master Behavior Profile ===")
                    print(f"Total Interactions: {profile.get('total_interactions', 0)}")
                    print(f"Model Confidence: {profile.get('model_confidence', 0):.2f}")
                    print("\nTraits:")
                    for trait, data in profile.get('traits', {}).items():
                        print(f"  • {trait}: {data.get('value', 'unknown')} (confidence: {data.get('confidence', 0):.2f})")
                    continue
                    
                # Process regular command
                response = self.process_command(command)
                print(f"\nArbiter: {response}")
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
                self.scribe.log_action(
                    "System error",
                    f"Error processing command: {str(e)}",
                    "error"
                )

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

if __name__ == "__main__":
    arbiter = Arbiter()
    arbiter.run()