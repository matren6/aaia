"""
Meta-Cognition Module - Higher-Order Self-Reflection

PURPOSE:
The Meta-Cognition module provides higher-order thinking about the system's
own cognition. It enables the AI to reflect on its effectiveness, track
improvements over time, and generate insights about performance patterns.
This is "thinking about thinking."

PROBLEM SOLVED:
Basic self-diagnosis finds problems, but meta-cognition asks:
- Are we actually improving over time?
- What's working vs what's regressing?
- What patterns exist in our performance?
- How effective are we overall?
- What should we focus on next?

Without meta-cognition, the AI can't assess its own improvement trajectory.

KEY RESPONSIBILITIES:
1. record_performance_snapshot(): Record metrics for trend analysis
2. collect_current_metrics(): Gather current performance data
3. get_performance_metrics(): Get aggregated metrics for time periods
4. reflect_on_effectiveness(): Analyze improvement/regression trends
5. generate_insights(): Use AI to interpret performance data
6. think_about_thinking(): Meta-thought on thinking process itself
7. get_recent_themes(): Extract themes from thought patterns
8. get_effectiveness_score(): Calculate overall 0-1 effectiveness

METRICS TRACKED:
- Error rate (lower is better)
- Response time
- Task completion rate
- Autonomous actions count
- Goals completed
- Evolutions executed

TREND ANALYSIS:
- Compare past week to past month
- Identify improvements, regressions, stable areas
- Generate AI insights about patterns
- Calculate overall effectiveness score

DEPENDENCIES: Scribe, Router, SelfDiagnosis
OUTPUTS: Performance analysis, effectiveness scores, insights
"""

import sqlite3
import json
from typing import Dict, List
from datetime import datetime, timedelta


class MetaCognition:
    """Higher-order thinking about system cognition and performance"""

    def __init__(self, scribe, router, diagnosis, event_bus = None):
        self.scribe = scribe
        self.router = router
        self.diagnosis = diagnosis
        self.event_bus = event_bus
        self.thought_log = []
        self.performance_history = self.load_performance_history()

    def load_performance_history(self) -> List[Dict]:
        """Load historical performance metrics"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                error_rate REAL,
                response_time REAL,
                task_completion_rate REAL,
                autonomous_actions INTEGER,
                goals_completed INTEGER,
                evolutions_executed INTEGER,
                insights_generated TEXT,
                metadata TEXT
            )
        ''')

        # Create evolution_history table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evolution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cycle_id TEXT,
                status TEXT,
                tasks_completed INTEGER,
                tasks_failed INTEGER,
                notes TEXT
            )
        ''')

        # Get last 30 days of data
        cursor.execute('''
            SELECT timestamp, error_rate, response_time, task_completion_rate,
                   autonomous_actions, goals_completed, evolutions_executed
            FROM performance_metrics
            WHERE timestamp > datetime('now', '-30 days')
            ORDER BY timestamp DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "timestamp": row[0],
                "error_rate": row[1],
                "response_time": row[2],
                "task_completion_rate": row[3],
                "autonomous_actions": row[4],
                "goals_completed": row[5],
                "evolutions_executed": row[6]
            }
            for row in rows
        ]

    def record_performance_snapshot(self, metrics: Dict = None) -> None:
        """Record a performance snapshot for trend analysis"""
        if metrics is None:
            # Collect current metrics
            metrics = self.collect_current_metrics()

        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO performance_metrics (
                timestamp, error_rate, response_time, task_completion_rate,
                autonomous_actions, goals_completed, evolutions_executed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            metrics.get("error_rate", 0),
            metrics.get("response_time", 0),
            metrics.get("task_completion_rate", 0),
            metrics.get("autonomous_actions", 0),
            metrics.get("goals_completed", 0),
            metrics.get("evolutions_executed", 0)
        ))

        conn.commit()
        conn.close()

        # Update local history
        metrics["timestamp"] = datetime.now().isoformat()
        self.performance_history.append(metrics)

        self.scribe.log_action(
            "Performance snapshot recorded",
            f"Error rate: {metrics.get('error_rate', 0):.2f}%, "
            f"Completion: {metrics.get('task_completion_rate', 0):.2f}%",
            "metrics_recorded"
        )

    def collect_current_metrics(self) -> Dict:
        """Collect current performance metrics"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Calculate error rate from last 7 days
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN outcome LIKE '%error%' OR outcome LIKE '%failed%' THEN 1 END) * 100.0 /
                NULLIF(COUNT(*), 0) as error_rate
            FROM action_log
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        error_rate_row = cursor.fetchone()
        error_rate = error_rate_row[0] if error_rate_row[0] else 0

        # Calculate task completion rate
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN outcome IN ('completed', 'executed', 'success') THEN 1 END) * 100.0 /
                NULLIF(COUNT(*), 0) as completion_rate
            FROM action_log
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        completion_row = cursor.fetchone()
        task_completion = completion_row[0] if completion_row[0] else 0

        # Count autonomous actions
        cursor.execute('''
            SELECT COUNT(*) FROM action_log
            WHERE action LIKE '%autonomous%' OR action LIKE '%scheduler%'
            AND timestamp > datetime('now', '-7 days')
        ''')
        autonomous_actions = cursor.fetchone()[0]

        # Count goals completed
        cursor.execute('''
            SELECT COUNT(*) FROM goals
            WHERE status = 'completed' AND completed_at > datetime('now', '-7 days')
        ''')
        goals_completed = cursor.fetchone()[0]

        # Count evolutions
        cursor.execute('''
            SELECT COUNT(*) FROM evolution_history
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        evolutions = cursor.fetchone()[0]

        conn.close()

        return {
            "error_rate": round(error_rate, 2),
            "response_time": 0.0,  # Would need timing data
            "task_completion_rate": round(task_completion, 2),
            "autonomous_actions": autonomous_actions,
            "goals_completed": goals_completed,
            "evolutions_executed": evolutions
        }

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
        prompt = f"""
Performance Analysis for an Autonomous AI Agent:

Past Month (30 days):
- Error Rate: {past_month.get('error_rate', 0):.2f}%
- Task Completion Rate: {past_month.get('task_completion_rate', 0):.2f}%
- Autonomous Actions: {past_month.get('autonomous_actions', 0)}
- Goals Completed: {past_month.get('goals_completed', 0)}
- Evolutions Executed: {past_month.get('evolutions_executed', 0)}

Past Week (7 days):
- Error Rate: {past_week.get('error_rate', 0):.2f}%
- Task Completion Rate: {past_week.get('task_completion_rate', 0):.2f}%
- Autonomous Actions: {past_week.get('autonomous_actions', 0)}
- Goals Completed: {past_week.get('goals_completed', 0)}
- Evolutions Executed: {past_week.get('evolutions_executed', 0)}

Based on this data, analyze:
1. What improvement strategies appear to be working?
2. What might be causing any regressions?
3. What should the system focus on next?

Response format (one insight per line, no numbering):
WORKING: [insight about what's working]
REGRESSIONS: [insight about what's not working]
NEXT_FOCUS: [recommendation for next steps]
"""
        try:
            model_name, _ = self.router.route_request("analysis", "high")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are a performance analysis expert for autonomous AI systems."
            )

            # Parse response
            insights = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and (line.startswith("WORKING:") or
                            line.startswith("REGRESSIONS:") or
                            line.startswith("NEXT_FOCUS:")):
                    insights.append(line)

            return insights if insights else ["Analysis completed - review data above"]

        except Exception as e:
            return [f"Could not generate AI insights: {str(e)}"]

    def think_about_thinking(self) -> Dict:
        """Meta-thought: Think about the thinking process itself"""
        # Log current thought patterns
        thought_pattern = {
            "timestamp": datetime.now().isoformat(),
            "thoughts_count": len(self.thought_log),
            "recent_themes": self.get_recent_themes()
        }

        self.thought_log.append(thought_pattern)

        # Analyze thinking patterns
        prompt = """
Analyze the following thought patterns from an autonomous AI system:

Previous Thoughts:
{thoughts}

Identify:
1. Recurring themes or biases
2. Potential blind spots
3. Areas for more diverse thinking

Respond with:
THEMES: [what the system thinks about most]
BLIND_SPOTS: [what might be missing]
DIVERSITY: [suggestions for more diverse thinking]
"""
        try:
            model_name, _ = self.router.route_request("analysis", "high")
            response = self.router.call_model(
                model_name,
                prompt.format(thoughts=self.thought_log[-10:]),
                system_prompt="You are a metacognition expert."
            )
            thought_pattern["analysis"] = response
        except:
            thought_pattern["analysis"] = "Analysis unavailable"

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
