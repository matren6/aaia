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
from datetime import datetime


class GoalSystem:
    """Autonomous goal generation and tracking system."""

    def __init__(self, scribe, router, economics):
        self.scribe = scribe
        self.router = router
        self.economics = economics
        self.active_goals = []
        self.completed_goals = []
        self._init_database()

    def _init_database(self):
        """Initialize goals database table"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_text TEXT NOT NULL,
                goal_type TEXT,
                priority INTEGER DEFAULT 3,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                progress INTEGER DEFAULT 0,
                expected_benefit TEXT,
                estimated_effort TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def generate_goals(self) -> List[str]:
        """Autonomously generate goals based on current state"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        # Analyze recent actions for patterns
        cursor.execute("""
            SELECT action, COUNT(*) as count 
            FROM action_log 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY action 
            ORDER BY count DESC 
            LIMIT 10
        """)
        frequent_actions = cursor.fetchall()
        conn.close()
        
        # Generate goals based on patterns
        goals = []
        
        if frequent_actions:
            actions_text = "\n".join(f"- {action}: {count} times" for action, count in frequent_actions)
            
            # Use AI to suggest goals
            prompt = f"""
Based on my recent frequent actions (last 7 days):
{actions_text}

Suggest 3 practical, achievable goals that would:
1. Improve efficiency
2. Address recurring pain points
3. Create new value

For each goal, estimate:
- Time to implement
- Expected benefit
- Required resources

Response format:
1. GOAL: [goal name]
BENEFIT: [expected benefit]
EFFORT: [estimated effort]
2. GOAL: [goal name]
BENEFIT: [expected benefit]
EFFORT: [estimated effort]
3. GOAL: [goal name]
BENEFIT: [expected benefit]
EFFORT: [estimated effort]
"""
            try:
                model_name, _ = self.router.route_request("planning", "high")
                response = self.router.call_model(
                    model_name,
                    prompt,
                    system_prompt="You are a strategic planner. Suggest practical, valuable goals."
                )
                goals.append(response)
                
                # Parse and store goals
                self._parse_and_store_goals(response)
                
            except Exception as e:
                goals.append(f"Goal generation failed: {e}")
        
        return goals

    def _parse_and_store_goals(self, response: str):
        """Parse AI response and store goals in database"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
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
            self._save_goal(cursor, current_goal, current_benefit, current_effort)
        
        conn.commit()
        conn.close()

    def _save_goal(self, cursor, goal_text: str, benefit: str, effort: str):
        """Save a single goal to database"""
        cursor.execute("""
            INSERT INTO goals (goal_text, goal_type, priority, status, expected_benefit, estimated_effort)
            VALUES (?, ?, ?, 'active', ?, ?)
        """, (goal_text, 'auto_generated', 3, benefit, effort))

    def get_active_goals(self) -> List[Dict]:
        """Get all active goals"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, goal_text, goal_type, priority, created_at, progress, expected_benefit, estimated_effort
            FROM goals
            WHERE status = 'active'
            ORDER BY priority, created_at
        """)
        
        goals = []
        for row in cursor.fetchall():
            goals.append({
                "id": row[0],
                "goal_text": row[1],
                "goal_type": row[2],
                "priority": row[3],
                "created_at": row[4],
                "progress": row[5],
                "expected_benefit": row[6],
                "estimated_effort": row[7]
            })
        
        conn.close()
        return goals

    def complete_goal(self, goal_id: int):
        """Mark a goal as completed"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE goals 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (goal_id,))
        
        conn.commit()
        conn.close()
        
        self.scribe.log_action(
            f"Goal completed: {goal_id}",
            "Goal marked as completed",
            "goal_completed"
        )

    def update_progress(self, goal_id: int, progress: int):
        """Update goal progress"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE goals 
            SET progress = ?
            WHERE id = ?
        """, (progress, goal_id))
        
        conn.commit()
        conn.close()

    def delete_goal(self, goal_id: int):
        """Delete a goal"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        
        conn.commit()
        conn.close()

    def get_goal_summary(self) -> Dict:
        """Get summary of all goals"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'active'")
        active_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'completed'")
        completed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM goals WHERE goal_type = 'auto_generated'")
        auto_generated = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "active": active_count,
            "completed": completed_count,
            "auto_generated": auto_generated
        }
