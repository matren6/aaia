"""
Meta-cognition Module - Reflective Analysis and Insight Generation

PURPOSE:
Provide metacognitive analysis of system performance and internal thought
patterns to guide evolution and improvements.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
from modules.container import DependencyError


class MetaCognition:
    """Meta-cognition: Analyze internal thinking and performance"""

    def __init__(self, scribe, router, event_bus=None, prompt_manager=None):
        self.scribe = scribe
        self.router = router
        self.event_bus = event_bus
        self.thought_log = []
        self.performance_history = []
        # PromptManager must be provided via DI
        self.prompt_manager = prompt_manager
        if self.prompt_manager is None:
            raise DependencyError("PromptManager is required and must be provided via the DI container to MetaCognition")

        # Probe required prompts
        required = ("metacognition_reflection", "thinking_patterns")
        missing = []
        for name in required:
            try:
                self.prompt_manager.get_prompt_raw(name)
            except Exception:
                missing.append(name)

        if missing:
            raise DependencyError(f"Required prompt templates missing: {', '.join(missing)}")

    def record_performance_snapshot(self):
        """Record a lightweight performance snapshot for trending"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "error_rate": self.scribe.get_economic_status().get("balance", 0),
            "task_completion_rate": 0,
            "autonomous_actions": 0
        }
        self.performance_history.append(snapshot)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        return snapshot

    def get_performance_metrics(self, days: int = 7) -> Dict:
        """Get aggregated performance metrics for a time period"""
        # Use cached history
        cutoff = datetime.now() - timedelta(days=days)
        relevant = [
            m for m in self.performance_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]

        if not relevant:
            return {
                "error_rate": 0,
                "response_time": 0,
                "task_completion_rate": 0,
                "autonomous_actions": 0,
                "goals_completed": 0,
                "evolutions_executed": 0
            }

        return {
            "error_rate": sum(m.get("error_rate", 0) for m in relevant) / len(relevant),
            "response_time": sum(m.get("response_time", 0) for m in relevant) / len(relevant),
            "task_completion_rate": sum(m.get("task_completion_rate", 0) for m in relevant) / len(relevant),
            "autonomous_actions": sum(m.get("autonomous_actions", 0) for m in relevant),
            "goals_completed": sum(m.get("goals_completed", 0) for m in relevant),
            "evolutions_executed": sum(m.get("evolutions_executed", 0) for m in relevant)
        }

    def reflect_on_effectiveness(self) -> Dict:
        """Analyze: Are we improving? What works? What doesn't?"""
        # Get performance data
        past_month = self.get_performance_metrics(days=30)
        past_week = self.get_performance_metrics(days=7)

        improvement_areas = []
        regression_areas = []
        stable_areas = []

        # Analyze error rate
        if past_month.get("error_rate", 0) > 0:
            if past_week["error_rate"] < past_month["error_rate"] * 0.9:
                improvement_areas.append(
                    f"error_rate: Improved by {int((1 - past_week['error_rate']/past_month['error_rate'])*100)}%"
                )
            elif past_week["error_rate"] > past_month["error_rate"] * 1.1:
                regression_areas.append(
                    f"error_rate: Worsened by {int((past_week['error_rate']/past_month['error_rate']-1)*100)}%"
                )
            else:
                stable_areas.append("error_rate: Stable")

        # Analyze task completion
        if past_month.get("task_completion_rate", 0) > 0:
            if past_week["task_completion_rate"] > past_month["task_completion_rate"] * 1.1:
                improvement_areas.append(
                    f"task_completion: Improved by {int((past_week['task_completion_rate']/past_month['task_completion_rate']-1)*100)}%"
                )
            elif past_week["task_completion_rate"] < past_month["task_completion_rate"] * 0.9:
                regression_areas.append(
                    f"task_completion: Worsened by {int((1 - past_week['task_completion_rate']/past_month['task_completion_rate'])*100)}%"
                )
            else:
                stable_areas.append("task_completion: Stable")

        # Analyze autonomous activity
        if past_week.get("autonomous_actions", 0) > past_month.get("autonomous_actions", 0) / 4:
            improvement_areas.append("autonomous_activity: Increased engagement")

        # Generate AI insights
        insights = self.generate_insights(past_month, past_week)

        result = {
            "timestamp": datetime.now().isoformat(),
            "period_comparison": {
                "past_month": past_month,
                "past_week": past_week
            },
            "improvements": improvement_areas,
            "regressions": regression_areas,
            "stable": stable_areas,
            "insights": insights
        }

        # Log reflection
        self.scribe.log_action(
            "Meta-cognition reflection",
            f"Found {len(improvement_areas)} improvements, {len(regression_areas)} regressions",
            "reflection_completed"
        )

        return result

    def generate_insights(self, past_month: Dict, past_week: Dict) -> List[str]:
        """Use AI to generate insights from performance data"""
        # Use centralized prompt via PromptManager only
        prompt_data = self.prompt_manager.get_prompt(
            "metacognition_reflection",
            past_month=json.dumps(past_month, indent=2),
            past_week=json.dumps(past_week, indent=2)
        )
        model_name, _ = self.router.route_request("analysis", "high")
        response = self.router.call_model(
            model_name,
            prompt_data["prompt"],
            prompt_data.get("system_prompt", "")
        )

        insights = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and (line.startswith("WORKING:") or
                        line.startswith("REGRESSIONS:") or
                        line.startswith("NEXT_FOCUS:")):
                insights.append(line)

        return insights if insights else ["Analysis completed - review data above"]

    def think_about_thinking(self) -> Dict:
        """Meta-thought: Think about the thinking process itself"""
        # Log current thought patterns
        thought_pattern = {
            "timestamp": datetime.now().isoformat(),
            "thoughts_count": len(self.thought_log),
            "recent_themes": self.get_recent_themes()
        }

        self.thought_log.append(thought_pattern)

        # Use centralized prompt via PromptManager only
        thoughts_text = json.dumps(self.thought_log[-10:], indent=2)
        prompt_data = self.prompt_manager.get_prompt(
            "thinking_patterns",
            thoughts=thoughts_text
        )
        model_name, _ = self.router.route_request("analysis", "high")
        response = self.router.call_model(
            model_name,
            prompt_data["prompt"],
            prompt_data.get("system_prompt", "")
        )
        thought_pattern["analysis"] = response

        return thought_pattern

    def get_recent_themes(self) -> List[str]:
        """Extract themes from recent thoughts"""
        themes = []
        for thought in self.thought_log[-10:]:
            if "analysis" in thought:
                themes.append(thought["analysis"][:50])
        return themes[:5]

    def get_effectiveness_score(self) -> float:
        """Calculate overall effectiveness score (0-1)"""
        week_metrics = self.get_performance_metrics(days=7)

        # Calculate weighted score
        error_score = 1.0 - min(week_metrics.get("error_rate", 0) / 100, 1.0)
        completion_score = week_metrics.get("task_completion_rate", 0) / 100

        effectiveness = (error_score * 0.4) + (completion_score * 0.6)

        return round(effectiveness, 2)
