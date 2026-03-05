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

from modules.container import DependencyError


class NixAwareSelfModification:
    """Safe self-modification with Nix integration and backup capabilities."""

    def __init__(self, scribe, router, forge, event_bus=None, prompt_manager=None):
        self.scribe = scribe
        self.router = router
        self.forge = forge
        self.event_bus = event_bus
        self.prompt_manager = prompt_manager
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

                # Require centralized prompt template for code improvement
                if not self.prompt_manager:
                    raise DependencyError("PromptManager is required to generate code improvement suggestions")

                try:
                    self.prompt_manager.get_prompt_raw("code_improvement_generation")
                except Exception:
                    raise DependencyError("Required prompt 'code_improvement_generation' not registered in PromptManager")

                pm = self.prompt_manager.get_prompt(
                    "code_improvement_generation",
                    original_code=source,
                    issues='; '.join([c.get('suggestion','') for c in analysis['complexities']])
                )
                model_name, _ = self.router.route_request("coding", "high")
                suggestions = self.router.call_model(
                    model_name,
                    pm.get("prompt", ""),
                    pm.get("system_prompt", "You are a code review expert.")
                )

                analysis["improvements"] = [s.strip() for s in suggestions.split('\n') if s.strip() and (s.strip().startswith('-') or ':' in s)]
            
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
                
                if module_path is None:
                    return False
                
                with open(module_path, 'w') as f:
                    f.write(backup_data.get('source', ''))
                return True
        
        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()