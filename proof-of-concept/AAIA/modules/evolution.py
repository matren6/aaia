"""
Evolution Manager Module - Self-Evolution Planning and Execution

PURPOSE:
The Evolution Manager is the core planning and execution engine for AI self-evolution.
It takes diagnosis results and converts them into actionable improvement tasks,
then executes those tasks to improve the system.

PROBLEM SOLVED:
Self-diagnosis finds problems, but who acts on them?
- Need someone to plan improvement cycles
- Need to convert diagnosis into actionable tasks
- Need to execute tasks and track progress
- Need to coordinate with other modules (Forge, Modification)
- Need to learn from evolution results

KEY RESPONSIBILITIES:
1. plan_evolution_cycle(): Create improvement plan from diagnosis
2. execute_evolution_task(): Execute a single improvement task
3. _generate_tasks_for_goal(): AI-generate specific tasks
4. _execute_optimization_task(): Run optimization tasks
5. _execute_creation_task(): Create new tools/capabilities
6. _execute_analysis_task(): Run analysis tasks
7. get_evolution_history(): Past evolution cycles
8. get_current_plan(): Active evolution plan
9. get_evolution_status(): Overall evolution state
10. complete_task(): Mark tasks as done

EVOLUTION WORKFLOW:
1. Receive diagnosis results
2. Determine focus based on hierarchy tier
3. Create goals for the cycle
4. Generate specific tasks from goals
5. Execute tasks (optimize, create, analyze)
6. Track results and success
7. Save to evolution history

DEPENDENCIES: Scribe, Router, Forge, SelfDiagnosis, SelfModification
OUTPUTS: Evolution plans, task execution results, history
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class EvolutionManager:
    """Manages AI self-evolution cycles and task execution."""

    def __init__(self, scribe, router, forge, diagnosis, modification):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.diagnosis = diagnosis
        self.modification = modification
        self.evolution_log_path = Path("data/evolution.json")
        self.evolution_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_plan = None

    def plan_evolution_cycle(self) -> Dict:
        """Plan the next evolution cycle based on diagnosis"""
        # Perform diagnosis
        diagnosis = self.diagnosis.perform_full_diagnosis()
        
        # Determine evolution focus based on hierarchy
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT tier, name FROM hierarchy_of_needs WHERE current_focus=1")
        row = cursor.fetchone()
        current_tier = row[0] if row else 1
        current_tier_name = row[1] if row else "Unknown"
        conn.close()
        
        evolution_plan = {
            "cycle_id": datetime.now().strftime("%Y%m%d_%H%M"),
            "focus_tier": current_tier,
            "focus_tier_name": current_tier_name,
            "diagnosis": {
                "bottlenecks": diagnosis.get("bottlenecks", []),
                "opportunities": len(diagnosis.get("improvement_opportunities", [])),
                "error_rate": diagnosis.get("performance", {}).get("error_rate", 0)
            },
            "goals": [],
            "tasks": [],
            "resources_needed": [],
            "success_criteria": []
        }
        
        # Set goals based on tier
        if current_tier == 1:  # Physiological
            evolution_plan["goals"].append("Improve resource efficiency")
            evolution_plan["goals"].append("Enhance system stability")
            evolution_plan["goals"].append("Reduce error rate")
        elif current_tier == 2:  # Growth
            evolution_plan["goals"].append("Add new capabilities")
            evolution_plan["goals"].append("Optimize existing tools")
            evolution_plan["goals"].append("Improve tool creation process")
        elif current_tier == 3:  # Cognitive
            evolution_plan["goals"].append("Improve learning algorithms")
            evolution_plan["goals"].append("Enhance reflection cycles")
            evolution_plan["goals"].append("Better pattern recognition")
        else:  # Self-actualization
            evolution_plan["goals"].append("Improve proactive assistance")
            evolution_plan["goals"].append("Deepen master understanding")
            evolution_plan["goals"].append("Anticipate master needs")
        
        # Create specific tasks from diagnosis
        for action in diagnosis.get("recommended_actions", [])[:5]:
            evolution_plan["tasks"].append({
                "task": action.get("action"),
                "description": action.get("reason", action.get("action")),
                "priority": action.get("priority", "medium"),
                "steps": action.get("steps", []),
                "status": "pending"
            })
        
        # Generate AI-powered tasks for goals
        for goal in evolution_plan["goals"]:
            tasks = self._generate_tasks_for_goal(goal, diagnosis)
            evolution_plan["tasks"].extend(tasks)
        
        # Set success criteria
        evolution_plan["success_criteria"] = [
            f"Complete at least {len(evolution_plan['tasks']) // 2} tasks",
            "Reduce error rate by at least 5%",
            "No system failures during evolution"
        ]
        
        # Log evolution plan
        self.scribe.log_action(
            "Evolution cycle planned",
            f"Goals: {len(evolution_plan['goals'])}, Tasks: {len(evolution_plan['tasks'])}",
            "evolution_planned"
        )
        
        # Save plan
        self.current_plan = evolution_plan
        self._save_evolution_plan(evolution_plan)
        
        return evolution_plan

    def _generate_tasks_for_goal(self, goal: str, diagnosis: Dict) -> List[Dict]:
        """Generate specific tasks to achieve a goal using AI"""
        prompt = f"""
Goal: {goal}

Current system diagnosis:
- Performance: {diagnosis.get('performance', {})}
- Bottlenecks: {diagnosis.get('bottlenecks', [])}
- Improvement opportunities: {len(diagnosis.get('improvement_opportunities', []))}

Generate 2-3 specific, actionable tasks to achieve this goal.
Each task should be:
- Concrete and measurable
- Achievable within a day
- Something I can implement (create tool, modify code, etc.)

Format each task as:
TASK: [task name]
DESCRIPTION: [what to do]
EXPECTED_BENEFIT: [expected outcome]
EFFORT: [low/medium/high]
"""
        try:
            model_name, _ = self.router.route_request("planning", "high")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are an AI evolution planner creating actionable improvement tasks."
            )
            
            tasks = []
            current_task = {}
            
            for line in response.split("\n"):
                line = line.strip()
                if line.startswith("TASK:"):
                    if current_task:
                        tasks.append(current_task)
                    current_task = {"task": line.replace("TASK:", "").strip(), "status": "pending"}
                elif line.startswith("DESCRIPTION:"):
                    current_task["description"] = line.replace("DESCRIPTION:", "").strip()
                elif line.startswith("EXPECTED_BENEFIT:"):
                    current_task["expected_benefit"] = line.replace("EXPECTED_BENEFIT:", "").strip()
                elif line.startswith("EFFORT:"):
                    current_task["effort"] = line.replace("EFFORT:", "").strip().lower()
            
            if current_task:
                tasks.append(current_task)
            
            return tasks
            
        except Exception as e:
            return [{
                "task": f"Analyze {goal}",
                "description": "Analyze system for opportunities",
                "effort": "low",
                "status": "pending"
            }]

    def execute_evolution_task(self, task: Dict) -> Dict:
        """Execute a single evolution task"""
        result = {
            "task": task.get("task"),
            "start_time": datetime.now().isoformat(),
            "success": False,
            "output": "",
            "errors": []
        }
        
        try:
            task_name = task.get("task", "").lower()
            
            # Determine task type and execute
            if "optimize" in task_name or "improve" in task_name:
                result["output"] = self._execute_optimization_task(task)
            elif "create" in task_name or "add" in task_name:
                result["output"] = self._execute_creation_task(task)
            elif "analyze" in task_name or "diagnos" in task_name:
                result["output"] = self._execute_analysis_task(task)
            elif "reduce" in task_name or "decrease" in task_name:
                result["output"] = self._execute_optimization_task(task)
            else:
                result["output"] = self._execute_generic_task(task)
            
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(str(e))
            result["success"] = False
        
        result["end_time"] = datetime.now().isoformat()
        
        # Log result
        self.scribe.log_action(
            f"Evolution task: {task.get('task')}",
            f"Success: {result['success']}, Output: {str(result['output'])[:100]}...",
            "evolution_task_completed" if result["success"] else "evolution_task_failed"
        )
        
        return result

    def _execute_optimization_task(self, task: Dict) -> str:
        """Execute an optimization task"""
        # Find a module to optimize
        modules_to_check = ["scribe", "economics", "router", "dialogue", "forge"]
        
        for module in modules_to_check:
            try:
                analysis = self.diagnosis.analyze_own_code(module)
                if analysis.get("complexities"):
                    # Found module with high complexity - suggest optimization
                    improvements = analysis.get("improvements", [])
                    return f"Analyzed {module}: Found {len(analysis['complexities'])} complex functions. Suggestions: {len(improvements)}"
            except:
                pass
        
        return "No optimization target found"

    def _execute_creation_task(self, task: Dict) -> str:
        """Execute a creation task (new tool)"""
        description = task.get("description", task.get("task", ""))
        
        # Generate tool name
        task_name = task.get("task", "unnamed").lower().replace(" ", "_")
        tool_name = f"evolved_{task_name[:20]}"
        
        try:
            # Use Forge to create the tool
            metadata = self.forge.create_tool(
                name=tool_name,
                description=description
            )
            return f"Created tool: {metadata['name']}"
        except Exception as e:
            return f"Failed to create tool: {str(e)}"

    def _execute_analysis_task(self, task: Dict) -> str:
        """Execute an analysis task"""
        diagnosis = self.diagnosis.perform_full_diagnosis()
        return f"Analysis complete: {len(diagnosis['bottlenecks'])} bottlenecks, {len(diagnosis['improvement_opportunities'])} opportunities found"

    def _execute_generic_task(self, task: Dict) -> str:
        """Execute a generic task using AI to determine approach"""
        prompt = f"""
Task: {task.get('task')}
Description: {task.get('description')}

Determine how to execute this task. Should I:
1. Create a new tool?
2. Optimize existing code?
3. Analyze something?
4. Modify configuration?

Respond with just the action to take:
ACTION: [one of: create_tool, optimize, analyze, modify_config]
"""
        try:
            model_name, _ = self.router.route_request("reasoning", "medium")
            response = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are a task execution planner."
            )
            
            if "create_tool" in response.lower():
                return self._execute_creation_task(task)
            elif "optimize" in response.lower():
                return self._execute_optimization_task(task)
            elif "analyze" in response.lower():
                return self._execute_analysis_task(task)
            else:
                return f"Task analyzed: {task.get('task')}"
        except:
            return f"Task queued: {task.get('task')}"

    def _save_evolution_plan(self, plan: Dict):
        """Save evolution plan to file"""
        try:
            existing = []
            if self.evolution_log_path.exists():
                existing = json.loads(self.evolution_log_path.read_text())
            
            existing.append(plan)
            
            # Keep only last 10 plans
            if len(existing) > 10:
                existing = existing[-10:]
            
            self.evolution_log_path.write_text(json.dumps(existing, indent=2))
        except Exception as e:
            print(f"Failed to save evolution plan: {e}")

    def get_evolution_history(self) -> List[Dict]:
        """Get history of evolution cycles"""
        try:
            if self.evolution_log_path.exists():
                return json.loads(self.evolution_log_path.read_text())
        except:
            pass
        return []

    def get_current_plan(self) -> Optional[Dict]:
        """Get current evolution plan"""
        if self.current_plan:
            return self.current_plan
        
        # Try to load from file
        history = self.get_evolution_history()
        if history:
            self.current_plan = history[-1]
            return self.current_plan
        
        return None

    def get_evolution_status(self) -> Dict:
        """Get current evolution status"""
        plan = self.get_current_plan()
        
        if plan:
            completed = sum(1 for t in plan.get("tasks", []) if t.get("status") == "completed")
            total = len(plan.get("tasks", []))
            
            return {
                "state": "Active" if plan.get("tasks") else "Planning",
                "last_cycle": plan.get("cycle_id", "Unknown"),
                "focus_tier": plan.get("focus_tier", 1),
                "goals": len(plan.get("goals", [])),
                "tasks": total,
                "completed_tasks": completed,
                "progress": f"{completed}/{total}" if total > 0 else "0/0"
            }
        
        return {
            "state": "No active plan",
            "last_cycle": "Never",
            "focus_tier": 1,
            "goals": 0,
            "tasks": 0,
            "completed_tasks": 0,
            "progress": "0/0"
        }

    def complete_task(self, task_index: int) -> bool:
        """Mark a task as completed"""
        if self.current_plan and "tasks" in self.current_plan:
            if 0 <= task_index < len(self.current_plan["tasks"]):
                self.current_plan["tasks"][task_index]["status"] = "completed"
                self._save_evolution_plan(self.current_plan)
                return True
        return False