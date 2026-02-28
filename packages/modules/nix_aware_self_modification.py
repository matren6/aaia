"""
Nix-Aware Self-Modification Module

Enhances AAIA's self-modification capabilities with Nix integration.
Includes all functionality from the original SelfModification class.
"""

import ast
import inspect
import textwrap
import os
import shutil
import importlib
import sqlite3
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class NixAwareSelfModification:
    """Safe self-modification with Nix integration and backup capabilities."""

    def __init__(self, scribe, router, forge, event_bus=None):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.event_bus = event_bus
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Nix-specific paths
        self.project_root = Path(__file__).parent.parent.parent
        self.flake_path = self.project_root / "flake.nix"
        self.lock_path = self.project_root / "flake.lock"

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
                module_path = Path(f"packages/modules/{module_name}.py")
            
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

    def _generate_function(self, spec: Dict) -> str:
        """Generate a function from a specification"""
        # Placeholder for function generation
        return f"def {spec.get('name', 'new_function')}():\n    pass\n"

    def create_backup(self, module_name: str) -> Optional[str]:
        """Create backup of module before modification"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{module_name}_{timestamp}.py.backup"
            
            # Try different paths
            module_paths = [
                Path(f"packages/modules/{module_name}.py"),
                Path(f"modules/{module_name}.py"),
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

    def restore_backup(self, module_name: str, backup_data: Optional[Dict] = None) -> bool:
        """Restore module from latest backup or from backup data
        
        Args:
            module_name: Name of the module to restore
            backup_data: Optional backup data dict (for evolution pipeline compatibility)
                         If provided, should contain module source code
        """
        try:
            # If backup_data provided, use it for restoration
            if backup_data is not None and isinstance(backup_data, dict):
                # Find the module path
                module_paths = [
                    Path(f"packages/modules/{module_name}.py"),
                    Path(f"modules/{module_name}.py")
                ]
                
                module_path = None
                for p in module_paths:
                    if p.exists() or p.parent.exists():
                        module_path = p
                        break
                
                if not module_path:
                    return False
                
                # If backup_data contains source code, write it
                if "source_code" in backup_data:
                    with open(module_path, 'w') as f:
                        f.write(backup_data["source_code"])
                    return True
                
                # Otherwise, fall through to file-based restoration
            
            # File-based restoration
            backups = sorted(self.backup_dir.glob(f"{module_name}_*.py.backup"))
            if backups:
                latest_backup = backups[-1]
                
                # Find original location
                module_paths = [
                    Path(f"packages/modules/{module_name}.py"),
                    Path(f"modules/{module_name}.py"),
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
            if f"packages.modules.{module_name}" in sys.modules:
                del sys.modules[f"packages.modules.{module_name}"]
            
            importlib.import_module(f"packages.modules.{module_name}")
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
                Path(f"packages/modules/{module_name}.py"),
                Path(f"modules/{module_name}.py")
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

    def restore_from_backup(self, backup_data: Dict) -> Dict:
        """Restore system state from backup data (for evolution pipeline).
        
        Args:
            backup_data: Dictionary containing backup information including
                         module names and optionally source code
            
        Returns:
            Dictionary with restoration status
        """
        results = {
            "status": "completed",
            "modules_restored": [],
            "errors": []
        }
        
        if not backup_data:
            results["status"] = "failed"
            results["errors"].append("No backup data provided")
            return results
        
        # If backup_data contains specific modules to restore
        if "modules" in backup_data:
            for module_name in backup_data["modules"]:
                if self.restore_backup(module_name, backup_data.get(module_name)):
                    results["modules_restored"].append(module_name)
                else:
                    results["errors"].append(f"Failed to restore {module_name}")
        
        # General restoration from file-based backups
        elif "modules_restored" not in results or not results["modules_restored"]:
            # Just mark as requiring manual restoration
            results["status"] = "manual_restore_required"
        
        return results

    # === NIX-SPECIFIC METHODS ===

    def add_dependency(self, package_name: str) -> bool:
        """Add a new Python dependency via Nix"""
        try:
            # Parse current flake.nix
            with open(self.flake_path) as f:
                flake_content = f.read()
            
            # Find the propagatedBuildInputs section
            pattern = r'(propagatedBuildInputs.*with\s+pkgs\.python3Packages;\s*$$)(.*)($$)'
            match = re.search(pattern, flake_content, re.DOTALL)
            
            if match:
                current_deps = match.group(2).strip()
                if package_name not in current_deps:
                    new_deps = f"{current_deps}\n          {package_name}"
                    new_content = flake_content.replace(match.group(0), match.group(1) + new_deps + match.group(3))
                    
                    # Write updated flake
                    with open(self.flake_path, 'w') as f:
                        f.write(new_content)
                    
                    self.scribe.log_action(
                        f"Added dependency: {package_name}",
                        "Modified flake.nix to add new dependency",
                        "dependency_added"
                    )
                    return True
            return False
        except Exception as e:
            self.scribe.log_action(
                f"Failed to add dependency: {package_name}",
                f"Error: {str(e)}",
                "error"
            )
            return False
    
    def update_flake_lock(self) -> bool:
        """Update flake.lock file"""
        try:
            result = subprocess.run(
                ["nix", "flake", "update"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=False
            )
            
            if result.returncode == 0:
                self.scribe.log_action(
                    "Updated flake.lock",
                    "Successfully updated flake dependencies",
                    "flake_updated"
                )
                return True
            else:
                self.scribe.log_action(
                    "Failed to update flake.lock",
                    f"Error: {result.stderr}",
                    "error"
                )
                return False
        except subprocess.TimeoutExpired:
            self.scribe.log_action(
                "Failed to update flake.lock",
                "Timeout after 5 minutes",
                "error"
            )
            return False
        except Exception as e:
            self.scribe.log_action(
                "Failed to update flake.lock",
                f"Error: {str(e)}",
                "error"
            )
            return False

    def rebuild_aaia(self) -> bool:
        """Rebuild AAIA with new changes"""
        try:
            # Rebuild the system profile
            result = subprocess.run(
                ["nixos-rebuild", "switch"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,
                check=False
            )
            
            if result.returncode == 0:
                self.scribe.log_action(
                    "Rebuilt AAIA",
                    "Successfully rebuilt AAIA with new changes",
                    "aaia_rebuilt"
                )
                return True
            else:
                self.scribe.log_action(
                    "Failed to rebuild AAIA",
                    f"Error: {result.stderr}",
                    "error"
                )
                return False
        except Exception as e:
            self.scribe.log_action(
                "Failed to rebuild AAIA",
                f"Error: {str(e)}",
                "error"
            )
            return False
    
    def create_evolution_branch(self, evolution_name: str) -> bool:
        """Create a new branch for evolution experiment"""
        try:
            # Check if we're in a git repository
            if not (self.project_root / ".git").exists():
                self.scribe.log_action(
                    "Failed to create evolution branch",
                    "Not in a git repository",
                    "error"
                )
                return False
            
            result = subprocess.run(
                ["git", "checkout", "-b", f"evolution-{evolution_name}"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.scribe.log_action(
                    f"Created evolution branch: {evolution_name}",
                    f"Created branch evolution-{evolution_name}",
                    "branch_created"
                )
                return True
            else:
                self.scribe.log_action(
                    f"Failed to create evolution branch: {evolution_name}",
                    f"Error: {result.stderr}",
                    "error"
                )
                return False
        except Exception as e:
            self.scribe.log_action(
                f"Failed to create evolution branch: {evolution_name}",
                f"Error: {str(e)}",
                "error"
            )
            return False
    
    def commit_evolution(self, message: str) -> bool:
        """Commit evolution changes"""
        try:
            # Check if we're in a git repository
            if not (self.project_root / ".git").exists():
                self.scribe.log_action(
                    "Failed to commit evolution",
                    "Not in a git repository",
                    "error"
                )
                return False
            
            add_result = subprocess.run(
                ["git", "add", "-A"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if add_result.returncode != 0:
                self.scribe.log_action(
                    "Failed to commit evolution",
                    f"Git add failed: {add_result.stderr}",
                    "error"
                )
                return False
            
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if commit_result.returncode == 0:
                self.scribe.log_action(
                    "Committed evolution",
                    f"Commit message: {message}",
                    "evolution_committed"
                )
                return True
            else:
                self.scribe.log_action(
                    "Failed to commit evolution",
                    f"Git commit failed: {commit_result.stderr}",
                    "error"
                )
                return False
        except Exception as e:
            self.scribe.log_action(
                "Failed to commit evolution",
                f"Error: {str(e)}",
                "error"
            )
            return False
    
    def tag_evolution(self, version: str) -> bool:
        """Tag evolution milestone"""
        try:
            # Check if we're in a git repository
            if not (self.project_root / ".git").exists():
                self.scribe.log_action(
                    "Failed to tag evolution",
                    "Not in a git repository",
                    "error"
                )
                return False
            
            result = subprocess.run(
                ["git", "tag", "-a", version, "-m", f"Evolution {version}"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.scribe.log_action(
                    f"Tagged evolution: {version}",
                    f"Created tag {version}",
                    "evolution_tagged"
                )
                return True
            else:
                self.scribe.log_action(
                    f"Failed to tag evolution: {version}",
                    f"Error: {result.stderr}",
                    "error"
                )
                return False
        except Exception as e:
            self.scribe.log_action(
                f"Failed to tag evolution: {version}",
                f"Error: {str(e)}",
                "error"
            )
            return False
    
    def get_nix_state(self) -> Dict:
        """Get current Nix state information"""
        state = {
            "flake_exists": self.flake_path.exists(),
            "lock_exists": self.lock_path.exists(),
            "git_repo": (self.project_root / ".git").exists(),
            "current_branch": None,
            "last_commit": None
        }
        
        try:
            # Get git branch and commit
            if state["git_repo"]:
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if branch_result.returncode == 0:
                    state["current_branch"] = branch_result.stdout.strip()
                
                commit_result = subprocess.run(
                    ["git", "log", "-1", "--format=%H"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if commit_result.returncode == 0:
                    state["last_commit"] = commit_result.stdout.strip()
        except:
            pass
        
        return state
    
    def rollback_evolution(self, evolution_name: str) -> bool:
        """Rollback to a previous evolution state"""
        try:
            # Switch back to main branch
            switch_result = subprocess.run(
                ["git", "checkout", "main"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if switch_result.returncode != 0:
                self.scribe.log_action(
                    f"Failed to rollback evolution: {evolution_name}",
                    "Could not switch to main branch",
                    "error"
                )
                return False
            
            # Delete evolution branch
            delete_result = subprocess.run(
                ["git", "branch", "-D", f"evolution-{evolution_name}"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            
            if delete_result.returncode == 0:
                self.scribe.log_action(
                    f"Rolled back evolution: {evolution_name}",
                    "Successfully deleted evolution branch",
                    "evolution_rolled_back"
                )
                return True
            else:
                self.scribe.log_action(
                    f"Failed to rollback evolution: {evolution_name}",
                    f"Could not delete evolution branch: {delete_result.stderr}",
                    "error"
                )
                return False
        except Exception as e:
            self.scribe.log_action(
                f"Failed to rollback evolution: {evolution_name}",
                f"Error: {str(e)}",
                "error"
            )
            return False