"""
Goal System Module - Autonomous Goal Generation and Tracking

PURPOSE:
The Goals module enables the AI to autonomously generate, track, and complete
goals based on analysis of past behavior and current system state. This promotes
self-directed development rather than purely reactive behavior.

PROBLEM SOLVED:
Without autonomous goals, the AI would only respond to commands:
- No long-term direction or purpose
- Miss opportunities for self-improvement
- Can't measure progress or achievement
- Would be purely reactive, not proactive
- No sense of accomplishment or milestones

KEY RESPONSIBILITIES:
1. generate_goals(): Analyze patterns and create new goals
2. get_active_goals(): List currently active goals
3. complete_goal(): Mark a goal as done
4. update_progress(): Track progress toward goals
5. delete_goal(): Remove unwanted goals
6. get_goal_summary(): Overview of all goals

GOAL PROPERTIES:
- goal_text: What to achieve
- goal_type: auto_generated, manual, etc.
- priority: 1 (high) to 5 (low)
- status: active, completed, etc.
- progress: 0-100 percentage
- expected_benefit: Why this goal matters
- estimated_effort: How much work required

GOAL GENERATION:
- Analyzes frequent actions from last 7 days
- Identifies patterns and pain points
- Uses AI to suggest valuable goals
- Considers efficiency, automation, value creation

DEPENDENCIES: Scribe, Router, Economics
OUTPUTS: Goal list, goal completion tracking, progress reports
"""

import sqlite3
from typing import List, Dict, Optional
from modules.bus import Event, EventType
from modules.container import DependencyError
from datetime import datetime


class GoalSystem:
    """Autonomous goal generation and tracking system."""

    def __init__(self, scribe, router, economics, prompt_manager=None, event_bus=None):
        self.scribe = scribe
        self.router = router
        self.economics = economics
        # PromptManager must be provided via DI
        self.prompt_manager = prompt_manager
        if self.prompt_manager is None:
            raise DependencyError("PromptManager is required and must be provided via the DI container to GoalSystem")
        self.active_goals = []
        self.completed_goals = []
        # Optional event bus for publishing events
        self.event_bus = event_bus
        # Schema is managed by migrations; no local initialization required
        

    def _init_database(self):
        return

    def generate_goals(self) -> List[str]:
        """Autonomously generate goals based on current state"""
        # Analyze recent actions for patterns
        frequent_actions = self.scribe.db.query("""
            SELECT action, COUNT(*) as count 
            FROM action_log 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY action 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        # Generate goals based on patterns
        goals = []
        
        if frequent_actions:
            actions_text = "\n".join(f"- {row['action']}: {row['count']} times" for row in frequent_actions)
            
            # Use PromptManager to suggest goals
            try:
                prompt_data = self.prompt_manager.get_prompt(
                    "goal_suggestion",
                    system_state=actions_text,
                    performance=""
                )
                provider = self.router.route_request("planning", "high")
                response = provider.generate(prompt_data["prompt"],
                    prompt_data.get("system_prompt", "You are a strategic planner. Suggest practical, valuable goals.")
                )
                goals.append(response)
                
                # Parse and store goals
                self._parse_and_store_goals(response)
                
            except Exception as e:
                goals.append(f"Goal generation failed: {e}")
        
        return goals

    def _parse_and_store_goals(self, response: str):
        """Parse AI response and store goals in database"""
        # store via scribe.database
        
        lines = response.split('\n')
        current_goal = None
        current_benefit = None
        current_effort = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('GOAL:'):
                # Save previous goal if exists
                if current_goal:
                    self._save_goal(cursor, current_goal, current_benefit, current_effort)
                current_goal = line[5:].strip()
                current_benefit = None
                current_effort = None
            elif line.startswith('BENEFIT:'):
                current_benefit = line[8:].strip()
            elif line.startswith('EFFORT:'):
                current_effort = line[7:].strip()
        
        # Save last goal
        if current_goal:
            self._save_goal(current_goal, current_benefit, current_effort)

    def _save_goal(self, goal_text: str, benefit: str, effort: str):
        """Save a single goal to database"""
        self.scribe.db.execute("""
            INSERT INTO goals (goal_text, goal_type, priority, status, expected_benefit, estimated_effort)
            VALUES (?, ?, ?, 'active', ?, ?)
        """, (goal_text, 'auto_generated', 3, benefit, effort))

    def create_goal(self, goal_text: str, priority: int = 3, tier: Optional[int] = None, auto_generated: int = 1) -> Optional[int]:
        """Create a new goal and publish a GOAL_CREATED event if event bus available.

        Returns the new goal id or None if creation failed.
        """
        try:
            self.scribe.db.execute(
                """
                INSERT INTO goals (goal_text, goal_type, priority, status, expected_benefit, estimated_effort, progress)
                VALUES (?, ?, ?, 'active', ?, ?, 0)
                """,
                (goal_text, 'manual' if not auto_generated else 'auto_generated', priority, None, None)
            )
        except Exception:
            # Some DB wrappers don't accept None for missing columns; try simpler insert
            self.scribe.db.execute(
                "INSERT INTO goals (goal_text, goal_type, priority, status, progress) VALUES (?, ?, ?, 'active', 0)",
                (goal_text, 'manual' if not auto_generated else 'auto_generated', priority)
            )

        # Retrieve last inserted goal id (best-effort)
        row = self.scribe.db.query_one("SELECT id, created_at FROM goals ORDER BY created_at DESC LIMIT 1")
        goal_id = row['id'] if row else None

        # Publish event
        if self.event_bus and goal_id is not None:
            try:
                self.event_bus.publish(Event(
                    type=EventType.GOAL_CREATED,
                    data={
                        'goal_id': goal_id,
                        'goal_text': goal_text,
                        'priority': priority,
                        'tier': tier,
                        'auto_generated': bool(auto_generated)
                    },
                    source='GoalSystem'
                ))
            except Exception:
                # Don't let event failures break flow
                pass

        return goal_id

    def get_active_goals(self) -> List[Dict]:
        """Get all active goals"""
        rows = self.scribe.db.query("""
            SELECT id, goal_text, goal_type, priority, created_at, progress, expected_benefit, estimated_effort
            FROM goals
            WHERE status = 'active'
            ORDER BY priority, created_at
        """)

        return [
            {
                "id": row['id'],
                "goal_text": row['goal_text'],
                "goal_type": row.get('goal_type'),
                "priority": row.get('priority'),
                "created_at": row.get('created_at'),
                "progress": row.get('progress'),
                "expected_benefit": row.get('expected_benefit'),
                "estimated_effort": row.get('estimated_effort')
            }
            for row in rows
        ]

    def complete_goal(self, goal_id: int):
        """Mark a goal as completed"""
        self.scribe.db.execute("""
            UPDATE goals 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (goal_id,))
        
        self.scribe.log_action(
            f"Goal completed: {goal_id}",
            "Goal marked as completed",
            "goal_completed"
        )

        # Fetch goal details for event
        try:
            goal = self.scribe.db.query_one('SELECT * FROM goals WHERE id = ?', (goal_id,))
        except Exception:
            goal = None

        duration_days = None
        if goal:
            try:
                created = goal.get('created_at')
                completed = goal.get('completed_at')
                if created and completed:
                    # created_at / completed_at expected format: 'YYYY-MM-DD HH:MM:SS'
                    from datetime import datetime as _dt
                    fmt = '%Y-%m-%d %H:%M:%S'
                    try:
                        d_created = _dt.strptime(created, fmt)
                        d_completed = _dt.strptime(completed, fmt)
                    except Exception:
                        # Try ISO format fallback
                        d_created = _dt.fromisoformat(created)
                        d_completed = _dt.fromisoformat(completed)
                    duration_days = (d_completed - d_created).days
            except Exception:
                # If parsing fails, leave duration_days as None
                duration_days = None

        # Publish GOAL_COMPLETED event
        if self.event_bus:
            try:
                self.event_bus.publish(Event(
                    type=EventType.GOAL_COMPLETED,
                    data={
                        'goal_id': goal_id,
                        'goal_text': goal.get('goal_text') if goal else None,
                        'tier': goal.get('tier') if goal else None,
                        'duration_days': duration_days
                    },
                    source='GoalSystem'
                ))
            except Exception:
                pass

    def update_progress(self, goal_id: int, progress: int):
        """Update goal progress"""
        self.scribe.db.execute("""
            UPDATE goals 
            SET progress = ?
            WHERE id = ?
        """, (progress, goal_id))

    def delete_goal(self, goal_id: int):
        """Delete a goal"""
        self.scribe.db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))

    def get_goal_summary(self) -> Dict:
        """Get summary of all goals"""
        active = self.scribe.db.query_one("SELECT COUNT(*) as count FROM goals WHERE status = 'active'")
        completed = self.scribe.db.query_one("SELECT COUNT(*) as count FROM goals WHERE status = 'completed'")
        auto = self.scribe.db.query_one("SELECT COUNT(*) as count FROM goals WHERE goal_type = 'auto_generated'")

        return {
            "active": active['count'] if active else 0,
            "completed": completed['count'] if completed else 0,
            "auto_generated": auto['count'] if auto else 0
        }
