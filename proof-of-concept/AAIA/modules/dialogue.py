# dialogue.py
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

from typing import Optional
from .scribe import Scribe
from .router import ModelRouter

class DialogueManager:
    def __init__(self, scribe: Scribe, router: ModelRouter):
        self.scribe = scribe
        self.router = router
        
    def structured_argument(self, master_command: str, context: str = "") -> str:
        """Implement structured argument protocol"""
        
        # Log understanding phase
        self.scribe.log_action(
            action=f"Analyzing command: {master_command[:50]}...",
            reasoning="Beginning structured argument protocol",
            outcome="pending"
        )
        
        # Use model to analyze command
        model_name, model_info = self.router.route_request("reasoning", "high")
        
        analysis_prompt = f"""
        As an AI partner analyzing a master's command, perform this analysis:
        
        Master's Command: {master_command}
        Context: {context}
        
        1. Understanding: What is the master's likely goal?
        2. Risk/Flaw Analysis: What potential issues exist?
        3. Alternative Approaches: What better methods might achieve the goal?
        
        Format your response as:
        UNDERSTANDING: [your analysis]
        RISKS: [list of risks]
        ALTERNATIVES: [list of alternatives]
        """
        
        response = self.router.call_model(
            model_name,
            analysis_prompt,
            system_prompt="You are a critical thinking partner analyzing commands for risks and better approaches."
        )
        
        # Parse response
        understanding = ""
        risks = []
        alternatives = []
        
        # Simple parsing (can be enhanced)
        lines = response.split('\n')
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