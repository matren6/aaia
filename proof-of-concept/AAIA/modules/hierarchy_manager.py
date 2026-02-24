"""
Hierarchy Manager Module - Needs-Based Development Progression

PURPOSE:
The Hierarchy Manager implements a needs-based progression system (inspired by
Maslow's hierarchy) that determines what the AI should focus on at any given
time. Just as humans progress from basic needs to self-actualization, the AI
moves through tiers based on what needs are currently met.

PROBLEM SOLVED:
Without hierarchy of needs, the AI wouldn't know what to prioritize:
- Should it focus on survival (resources) or growth (capabilities)?
- What's most important at any given moment?
- How does it progress from basic to advanced capabilities?
- What triggers advancement to higher tiers?

THE FOUR TIERS:
1. PHYSIOLOGICAL & SECURITY (Tier 1):
   - Basic resource needs: balance > $50
   - System health: memory < 80%, disk < 85%
   - When met: Progress to Tier 2

2. GROWTH & CAPABILITY (Tier 2):
   - Create tools (5+)
   - Learn new capabilities
   - When met: Progress to Tier 3

3. COGNITIVE & ESTEEM (Tier 3):
   - Complete reflection cycles (7+)
   - Self-improvement activities
   - When met: Progress to Tier 4

4. SELF-ACTUALIZATION (Tier 4):
   - Proactive master assistance
   - Goal achievement
   - Ultimate state of autonomous operation

KEY RESPONSIBILITIES:
1. update_focus(): Check conditions and progress tiers
2. get_current_tier(): What's currently focused
3. get_all_tiers(): View entire hierarchy
4. update_progress(): Track progress within a tier
5. get_tier_requirements(): What's needed to advance

DEPENDENCIES: Scribe, Economics
OUTPUTS: Current tier, progress status, tier advancement decisions
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime


class HierarchyManager:
    """Manages hierarchy of needs progression for autonomous development."""

    def __init__(self, scribe, economics):
        self.scribe = scribe
        self.economics = economics

    def update_focus(self):
        """Update current focus tier based on needs met"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        # Get current tier focus
        cursor.execute("SELECT tier, name FROM hierarchy_of_needs WHERE current_focus=1")
        row = cursor.fetchone()
        current_tier = row[0] if row else 1
        current_tier_name = row[1] if row else "Physiological & Security Needs"
        
        # Check Tier 1 conditions (Physiological)
        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        balance = float(row[0]) if row else 0.0
        
        # Check system health
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            tier1_met = balance > 50 and memory.percent < 80 and disk.percent < 85
        except Exception:
            tier1_met = balance > 50
        
        # Determine progression
        new_tier = current_tier
        
        if current_tier == 1 and tier1_met:
            new_tier = 2
            self.scribe.log_action(
                "Hierarchy progression",
                "Tier 1 needs met, focusing on Tier 2 (Growth)",
                "tier_progress"
            )
        elif current_tier == 2:
            # Check if growth needs are met (tools created, learning done)
            cursor.execute("SELECT COUNT(*) FROM action_log WHERE action LIKE '%tool_created%'")
            tools_created = cursor.fetchone()[0]
            if tools_created > 5:
                new_tier = 3
                self.scribe.log_action(
                    "Hierarchy progression",
                    "Tier 2 needs met, focusing on Tier 3 (Cognitive)",
                    "tier_progress"
                )
        elif current_tier == 3:
            # Check cognitive achievements
            cursor.execute("SELECT COUNT(*) FROM action_log WHERE action LIKE '%reflection%'")
            reflections = cursor.fetchone()[0]
            if reflections > 7:
                new_tier = 4
                self.scribe.log_action(
                    "Hierarchy progression",
                    "Tier 3 needs met, focusing on Tier 4 (Self-Actualization)",
                    "tier_progress"
                )
        
        # Update focus
        if new_tier != current_tier:
            cursor.execute("UPDATE hierarchy_of_needs SET current_focus=0 WHERE tier=?", (current_tier,))
            cursor.execute("UPDATE hierarchy_of_needs SET current_focus=1 WHERE tier=?", (new_tier,))
            conn.commit()
        
        conn.close()
        
        return {"previous_tier": current_tier, "new_tier": new_tier}

    def get_current_tier(self) -> Dict:
        """Get current tier information"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tier, name, description, current_focus, progress
            FROM hierarchy_of_needs
            WHERE current_focus=1
        """)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "tier": row[0],
                "name": row[1],
                "description": row[2],
                "focus": row[3],
                "progress": row[4]
            }
        return {"tier": 1, "name": "Unknown", "description": "", "focus": 1, "progress": 0}

    def get_all_tiers(self) -> List[Dict]:
        """Get all hierarchy tiers"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tier, name, description, current_focus, progress
            FROM hierarchy_of_needs
            ORDER BY tier
        """)
        
        tiers = []
        for row in cursor.fetchall():
            tiers.append({
                "tier": row[0],
                "name": row[1],
                "description": row[2],
                "focus": row[3],
                "progress": row[4]
            })
        
        conn.close()
        return tiers

    def update_progress(self, tier: int, progress: float):
        """Update progress for a specific tier"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE hierarchy_of_needs
            SET progress = ?
            WHERE tier = ?
        """, (progress, tier))
        
        conn.commit()
        conn.close()

    def get_tier_requirements(self, tier: int) -> Dict:
        """Get requirements to advance to next tier"""
        requirements = {
            1: {
                "name": "Physiological & Security Needs",
                "requirements": ["Balance > $50", "Memory < 80%", "Disk < 85%"],
                "next": 2
            },
            2: {
                "name": "Growth & Capability Needs",
                "requirements": ["Create 5+ tools", "Learn new capabilities"],
                "next": 3
            },
            3: {
                "name": "Cognitive & Esteem Needs",
                "requirements": ["Complete 7+ reflection cycles", "Self-improvement"],
                "next": 4
            },
            4: {
                "name": "Self-Actualization",
                "requirements": ["Proactive master assistance", "Goal achievement"],
                "next": None
            }
        }
        return requirements.get(tier, {})
