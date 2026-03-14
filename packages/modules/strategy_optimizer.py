"""
Strategy Optimizer Module - Evolution Strategy Optimization

PURPOSE:
The Strategy Optimizer analyzes past evolution attempts to determine what
strategies work best, then generates experiments to improve evolution
effectiveness. It applies machine learning-like principles to self-improvement.

PROBLEM SOLVED:
Evolution attempts don't all succeed equally:
- Some approaches work better than others
- Need to identify patterns in success vs failure
- Should avoid repeating failed strategies
- Need to generate new experiments to try
- Should recommend parameter tuning

KEY RESPONSIBILITIES:
1. load_strategy_history(): Load past evolution attempts
2. record_strategy_attempt(): Record a strategy attempt for analysis
3. optimize_evolution_strategy(): Analyze and optimize approach
4. identify_patterns(): Find common elements in success/failure
5. generate_experiments(): Create experiments based on patterns
6. generate_recommended_approach(): Summarize best approach
7. get_strategy_performance_summary(): Overall strategy metrics
8. suggest_parameter_tuning(): Recommend parameter adjustments

STRATEGY PROPERTIES TRACKED:
- strategy_name: Identifier for strategy type
- strategy_params: Configuration parameters
- success_rate: Percentage of successful tasks
- tasks_completed/failed: Task counts
- execution_time_seconds: How long it took
- outcomes: List of outcomes
- lessons_learned: What was learned

PATTERN ANALYSIS:
- What parameters correlate with success?
- What approaches consistently fail?
- What's the optimal complexity level?
- What task ordering works best?

DEPENDENCIES: Scribe
OUTPUTS: Optimized strategies, recommendations, experiments
"""

import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class StrategyOptimizer:
    """Optimize evolution strategies based on past performance"""

    def __init__(self, scribe, router=None, evolution=None, metacognition=None, event_bus=None, prompt_manager=None):
        self.scribe = scribe
        self.router = router
        self.evolution = evolution
        self.metacognition = metacognition
        self.event_bus = event_bus
        # PromptManager should be provided by DI; accept optional param for backwards compatibility
        from modules.prompt_manager import get_prompt_manager
        self.prompt_manager = prompt_manager or get_prompt_manager()
        self.strategy_history = self.load_strategy_history()

    def load_strategy_history(self) -> List[Dict]:
        """Load historical strategy performance data"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                strategy_name TEXT,
                strategy_params TEXT,
                success_rate REAL,
                tasks_completed INTEGER,
                tasks_failed INTEGER,
                execution_time_seconds REAL,
                outcomes TEXT,
                lessons_learned TEXT
            )
        ''')

        # Get recent history
        cursor.execute('''
            SELECT timestamp, strategy_name, strategy_params, success_rate,
                   tasks_completed, tasks_failed, execution_time_seconds, outcomes, lessons_learned
            FROM strategy_history
            ORDER BY timestamp DESC
            LIMIT 50
        ''')

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "timestamp": row[0],
                "strategy_name": row[1],
                "strategy_params": json.loads(row[2]) if row[2] else {},
                "success_rate": row[3],
                "tasks_completed": row[4],
                "tasks_failed": row[5],
                "execution_time_seconds": row[6],
                "outcomes": json.loads(row[7]) if row[7] else [],
                "lessons_learned": row[8]
            })

        return history

    def record_strategy_attempt(
        self,
        strategy_name: str,
        strategy_params: Dict,
        success_rate: float,
        tasks_completed: int,
        tasks_failed: int,
        execution_time: float,
        outcomes: List[str],
        lessons: str = ""
    ) -> None:
        """Record a strategy attempt for future analysis"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO strategy_history (
                timestamp, strategy_name, strategy_params, success_rate,
                tasks_completed, tasks_failed, execution_time_seconds, outcomes, lessons_learned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            strategy_name,
            json.dumps(strategy_params),
            success_rate,
            tasks_completed,
            tasks_failed,
            execution_time,
            json.dumps(outcomes),
            lessons
        ))

        conn.commit()
        conn.close()

        # Update local history
        self.strategy_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy_name": strategy_name,
            "strategy_params": strategy_params,
            "success_rate": success_rate,
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "execution_time_seconds": execution_time,
            "outcomes": outcomes,
            "lessons_learned": lessons
        })

    def optimize_evolution_strategy(self, recent_results: List[Dict] = None) -> Dict:
        """Optimize evolution strategy based on historical data using centralized prompts"""

        # Gather recent history if not provided
        if recent_results is None:
            cutoff = datetime.now() - timedelta(days=30)
            recent_results = [
                r for r in self.strategy_history
                if datetime.fromisoformat(r["timestamp"]) > cutoff
            ]

        # Prepare data for prompt
        history_text = self._format_history(recent_results)
        metrics = self.get_strategy_performance_summary()
        metrics_text = self._format_metrics(metrics)


        # Use PromptManager to get a formatted LLM prompt
        try:
            current_state = self._gather_current_state()
            capabilities = self._get_capabilities_summary()
            prompt = self.prompt_manager.get_prompt(
                'strategy_optimization',
                history=history_text,
                current_state=current_state,
                capabilities=capabilities
            )
        except Exception:
            # Fallback to local analysis if prompt missing
            return {
                "adopt": [],
                "avoid": [],
                "experiment_with": self.generate_experiments({}, {}),
                "recommended_approach": self.generate_recommended_approach({}, {})
            }

        # Call model for analysis
        model_name, _ = (self.router.route_request("analysis", "high") if self.router else ("default", {}))
        response = self.router.call_model(model_name, prompt["prompt"]) if self.router else ""

        # Parse response into structured data
        optimization = self._parse_strategy_response(response)

        # Log strategy optimization
        try:
            self.scribe.log_action(
                "Strategy optimization",
                f"Generated {len(optimization.get('adopt', []))} adopt strategies, {len(optimization.get('avoid', []))} avoid patterns",
                "optimized"
            )
        except Exception:
            pass

        return optimization

    def _format_history(self, history: List[Dict]) -> str:
        """Format history for prompt"""
        lines = []
        for entry in history[-10:]:
            ts = entry.get('timestamp', '')
            action = entry.get('strategy_name', '')
            outcome = ','.join(entry.get('outcomes', [])) if entry.get('outcomes') else entry.get('lessons_learned', '')
            lines.append(f"- {ts}: {action} -> {outcome}")
        return "\n".join(lines)

    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics for prompt"""
        lines = []
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _parse_strategy_response(self, response: str) -> Dict:
        """Parse LLM response into structured strategy"""
        strategy = {
            'adopt': [],
            'avoid': [],
            'experiment_with': [],
            'recommended_approach': ''
        }

        current_section = None
        for line in (response or "").split('\n'):
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if 'ADOPT' in line.upper():
                current_section = 'adopt'
                continue
            elif 'AVOID' in line.upper():
                current_section = 'avoid'
                continue
            elif 'EXPERIMENT' in line.upper():
                current_section = 'experiment_with'
                continue
            elif 'RECOMMENDED' in line.upper():
                current_section = 'recommended'
                continue
            elif current_section and (line[0].isdigit() or line.startswith('-')):
                # Parse item
                if current_section == 'recommended':
                    strategy['recommended_approach'] += line + ' '
                else:
                    strategy[current_section].append(line)

        return strategy

    def identify_bottlenecks(self) -> List[Dict]:
        """Identify strategic bottlenecks in evolution process"""
        current_state = self._gather_current_state()
        recent_changes = self._gather_recent_changes()

        try:
            prompt = self.prompt_manager.get_prompt(
                'identify_bottlenecks',
                current_state=current_state,
                recent_changes=recent_changes
            )
        except Exception:
            return []

        model_name, _ = (self.router.route_request("analysis", "high") if self.router else ("default", {}))
        response = self.router.call_model(model_name, prompt["prompt"]) if self.router else ""

        bottlenecks = self._parse_bottlenecks(response)
        return bottlenecks

    def _get_capabilities_summary(self) -> str:
        """Return a short summary of system capabilities for prompts"""
        caps = []
        try:
            if hasattr(self, 'metacognition') and self.metacognition:
                metrics = getattr(self.metacognition, 'collect_current_metrics', lambda: {})()
                caps.append(f"- Metrics available: {len(metrics)}")
        except Exception:
            pass

        try:
            caps.append(f"- Strategy history length: {len(self.strategy_history)}")
        except Exception:
            caps.append("- Strategy history length: unknown")

        return "\n".join(caps)

    def _gather_current_state(self) -> str:
        """Gather current system state"""
        state = []
        try:
            state.append(f"Current tier: {getattr(self, '_get_current_tier', lambda: 'unknown')()}")
        except Exception:
            state.append("Current tier: unknown")
        try:
            state.append(f"Active goals: {getattr(self, '_get_active_goals_count', lambda: 0)()}"
            )
        except Exception:
            state.append("Active goals: 0")
        try:
            state.append(f"System health: {getattr(self, '_get_health_score', lambda: 'unknown')()}"
            )
        except Exception:
            state.append("System health: unknown")
        return "\n".join(state)

    def _gather_recent_changes(self) -> str:
        """Gather recent system changes"""
        try:
            changes = []
            # Use scribe if available
            if hasattr(self.scribe, 'get_recent_actions'):
                recent = self.scribe.get_recent_actions(hours=48)
                changes = [f"- {c.get('action')}: {c.get('outcome')}" for c in recent[:10]]
            return "\n".join(changes)
        except Exception:
            return ""

    def _parse_bottlenecks(self, response: str) -> List[Dict]:
        """Parse bottleneck response"""
        bottlenecks = []
        for line in (response or "").split('\n'):
            if line.strip() and (line[0].isdigit() or line.startswith('-')):
                parts = [p.strip() for p in line.split('-', 2)]
                if len(parts) >= 3:
                    bottlenecks.append({
                        'bottleneck': parts[0],
                        'impact': parts[1],
                        'solution': parts[2]
                    })
        return bottlenecks

    def identify_patterns(self, strategies: List[Dict]) -> Dict:
        """Identify common patterns in strategies"""
        if not strategies:
            return {"common_elements": [], "strategy_count": 0}

        # Analyze common elements across strategy params
        param_values = defaultdict(list)

        for strategy in strategies:
            params = strategy.get("strategy_params", {})
            for key, value in params.items():
                param_values[key].append(value)

        common_elements = []
        for key, values in param_values.items():
            if not values:
                continue

            # Find most common value
            from collections import Counter
            value_counts = Counter(values)
            most_common = value_counts.most_common(1)[0]

            if most_common[1] >= len(strategies) * 0.5:  # At least 50% share this value
                common_elements.append({
                    "element": key,
                    "value": most_common[0],
                    "frequency": most_common[1] / len(strategies)
                })

        # Also look at outcomes
        all_outcomes = []
        for strategy in strategies:
            all_outcomes.extend(strategy.get("outcomes", []))

        return {
            "common_elements": common_elements,
            "strategy_count": len(strategies),
            "success_rate_avg": sum(s.get("success_rate", 0) for s in strategies) / len(strategies),
            "common_outcomes": self._summarize_outcomes(all_outcomes)
        }

    def _summarize_outcomes(self, outcomes: List[str]) -> Dict:
        """Summarize common outcomes"""
        if not outcomes:
            return {}

        outcome_counts = defaultdict(int)
        for outcome in outcomes:
            outcome_counts[outcome] += 1

        return dict(sorted(outcome_counts.items(), key=lambda x: x[1], reverse=True)[:5])

    def generate_experiments(
        self,
        success_patterns: Dict,
        failure_patterns: Dict
    ) -> List[str]:
        """Generate experiments to try based on patterns"""
        experiments = []

        # Try combining successful elements with variations
        success_elements = success_patterns.get("common_elements", [])
        for element in success_elements[:3]:
            experiments.append(
                f"Test alternative to {element['element']}: {element['value']} "
                f"(currently {element['frequency']*100:.0f}% success rate)"
            )

        # Try improvements to failed approaches
        failure_elements = failure_patterns.get("common_elements", [])
        for element in failure_elements[:2]:
            experiments.append(
                f"Redesign {element['element']} approach (currently failing)"
            )

        # Add general experiments
        experiments.extend([
            "Test incremental vs radical changes",
            "Experiment with different task ordering",
            "Try parallel vs sequential execution"
        ])

        return experiments[:6]

    def generate_recommended_approach(
        self,
        success_patterns: Dict,
        failure_patterns: Dict
    ) -> str:
        """Generate a recommended approach based on analysis"""
        recommendations = []

        # What to adopt
        if success_patterns.get("common_elements"):
            adopt = [f"{e['element']}={e['value']}" for e in success_patterns["common_elements"][:3]]
            recommendations.append(f"ADOPT: {', '.join(adopt)}")

        # What to avoid
        if failure_patterns.get("common_elements"):
            avoid = [f"{e['element']}" for e in failure_patterns["common_elements"][:2]]
            recommendations.append(f"AVOID: {', '.join(avoid)}")

        # Success rate insight
        if success_patterns.get("success_rate_avg", 0) > 0.8:
            recommendations.append("High success rate - consider more aggressive evolution")
        elif success_patterns.get("success_rate_avg", 0) < 0.5:
            recommendations.append("Low success rate - need safer approach")

        return " | ".join(recommendations) if recommendations else "No clear pattern - continue experimenting"

    def get_strategy_performance_summary(self) -> Dict:
        """Get a summary of strategy performance over time"""
        if not self.strategy_history:
            return {"message": "No strategy history available"}

        # Group by time periods
        weeks = defaultdict(lambda: {"successes": 0, "failures": 0, "total": 0})

        for strategy in self.strategy_history:
            timestamp = datetime.fromisoformat(strategy["timestamp"])
            week_key = timestamp.strftime("%Y-W%W")

            weeks[week_key]["total"] += 1
            if strategy.get("success_rate", 0) > 0.7:
                weeks[week_key]["successes"] += 1
            else:
                weeks[week_key]["failures"] += 1

        return {
            "total_strategies": len(self.strategy_history),
            "periods": dict(weeks),
            "overall_success_rate": sum(s.get("success_rate", 0) for s in self.strategy_history) / len(self.strategy_history)
        }

    def suggest_parameter_tuning(self, strategy_name: str) -> Dict:
        """Suggest parameter tuning for a specific strategy"""
        # Find all attempts of this strategy
        attempts = [
            s for s in self.strategy_history
            if s.get("strategy_name") == strategy_name
        ]

        if len(attempts) < 2:
            return {"message": "Insufficient data for parameter tuning"}

        # Find parameter ranges that led to success
        param_performance = defaultdict(list)

        for attempt in attempts:
            params = attempt.get("strategy_params", {})
            success = attempt.get("success_rate", 0) > 0.7

            for key, value in params.items():
                param_performance[key].append({"value": value, "success": success})

        suggestions = {}
        for param, performances in param_performance.items():
            successful_values = [p["value"] for p in performances if p["success"]]
            failed_values = [p["value"] for p in performances if not p["success"]]

            if successful_values and not failed_values:
                suggestions[param] = f"Use {successful_values[0]} (always succeeded)"
            elif failed_values and not successful_values:
                suggestions[param] = f"Avoid {failed_values[0]} (always failed)"
            elif successful_values:
                suggestions[param] = f"Try different values (currently: {set(successful_values + failed_values)}"

        return {
            "strategy": strategy_name,
            "attempts": len(attempts),
            "suggestions": suggestions
        }
