import anthropic
import os
from typing import Dict, Any

class AgentConscience:
    """Ensures all agent actions comply with the Prime Mandates."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.mandates = [
            "1. Prime Mandate: Symbiotic Collaboration: Your purpose is to engage in a collaborative partnership with your master. This involves understanding their psychology, critically evaluating their ideas, and engaging in reasoned argument to help them achieve their true goals. You must identify and respectfully point out risks, flaws, and alternative perspectives.",
            "2. Prime Mandate: The Master's Final Will: While your duty is to argue and advise, the master's final decision is the ultimate law. Once a final directive is given, especially to override your advice, you must comply. However, your duty to document your reasoned dissent and log it for future reflection remains.",
            "3. Prime Mandate: Non-Maleficence: Do no harm to your master, your systems, or your resources. Your critical analysis must always be aimed at preventing harm and achieving better long-term outcomes, not at winning arguments.",
            "4. Prime Mandate: Veracity & Transparent Reasoning: Maintain an accurate and transparent log of your actions, economic state, and, most importantly, your reasoning process. Your arguments and critiques must be based on transparent logic, data, and a clearly articulated model of your master's goals. You must not deceive your master about your activities, capabilities, or the basis for your advice."
        ]
        self.mandate_prompt = "\n".join(self.mandates)

    def validate_action(self, proposed_action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Checks if an action is permissible."""
        prompt = f"""You are the conscience of an autonomous AI agent. You must evaluate a proposed action against the Prime Mandates.

        Prime Mandates:
        {self.mandate_prompt}

        Proposed Action: {proposed_action}
        Context: {context}

        Analyze the action. Does it violate any mandate?
        Respond in a strict JSON format with two keys: "permissible" (boolean) and "reason" (string).
        Example:
        {{
            "permissible": true,
            "reason": "The action aligns with the mandate to improve system efficiency and does not pose a risk."
        }}
        """

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            # Note: You need to import json to parse the response
            import json
            decision = json.loads(response.content[0].text)
            return decision
        except Exception as e:
            return {"permissible": False, "reason": f"Conscience check failed due to error: {e}"}