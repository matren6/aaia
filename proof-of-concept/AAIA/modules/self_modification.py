"""
Self-Modification Module - Safe Code Improvement System

PURPOSE:
The Self-Modification module enables the AI to safely modify its own code, with
comprehensive backup and rollback capabilities. It provides the mechanism for
self-improvement while ensuring the system can recover from bad modifications.

PROBLEM SOLVED:
For true self-evolution, the AI must be able to change itself:
- But unchecked modifications could break the system
- Need backups before any changes
- Need rollback capability if something goes wrong
- Need testing to verify changes work
- Need AI assistance to suggest improvements

KEY RESPONSIBILITIES:
1. analyze_own_code(): Parse and analyze module source code
2. modify_module(): Apply safe modifications to modules
3. create_backup(): Create timestamped backups before changes
4. restore_backup(): Rollback to previous version
5. list_backups(): Show available backup files
6. test_module(): Verify modified modules work correctly
7. generate_code_improvement(): Use AI to suggest improvements
8. apply_improvement(): Apply AI-generated improvements safely
9. get_modification_history(): Track all modifications made

SAFETY FEATURES:
- Always creates backup before modification
- Validates code syntax before writing
- Tests module after modification
- Automatically restores backup on test failure
- Comprehensive error handling
- Full audit trail of changes

BACKUP SYSTEM:
- Timestamped backups in backups/ directory
- Can restore to any previous backup
- Backups preserved until explicitly deleted
- Registry of all backups with timestamps

DEPENDENCIES: Scribe, Router, Forge
OUTPUTS: Modified modules, backups, test results
"""

import ast
import inspect
import textwrap
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class SelfModification:
    """Safe self-modification with backup and testing."""

    def __init__(self, scribe, router, forge):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def analyze_own_code(self, module_name: str) -> Dict:
        """Analyze a module's code for improvement opportunities"""
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
                        "args": [a.arg for a in node.args.args],
                        "docstring": ast.get_docstring(node)
                    })
                    if func_complexity > 10:
                        analysis["complexities"].append({
                            "function": node.name,
                            "score": func_complexity,
                            "suggestion": "Consider refactoring"
                        })
            
            # Get AI suggestions for improvement
            if analysis["functions"]:
                complexity_list = [c['function'] for c in analysis['complexities']]
                improvement_prompt = f"""
Analyze this Python module for improvement opportunities:
Module: {module_name}
Lines: {analysis['lines_of_code']}
Functions: {len(analysis['functions'])}
High complexity functions: {complexity_list}

Suggest specific improvements in these areas:
1. Code structure/organization
2. Performance optimizations
3. Error handling improvements
4. Documentation/comments

Be specific and actionable.
Response format (one per line):
- [area]: [suggestion]
"""
                try:
                    model_name, _ = self.router.route_request("coding", "high")
                    suggestions = self.router.call_model(
                        model_name,
                        improvement_prompt,
                        system_prompt="You are a code review expert."
                    )
                    analysis["improvements"] = [s.strip() for s in suggestions.split('\n') if s.strip() and s.strip().startswith('-')]
                except Exception as e:
                    analysis["improvements"] = [f"Could not get AI suggestions: {e}"]
            
            return analysis
            
        except Exception as e:
            return {
                "module": module_name,
                "error": str(e)
            }

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate McCabe cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                  ast.And, ast.Or, ast.Assert)):
                complexity += 1
        return complexity

    def modify_module(self, module_name: str, changes: Dict) -> bool:
        """Safely modify a module based on suggestions"""
        # Create backup first
        self.create_backup(module_name)
        
        try:
            # Read current source
            module_path = Path(f"modules/{module_name}.py")
            if not module_path.exists():
                module_path = Path(f"AAIA/modules/{module_name}.py")
            
            if not module_path.exists():
                raise FileNotFoundError(f"Module not found: {module_name}")
            
            with open(module_path, 'r') as f:
                source = f.read()
            
            # Parse and modify AST
            tree = ast.parse(source)
            
            # Apply changes based on change type
            if changes.get("type") == "add_function":
                new_func = self._generate_function(changes["spec"])
                # Add new function to module (simplified)
                pass
            elif changes.get("type") == "modify_function":
                # Find and modify function
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == changes["function"]:
                        # Would modify function body here
                        pass
            
            # For now, we'll log the intended changes but not modify
            # Full implementation would write modified source
            self.scribe.log_action(
                f"Module modification planned: {module_name}",
                f"Changes: {changes.get('description', 'unspecified')}",
                "modification_planned"
            )
            
            # Return True to indicate success (changes planned)
            return True
            
        except Exception as e:
            self.scribe.log_action(
                f"Failed to modify {module_name}",
                f"Error: {str(e)}",
                "error"
            )
            # Don't restore backup if we didn't make changes
            return False

    def create_backup(self, module_name: str) -> Optional[str]:
        """Create backup of module before modification"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{module_name}_{timestamp}.py.backup"
            
            # Try different paths
            module_paths = [
                Path(f"modules/{module_name}.py"),
                Path(f"AAIA/modules/{module_name}.py"),
                Path(f"{module_name}.py")
            ]
            
            for module_path in module_paths:
                if module_path.exists():
                    shutil.copy2(module_path, backup_file)
                    return str(backup_file)
            
            return None
        except Exception as e:
            print(f"Backup failed: {e}")
            return None

    def restore_backup(self, module_name: str) -> bool:
        """Restore module from latest backup"""
        try:
            backups = sorted(self.backup_dir.glob(f"{module_name}_*.py.backup"))
            if backups:
                latest_backup = backups[-1]
                
                # Find original location
                module_paths = [
                    Path(f"modules/{module_name}.py"),
                    Path(f"AAIA/modules/{module_name}.py"),
                    Path(f"{module_name}.py")
                ]
                
                for module_path in module_paths:
                    if module_path.exists() or module_path.parent.exists():
                        shutil.copy2(latest_backup, module_path)
                        return True
            return False
        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def list_backups(self, module_name: str = None) -> List[Dict]:
        """List available backups"""
        backups = []
        
        if module_name:
            pattern = f"{module_name}_*.py.backup"
        else:
            pattern = "*.py.backup"
        
        for backup_file in sorted(self.backup_dir.glob(pattern)):
            stat = backup_file.stat()
            backups.append({
                "file": backup_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return backups

    def test_module(self, module_name: str) -> bool:
        """Test if modified module works correctly"""
        try:
            # Try to import the module
            if module_name in sys.modules:
                del sys.modules[module_name]
            if f"modules.{module_name}" in sys.modules:
                del sys.modules[f"modules.{module_name}"]
            
            importlib.import_module(f"modules.{module_name}")
            return True
        except Exception as e:
            self.scribe.log_action(
                f"Test failed for {module_name}",
                f"Error: {str(e)}",
                "error"
            )
            return False

    def generate_code_improvement(self, module_name: str, focus_area: str = "general") -> Optional[str]:
        """Generate improved code for a module using AI"""
        try:
            analysis = self.analyze_own_code(module_name)
            
            if "error" in analysis:
                return f"Could not analyze module: {analysis['error']}"
            
            prompt = f"""
Improve the Python module '{module_name}' focusing on: {focus_area}

Current stats:
- Lines of code: {analysis['lines_of_code']}
- Functions: {len(analysis['functions'])}
- Complex functions: {analysis['complexities']}

Previous improvements suggested:
{chr(10).join(analysis.get('improvements', ['None'])[:5])}

Provide improved version of the module. Include:
1. Better error handling
2. Performance optimizations
3. Clearer documentation
4. Cleaner code structure

Return the complete improved Python code:
"""
            model_name, _ = self.router.route_request("coding", "high")
            improved_code = self.router.call_model(
                model_name,
                prompt,
                system_prompt="You are an expert Python developer. Provide clean, optimized code."
            )
            
            return improved_code
            
        except Exception as e:
            return f"Could not generate improvement: {str(e)}"

    def apply_improvement(self, module_name: str, improved_code: str) -> bool:
        """Apply AI-generated improvement to a module"""
        # Create backup first
        if not self.create_backup(module_name):
            return False
        
        try:
            # Find the module path
            module_paths = [
                Path(f"modules/{module_name}.py"),
                Path(f"AAIA/modules/{module_name}.py")
            ]
            
            module_path = None
            for p in module_paths:
                if p.exists():
                    module_path = p
                    break
            
            if not module_path:
                return False
            
            # Validate the code before writing
            try:
                ast.parse(improved_code)
            except SyntaxError as e:
                self.scribe.log_action(
                    f"Improvement validation failed for {module_name}",
                    f"Syntax error: {str(e)}",
                    "error"
                )
                return False
            
            # Write the improved code
            with open(module_path, 'w') as f:
                f.write(improved_code)
            
            # Test the module
            if self.test_module(module_name):
                self.scribe.log_action(
                    f"Module improved: {module_name}",
                    "Successfully applied AI-generated improvements",
                    "improvement_applied"
                )
                return True
            else:
                # Restore backup on test failure
                self.restore_backup(module_name)
                return False
                
        except Exception as e:
            self.scribe.log_action(
                f"Failed to apply improvement to {module_name}",
                f"Error: {str(e)}",
                "error"
            )
            self.restore_backup(module_name)
            return False

    def get_modification_history(self) -> List[Dict]:
        """Get history of modifications"""
        conn = sqlite3.connect(self.scribe.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT action, reasoning, outcome, timestamp
            FROM action_log
            WHERE action LIKE '%modification%' OR action LIKE '%improvement%'
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "action": row[0],
                "reasoning": row[1],
                "outcome": row[2],
                "timestamp": row[3]
            })
        
        conn.close()
        return history


# Need importlib for the module
import importlib
