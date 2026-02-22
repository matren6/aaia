# main.py
import sys
import time
import sqlite3
from datetime import datetime
from modules import *
from modules.forge import Forge, TOOL_TEMPLATES
from modules.scheduler import AutonomousScheduler
from modules.goals import GoalSystem
from modules.hierarchy_manager import HierarchyManager
from typing import Optional

class Arbiter:
    def __init__(self):
        self.scribe = Scribe()
        self.economics = EconomicManager(self.scribe)
        self.mandates = MandateEnforcer(self.scribe)
        self.router = ModelRouter(self.economics)
        self.dialogue = DialogueManager(self.scribe, self.router)
        self.forge = Forge(self.router, self.scribe)
        
        # Autonomous modules
        self.scheduler = AutonomousScheduler(
            self.scribe, self.router, self.economics, self.forge
        )
        self.goals = GoalSystem(self.scribe, self.router, self.economics)
        self.hierarchy_manager = HierarchyManager(self.scribe, self.economics)
        
        # Initialize hierarchy
        self.init_hierarchy()
        
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


if __name__ == "__main__":
    arbiter = Arbiter()
    arbiter.run()