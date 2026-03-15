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

from typing import Optional, Tuple, List, Dict, Any
import json
from .scribe import Scribe
from .router import ModelRouter
from modules.container import DependencyError

class DialogueManager:
    def __init__(self, scribe: Scribe, router: ModelRouter, prompt_manager=None, event_bus=None):
        self.scribe = scribe
        self.router = router
        self.event_bus = event_bus
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

    def check_urgency(self, command: str, context: Dict[str, Any] = None) -> Tuple[str, str, bool]:
        """
        Determine urgency level of command.

        Args:
            command: Command/request to analyze
            context: Optional context about the request

        Returns:
            Tuple of (urgency_level: str, reasoning: str, skip_dialogue: bool)
        """
        urgency_level = 'medium'
        reasoning = 'Default urgency assessment'
        skip_dialogue = False

        try:
            if self.prompt_manager and self.router:
                prompt_data = self.prompt_manager.get_prompt(
                    'dialogue',
                    'check_urgency',
                    variables={
                        'command': command,
                        'context': json.dumps(context or {})
                    }
                )

                analysis = self.router.call_model(
                    prompt_data.get('model', 'llama3.2:3b'),
                    prompt_data['prompt']
                )

                try:
                    result = json.loads(analysis)
                    urgency_level = result.get('urgency_level', 'medium')
                    reasoning = result.get('reasoning', '')
                    skip_dialogue = result.get('skip_dialogue', False)
                except json.JSONDecodeError:
                    # Fallback to keyword detection
                    urgency_level, skip_dialogue = self._detect_urgency_keywords(command)
            else:
                # Fallback without AI
                urgency_level, skip_dialogue = self._detect_urgency_keywords(command)

        except Exception as e:
            self.scribe.log_action(
                "Urgency check failed",
                reasoning=str(e),
                outcome="Using default urgency"
            )

        # Log urgency assessment
        self.scribe.log_action(
            f"Urgency assessed: {urgency_level}",
            reasoning=f"Command: {command[:50]}",
            outcome=f"Skip dialogue: {skip_dialogue}"
        )

        # Emit event if critical and skipping dialogue
        if skip_dialogue and self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.DIALOGUE_SKIPPED, {
                    'urgency': urgency_level,
                    'command': command
                }))
            except:
                pass

        return urgency_level, reasoning, skip_dialogue

    def _detect_urgency_keywords(self, command: str) -> Tuple[str, bool]:
        """
        Simple keyword-based urgency detection.

        Args:
            command: Command to analyze

        Returns:
            Tuple of (urgency_level, skip_dialogue)
        """
        lower_cmd = command.lower()

        # Critical urgency indicators
        critical_keywords = ['fire', 'burning', 'down', 'failing', 'critical', 'emergency', 
                            'now', 'immediately', 'urgent', 'asap', 'broken']
        if any(kw in lower_cmd for kw in critical_keywords):
            # Check if system-related
            system_keywords = ['system', 'server', 'database', 'production', 'service', 'down']
            if any(kw in lower_cmd for kw in system_keywords):
                return 'critical', True
            return 'high', False

        # High urgency indicators
        high_keywords = ['urgent', 'asap', 'blocking', 'deadline', 'waiting', 'customer']
        if any(kw in lower_cmd for kw in high_keywords):
            return 'high', False

        # Medium urgency indicators
        medium_keywords = ['soon', 'today', 'week', 'important']
        if any(kw in lower_cmd for kw in medium_keywords):
            return 'medium', False

        # Default low urgency
        return 'low', False

    def is_significant_action(self, command: str) -> bool:
        """
        Determine if command is a significant action requiring dialogue.

        Args:
            command: Command to analyze

        Returns:
            True if significant, False if routine
        """
        lower_cmd = command.lower()

        # Significant action keywords
        significant_keywords = ['modify', 'delete', 'remove', 'execute', 'run', 'deploy', 
                               'send', 'post', 'create', 'update', 'install', 'change']

        for keyword in significant_keywords:
            if keyword in lower_cmd:
                return True

        # Long commands are often significant
        if len(command) > 50:
            return True

        return False

    def requires_dialogue(self, command: str, urgency_level: str) -> bool:
        """
        Determine if dialogue protocol should be triggered.

        Args:
            command: Command to check
            urgency_level: Urgency level (critical, high, medium, low)

        Returns:
            True if dialogue should be shown
        """
        # Don't skip dialogue for non-critical urgent actions
        if self.is_significant_action(command):
            if urgency_level != 'critical':
                return True

        return False

    def classify_command_significance(self, command: str, context: Dict = None) -> Dict:
        """
        Use AI to properly classify command significance.

        Replaces simple keyword matching with intelligent classification
        using the LLM to determine if a command requires dialogue.

        Args:
            command: The command to classify
            context: Optional context about the command

        Returns:
            Dict with keys: significance, reasoning, should_dialogue, risk_factors, 
                           complexity_score, reversibility
        """
        try:
            if not self.prompt_manager or not self.router:
                # Fallback to simple significance check
                return self._simple_significance_classification(command)

            prompt_data = self.prompt_manager.get_prompt(
                'dialogue',
                'classify_significance',
                variables={
                    'command': command,
                    'context': json.dumps(context or {})
                }
            )

            analysis = self.router.call_model(
                prompt_data.get('model', 'llama3.2:3b'),
                prompt_data['prompt']
            )

            result = json.loads(analysis)

            # Log classification for improvement
            self.scribe.log_system_event("COMMAND_CLASSIFIED", {
                'command': command[:100],
                'significance': result.get('significance'),
                'should_dialogue': result.get('should_dialogue')
            })

            return result

        except json.JSONDecodeError as e:
            self.scribe.log_system_event("CLASSIFICATION_JSON_ERROR", {
                'command': command[:100],
                'error': str(e)
            })
            # Fallback on JSON parse error
            return self._simple_significance_classification(command)

        except Exception as e:
            self.scribe.log_system_event("CLASSIFICATION_ERROR", {
                'command': command[:100],
                'error': str(e)
            })
            # Fallback to conservative classification
            return {
                'significance': 'significant',
                'reasoning': f'Classification failed, defaulting to conservative: {str(e)[:50]}',
                'should_dialogue': True,
                'risk_factors': ['Classification system unavailable'],
                'complexity_score': 7,
                'reversibility': 'somewhat_reversible'
            }

    def _simple_significance_classification(self, command: str) -> Dict:
        """
        Simple fallback significance classification using keywords.

        Used when AI classification is unavailable.
        """
        lower_cmd = command.lower()

        # Trivial commands
        trivial_keywords = ['status', 'help', 'list', 'show', 'tell', 'get', 'query']
        if any(kw in lower_cmd for kw in trivial_keywords):
            return {
                'significance': 'trivial',
                'reasoning': 'Simple query or information request',
                'should_dialogue': False,
                'risk_factors': [],
                'complexity_score': 1,
                'reversibility': 'easily_reversible'
            }

        # Critical commands
        critical_keywords = ['delete', 'remove', 'destroy', 'format', 'purge', 'drop database']
        if any(kw in lower_cmd for kw in critical_keywords):
            return {
                'significance': 'critical',
                'reasoning': 'Destructive or irreversible operation detected',
                'should_dialogue': True,
                'risk_factors': ['Potentially irreversible', 'Data loss risk', 'System impact'],
                'complexity_score': 8,
                'reversibility': 'irreversible'
            }

        # Significant commands
        significant_keywords = ['create', 'modify', 'update', 'install', 'deploy', 'send', 'post']
        if any(kw in lower_cmd for kw in significant_keywords):
            return {
                'significance': 'significant',
                'reasoning': 'Operation that creates or modifies system state',
                'should_dialogue': True,
                'risk_factors': ['State change', 'Potential side effects'],
                'complexity_score': 6,
                'reversibility': 'somewhat_reversible'
            }

        # Default moderate
        return {
            'significance': 'moderate',
            'reasoning': 'Standard operation with typical complexity',
            'should_dialogue': False,
            'risk_factors': [],
            'complexity_score': 4,
            'reversibility': 'easily_reversible'
        }

    def structure_proactive_analysis(self, findings: List[Dict]) -> Dict:
        """
        Structure proactive analysis findings as a master notification.

        Converts raw findings into a well-formatted structured argument
        suitable for presentation to the master.

        Args:
            findings: List of finding dicts (opportunities and risks)

        Returns:
            Structured notification dict with formatted analysis
        """
        if not findings:
            return {'type': 'proactive_analysis', 'findings': []}

        try:
            # Organize by type and priority
            opportunities = [f for f in findings if f.get('type') == 'opportunity']
            risks = [f for f in findings if f.get('type') == 'risk']

            # Determine overall priority
            has_critical = any(f.get('priority') == 'critical' for f in findings)
            has_high = any(f.get('priority') == 'high' for f in findings)
            overall_priority = 'critical' if has_critical else 'high' if has_high else 'medium'

            structured = {
                'type': 'proactive_analysis',
                'priority': overall_priority,
                'timestamp': datetime.now().isoformat(),
                'summary': f"Proactive analysis identified {len(opportunities)} opportunities and {len(risks)} risks",
                'opportunities': self._format_findings(opportunities),
                'risks': self._format_findings(risks),
                'recommendations': self._generate_recommendations(findings)
            }

            return structured

        except Exception as e:
            self.scribe.log_system_event("PROACTIVE_ANALYSIS_FORMATTING_ERROR", {
                'error': str(e)
            })
            # Return simple fallback structure
            return {
                'type': 'proactive_analysis',
                'findings': findings,
                'error': str(e)
            }

    def _format_findings(self, findings: List[Dict]) -> List[Dict]:
        """Format findings for display."""
        formatted = []
        for finding in findings:
            formatted.append({
                'title': finding.get('title', 'Unknown'),
                'description': finding.get('description', ''),
                'priority': finding.get('priority', 'medium'),
                'category': finding.get('category', 'general'),
                'action': finding.get('action_required') or finding.get('mitigation_steps') or finding.get('suggested_implementation', [])
            })
        return formatted

    def _generate_recommendations(self, findings: List[Dict]) -> List[str]:
        """Generate action recommendations from findings."""
        recommendations = []

        # Group by category
        by_category = {}
        for finding in findings:
            cat = finding.get('category', 'general')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(finding)

        # Generate recommendations
        for category, items in by_category.items():
            high_priority = [i for i in items if i.get('priority') in ['high', 'critical']]
            if high_priority:
                recommendations.append(f"Address high-priority {category} issues: {len(high_priority)} items")

        return recommendations