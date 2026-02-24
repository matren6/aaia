"""
Intent Predictor Module - Predictive Master Needs Analysis

PURPOSE:
The Intent Predictor predicts the master's needs before commands are given by
analyzing behavioral patterns, temporal patterns, and contextual sequences.
This enables proactive assistance rather than purely reactive responses.

PROBLEM SOLVED:
A reactive AI only responds to commands. But what if we could predict
what the master needs before they ask?
- Master uses same commands at certain times
- Tasks follow predictable sequences
- Understanding patterns enables proactive help
- Can suggest capabilities before they're needed

KEY RESPONSIBILITIES:
1. load_master_model(): Build model of master's preferences
2. update_model_from_interaction(): Learn from each interaction
3. get_recent_commands(): Fetch recent command history
4. predict_next_commands(): Predict likely next commands
5. analyze_temporal_patterns(): When does master typically act?
6. analyze_sequential_patterns(): What command sequences occur?
7. parse_predictions(): Convert AI predictions to structured format
8. proactive_development_suggestions(): Suggest capabilities based on predictions
9. analyze_capability_gap(): What capability would help predicted command?
10. get_master_profile(): Summary of learned master traits

MASTER MODEL PROPERTIES:
- communication_style: polite, direct, etc.
- preferred_complexity: low, medium, high
- task_preference: creative, problem_solving, analytical
- session_pattern: varied, consistent
- autonomy_acceptance: minimal, moderate, high

Each trait has:
- value: The trait value
- confidence: How certain we are (0-1)
- evidence_count: How many observations support it

DEPENDENCIES: Scribe, Router
OUTPUTS: Predictions of next commands, master profile
"""

import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class IntentPredictor:
    """Predict master's needs before commands are given"""

    def __init__(self, scribe, router):
        self.scribe = scribe
        self.router = router
        self.master_model = self.load_master_model()
        self.context_window = 10  # Number of recent commands to consider

    def load_master_model(self) -> Dict:
        """Load and update model of master's preferences/patterns"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Create table for master model
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS master_model (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trait TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 0.1,
                evidence_count INTEGER DEFAULT 1,
                last_updated TEXT
            )
        ''')

        # Get existing traits
        cursor.execute("SELECT trait, value, confidence, evidence_count FROM master_model")
        rows = cursor.fetchall()
        conn.close()

        model = {}
        for trait, value, confidence, count in rows:
            model[trait] = {
                "value": value,
                "confidence": min(confidence, 1.0),
                "evidence_count": count
            }

        # If model is empty, initialize with defaults
        if not model:
            model = self._initialize_default_model()
            self.save_master_model(model)

        return model

    def _initialize_default_model(self) -> Dict:
        """Initialize with default trait values"""
        return {
            "communication_style": {"value": "direct", "confidence": 0.1, "evidence_count": 1},
            "preferred_complexity": {"value": "medium", "confidence": 0.1, "evidence_count": 1},
            "task_preference": {"value": "practical", "confidence": 0.1, "evidence_count": 1},
            "session_pattern": {"value": "varied", "confidence": 0.1, "evidence_count": 1},
            "autonomy_acceptance": {"value": "moderate", "confidence": 0.1, "evidence_count": 1}
        }

    def save_master_model(self, model: Dict) -> None:
        """Save master model to database"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        for trait, data in model.items():
            cursor.execute('''
                INSERT OR REPLACE INTO master_model (trait, value, confidence, evidence_count, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                trait,
                data["value"],
                data["confidence"],
                data.get("evidence_count", 1),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

    def update_model_from_interaction(self, command: str, outcome: str) -> None:
        """Update the master model based on interactions"""
        command_lower = command.lower()

        # Analyze communication style
        if any(word in command_lower for word in ["please", "could you", "would you"]):
            self._update_trait("communication_style", "polite", 0.1)
        elif len(command.split()) < 5 and not any(word in command_lower for word in ["explain", "why"]):
            self._update_trait("communication_style", "direct", 0.1)

        # Analyze complexity preference
        if any(word in command_lower for word in ["simple", "basic", "quick"]):
            self._update_trait("preferred_complexity", "low", 0.15)
        elif any(word in command_lower for word in ["detailed", "comprehensive", "thorough"]):
            self._update_trait("preferred_complexity", "high", 0.15)

        # Analyze task preference
        if any(word in command_lower for word in ["create", "make", "build"]):
            self._update_trait("task_preference", "creative", 0.1)
        elif any(word in command_lower for word in ["fix", "repair", "debug"]):
            self._update_trait("task_preference", "problem_solving", 0.1)
        elif any(word in command_lower for word in ["analyze", "review", "check"]):
            self._update_trait("task_preference", "analytical", 0.1)

        # Analyze autonomy acceptance based on outcome
        if "success" in outcome.lower() or "completed" in outcome.lower():
            # Positive outcome - might indicate good alignment
            pass

    def _update_trait(self, trait: str, value: str, evidence_weight: float) -> None:
        """Update a specific trait in the master model"""
        if trait not in self.master_model:
            self.master_model[trait] = {"value": value, "confidence": 0.1, "evidence_count": 1}
            return

        current = self.master_model[trait]

        if current["value"] == value:
            # Same value - increase confidence
            current["confidence"] = min(current["confidence"] + evidence_weight, 1.0)
            current["evidence_count"] = current.get("evidence_count", 1) + 1
        else:
            # Different value - decrease confidence
            current["confidence"] = max(current["confidence"] - evidence_weight / 2, 0.1)

        # Save updated model
        self.save_master_model(self.master_model)

    def get_recent_commands(self, limit: int = 20) -> List[Dict]:
        """Get recent commands from the log"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT action, reasoning, outcome, timestamp
            FROM action_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "action": row[0],
                "reasoning": row[1],
                "outcome": row[2],
                "timestamp": row[3]
            }
            for row in rows
        ]

    def predict_next_commands(self, recent_context: List[str] = None) -> List[Dict]:
        """Predict what commands master might give next"""
        if recent_context is None:
            recent_commands = self.get_recent_commands(10)
            recent_context = [cmd["action"] for cmd in recent_commands]

        # Analyze temporal patterns
        temporal_pattern = self.analyze_temporal_patterns()

        # Analyze sequential patterns
        sequential_pattern = self.analyze_sequential_patterns(recent_context)

        # Build prediction prompt
        context_str = "\n".join(f"- {ctx}" for ctx in recent_context[-5:])

        prompt = f"""
You are a behavioral prediction expert for an AI assistant.

Recent Command Context:
{context_str}

Master's Behavioral Model:
{json.dumps(self.master_model, indent=2)}

Temporal Patterns:
- Time of day preference: {temporal_pattern.get('time_preference', 'varied')}
- Day of week pattern: {temporal_pattern.get('day_preference', 'varied')}

Sequential Patterns:
{sequential_pattern}

Based on this context and patterns, predict the 3 most likely next commands the master will give.
Consider:
1. Temporal patterns (time of day, day of week)
2. Sequential patterns (command chains)
3. Intent progression (simple -> complex tasks)
4. Recent topics of interest

Format each prediction exactly as:
PREDICTION: [command or task description]
CONFIDENCE: [0.00-1.00]
RATIONALE: [why this prediction makes sense]

Repeat this format 3 times for top 3 predictions.
"""

        try:
            model_name, _ = self.router.route_request("prediction", "high")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are a behavioral prediction expert."
            )

            predictions = self.parse_predictions(response)

            self.scribe.log_action(
                "Intent prediction",
                f"Made {len(predictions)} predictions",
                "prediction_completed"
            )

            return predictions

        except Exception as e:
            return [{"error": f"Prediction failed: {str(e)}"}]

    def analyze_temporal_patterns(self) -> Dict:
        """Analyze temporal patterns in master's behavior"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Get hour distribution
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM action_log
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 3
        ''')

        hour_rows = cursor.fetchall()
        most_active_hours = [row[0] for row in hour_rows] if hour_rows else []

        # Get day of week distribution
        cursor.execute('''
            SELECT strftime('%w', timestamp) as day, COUNT(*) as count
            FROM action_log
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY day
            ORDER BY count DESC
        ''')

        day_rows = cursor.fetchall()
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        most_active_days = [days[int(row[0])] for row in day_rows[:3]] if day_rows else []

        conn.close()

        return {
            "time_preference": ", ".join(most_active_hours) if most_active_hours else "varied",
            "day_preference": ", ".join(most_active_days) if most_active_days else "varied"
        }

    def analyze_sequential_patterns(self, recent_context: List[str]) -> str:
        """Analyze sequential patterns in commands"""
        if len(recent_context) < 2:
            return "Insufficient data for sequential analysis"

        # Find common sequences
        patterns = []
        for i in range(len(recent_context) - 1):
            patterns.append(f"{recent_context[i]} -> {recent_context[i+1]}")

        # Look for repeated patterns
        pattern_counts = defaultdict(int)
        for p in patterns:
            pattern_counts[p] += 1

        # Return most common
        common = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        return "\n".join(f"{p[0]}: {p[1]}x" for p in common) if common else "No clear patterns"

    def parse_predictions(self, response: str) -> List[Dict]:
        """Parse AI prediction response into structured format"""
        predictions = []
        current_pred = {}

        for line in response.strip().split('\n'):
            line = line.strip()

            if line.startswith("PREDICTION:") and ":" in line:
                if current_pred and "command" in current_pred:
                    predictions.append(current_pred)
                current_pred = {"command": line.split(":", 1)[1].strip()}

            elif line.startswith("CONFIDENCE:") and current_pred:
                try:
                    current_pred["confidence"] = float(line.split(":", 1)[1].strip())
                except:
                    current_pred["confidence"] = 0.5

            elif line.startswith("RATIONALE:") and current_pred:
                current_pred["rationale"] = line.split(":", 1)[1].strip()

        # Don't forget last prediction
        if current_pred and "command" in current_pred:
            predictions.append(current_pred)

        return predictions

    def proactive_development_suggestions(self) -> List[Dict]:
        """Suggest developments based on predicted needs"""
        predictions = self.predict_next_commands()

        if not predictions or "error" in predictions[0]:
            return []

        suggestions = []

        for prediction in predictions:
            command = prediction.get("command", "")
            confidence = prediction.get("confidence", 0.5)

            # Only suggest for high-confidence predictions
            if confidence < 0.5:
                continue

            # Analyze what capability would help fulfill this predicted command
            capability = self.analyze_capability_gap(command)

            if capability:
                suggestions.append({
                    "predicted_command": command,
                    "confidence": confidence,
                    "suggested_capability": capability["name"],
                    "rationale": capability["reasoning"],
                    "priority": "high" if confidence > 0.7 else "medium"
                })

        return suggestions

    def analyze_capability_gap(self, command: str) -> Optional[Dict]:
        """Analyze what capability would help with predicted command"""
        prompt = f"""
Analyze this predicted command and determine what capability would help execute it:

Predicted Command: {command}

What new capability (if any) would help this system execute this command better?

Response format (one of these options):
CAPABILITY_NEEDED: [name of needed capability or 'none']
REASONING: [brief explanation]
"""

        try:
            model_name, _ = self.router.route_request("analysis", "medium")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are a capability analysis expert."
            )

            # Parse response
            lines = response.strip().split('\n')
            capability_name = None
            reasoning = ""

            for line in lines:
                line = line.strip()
                if line.startswith("CAPABILITY_NEEDED:") and ":" in line:
                    name = line.split(":", 1)[1].strip()
                    if name.lower() != "none":
                        capability_name = name
                elif line.startswith("REASONING:") and ":" in line:
                    reasoning = line.split(":", 1)[1].strip()

            if capability_name:
                return {"name": capability_name, "reasoning": reasoning}

        except:
            pass

        return None

    def get_master_profile(self) -> Dict:
        """Get summary of master model"""
        return {
            "traits": self.master_model,
            "total_interactions": sum(
                t.get("evidence_count", 1) for t in self.master_model.values()
            ),
            "model_confidence": sum(
                t.get("confidence", 0) for t in self.master_model.values()
            ) / max(len(self.master_model), 1)
        }
