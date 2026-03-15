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
from modules.container import DependencyError


class CapabilityDiscovery:
    """Discover new capabilities the system could develop"""

    def __init__(self, scribe, router, forge, event_bus=None, prompt_manager=None):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.event_bus = event_bus
        # PromptManager must be provided via DI
        self.prompt_manager = prompt_manager
        if self.prompt_manager is None:
            raise DependencyError("PromptManager is required and must be provided via the DI container to CapabilityDiscovery")
        self.known_capabilities = self.load_capability_knowledge()

    def load_capability_knowledge(self) -> Dict:
        """Load or initialize capability knowledge base"""
        # Use a local capability_knowledge table for historical reasons; create if missing
        try:
            self.scribe.db.execute('''
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
        except Exception:
            pass

        rows = self.scribe.db.query("SELECT capability, description, value, complexity, dependencies, status FROM capability_knowledge")

        capabilities = {}
        for row in rows:
            capabilities[row['capability']] = {
                "description": row['description'],
                "value": row['value'],
                "complexity": row['complexity'],
                "dependencies": json.loads(row['dependencies']) if row['dependencies'] else [],
                "status": row['status']
            }

        return capabilities

    def save_capability(self, capability: Dict) -> None:
        """Save a discovered capability to knowledge base"""
        self.scribe.db.execute('''
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

    def discover_new_capabilities(self) -> List[Dict]:
        """Discover capabilities we don't have but could develop"""
        # Analyze multiple sources
        frequent_commands = self.analyze_command_patterns()
        potential_integrations = self.analyze_potential_integrations()
        system_gaps = self.identify_system_gaps()

        # Use PromptManager to suggest capabilities
        try:
            # Build a combined capabilities summary to pass to the prompt template
            combined = (
                f"Current Capabilities:\n{self._format_current_capabilities()}\n\n"
                f"Frequent Commands:\n{chr(10).join(f'  - {cmd}' for cmd in frequent_commands[:10])}\n\n"
                f"Potential Integrations:\n{chr(10).join(f'  - {intg}' for intg in potential_integrations[:10])}\n\n"
                f"Identified Gaps:\n{chr(10).join(f'  - {gap}' for gap in system_gaps[:10])}"
            )

            prompt_data = self.prompt_manager.get_prompt(
                "capability_analysis",
                capabilities=combined
            )

            provider = self.router.route_request("planning", "high")
            response = provider.generate(prompt_data["prompt"],
                prompt_data.get("system_prompt", "You are a capability discovery expert for autonomous AI systems.")
            )

            capabilities = self.parse_capability_suggestions(response)

            # Save discovered capabilities and publish discovery events
            for cap in capabilities:
                self.save_capability(cap)
                # Publish capability discovered event for each capability
                if self.event_bus:
                    try:
                        from modules.bus import Event, EventType
                        self.event_bus.publish(Event(
                            type=EventType.CAPABILITY_DISCOVERED,
                            data=cap,
                            source='CapabilityDiscovery'
                        ))
                    except Exception:
                        pass

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
        rows = self.scribe.db.query('''
            SELECT action, COUNT(*) as frequency
            FROM action_log
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY action
            ORDER BY frequency DESC
            LIMIT 20
        ''')

        return [row['action'][:100] for row in rows]

    def analyze_potential_integrations(self) -> List[str]:
        """Analyze potential external API/service integrations"""
        integrations = []

        # Check for common API patterns in past actions
        rows = self.scribe.db.query('''
            SELECT DISTINCT action FROM action_log
            WHERE action LIKE '%api%' OR action LIKE '%http%' OR action LIKE '%request%'
            OR action LIKE '%fetch%' OR action LIKE '%web%'
            LIMIT 10
        ''')

        for row in rows:
            integrations.append(row['action'][:50])

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
        rows = self.scribe.db.query('''
            SELECT action, COUNT(*) as failure_count
            FROM action_log
            WHERE (outcome LIKE '%error%' OR outcome LIKE '%failed%')
            AND timestamp > datetime('now', '-30 days')
            GROUP BY action
            ORDER BY failure_count DESC
            LIMIT 10
        ''')

        for row in rows:
            action = row['action']
            count = row['failure_count']
            if count >= 2:
                gaps.append(f"Failed: {action[:50]} (failed {count}x)")

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
        rows = self.scribe.db.query('''
            SELECT capability, description, value, complexity, dependencies, status
            FROM capability_knowledge
            WHERE status IN ('discovered', 'recommended', 'in_progress')
            ORDER BY value DESC, complexity ASC
            LIMIT 10
        ''')

        priorities = []
        for row in rows:
            priority_score = row['value'] / max(row['complexity'], 1) if row['value'] and row['complexity'] else 0

            priorities.append({
                "name": row['capability'],
                "description": row['description'],
                "value": row['value'],
                "complexity": row['complexity'],
                "dependencies": json.loads(row['dependencies']) if row['dependencies'] else [],
                "status": row['status'],
                "priority_score": round(priority_score, 2)
            })

        priorities.sort(key=lambda x: x["priority_score"], reverse=True)

        return priorities

    def mark_capability_developed(self, capability_name: str) -> None:
        """Mark a capability as developed"""
        self.scribe.db.execute('''
            UPDATE capability_knowledge
            SET status = 'developed', developed_at = ?
            WHERE capability = ?
        ''', (datetime.now().isoformat(), capability_name))

        self.scribe.log_action(
            "Capability developed",
            f"{capability_name} marked as developed",
            "capability_developed"
        )
