"""
Self-Diagnosis Module

Comprehensive system self-assessment and improvement opportunity identification.
Enables the AI to analyze its own performance, identify bottlenecks, and find
areas for self-improvement.
"""

import sqlite3
import ast
import importlib
import inspect
import sys
from typing import Dict, List, Tuple
from datetime import datetime


class SelfDiagnosis:
    """System self-diagnosis and assessment module."""

    def __init__(self, scribe, router, forge):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.diagnosis_interval = 3600  # 1 hour in seconds

    def perform_full_diagnosis(self) -> Dict:
        """Comprehensive system self-assessment"""
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "modules": self.assess_modules(),
            "performance": self.assess_performance(),
            "capabilities": self.assess_capabilities(),
            "bottlenecks": self.identify_bottlenecks(),
            "improvement_opportunities": self.find_improvement_opportunities(),
            "recommended_actions": []
        }

        # Generate recommendations
        diagnosis["recommended_actions"] = self.generate_improvement_plan(diagnosis)

        # Log diagnosis
        self.scribe.log_action(
            "System self-diagnosis",
            f"Found {len(diagnosis['improvement_opportunities'])} opportunities",
            "diagnosis_completed"
        )

        return diagnosis

    def assess_modules(self) -> Dict:
        """Assess health and functionality of all modules"""
        modules_to_check = [
            "scribe", "mandates", "economics", 
            "dialogue", "router", "forge", "scheduler",
            "goals", "hierarchy_manager"
        ]
        assessment = {}

        for module_name in modules_to_check:
            try:
                module = importlib.import_module(f"modules.{module_name}")
                # Get all callable attributes (functions and classes)
                callables = [m for m in dir(module) if not m.startswith('_') and 
                            callable(getattr(module, m))]
                
                assessment[module_name] = {
                    "status": "healthy",
                    "methods": len(callables),
                    "last_error": None
                }
            except Exception as e:
                assessment[module_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return assessment

    def assess_performance(self) -> Dict:
        """Analyze system performance metrics"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        # Get action statistics
        cursor.execute("""
            SELECT 
                AVG(LENGTH(action)) as avg_action_length,
                AVG(LENGTH(reasoning)) as avg_reasoning_length,
                COUNT(*) as total_actions,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM action_log
        """)
        stats = cursor.fetchone()

        # Get error rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN outcome LIKE '%error%' THEN 1 END) as error_count,
                COUNT(*) as total_actions
            FROM action_log
        """)
        errors = cursor.fetchone()

        error_rate = (errors[0] / errors[1]) * 100 if errors[1] > 0 else 0

        # Get recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM action_log 
            WHERE timestamp > datetime('now', '-1 hour')
        """)
        recent_actions = cursor.fetchone()[0]

        conn.close()

        return {
            "avg_action_length": round(stats[0] or 0, 2),
            "avg_reasoning_length": round(stats[1] or 0, 2),
            "total_actions": stats[2] or 0,
            "active_days": stats[3] or 0,
            "error_rate": round(error_rate, 2),
            "recent_actions_1h": recent_actions
        }

    def assess_capabilities(self) -> Dict:
        """Assess current AI capabilities"""
        # Check available tools
        tools = self.forge.list_tools()
        
        # Check scheduler tasks
        from modules.scheduler import AutonomousScheduler
        # We'll need to pass scheduler or check differently
        
        # Check goals
        goals = self.goals.get_active_goals() if hasattr(self, 'goals') else []

        return {
            "tools_count": len(tools),
            "tools": [t["name"] for t in tools],
            "active_goals": len(goals) if isinstance(goals, list) else 0
        }

    def identify_bottlenecks(self) -> List[str]:
        """Identify system bottlenecks"""
        bottlenecks = []

        # Check database performance
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM action_log")
        log_count = cursor.fetchone()[0]

        if log_count > 10000:
            bottlenecks.append(f"Large action log may slow queries ({log_count} entries)")

        # Check tool count
        tools = self.forge.list_tools()
        if len(tools) > 20:
            bottlenecks.append(f"Many tools may impact loading time ({len(tools)} tools)")

        # Check memory usage
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                bottlenecks.append(f"High memory usage: {memory.percent}%")
        except Exception:
            pass

        # Check disk usage
        try:
            import psutil
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                bottlenecks.append(f"Low disk space: {disk.percent}%")
        except Exception:
            pass

        conn.close()
        return bottlenecks

    def find_improvement_opportunities(self) -> List[Dict]:
        """Find opportunities for self-improvement"""
        opportunities = []

        # Analyze frequent actions for automation potential
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT action, COUNT(*) as frequency
            FROM action_log 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY action 
            HAVING frequency > 3
            ORDER BY frequency DESC
            LIMIT 10
        """)
        frequent_actions = cursor.fetchall()
        conn.close()

        for action, freq in frequent_actions:
            # Use AI to suggest improvement
            prompt = f"""
Action performed frequently in the last week: '{action[:100]}'
Frequency: {freq} times

Suggest ways to improve this:
1. AUTOMATION: How could this be automated?
2. OPTIMIZATION: How could it be faster/cheaper?
3. ELIMINATION: Is this unnecessary?

Response format:
AUTOMATION: [suggestion]
OPTIMIZATION: [suggestion]
ELIMINATION: [if applicable]
"""
            try:
                model_name, _ = self.router.route_request("analysis", "medium")
                suggestion = self.router.call_model(
                    model_name,
                    prompt,
                    system_prompt="You are a process optimization expert."
                )
                opportunities.append({
                    "action": action[:50],
                    "frequency": freq,
                    "suggestion": suggestion
                })
            except Exception:
                pass

        return opportunities

    def generate_improvement_plan(self, diagnosis: Dict) -> List[Dict]:
        """Generate actionable improvement plan"""
        actions = []

        # Based on bottlenecks
        for bottleneck in diagnosis.get("bottlenecks", []):
            if "memory" in bottleneck.lower():
                actions.append({
                    "action": "Optimize memory usage",
                    "priority": "high",
                    "reason": bottleneck,
                    "steps": [
                        "Analyze memory consumption patterns",
                        "Implement caching for frequent queries",
                        "Clean up unused objects"
                    ]
                })
            elif "log" in bottleneck.lower():
                actions.append({
                    "action": "Archive old logs",
                    "priority": "medium",
                    "reason": bottleneck,
                    "steps": [
                        "Create archiving mechanism",
                        "Move logs > 30 days to archive",
                        "Implement log rotation"
                    ]
                })
            elif "disk" in bottleneck.lower():
                actions.append({
                    "action": "Free up disk space",
                    "priority": "high",
                    "reason": bottleneck,
                    "steps": [
                        "Clean temporary files",
                        "Archive old data",
                        "Remove unused tools"
                    ]
                })
            elif "tools" in bottleneck.lower():
                actions.append({
                    "action": "Consolidate tools",
                    "priority": "low",
                    "reason": bottleneck,
                    "steps": [
                        "Review unused tools",
                        "Remove redundant tools",
                        "Optimize tool loading"
                    ]
                })

        # Based on opportunities
        for opportunity in diagnosis.get("improvement_opportunities", []):
            if "AUTOMATION:" in opportunity.get("suggestion", ""):
                actions.append({
                    "action": f"Automate: {opportunity['action'][:30]}...",
                    "priority": "medium",
                    "reason": f"Frequently performed ({opportunity['frequency']}x)",
                    "suggestion": opportunity["suggestion"],
                    "steps": [
                        "Design automation workflow",
                        "Create tool using Forge",
                        "Test and deploy"
                    ]
                })

        # Add general improvements based on performance
        perf = diagnosis.get("performance", {})
        if perf.get("error_rate", 0) > 10:
            actions.append({
                "action": "Reduce error rate",
                "priority": "high",
                "reason": f"Error rate: {perf['error_rate']}%",
                "steps": [
                    "Analyze error patterns",
                    "Add error handling",
                    "Improve validation"
                ]
            })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return actions

    def analyze_own_code(self, module_name: str) -> Dict:
        """Analyze a specific module's code for improvement opportunities"""
        try:
            module = importlib.import_module(f"modules.{module_name}")
            source = inspect.getsource(module)
            
            # Parse AST
            tree = ast.parse(source)
            
            analysis = {
                "module": module_name,
                "lines_of_code": len(source.splitlines()),
                "functions": [],
                "complexities": [],
                "improvements": []
            }
            
            # Analyze functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_complexity = self._calculate_complexity(node)
                    analysis["functions"].append({
                        "name": node.name,
                        "complexity": func_complexity,
                        "args": [a.arg for a in node.args.args]
                    })
                    if func_complexity > 10:  # High complexity threshold
                        analysis["complexities"].append({
                            "function": node.name,
                            "score": func_complexity,
                            "suggestion": "Consider refactoring"
                        })
            
            # Get AI suggestions for improvement
            if analysis["functions"]:
                improvement_prompt = f"""
Analyze this Python module for improvement opportunities:
Module: {module_name}
Lines: {analysis['lines_of_code']}
Functions: {len(analysis['functions'])}
High complexity functions: {[c['function'] for c in analysis['complexities']]}

Suggest specific improvements in these areas:
1. Code structure/organization
2. Performance optimizations
3. Error handling improvements
4. Documentation/comments

Be specific and actionable.
Response format (one line per suggestion):
- [area]: [suggestion]
"""
                model_name, _ = self.router.route_request("coding", "high")
                suggestions = self.router.call_model(
                    model_name,
                    improvement_prompt,
                    system_prompt="You are a code review expert."
                )
                analysis["improvements"] = [s.strip() for s in suggestions.split('\n') if s.strip()]
            
            return analysis
            
        except Exception as e:
            return {
                "module": module_name,
                "error": str(e)
            }

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                  ast.And, ast.Or, ast.Assert)):
                complexity += 1
        return complexity

    def get_diagnosis_summary(self) -> str:
        """Get a human-readable diagnosis summary"""
        diagnosis = self.perform_full_diagnosis()
        
        summary = f"""
=== System Diagnosis ===
Timestamp: {diagnosis['timestamp']}

--- Module Health ---
"""
        for module, status in diagnosis['modules'].items():
            summary += f"  {module}: {status['status']}\n"
        
        summary += f"""
--- Performance ---
  Total Actions: {diagnosis['performance']['total_actions']}
  Error Rate: {diagnosis['performance']['error_rate']}%
  Active Days: {diagnosis['performance']['active_days']}
  Recent (1h): {diagnosis['performance']['recent_actions_1h']}
"""
        
        if diagnosis['bottlenecks']:
            summary += "\n--- Bottlenecks ---\n"
            for b in diagnosis['bottlenecks']:
                summary += f"  ! {b}\n"
        
        if diagnosis['improvement_opportunities']:
            summary += f"\n--- Opportunities ({len(diagnosis['improvement_opportunities'])}) ---\n"
            for opp in diagnosis['improvement_opportunities'][:3]:
                summary += f"  • {opp['action']} (freq: {opp['frequency']})\n"
        
        if diagnosis['recommended_actions']:
            summary += f"\n--- Recommended Actions ({len(diagnosis['recommended_actions'])}) ---\n"
            for action in diagnosis['recommended_actions'][:5]:
                summary += f"  [{action['priority'].upper()}] {action['action']}\n"
        
        return summary
