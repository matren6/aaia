# modules/dialogue.py
"""
Dialogue Manager Module - Structured Communication Protocol

PURPOSE:
The Dialogue Manager implements a structured argument protocol for processing
and analyzing the master's commands. It provides critical thinking capabilities
that help identify risks, alternative approaches, and potential issues with
requested actions.

PROBLEM SOLVED:
When receiving a command, the AI shouldn't just execute it blindly. The Dialogue
Manager adds a layer of analysis that:
1. Ensures understanding of the master's true intent
2. Identifies potential risks or flaws in the command
3. Suggests alternative (potentially better) approaches
4. Creates a record of the reasoning process
5. Provides transparency into AI decision-making

Without this, the AI would be a simple command executor rather than a
thoughtful partner.

KEY RESPONSIBILITIES:
1. Implement structured argument protocol
2. Analyze commands for understanding, risks, alternatives
3. Use AI to perform critical analysis of commands
4. Log dialogue phases and reasoning
5. Parse structured responses into components
6. Provide feedback on command analysis

DIALOGUE PHASES:
- Understanding: What is the master trying to achieve?
- Risk Analysis: What could go wrong?
- Alternative Approaches: Is there a better way?
- Recommendation: What should be done?

DEPENDENCIES: Scribe, Router
OUTPUTS: Tuple of (understanding, risks, alternatives)
"""

from typing import Optional, Tuple, List
from .scribe import Scribe
from .router import ModelRouter
from modules.container import DependencyError

class DialogueManager:
    def __init__(self, scribe: Scribe, router: ModelRouter, prompt_manager=None):
        self.scribe = scribe
        self.router = router
        # PromptManager should be provided via DI (mandatory)
        self.prompt_manager = prompt_manager
        if self.prompt_manager is None:
            raise DependencyError("PromptManager is required and must be provided via the DI container to DialogueManager")

        # Ensure required prompt template is registered
        try:
            self.prompt_manager.get_prompt_raw("command_understanding")
        except Exception:
            raise DependencyError("Required prompt 'command_understanding' not registered in PromptManager")
        
    def structured_argument(self, master_command: str, context: str = "") -> Tuple[str, List[str], List[str]]:
        """Implement structured argument protocol
        
        Returns:
            Tuple of (understanding: str, risks: List[str], alternatives: List[str])
        """
        
        # Log understanding phase
        self.scribe.log_action(
            action=f"Analyzing command: {master_command[:50]}...",
            reasoning="Beginning structured argument protocol",
            outcome="pending"
        )
        
        # Use centralized PromptManager prompt only
        prompt_data = self.prompt_manager.get_prompt(
            "command_understanding",
            command=master_command,
            context=context
        )
        model_name, _ = self.router.route_request("reasoning", "high")
        response = self.router.call_model(
            model_name,
            prompt_data["prompt"],
            prompt_data.get("system_prompt", "")
        )

        # Parse response
        understanding = ""
        risks = []
        alternatives = []
        
        # Simple parsing (can be enhanced)
        lines = response.split('\n') if response else []
        current_section = None
        
        for line in lines:
            if line.startswith("UNDERSTANDING:"):
                current_section = "understanding"
                understanding = line.replace("UNDERSTANDING:", "").strip()
            elif line.startswith("RISKS:"):
                current_section = "risks"
            elif line.startswith("ALTERNATIVES:"):
                current_section = "alternatives"
            elif current_section == "risks" and line.strip():
                risks.append(line.strip())
            elif current_section == "alternatives" and line.strip():
                alternatives.append(line.strip())
                
        # Log for reflection
        self.scribe.log_action(
            action="Structured argument analysis",
            reasoning=f"Command: {master_command}",
            outcome=f"Found {len(risks)} risks and {len(alternatives)} alternatives"
        )
        
        return understanding, risks, alternatives