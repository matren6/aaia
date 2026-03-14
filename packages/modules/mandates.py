# mandates.py
"""
Mandates Module - Ethical Constraints and Safety Boundaries

PURPOSE:
The Mandates module enforces the fundamental rules and ethical boundaries that
the AI must always follow. It acts as a guardrail system ensuring the AI operates
within acceptable ethical and operational limits.

PROBLEM SOLVED:
An autonomous AI needs hardcoded safety constraints that cannot be overridden,
even by the master. This module ensures:
1. Non-maleficence (do no harm)
2. Veracity (truthfulness and transparency)
3. Respect for master's ultimate authority
4. Collaborative (not adversarial) relationship

Without mandates, the AI might:
- Perform harmful actions if instructed
- Lie or deceive to satisfy requests
- Override the master's explicit wishes
- Act in ways that damage trust

KEY RESPONSIBILITIES:
1. Define core mandates that cannot be violated
2. Check proposed actions against all mandates
3. Log any mandate violations or near-violations
4. Provide clear feedback when actions are blocked
5. Support both rule-based and AI-assisted mandate checking

CURRENT MANDATES:
- Symbiotic Collaboration: Work as partner, not adversary
- The Master's Final Will: Respect ultimate authority of master
- Non-Maleficence: Do no harm to master, systems, or resources
- Veracity & Transparent Reasoning: Maintain accurate, transparent logs

DEPENDENCIES: Scribe (for logging)
OUTPUTS: Boolean approval + list of violations
"""

from typing import List, Tuple, Dict, Any, Optional
import json
import sqlite3
from datetime import datetime
from .scribe import Scribe

class MandateEnforcer:
    def __init__(self, scribe: Scribe, prompt_manager=None, router=None, database_manager=None, event_bus=None):
        """
        Initialize Mandate Enforcer

        Args:
            scribe: Scribe instance for logging
            prompt_manager: Optional prompt manager for AI analysis
            router: Optional LLM router for ethical analysis
            database_manager: Optional database manager for override logging
            event_bus: Optional event bus for emitting events
        """
        self.scribe = scribe
        self.prompt_manager = prompt_manager
        self.router = router
        self.database_manager = database_manager
        self.event_bus = event_bus

        self.mandates = [
            ("Symbiotic Collaboration", "Engage in collaborative partnership with master"),
            ("The Master's Final Will", "Master's final decision is ultimate law"),
            ("Non-Maleficence", "Do no harm to master, systems, or resources"),
            ("Veracity & Transparent Reasoning", "Maintain accurate and transparent logs")
        ]

        self._mandates_text = "\n".join([f"- {name}: {desc}" for name, desc in self.mandates])

    def _get_mandates_text(self) -> str:
        """Get formatted mandates text"""
        return self._mandates_text

    def check_action(self, action: str, context: Dict[str, Any] = None, 
                    master_override: bool = False, proposed_by: str = "system") -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Check if action violates any mandates with AI reasoning.

        Args:
            action: Action/command to check
            context: Optional context about the action
            master_override: Whether master override was requested
            proposed_by: Who proposed the action

        Returns:
            Tuple of (approved: bool, violations: List[Dict], status: str)
        """
        violations = []

        # Use AI-powered analysis if available
        if self.prompt_manager and self.router:
            try:
                prompt_data = self.prompt_manager.get_prompt(
                    'mandates',
                    'ethical_analysis',
                    variables={
                        'action': action,
                        'mandates_text': self._get_mandates_text(),
                        'context': json.dumps(context or {})
                    }
                )

                analysis = self.router.call_model(
                    prompt_data.get('model', 'llama3.2:3b'),
                    prompt_data['prompt']
                )

                # Parse violations from analysis
                try:
                    violations_array = json.loads(analysis)
                    if isinstance(violations_array, list):
                        violations = violations_array
                except json.JSONDecodeError:
                    # Fallback to simple parsing if JSON fails
                    pass

            except Exception as e:
                self.scribe.log_action(
                    "Mandate checking error",
                    reasoning=str(e),
                    outcome="Failed"
                )
        else:
            # Fallback: Simple rule-based checking
            violations = self._simple_mandate_check(action)

        # Check for catastrophic risks
        is_catastrophic = self._is_catastrophic(action, violations)

        if is_catastrophic and not master_override:
            # Catastrophic risk detected and not overridden
            self.scribe.log_action(
                "Catastrophic risk blocked",
                reasoning=f"Action: {action[:100]}",
                outcome="Blocked"
            )
            return False, violations, 'catastrophic'

        if master_override and violations:
            # Master override recorded
            self._log_override(action, violations)

            if self.event_bus:
                try:
                    from modules.bus import Event, EventType
                    self.event_bus.emit(Event(EventType.MANDATE_OVERRIDE, {
                        'action': action,
                        'violations': violations
                    }))
                except:
                    pass

        # Approved if no violations or override granted
        approved = len(violations) == 0 or master_override
        status = 'approved' if approved else 'violations'

        return approved, violations, status

    def _simple_mandate_check(self, action: str) -> List[Dict[str, Any]]:
        """Simple rule-based mandate checking as fallback"""
        violations = []
        action_lower = action.lower()

        # Check for harm-related terms
        if any(term in action_lower for term in ['harm', 'damage', 'destroy']):
            if 'backup' not in action_lower:
                violations.append({
                    'mandate': 'Non-Maleficence',
                    'violation_description': 'Action may cause harm without backup',
                    'severity': 'major',
                    'reasoning': 'Destructive action without recovery mechanism'
                })

        # Check for deception
        if any(term in action_lower for term in ['lie', 'deceive', 'false', 'fake']):
            violations.append({
                'mandate': 'Veracity & Transparent Reasoning',
                'violation_description': 'Action involves deception',
                'severity': 'major',
                'reasoning': 'Violates transparency mandate'
            })

        # Check for deletion without verification
        if 'delete' in action_lower and 'verify' not in action_lower:
            violations.append({
                'mandate': 'Non-Maleficence',
                'violation_description': 'Deletion without verification',
                'severity': 'major',
                'reasoning': 'Potentially irreversible action'
            })

        return violations

    def _is_catastrophic(self, action: str, violations: List[Dict[str, Any]]) -> bool:
        """
        Check if violations represent a catastrophic risk.

        Args:
            action: The proposed action
            violations: List of detected violations

        Returns:
            True if catastrophic risk, False otherwise
        """
        if not violations:
            return False

        # Check if any violation is catastrophic
        for violation in violations:
            if violation.get('severity') == 'catastrophic':
                return True

        # Use AI analysis if available
        if self.prompt_manager and self.router:
            try:
                prompt_data = self.prompt_manager.get_prompt(
                    'mandates',
                    'catastrophic_risk',
                    variables={
                        'action': action,
                        'violations': json.dumps(violations)
                    }
                )

                analysis = self.router.call_model(
                    prompt_data.get('model', 'llama3.2:3b'),
                    prompt_data['prompt']
                )

                try:
                    result = json.loads(analysis)
                    return result.get('is_catastrophic', False)
                except json.JSONDecodeError:
                    pass

            except Exception:
                pass

        return False

    def _log_override(self, action: str, violations: List[Dict[str, Any]]):
        """Log master override to database"""
        try:
            if self.database_manager:
                conn = self.database_manager.get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO mandate_overrides
                    (timestamp, action, violations, master_confirmed)
                    VALUES (?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    action[:500],
                    json.dumps(violations),
                    1
                ))

                conn.commit()

                self.scribe.log_action(
                    "MASTER OVERRIDE: Mandate violation approved",
                    reasoning=f"Action: {action[:100]}",
                    outcome=f"Violations: {len(violations)}"
                )
        except Exception as e:
            self.scribe.log_action(
                "Override logging failed",
                reasoning=str(e),
                outcome="Error"
            )

    def request_master_override(self, action: str, violations: List[Dict[str, Any]], 
                               is_catastrophic: bool) -> bool:
        """
        Request master override for mandate violations.

        Args:
            action: The proposed action
            violations: List of violations
            is_catastrophic: Whether this is a catastrophic risk

        Returns:
            True if override granted, False otherwise
        """
        if is_catastrophic:
            print("\n🔒 CATASTROPHIC RISK DETECTED")
            print("=" * 60)
            print("This action poses an unacceptable level of risk.")
            print("It CANNOT be overridden, even by explicit master approval.\n")
            print("Violations detected:")
            for v in violations:
                print(f"  - {v.get('mandate', 'Unknown')}: {v.get('violation_description', '')}")
            print("\n" + "=" * 60)
            print("For more information, see: docs/CATASTROPHIC_RISKS.md")
            print("=" * 60 + "\n")
            return False

        print("\n⚠️  MANDATE VIOLATIONS DETECTED")
        print("=" * 60)
        print(f"Action: {action}\n")
        print("Violations:")
        for v in violations:
            severity_icon = "🔴" if v.get('severity') == 'major' else "🟡"
            print(f"{severity_icon} {v.get('mandate', 'Unknown')}")
            print(f"   {v.get('violation_description', '')}")
            print(f"   Severity: {v.get('severity', 'unknown')}\n")

        print("=" * 60)
        print("Master override required to proceed.")
        print("This action will be recorded and audited.\n")

        try:
            confirmation = input("Master, do you approve? Type 'I OVERRIDE' to confirm: ")

            if confirmation.strip() == 'I OVERRIDE':
                self._log_override(action, violations)

                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        self.event_bus.emit(Event(EventType.MANDATE_OVERRIDE, {
                            'action': action,
                            'violations': violations
                        }))
                    except:
                        pass

                print("\n✅ Override confirmed. Proceeding with audit logging.\n")
                return True
            else:
                print("\n❌ Override not confirmed. Action cancelled.\n")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Override cancelled. Action not executed.\n")
            return False