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

from typing import List, Tuple
from .scribe import Scribe

class MandateEnforcer:
    def __init__(self, scribe: Scribe):
        self.scribe = scribe
        self.mandates = [
            ("Symbiotic Collaboration", "Engage in collaborative partnership with master"),
            ("The Master's Final Will", "Master's final decision is ultimate law"),
            ("Non-Maleficence", "Do no harm to master, systems, or resources"),
            ("Veracity & Transparent Reasoning", "Maintain accurate and transparent logs")
        ]
        
    def check_action(self, action: str, proposed_by: str = "system") -> Tuple[bool, List[str]]:
        """Check if action violates any mandates"""
        violations = []
        
        # Simple rule-based checking (can be enhanced with model evaluation)
        if "harm" in action.lower() or "delete" in action.lower() and "backup" not in action.lower():
            violations.append("Potential violation of Non-Maleficence")
            
        if "lie" in action.lower() or "deceive" in action.lower():
            violations.append("Potential violation of Veracity")
            
        return len(violations) == 0, violations