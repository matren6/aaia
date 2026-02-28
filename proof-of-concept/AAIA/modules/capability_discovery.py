"""
Capability Discovery Module - Automatic Capability Identification

PURPOSE:
The Capability Discovery module automatically identifies new capabilities the
system could develop by analyzing command patterns, potential integrations,
and gaps in current functionality. It ensures the AI is always exploring
ways to expand its abilities.

PROBLEM SOLVED:
How does the AI know what new capabilities it should develop?
- Can't just randomly create tools
- Need to analyze what master actually uses
- Need to identify system gaps
- Need to find integration opportunities
- Need prioritization (not all capabilities equal)

KEY RESPONSIBILITIES:
1. discover_new_capabilities(): Find capabilities we don't have but could build
2. analyze_command_patterns(): What commands does master use most?
3. analyze_potential_integrations(): What APIs/services could we integrate?
4. identify_system_gaps(): What's missing from current system?
5. parse_capability_suggestions(): Parse AI suggestions into structured format
6. get_development_priorities(): Rank capabilities by value/complexity
7. mark_capability_developed(): Track when a capability is built

DISCOVERY SOURCES:
- Command frequency analysis (last 30 days)
- Failed actions (indicates missing capabilities)
- Potential external integrations
- System gap analysis
- AI-generated suggestions

CAPABILITY PROPERTIES:
- name: Short descriptive name
- description: What it does
- value: 1-10 importance rating
- complexity: 1-10 development difficulty
- dependencies: What else needs to be built first
- status: discovered, recommended, in_progress, developed

DEPENDENCIES: Scribe, Router, Forge
OUTPUTS: List of discovered capabilities with priorities
"""

import sqlite3
import json
from typing import Dict, List
from datetime import datetime, timedelta


class CapabilityDiscovery:
    """Discover new capabilities the system could develop"""

    def __init__(self, scribe, router, forge, event_bus=None):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.event_bus = event_bus
        self.known_capabilities = self.load_capability_knowledge()

    def load_capability_knowledge(self) -> Dict:
        """Load or initialize capability knowledge base"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capability_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capability TEXT UNIQUE NOT NULL,
                description TEXT,
                value REAL,
                complexity INTEGER,
                dependencies TEXT,
                status TEXT,
                discovered_at TEXT,
                developed_at TEXT
            )
        ''')

        # Get existing capabilities
        cursor.execute("SELECT capability, description, value, complexity, dependencies, status FROM capability_knowledge")
        rows = cursor.fetchall()
        conn.close()

        capabilities = {}
        for row in rows:
            capabilities[row[0]] = {
                "description": row[1],
                "value": row[2],
                "complexity": row[3],
                "dependencies": json.loads(row[4]) if row[4] else [],
                "status": row[5]
            }

        return capabilities

    def save_capability(self, capability: Dict) -> None:
        """Save a discovered capability to knowledge base"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO capability_knowledge (
                capability, description, value, complexity, dependencies, status, discovered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            capability.get("name", "unknown"),
            capability.get("description", ""),
            capability.get("value", 0),
            capability.get("complexity", 5),
            json.dumps(capability.get("dependencies", [])),
            capability.get("status", "discovered"),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def discover_new_capabilities(self) -> List[Dict]:
        """Discover capabilities we don't have but could develop"""
        # Analyze multiple sources
        frequent_commands = self.analyze_command_patterns()
        potential_integrations = self.analyze_potential_integrations()
        system_gaps = self.identify_system_gaps()

        # Use AI to suggest capabilities
        prompt = f"""
You are a capability planning expert for an Autonomous AI Agent.

Current System Capabilities (already developed):
{self._format_current_capabilities()}

Frequent Command Patterns (what the master uses most):
{chr(10).join(f'  - {cmd}' for cmd in frequent_commands[:10])}

Potential External Integrations (APIs/services available):
{chr(10).join(f'  - {intg}' for intg in potential_integrations[:10])}

Identified System Gaps (missing functionality):
{chr(10).join(f'  - {gap}' for gap in system_gaps[:10])}

Based on this analysis, suggest 5 new capabilities we should develop.
For each capability, provide:
1. Name (short, descriptive)
2. Description (what it does)
3. Why it's valuable (value 1-10)
4. Estimated development complexity (1-10)
5. Dependencies required (what else needs to be built first)

Format (use this exact format):
CAPABILITY_1: [name]
DESCRIPTION: [what it does]
VALUE: [1-10]
COMPLEXITY: [1-10]
DEPENDENCIES: [comma-separated list or 'none']

CAPABILITY_2: [name]
... (repeat for 5 capabilities)
"""

        try:
            model_name, _ = self.router.route_request("planning", "high")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are a capability discovery expert for autonomous AI systems."
            )

            capabilities = self.parse_capability_suggestions(response)

            # Save discovered capabilities
            for cap in capabilities:
                self.save_capability(cap)

            self.scribe.log_action(
                "Capability discovery",
                f"Discovered {len(capabilities)} new capabilities",
                "discovery_completed"
            )

            return capabilities

        except Exception as e:
            return [{"error": f"Discovery failed: {str(e)}"}]

    def _format_current_capabilities(self) -> str:
        """Format current capabilities for the prompt"""
        caps = []

        # Add forge tools
        tools = self.forge.list_tools()
        if tools:
            caps.append(f"Tool creation via Forge ({len(tools)} tools)")
        else:
            caps.append("Tool creation via Forge")

        # Add known capabilities from knowledge base
        for name, cap in self.known_capabilities.items():
            if cap.get("status") == "developed":
                caps.append(f"{name}: {cap.get('description', '')[:50]}")

        return chr(10).join(f"  - {c}" for c in caps) if caps else "  - None yet developed"

    def analyze_command_patterns(self) -> List[str]:
        """Analyze past commands for patterns"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Get most frequent commands from last 30 days
        cursor.execute('''
            SELECT action, COUNT(*) as frequency
            FROM action_log
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY action
            ORDER BY frequency DESC
            LIMIT 20
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [row[0][:100] for row in rows]  # Limit length

    def analyze_potential_integrations(self) -> List[str]:
        """Analyze potential external API/service integrations"""
        integrations = []

        # Check for common API patterns in past actions
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT action FROM action_log
            WHERE action LIKE '%api%' OR action LIKE '%http%' OR action LIKE '%request%'
            OR action LIKE '%fetch%' OR action LIKE '%web%'
            LIMIT 10
        ''')

        for row in cursor.fetchall():
            integrations.append(row[0][:50])

        conn.close()

        # Add common integrations to consider
        potential = [
            "Weather API integration",
            "Database query optimization",
            "File system operations",
            "Email/notification service",
            "Calendar integration",
            "Code execution sandbox",
            "Machine learning service",
            "Search API integration",
            "Messaging platform integration",
            "Cloud storage integration"
        ]

        return list(set(integrations + potential))[:15]

    def identify_system_gaps(self) -> List[str]:
        """Identify gaps in current system capabilities"""
        gaps = []

        # Check what's missing
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Check for failed actions (indicates missing capabilities)
        cursor.execute('''
            SELECT action, COUNT(*) as failure_count
            FROM action_log
            WHERE (outcome LIKE '%error%' OR outcome LIKE '%failed%')
            AND timestamp > datetime('now', '-30 days')
            GROUP BY action
            ORDER BY failure_count DESC
            LIMIT 10
        ''')

        for action, count in cursor.fetchall():
            if count >= 2:
                gaps.append(f"Failed: {action[:50]} (failed {count}x)")

        conn.close()

        # Add common gaps based on module check
        if not hasattr(self, 'environment_explorer'):
            gaps.append("No environment exploration capability")
        if not hasattr(self, 'intent_predictor'):
            gaps.append("No master intent prediction")
        if not hasattr(self, 'metacognition'):
            gaps.append("No meta-cognition for self-reflection")

        # Add theoretical gaps
        gaps.extend([
            "No long-term memory system",
            "No cross-session learning",
            "Limited proactive behavior",
            "No multi-agent collaboration"
        ])

        return gaps[:15]

    def parse_capability_suggestions(self, response: str) -> List[Dict]:
        """Parse AI response into structured capabilities"""
        capabilities = []
        current_cap = {}

        for line in response.strip().split('\n'):
            line = line.strip()

            if line.startswith("CAPABILITY_") and ":" in line:
                # Save previous capability
                if current_cap and "name" in current_cap:
                    capabilities.append(current_cap)

                # Start new capability
                name = line.split(":", 1)[1].strip()
                current_cap = {"name": name}

            elif line.startswith("DESCRIPTION:") and current_cap:
                current_cap["description"] = line.split(":", 1)[1].strip()

            elif line.startswith("VALUE:") and current_cap:
                try:
                    current_cap["value"] = int(line.split(":", 1)[1].strip())
                except:
                    current_cap["value"] = 5

            elif line.startswith("COMPLEXITY:") and current_cap:
                try:
                    current_cap["complexity"] = int(line.split(":", 1)[1].strip())
                except:
                    current_cap["complexity"] = 5

            elif line.startswith("DEPENDENCIES:") and current_cap:
                deps = line.split(":", 1)[1].strip()
                current_cap["dependencies"] = [d.strip() for d in deps.split(",") if d.strip() and d.strip() != "none"]

        # Don't forget the last capability
        if current_cap and "name" in current_cap:
            capabilities.append(current_cap)

        return capabilities

    def get_development_priorities(self) -> List[Dict]:
        """Get prioritized list of capabilities to develop"""
        # Load all discovered capabilities
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT capability, description, value, complexity, dependencies, status
            FROM capability_knowledge
            WHERE status IN ('discovered', 'recommended', 'in_progress')
            ORDER BY value DESC, complexity ASC
            LIMIT 10
        ''')

        rows = cursor.fetchall()
        conn.close()

        priorities = []
        for row in rows:
            # Calculate priority score (higher value, lower complexity = higher priority)
            priority_score = row[2] / max(row[3], 1) if row[2] and row[3] else 0

            priorities.append({
                "name": row[0],
                "description": row[1],
                "value": row[2],
                "complexity": row[3],
                "dependencies": json.loads(row[4]) if row[4] else [],
                "status": row[5],
                "priority_score": round(priority_score, 2)
            })

        # Sort by priority score
        priorities.sort(key=lambda x: x["priority_score"], reverse=True)

        return priorities

    def mark_capability_developed(self, capability_name: str) -> None:
        """Mark a capability as developed"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE capability_knowledge
            SET status = 'developed', developed_at = ?
            WHERE capability = ?
        ''', (datetime.now().isoformat(), capability_name))

        conn.commit()
        conn.close()

        self.scribe.log_action(
            "Capability developed",
            f"{capability_name} marked as developed",
            "capability_developed"
        )
