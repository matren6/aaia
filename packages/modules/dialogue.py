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
        provider = self.router.route_request("reasoning", "high")
        response = provider.generate(prompt_data["prompt"],
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

    def create_pending_dialogue(self, command: str, understanding: str, 
                               risks: List[str], alternatives: List[str],
                               context: str = "") -> int:
        """
        Create pending dialogue for web GUI (non-blocking).

        Instead of blocking with input(), creates a record that appears
        in the web GUI for master to respond to asynchronously.

        Args:
            command: Original command
            understanding: AI's understanding of goal
            risks: List of identified risks
            alternatives: List of alternative approaches
            context: Additional context

        Returns:
            Dialogue ID for tracking
        """
        import json
        from datetime import datetime

        # Store in database
        conn = self.scribe.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pending_dialogues
            (timestamp, command, understanding, risks, alternatives, context, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            datetime.now().isoformat(),
            command[:500],
            understanding[:500],
            json.dumps(risks),
            json.dumps(alternatives),
            context[:500] if context else None
        ))

        conn.commit()
        dialogue_id = cursor.lastrowid

        # Log creation
        self.scribe.log_action(
            f"Pending dialogue created: {command[:50]}",
            reasoning=f"Risks: {len(risks)}, Alternatives: {len(alternatives)}",
            outcome=f"Awaiting master response (dialogue_id={dialogue_id})"
        )

        # Emit event for web GUI to pick up
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.DIALOGUE_PENDING, {
                    'dialogue_id': dialogue_id,
                    'command': command,
                    'risks_count': len(risks),
                    'alternatives_count': len(alternatives)
                }))
            except:
                pass

        return dialogue_id

    def get_pending_dialogues(self, status: str = 'pending') -> List[Dict]:
        """
        Get all pending dialogues for web GUI display.

        Args:
            status: Filter by status (pending/responded/cancelled)

        Returns:
            List of dialogue records
        """
        import json

        conn = self.scribe.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, timestamp, command, understanding, risks, alternatives,
                   context, status, master_response, master_decision, final_command
            FROM pending_dialogues
            WHERE status = ?
            ORDER BY timestamp DESC
        ''', (status,))

        dialogues = []
        for row in cursor.fetchall():
            try:
                dialogues.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'command': row[2],
                    'understanding': row[3],
                    'risks': json.loads(row[4]) if row[4] else [],
                    'alternatives': json.loads(row[5]) if row[5] else [],
                    'context': row[6],
                    'status': row[7],
                    'master_response': row[8],
                    'master_decision': row[9],
                    'final_command': row[10]
                })
            except:
                continue

        return dialogues

    def respond_to_dialogue(self, dialogue_id: int, decision: str, 
                           modified_command: str = None) -> bool:
        """
        Master responds to pending dialogue (called from web GUI).

        Args:
            dialogue_id: ID of pending dialogue
            decision: Master's decision (proceed/modify/cancel/1-N)
            modified_command: Modified command if decision='modify'

        Returns:
            True if response recorded successfully
        """
        from datetime import datetime

        conn = self.scribe.get_connection()
        cursor = conn.cursor()

        # Get the dialogue
        cursor.execute('''
            SELECT command, alternatives FROM pending_dialogues WHERE id = ?
        ''', (dialogue_id,))

        row = cursor.fetchone()
        if not row:
            return False

        original_command = row[0]
        alternatives = json.loads(row[1]) if row[1] else []

        # Determine final command
        final_command = original_command
        master_decision = 'proceed'

        if decision == 'c':
            master_decision = 'cancel'
        elif decision == 'm':
            master_decision = 'modify'
            final_command = modified_command or original_command
        elif decision.isdigit() and alternatives:
            idx = int(decision) - 1
            if 0 <= idx < len(alternatives):
                master_decision = 'proceed'
                final_command = alternatives[idx]

        # Update dialogue
        cursor.execute('''
            UPDATE pending_dialogues
            SET status = 'responded',
                master_response = ?,
                master_decision = ?,
                final_command = ?,
                responded_at = ?
            WHERE id = ?
        ''', (
            decision,
            master_decision,
            final_command,
            datetime.now().isoformat(),
            dialogue_id
        ))

        conn.commit()

        # Log response
        self.scribe.log_action(
            f"Master responded to dialogue {dialogue_id}",
            reasoning=f"Decision: {master_decision}",
            outcome=f"Command: {final_command[:50]}"
        )

        # Emit event
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.DIALOGUE_RESPONDED, {
                    'dialogue_id': dialogue_id,
                    'decision': master_decision,
                    'final_command': final_command
                }))
            except:
                pass

        return True

    def present_structured_argument(self, command: str, understanding: str, 
                               risks: List[str], alternatives: List[str],
                               context: str = "", mode: str = "auto") -> Dict[str, Any]:
        """
        Present structured argument to master.

        Mode-aware implementation:
        - 'auto': Detect if running in web mode or console mode
        - 'web': Create pending dialogue for web GUI (non-blocking)
        - 'console': Use interactive console input (blocking)

        Args:
            command: Original command
            understanding: AI's understanding of goal
            risks: List of identified risks
            alternatives: List of alternative approaches
            context: Additional context
            mode: 'auto', 'web', or 'console'

        Returns:
            Dict with keys:
            - master_confirmed_understanding: bool
            - master_response: str
            - master_decision: 'proceed' | 'modify' | 'cancel' | 'pending'
            - final_command: str (if modified)
            - dialogue_id: int (if web mode)
        """
        # Auto-detect mode
        if mode == "auto":
            # Check if web server is available
            try:
                from modules.settings import get_config
                config = get_config()
                mode = "web" if config.web_server.enabled else "console"
            except:
                mode = "console"

        if mode == "web":
            # Non-blocking: Create pending dialogue for web GUI
            dialogue_id = self.create_pending_dialogue(
                command, understanding, risks, alternatives, context
            )

            return {
                'master_confirmed_understanding': False,
                'master_response': 'pending',
                'master_decision': 'pending',
                'final_command': command,
                'dialogue_id': dialogue_id,
                'mode': 'web'
            }

        else:
            # Blocking: Interactive console dialogue (original implementation)
            return self._present_structured_argument_console(
                command, understanding, risks, alternatives, context
            )

    def _present_structured_argument_console(self, command: str, understanding: str,
                                            risks: List[str], alternatives: List[str],
                                            context: str = "") -> Dict[str, Any]:
        """
        Interactive console dialogue (original implementation).
        Only used when web GUI is not available.
        """
        print("\n" + "="*70)
        print("📋 STRUCTURED ARGUMENT PROTOCOL")
        print("="*70 + "\n")

        # Phase 1: Understanding
        print("1️⃣  UNDERSTANDING:")
        print(f"   My understanding of your goal is:")
        print(f"   '{understanding}'\n")

        confirmed = input("   Is this correct? [y/n]: ").strip().lower()

        if confirmed != 'y':
            print("\n   Please clarify your goal:")
            clarification = input("   > ")
            # Re-analyze with clarification
            understanding, risks, alternatives = self.structured_argument(
                command, context=f"{context}\nClarification: {clarification}"
            )
            print(f"\n   Updated understanding: '{understanding}'\n")

        # Phase 2: Risks
        if risks:
            print("2️⃣  IDENTIFIED RISKS/FLAWS:")
            for i, risk in enumerate(risks, 1):
                print(f"   {i}. {risk}")
            print()
        else:
            print("2️⃣  IDENTIFIED RISKS/FLAWS: None detected\n")

        # Phase 3: Alternatives
        if alternatives:
            print("3️⃣  PROPOSED ALTERNATIVES:")
            for i, alt in enumerate(alternatives, 1):
                print(f"   {i}. {alt}")
            print()
        else:
            print("3️⃣  PROPOSED ALTERNATIVES: None identified\n")

        # Phase 4: Request for Dialogue
        print("4️⃣  REQUEST FOR DIALOGUE:")
        print("   I recommend we discuss this before proceeding.\n")
        print("   Your options:")
        print("   [p] Proceed with original command")
        print("   [m] Modify the command")
        print("   [c] Cancel")

        if alternatives:
            print("   [1-N] Use alternative N")

        print()
        decision = input("   Your decision: ").strip().lower()

        # Log dialogue
        self.scribe.log_action(
            f"Structured dialogue completed for: {command[:50]}",
            reasoning=f"Risks: {len(risks)}, Alternatives: {len(alternatives)}",
            outcome=f"Master decision: {decision}"
        )

        # Emit event
        if self.event_bus:
            try:
                from modules.bus import Event, EventType
                self.event_bus.emit(Event(EventType.DIALOGUE_COMPLETED, {
                    'command': command,
                    'decision': decision,
                    'risks_count': len(risks),
                    'alternatives_count': len(alternatives)
                }))
            except:
                pass

        # Parse decision
        result = {
            'master_confirmed_understanding': confirmed == 'y',
            'master_response': decision,
            'master_decision': 'cancel',
            'final_command': command,
            'mode': 'console'
        }

        if decision == 'p':
            result['master_decision'] = 'proceed'
        elif decision == 'c':
            result['master_decision'] = 'cancel'
        elif decision == 'm':
            result['master_decision'] = 'modify'
            print("\n   Enter modified command:")
            result['final_command'] = input("   > ").strip()
        elif decision.isdigit() and alternatives:
            idx = int(decision) - 1
            if 0 <= idx < len(alternatives):
                result['master_decision'] = 'proceed'
                result['final_command'] = alternatives[idx]

        print("\n" + "="*70 + "\n")

        return result

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