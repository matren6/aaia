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
from modules.bus import Event, EventType




class HierarchyManager:
    """Manages hierarchy of needs progression for autonomous development."""

    def __init__(self, scribe, economics, event_bus=None):
        self.scribe = scribe
        self.economics = economics
        self.event_bus = event_bus

        # Subscribe to relevant events if bus is available
        if self.event_bus:
            try:
                self.event_bus.subscribe(EventType.GOAL_COMPLETED, self._on_goal_completed)
                self.event_bus.subscribe(EventType.TOOL_CREATED, self._on_tool_created)
                # Subscribe to capability discovered and reflection completed events
                self.event_bus.subscribe(EventType.CAPABILITY_DISCOVERED, self._on_capability_discovered)
                self.event_bus.subscribe(EventType.REFLECTION_COMPLETED, self._on_capability_discovered)
            except Exception:
                pass

    def update_focus(self):
        """Update current focus tier based on needs met (Phase 3: with profitability gate)"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Get current tier focus
        cursor.execute("SELECT tier, name FROM hierarchy_of_needs WHERE current_focus=1")
        row = cursor.fetchone()
        current_tier = row[0] if row else 1
        current_tier_name = row[1] if row else "Physiological & Security Needs"

        # Check Tier 1 conditions (Physiological & Security)
        cursor.execute("SELECT value FROM system_state WHERE key='current_balance'")
        row = cursor.fetchone()
        balance = float(row[0]) if row else 0.0

        # Phase 3: Get profitability report (last 30 days)
        profitability = self.economics.get_profitability_report(days=30)
        is_profitable = profitability.get('is_profitable', False)
        net_profit = profitability.get('net_profit', 0)

        # Check system health
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Phase 3: UPDATED Tier 1 requirements
            # Must have: balance > $50, profitable operation, healthy system
            tier1_met = (
                balance > 50 and                # Minimum balance
                is_profitable and               # NET POSITIVE over 30 days
                net_profit > 10 and             # Meaningful profit margin
                memory.percent < 80 and         # Memory under control
                disk.percent < 85               # Disk space OK
            )
        except Exception:
            tier1_met = balance > 50 and is_profitable and net_profit > 10

        # Log Tier 1 status
        if current_tier == 1:
            self.scribe.log_action(
                "Tier 1 status check",
                reasoning=f"Balance: ${balance:.2f}, Profitable: {is_profitable}, Net: ${net_profit:.2f}/month",
                outcome="Met" if tier1_met else "Not met"
            )

        # Determine progression (Phase 3: with regression logic)
        new_tier = current_tier

        if current_tier == 1 and tier1_met:
            new_tier = 2
            self.scribe.log_action(
                "🎉 Hierarchy progression: Tier 1 → Tier 2",
                reasoning=f"Tier 1 needs met (profitable: ${net_profit:.2f}/month)",
                outcome="Focusing on Growth & Capability"
            )

        elif current_tier > 1 and not tier1_met:
            # Phase 3: REGRESSION - Drop back to Tier 1 if Tier 1 needs no longer met
            new_tier = 1
            reason = []
            if not is_profitable:
                reason.append("unprofitable")
            if balance <= 50:
                reason.append("low balance")
            if net_profit <= 10:
                reason.append("low profit margin")

            self.scribe.log_action(
                f"⚠️ Hierarchy regression: Tier {current_tier} → Tier 1",
                reasoning=f"Tier 1 needs lost ({', '.join(reason)}). Profitable: {is_profitable}, Net: ${net_profit:.2f}",
                outcome="Refocusing on survival"
            )

        elif current_tier == 2 and tier1_met:
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
        elif current_tier == 3 and tier1_met:
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

    def update_tier_progress(self, tier: int, delta: float):
        """Increment progress for a tier by delta (0-1 scale)."""
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT progress FROM hierarchy_of_needs WHERE tier = ?", (tier,))
            row = cursor.fetchone()
            current = float(row[0]) if row and row[0] is not None else 0.0
            new = max(0.0, min(1.0, current + delta))
            cursor.execute("UPDATE hierarchy_of_needs SET progress = ? WHERE tier = ?", (new, tier))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _on_goal_completed(self, event: Event):
        """Handle goal completion events"""
        tier = event.data.get('tier') if event and getattr(event, 'data', None) else None
        if tier:
            # Add progress when goals are completed
            self.update_tier_progress(tier, 0.1)
            try:
                self.scribe.log_action(
                    f"Tier {tier} progress updated due to goal completion",
                    "Event-driven tier progress",
                    "tier_progress"
                )
            except Exception:
                pass

    def _on_tool_created(self, event: Event):
        """Handle tool creation events"""
        # Tool creation contributes to growth (tier 2)
        try:
            self.update_tier_progress(2, 0.05)
        except Exception:
            pass

    def _on_capability_discovered(self, event: Event):
        """Handle capability discovery events"""
        try:
            self.update_tier_progress(3, 0.03)
        except Exception:
            pass
        
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


    def force_tier(self, tier: int):
        """
        Force system to specific tier (used during crisis by Phase 3).

        Args:
            tier: Tier number to force (1-4)
        """
        if tier < 1 or tier > 4:
            return

        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Clear all focus
        cursor.execute("UPDATE hierarchy_of_needs SET current_focus=0")

        # Set new focus
        cursor.execute("UPDATE hierarchy_of_needs SET current_focus=1 WHERE tier=?", (tier,))

        conn.commit()
        conn.close()

        self.scribe.log_action(
            f"Tier forced to {tier}",
            reasoning="External override (e.g., crisis response)",
            outcome=f"Tier {tier} active"
        )

    def get_tier_requirements(self, tier: int) -> Dict:
        """Get requirements to advance to next tier (Phase 3: updated for profitability)"""
        requirements = {
            1: {
                "name": "Physiological & Security Needs",
                "requirements": ["Balance > $50", "Net positive income", "Memory < 80%", "Disk < 85%"],
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
