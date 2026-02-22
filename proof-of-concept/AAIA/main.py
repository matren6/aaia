# main.py
import sys
import time
import sqlite3
from modules import *
from modules.forge import Forge, TOOL_TEMPLATES
from typing import Optional

class Arbiter:
    def __init__(self):
        self.scribe = Scribe()
        self.economics = EconomicManager(self.scribe)
        self.mandates = MandateEnforcer(self.scribe)
        self.router = ModelRouter(self.economics)
        self.dialogue = DialogueManager(self.scribe, self.router)
        self.forge = Forge(self.router, self.scribe)
        
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
        print("Autonomous Agent System Initialized")
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
                    
                    print(f"Actions logged: {action_count}")
                    print(f"Current balance: ${balance}")
                    print(f"Focus tier: Physiological & Security Needs")
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

if __name__ == "__main__":
    arbiter = Arbiter()
    arbiter.run()