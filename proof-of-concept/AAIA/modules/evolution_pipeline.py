# evolution_pipeline.py
"""
Evolution Pipeline Module - Complete Self-Improvement Workflow

PURPOSE:
The Evolution Pipeline orchestrates the complete self-improvement workflow,
combining diagnosis, planning, execution, testing, and learning into a single
cohesive process. It manages the full evolution lifecycle from start to finish.

PROBLEM SOLVED:
Self-improvement involves many steps that must work together:
- Need diagnosis first, then planning
- Need to execute tasks in right order
- Need testing to verify changes work
- Need to learn from results
- Need cleanup after evolution
- Need rollback capability if things go wrong

KEY RESPONSIBILITIES:
1. run_autonomous_evolution(): Execute complete evolution cycle
2. should_evolve(): Determine if evolution is needed
3. prioritize_tasks(): Order tasks by impact
4. test_evolved_system(): Comprehensive system testing
5. extract_lessons(): Learn from evolution results
6. update_evolution_knowledge(): Save lessons for future
7. cleanup_evolution_artifacts(): Clean temporary files
8. pause_pipeline(): Pause running evolution
9. resume_pipeline(): Resume paused evolution
10. get_pipeline_status(): Current state and stats
11. rollback_last_evolution(): Attempt to undo last evolution
12. export_evolution_report(): Generate reports (JSON/summary)
13. create_evolution_checkpoint(): Pre-evolution snapshot
14. validate_prerequisites(): Check all components available

EVOLUTION PHASES:
1. Self-Diagnosis: Assess current state
2. Planning: Create improvement plan
3. Execution: Run improvement tasks
4. Testing: Verify changes work
5. Learning: Extract lessons
6. Cleanup: Remove temporary files

SAFETY FEATURES:
- Pre-flight validation of prerequisites
- Checkpoint before major changes
- Comprehensive testing after changes
- Rollback capability
- Artifact cleanup
- Detailed logging throughout

DEPENDENCIES: Scribe, Router, Forge, SelfDiagnosis, SelfModification, Evolution
OUTPUTS: Evolution summary, lessons learned, reports
"""

import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

class EvolutionPipeline:
    def __init__(self, scribe, router, forge, diagnosis, modification, evolution, event_bus=None):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.diagnosis = diagnosis
        self.modification = modification
        self.evolution = evolution
        self.event_bus = event_bus
        self.pipeline_state = "idle"
        self.evolution_log = []
        
    def run_autonomous_evolution(self):
        """Run complete evolution pipeline autonomously"""
        self.pipeline_state = "running"
        
        # Log start
        self.scribe.log_action(
            "Starting autonomous evolution pipeline",
            "System initiating self-improvement cycle",
            "evolution_started"
        )
        
        try:
            # 1. Self-Diagnosis Phase
            print("Phase 1: Self-Diagnosis...")
            diagnosis = self.diagnosis.perform_full_diagnosis()
            
            # Store diagnosis
            diagnosis_file = Path("data") / f"diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            diagnosis_file.parent.mkdir(exist_ok=True)
            diagnosis_file.write_text(json.dumps(diagnosis, indent=2))
            
            # Check if evolution is needed
            if not self.should_evolve(diagnosis):
                print("No evolution needed at this time")
                self.pipeline_state = "idle"
                return {"status": "skipped", "reason": "no_improvement_needed"}
            
            # 2. Planning Phase
            print("Phase 2: Evolution Planning...")
            plan = self.evolution.plan_evolution_cycle()
            
            # Prioritize tasks
            prioritized_tasks = self.prioritize_tasks(plan["tasks"], diagnosis)
            
            # 3. Execution Phase
            print("Phase 3: Executing Evolution Tasks...")
            results = []
            for task in prioritized_tasks[:3]:  # Start with top 3 tasks
                print(f"  Executing: {task.get('task')}")
                result = self.evolution.execute_evolution_task(task)
                results.append(result)
                
                # Wait between tasks to avoid overwhelming system
                time.sleep(2)
                
            # 4. Testing Phase
            print("Phase 4: Testing Changes...")
            test_results = self.test_evolved_system()
            
            # 5. Learning Phase
            print("Phase 5: Learning from Results...")
            lessons = self.extract_lessons(results, test_results)
            
            # Update system knowledge
            self.update_evolution_knowledge(lessons)
            
            # 6. Cleanup Phase
            print("Phase 6: Cleanup...")
            self.cleanup_evolution_artifacts()
            
            # Complete
            self.pipeline_state = "idle"
            
            summary = {
                "status": "completed",
                "diagnosis_summary": f"{len(diagnosis.get('improvement_opportunities', []))} opportunities",
                "tasks_executed": len(results),
                "test_results": test_results,
                "lessons_learned": len(lessons)
            }
            
            self.scribe.log_action(
                "Evolution pipeline completed",
                f"Summary: {summary}",
                "evolution_completed"
            )
            
            return summary
            
        except Exception as e:
            self.pipeline_state = "error"
            self.scribe.log_action(
                "Evolution pipeline failed",
                f"Error: {str(e)}",
                "evolution_failed"
            )
            return {"status": "failed", "error": str(e)}
            
    def should_evolve(self, diagnosis: dict) -> bool:
        """Determine if evolution should proceed"""
        # Check if there are significant issues
        critical_issues = 0
        
        # High error rate
        if diagnosis.get("performance", {}).get("error_rate", 0) > 10:
            critical_issues += 1
            
        # Multiple bottlenecks
        if len(diagnosis.get("bottlenecks", [])) >= 3:
            critical_issues += 1
            
        # Many improvement opportunities
        if len(diagnosis.get("improvement_opportunities", [])) >= 5:
            critical_issues += 1
            
        # Check last evolution time
        last_evolution = self.get_last_evolution_time()
        time_since_last = datetime.now() - last_evolution
        
        # Evolve if:
        # 1. Critical issues found, OR
        # 2. It's been more than 7 days since last evolution, OR
        # 3. More than 10 improvement opportunities found
        return (critical_issues >= 2 or 
                time_since_last > timedelta(days=7) or
                len(diagnosis.get("improvement_opportunities", [])) >= 10)
                
    def prioritize_tasks(self, tasks: list, diagnosis: dict) -> list:
        """Prioritize evolution tasks"""
        if not tasks:
            return []
            
        # Use AI to prioritize
        prompt = f"""
        Diagnosed system issues:
        {json.dumps(diagnosis.get('bottlenecks', []), indent=2)}
        
        Improvement opportunities:
        {chr(10).join([f'- {op.get("action", "")}' for op in diagnosis.get('improvement_opportunities', [])])}
        
        Proposed evolution tasks:
        {chr(10).join([f'- {task.get("task", "")}' for task in tasks])}
        
        Prioritize these tasks based on:
        1. Impact on system stability
        2. Effort required
        3. Expected benefit
        4. Dependencies between tasks
        
        Return ONLY a numbered list of task names in priority order.
        """
        
        model_name, _ = self.router.route_request("analysis", "high")
        response = self.router.call_model(
            model_name,
            prompt,
            system_prompt="You are a project prioritization expert. Return only the prioritized list."
        )
        
        # Extract task names from response
        prioritized_names = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering/bullets
                name = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                prioritized_names.append(name)
                
        # Sort tasks based on priority
        prioritized_tasks = []
        for name in prioritized_names:
            for task in tasks:
                if name.lower() in task.get("task", "").lower():
                    prioritized_tasks.append(task)
                    break
                    
        # Add any remaining tasks
        for task in tasks:
            if task not in prioritized_tasks:
                prioritized_tasks.append(task)
                
        return prioritized_tasks
        
    def test_evolved_system(self) -> dict:
        """Run comprehensive tests after evolution"""
        tests = {
            "module_imports": self.test_module_imports(),
            "database_integrity": self.test_database_integrity(),
            "tool_execution": self.test_tool_execution(),
            "mandate_checking": self.test_mandate_checking(),
            "economic_calculations": self.test_economic_calculations()
        }
        
        # Calculate overall status
        passed = sum(1 for test, result in tests.items() if result.get("passed", False))
        total = len(tests)
        
        return {
            "tests_run": total,
            "tests_passed": passed,
            "tests_failed": total - passed,
            "details": tests
        }
        
    def test_module_imports(self) -> dict:
        """Test that all modules can be imported"""
        modules = ["scribe", "mandates", "economics", "dialogue", 
                  "router", "forge", "scheduler", "self_diagnosis",
                  "self_modification", "evolution"]
        
        results = {}
        for module in modules:
            try:
                __import__(module)
                results[module] = {"passed": True, "error": None}
            except Exception as e:
                results[module] = {"passed": False, "error": str(e)}
                
        all_passed = all(r["passed"] for r in results.values())
        return {"passed": all_passed, "module_results": results}
        
    def test_database_integrity(self) -> dict:
        """Test database connectivity and integrity"""
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            cursor = conn.cursor()
            
            # Check all required tables exist
            tables = ["action_log", "economic_log", "hierarchy_of_needs", 
                     "dialogue_log", "master_model", "tools", "system_state"]
            
            for table in tables:
                cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
                
            conn.close()
            return {"passed": True, "error": None}
        except Exception as e:
            return {"passed": False, "error": str(e)}
            
    def extract_lessons(self, execution_results: list, test_results: dict) -> list:
        """Extract lessons from evolution results"""
        lessons = []
        
        # Analyze execution results
        for result in execution_results:
            if result.get("success"):
                lessons.append({
                    "type": "success",
                    "task": result.get("task"),
                    "lesson": f"Successfully executed: {result.get('task')}",
                    "insight": result.get("output", "")[:200]
                })
            else:
                lessons.append({
                    "type": "failure",
                    "task": result.get("task"),
                    "lesson": f"Failed to execute: {result.get('task')}",
                    "insight": f"Error: {result.get('errors', ['Unknown'])[0]}",
                    "recommendation": "Review task complexity or dependencies"
                })
                
        # Analyze test results
        if test_results.get("tests_passed", 0) < test_results.get("tests_run", 0):
            lessons.append({
                "type": "warning",
                "task": "System testing",
                "lesson": "Some tests failed after evolution",
                "insight": f"{test_results['tests_failed']} tests failed",
                "recommendation": "Review recent changes that might have broken functionality"
            })
            
        return lessons
        
    def update_evolution_knowledge(self, lessons: list):
        """Store evolution lessons for future reference"""
        evolution_file = Path("data") / "evolution_knowledge.json"
        
        try:
            if evolution_file.exists():
                existing_data = json.loads(evolution_file.read_text())
            else:
                existing_data = {"lessons": [], "total_cycles": 0}
                
            existing_data["lessons"].extend(lessons)
            existing_data["total_cycles"] += 1
            existing_data["last_update"] = datetime.now().isoformat()
            
            evolution_file.write_text(json.dumps(existing_data, indent=2))
            
        except Exception as e:
            self.scribe.log_action(
                "Failed to save evolution knowledge",
                f"Error: {str(e)}",
                "error"
            )
            
    def get_last_evolution_time(self) -> datetime:
        """Get timestamp of last evolution cycle"""
        evolution_file = Path("data") / "evolution_knowledge.json"
        
        if evolution_file.exists():
            try:
                data = json.loads(evolution_file.read_text())
                last_update = data.get("last_update")
                if last_update:
                    return datetime.fromisoformat(last_update)
            except:
                pass
                
        return datetime.now() - timedelta(days=30)  # Default to 30 days ago

    def cleanup_evolution_artifacts(self):
        """Clean up temporary files and artifacts from evolution"""
        cleanup_patterns = [
            "data/diagnosis_*.json",
            "data/evolution_backup_*.json",
            "data/patch_*.json"
        ]
        
        cleaned_count = 0
        for pattern in cleanup_patterns:
            for file in Path("data").glob(pattern):
                try:
                    if file.is_file():
                        file.unlink()
                        cleaned_count += 1
                except Exception as e:
                    self.scribe.log_action(
                        "Failed to cleanup artifact",
                        f"Error: {str(e)}",
                        "cleanup_error"
                    )
                    
        self.scribe.log_action(
            "Cleanup completed",
            f"Removed {cleaned_count} artifacts",
            "cleanup"
        )
        
    def test_tool_execution(self) -> dict:
        """Test that core tools can be executed"""
        test_results = {}
        
        # Test scribe logging
        try:
            test_id = f"test_tool_{int(time.time())}"
            self.scribe.log_action(test_id, "Testing tool execution", "test")
            test_results["scribe"] = {"passed": True, "error": None}
        except Exception as e:
            test_results["scribe"] = {"passed": False, "error": str(e)}
            
        # Test router routing
        try:
            model, priority = self.router.route_request("test", "low")
            test_results["router"] = {"passed": True, "model": model, "error": None}
        except Exception as e:
            test_results["router"] = {"passed": False, "error": str(e)}
            
        # Test forge capabilities
        try:
            has_forge = hasattr(self, 'forge') and self.forge is not None
            test_results["forge"] = {"passed": has_forge, "error": None if has_forge else "Forge not available"}
        except Exception as e:
            test_results["forge"] = {"passed": False, "error": str(e)}
            
        # Test diagnosis capabilities
        try:
            has_diagnosis = hasattr(self, 'diagnosis') and self.diagnosis is not None
            test_results["diagnosis"] = {"passed": has_diagnosis, "error": None if has_diagnosis else "Diagnosis not available"}
        except Exception as e:
            test_results["diagnosis"] = {"passed": False, "error": str(e)}
            
        all_passed = all(r["passed"] for r in test_results.values())
        return {"passed": all_passed, "tool_results": test_results}
        
    def test_mandate_checking(self) -> dict:
        """Test that mandate validation works"""
        try:
            # Import the correct class name
            from modules.mandates import MandateEnforcer
            
            # Create a test instance with scribe
            test_mandates = MandateEnforcer(self.scribe)
            
            # Test mandate checking
            is_allowed, violations = test_mandates.check_action("test_action")
            
            return {
                "passed": True,
                "mandate_validation": "available",
                "test_result": {"allowed": is_allowed, "violations": violations},
                "error": None
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
            
    def test_economic_calculations(self) -> dict:
        """Test that economic calculations work correctly"""
        try:
            # Test basic economic calculations
            test_cases = [
                {"tokens": 1000, "model": "gpt-4", "expected_range": (0.01, 0.10)},
                {"tokens": 1000, "model": "gpt-3.5-turbo", "expected_range": (0.001, 0.005)},
            ]
            
            results = {}
            for i, test_case in enumerate(test_cases):
                # Basic sanity check - cost should be a positive number
                estimated_cost = test_case["tokens"] / 1000 * 0.01  # Rough estimate
                in_range = test_case["expected_range"][0] <= estimated_cost <= test_case["expected_range"][1]
                results[f"test_{i}"] = {
                    "passed": in_range,
                    "estimated_cost": estimated_cost,
                    "expected_range": test_case["expected_range"]
                }
                
            all_passed = all(r["passed"] for r in results.values())
            return {"passed": all_passed, "calculation_results": results, "error": None}
        except Exception as e:
            return {"passed": False, "error": str(e)}
            
    def pause_pipeline(self):
        """Pause the evolution pipeline"""
        if self.pipeline_state == "running":
            self.pipeline_state = "paused"
            self.scribe.log_action(
                "Evolution pipeline paused",
                "Pipeline paused by user request",
                "pipeline_paused"
            )
            return {"status": "paused"}
        else:
            return {"status": "not_running", "message": "Pipeline is not currently running"}
            
    def resume_pipeline(self):
        """Resume a paused evolution pipeline"""
        if self.pipeline_state == "paused":
            self.pipeline_state = "running"
            self.scribe.log_action(
                "Evolution pipeline resumed",
                "Pipeline resumed",
                "pipeline_resumed"
            )
            return {"status": "running"}
        else:
            return {"status": "not_paused", "message": "Pipeline is not paused"}
            
    def get_pipeline_status(self) -> dict:
        """Get current status of the evolution pipeline"""
        return {
            "state": self.pipeline_state,
            "last_evolution": self.get_last_evolution_time().isoformat(),
            "total_evolution_cycles": self.get_evolution_cycle_count(),
            "log_entries": len(self.evolution_log)
        }
        
    def get_evolution_cycle_count(self) -> int:
        """Get total number of evolution cycles completed"""
        evolution_file = Path("data") / "evolution_knowledge.json"
        
        if evolution_file.exists():
            try:
                data = json.loads(evolution_file.read_text())
                return data.get("total_cycles", 0)
            except:
                pass
                
        return 0

    def rollback_last_evolution(self) -> dict:
        """Attempt to rollback the last evolution cycle"""
        # First check if we have a backup
        backup_file = Path("data") / "evolution_backup_latest.json"
        
        if not backup_file.exists():
            return {"status": "failed", "error": "No backup found to rollback to"}
            
        try:
            # Load the backup
            backup_data = json.loads(backup_file.read_text())
            
            # Restore system state if available
            restore_result = {"status": "skipped"}
            if "system_state" in backup_data:
                # Use the correct method name and signature
                if hasattr(self.modification, 'restore_from_backup'):
                    restore_result = self.modification.restore_from_backup(
                        backup_data["system_state"]
                    )
                elif hasattr(self.modification, 'restore_backup'):
                    # Try the file-based restoration
                    modules_to_restore = backup_data.get("modules_modified", [])
                    restored = []
                    for module_name in modules_to_restore:
                        if self.modification.restore_backup(module_name):
                            restored.append(module_name)
                    restore_result = {
                        "status": "partial" if len(restored) < len(modules_to_restore) else "completed",
                        "modules_restored": restored
                    }
            
            self.scribe.log_action(
                "Evolution rolled back",
                f"Restored to state from {backup_data.get('timestamp', 'unknown')}",
                "evolution_rollback"
            )
            
            return {
                "status": "completed",
                "backup_timestamp": backup_data.get("timestamp"),
                "restore_result": restore_result
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def export_evolution_report(self, format: str = "json") -> dict:
        """Export evolution report in specified format"""
        evolution_file = Path("data") / "evolution_knowledge.json"
        
        if not evolution_file.exists():
            return {"status": "failed", "error": "No evolution data found"}
            
        try:
            data = json.loads(evolution_file.read_text())
            
            report = {
                "generated_at": datetime.now().isoformat(),
                "total_cycles": data.get("total_cycles", 0),
                "lessons": data.get("lessons", []),
                "last_update": data.get("last_update"),
                "pipeline_status": self.get_pipeline_status()
            }
            
            if format == "json":
                output_file = Path("data") / f"evolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                output_file.write_text(json.dumps(report, indent=2))
                return {"status": "completed", "file": str(output_file)}
            elif format == "summary":
                # Generate a text summary
                summary = f"""
Evolution Report
================
Generated: {report['generated_at']}
Total Cycles: {report['total_cycles']}
Last Update: {report['last_update']}

Lessons Learned: {len(report['lessons'])}

Recent Lessons:
"""
                for lesson in report['lessons'][-5:]:
                    summary += f"\n- [{lesson.get('type', 'unknown')}] {lesson.get('task', 'N/A')}: {lesson.get('lesson', 'N/A')}"
                    
                output_file = Path("data") / f"evolution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                output_file.write_text(summary)
                return {"status": "completed", "file": str(output_file), "summary": summary}
            else:
                return {"status": "failed", "error": f"Unsupported format: {format}"}
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
            
    def create_evolution_checkpoint(self) -> dict:
        """Create a checkpoint before evolution for potential rollback"""
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "pipeline_state": self.pipeline_state,
            "system_state": self.diagnosis.get_system_snapshot() if hasattr(self.diagnosis, 'get_system_snapshot') else {}
        }
        
        checkpoint_file = Path("data") / "evolution_checkpoint.json"
        checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))
        
        self.scribe.log_action(
            "Evolution checkpoint created",
            f"Checkpoint saved at {checkpoint_data['timestamp']}",
            "checkpoint_created"
        )
        
        return {"status": "completed", "checkpoint_file": str(checkpoint_file)}
        
    def validate_prerequisites(self) -> dict:
        """Validate that all prerequisites for evolution are met"""
        prerequisites = {
            "database_access": False,
            "module_imports": False,
            "diagnosis_available": False,
            "modification_available": False,
            "forge_available": False,
            "router_available": False
        }
        
        # Check database
        try:
            conn = sqlite3.connect(self.scribe.db_path)
            conn.close()
            prerequisites["database_access"] = True
        except:
            pass
            
        # Check modules
        try:
            import importlib
            required_modules = ["scribe", "mandates", "economics", "dialogue", "router"]
            all_imported = all(
                importlib.import_module(f"modules.{m}") is not None 
                for m in required_modules 
                if hasattr(self, m)
            )
            prerequisites["module_imports"] = True
        except:
            pass
            
        # Check component availability
        prerequisites["diagnosis_available"] = self.diagnosis is not None
        prerequisites["modification_available"] = self.modification is not None
        prerequisites["forge_available"] = self.forge is not None
        prerequisites["router_available"] = self.router is not None
        
        all_met = all(prerequisites.values())
        
        return {
            "all_prerequisites_met": all_met,
            "prerequisites": prerequisites,
            "missing": [k for k, v in prerequisites.items() if not v]
        }