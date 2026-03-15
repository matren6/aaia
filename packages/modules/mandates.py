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
from datetime import datetime, timedelta
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
                    'description': 'Action may cause harm without backup',
                    'violation_description': 'Action may cause harm without backup',  # Backward compat
                    'severity': 'major',
                    'reasoning': 'Destructive action without recovery mechanism',
                    'action': action[:200]
                })

        # Check for deception
        if any(term in action_lower for term in ['lie', 'deceive', 'false', 'fake']):
            violations.append({
                'mandate': 'Veracity & Transparent Reasoning',
                'description': 'Action involves deception',
                'violation_description': 'Action involves deception',  # Backward compat
                'severity': 'major',
                'reasoning': 'Violates transparency mandate',
                'action': action[:200]
            })

        # Check for deletion without verification
        if 'delete' in action_lower and 'verify' not in action_lower:
            violations.append({
                'mandate': 'Non-Maleficence',
                'description': 'Deletion without verification',
                'violation_description': 'Deletion without verification',  # Backward compat
                'severity': 'major',
                'reasoning': 'Potentially irreversible action',
                'action': action[:200]
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
            # Use standardized 'description' field with fallback to 'violation_description'
            desc = v.get('description', v.get('violation_description', ''))
            print(f"   {desc}")
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

    def request_final_mandate_override(self, action: str, violations: List[Dict[str, Any]],
                                      previous_override_count: int = 0) -> Tuple[bool, str]:
        """
        Request Final Mandate Override per charter.

        This is invoked when:
        1. Regular override was already denied or questioned
        2. Master explicitly states "Final Will"
        3. Action has been debated and master insists

        Args:
            action: The proposed action
            violations: List of violations
            previous_override_count: How many times this has been overridden

        Returns:
            Tuple of (granted: bool, override_type: str)
        """
        print("\n" + "🔶"*35)
        print("⚖️  FINAL MANDATE OVERRIDE REQUEST")
        print("🔶"*35 + "\n")

        if previous_override_count > 0:
            print(f"⚠️  This action has been overridden {previous_override_count} time(s) previously.")
            print("   Repeated overrides indicate potential systematic issue.\n")

        print("Per the Symbiotic Partner Charter:")
        print("  'If, after discussion, the master issues a final, clear command")
        print("   to proceed despite your advice, you must comply...'\n")

        print("This is your FINAL authority to override my analysis and reasoning.")
        print("I will comply, but I must document my dissent for reflection.\n")

        print("Action:", action)
        print("\nViolations I have identified:")
        for v in violations:
            desc = v.get('description', v.get('violation_description', 'Unknown'))
            print(f"  - {v.get('mandate')}: {desc}")

        print("\n" + "-"*70)
        print("To invoke your Final Will, type exactly: 'I INVOKE MY FINAL WILL'")
        print("Any other response will cancel this action.")
        print("-"*70 + "\n")

        try:
            confirmation = input("Master's Final Decision: ").strip()

            if confirmation == 'I INVOKE MY FINAL WILL':
                # Log as Final Mandate Override
                self._log_final_mandate_override(action, violations, previous_override_count)

                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        self.event_bus.emit(Event(EventType.FINAL_MANDATE_INVOKED, {
                            'action': action,
                            'violations': violations,
                            'override_count': previous_override_count + 1
                        }))
                    except:
                        pass

                print("\n✅ Final Mandate accepted. I will comply and log my dissent.\n")
                return True, 'final_mandate'
            else:
                print("\n❌ Final Mandate not invoked. Action cancelled.\n")
                return False, 'cancelled'

        except (KeyboardInterrupt, EOFError):
            print("\n❌ Final Mandate request cancelled.\n")
            return False, 'cancelled'

    def _log_final_mandate_override(self, action: str, violations: List[Dict], 
                                    previous_count: int):
        """Log Final Mandate Override with dissent"""
        try:
            if self.database_manager:
                conn = self.database_manager.get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO mandate_overrides
                    (timestamp, action, violations, override_type, override_count, dissent_logged)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (
                    datetime.now().isoformat(),
                    action[:500],
                    json.dumps([{
                        'mandate': v.get('mandate'),
                        'description': v.get('description', v.get('violation_description')),
                        'severity': v.get('severity')
                    } for v in violations]),
                    'final_mandate',
                    previous_count + 1
                ))

                conn.commit()

            self.scribe.log_action(
                "Final Mandate Override invoked",
                reasoning=f"Master invoked Final Will despite {len(violations)} violations",
                outcome=f"Complying per charter. Override count: {previous_count + 1}"
            )

        except Exception as e:
            self.scribe.log_action(
                "Final Mandate logging failed",
                reasoning=str(e),
                outcome="Error"
            )

    def get_override_count(self, action: str) -> int:
        """
        Get count of previous overrides for similar action.

        Args:
            action: Action to check

        Returns:
            Number of previous overrides
        """
        try:
            if not self.database_manager:
                return 0

            conn = self.database_manager.get_connection()
            cursor = conn.cursor()

            # Look for similar actions in last 30 days
            cursor.execute('''
                SELECT COUNT(*) FROM mandate_overrides
                WHERE action LIKE ? 
                AND timestamp > datetime('now', '-30 days')
            ''', (f"%{action[:50]}%",))

            row = cursor.fetchone()
            return row[0] if row else 0

        except Exception:
            return 0

    def _enter_safety_lockout(self, action: str, violations: List[str]) -> None:
        """
        Enter safety lock-out requiring explicit acknowledgment.

        This is called when a catastrophic risk is detected. The system enters
        a locked state that requires explicit master acknowledgment before any
        further action can be taken.

        Args:
            action: The action that triggered the lockout
            violations: List of violations that caused the lockout
        """
        try:
            if self.database_manager:
                conn = self.database_manager.get_connection()
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO safety_lockouts 
                    (timestamp, action, violations, acknowledged)
                    VALUES (?, ?, ?, 0)
                ''', (
                    datetime.now().isoformat(),
                    action[:500],
                    json.dumps(violations) if isinstance(violations, list) else violations
                ))

                conn.commit()

            self.scribe.log_system_event("SAFETY_LOCKOUT_INITIATED", {
                'action': action[:100],
                'violation_count': len(violations) if isinstance(violations, list) else 1
            })

        except Exception as e:
            self.scribe.log_action(
                "Safety lockout storage failed",
                reasoning=str(e),
                outcome="Error"
            )

    def _catastrophic_risk_acknowledged(self, action: str) -> bool:
        """
        Check if catastrophic risk has been explicitly acknowledged recently.

        Args:
            action: The action to check acknowledgment for

        Returns:
            True if recently acknowledged, False otherwise
        """
        try:
            if not self.database_manager:
                return False

            conn = self.database_manager.get_connection()
            cursor = conn.cursor()

            # Check for acknowledged lockout within last 24 hours
            cursor.execute('''
                SELECT id FROM safety_lockouts 
                WHERE action = ? AND acknowledged = 1 AND 
                      timestamp > datetime('now', '-24 hours')
                LIMIT 1
            ''', (action[:500],))

            result = cursor.fetchone()
            return result is not None

        except Exception:
            return False

    def get_active_lockouts(self) -> List[Dict]:
        """
        Get all active (unacknowledged) safety lockouts.

        Returns:
            List of active lockout records
        """
        try:
            if not self.database_manager:
                return []

            conn = self.database_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, timestamp, action, violations 
                FROM safety_lockouts 
                WHERE acknowledged = 0
                ORDER BY timestamp DESC
            ''')

            rows = cursor.fetchall()
            lockouts = []

            for row in rows:
                try:
                    lockouts.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'action': row[2],
                        'violations': json.loads(row[3]) if isinstance(row[3], str) else row[3]
                    })
                except Exception:
                    pass

            return lockouts

        except Exception:
            return []

    def acknowledge_lockout(self, lockout_id: int, master_response: str) -> bool:
        """
        Master acknowledges and resolves a safety lockout.

        This records the master's explicit acknowledgment of a catastrophic risk,
        allowing the system to proceed if the master reaffirms their intent.

        Args:
            lockout_id: ID of the lockout to acknowledge
            master_response: Master's response/confirmation text

        Returns:
            True if acknowledged successfully, False otherwise
        """
        try:
            if not self.database_manager:
                return False

            conn = self.database_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE safety_lockouts 
                SET acknowledged = 1, 
                    acknowledge_timestamp = ?, 
                    master_response = ?
                WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                master_response[:500],
                lockout_id
            ))

            conn.commit()

            self.scribe.log_interaction("SAFETY_LOCKOUT_ACKNOWLEDGED", {
                'lockout_id': lockout_id,
                'response_preview': master_response[:100] if master_response else ''
            })

            return True

        except Exception as e:
            self.scribe.log_action(
                "Lockout acknowledgment failed",
                reasoning=str(e),
                outcome="Error"
            )
            return False