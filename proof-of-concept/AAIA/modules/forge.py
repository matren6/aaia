"""
Tool Forge Module - Dynamic Tool Creation System

PURPOSE:
The Forge is the AI's tool-creation capability - it allows the system to
generate and deploy new capabilities dynamically. Rather than being limited
to pre-programmed functions, the AI can create new tools based on need,
using AI to generate the code.

PROBLEM SOLVED:
Traditional AI systems are static - they can only do what they were
programmed to do. The Forge solves this by enabling:
1. Dynamic capability creation: New tools as needed
2. AI-assisted code generation: Use AI to write tool code
3. Safe code validation: Verify generated code before execution
4. Tool lifecycle management: Create, register, use, delete
5. Capability expansion: System can grow beyond original programming

KEY RESPONSIBILITIES:
1. Generate tool code using AI (via router)
2. Validate generated code (syntax, AST parsing)
3. Perform safety checks on generated code
4. Create tool files in tools directory
5. Maintain tool registry
6. Execute tools on demand
7. Delete/manage existing tools
8. Provide tool templates for common operations

WHAT IT CAN CREATE:
- Data processing tools
- File operation tools
- API integration tools
- Analysis tools
- Automation tools
- Any custom functionality needed

SAFETY FEATURES:
- AST parsing to validate code structure
- Checks for dangerous operations (eval, exec, subprocess)
- File system access warnings
- Module wrapping with entry points
- Registry for tracking all tools

DEPENDENCIES: Router, Scribe
OUTPUTS: New tool files, tool metadata, execution results
"""

import os
import json
import ast
import inspect
import re
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional


class Forge:
    """Dynamic tool creation system for extending AI capabilities."""

    def __init__(self, router, scribe, tools_dir: str = "tools"):
        """
        Initialize the Forge with router and scribe dependencies.
        
        Args:
            router: Model router for AI code generation
            scribe: Scribe instance for logging
            tools_dir: Directory to store tools
        """
        self.router = router
        self.scribe = scribe
        self.tools_dir = Path(tools_dir)
        self.tools_dir.mkdir(exist_ok=True)
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_existing_tools()

    def _load_existing_tools(self):
        """Load all existing tools from the tools directory."""
        registry_path = self.tools_dir / "_registry.json"
        if registry_path.exists():
            try:
                self._registry = json.loads(registry_path.read_text())
            except json.JSONDecodeError:
                self._registry = {}
        
        # Also scan for tool files not in registry
        for tool_file in self.tools_dir.glob("*.py"):
            if tool_file.stem.startswith("_"):
                continue
            if tool_file.stem not in self._registry:
                self._registry[tool_file.stem] = {
                    "path": str(tool_file),
                    "status": "discovered"
                }

    def create_tool(
        self,
        name: str,
        description: str,
        code: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new tool from description or provided code.
        
        Args:
            name: Tool name (must be valid Python identifier)
            description: What the tool does
            code: Optional Python function code. If None, AI generates it.
            parameters: Optional parameter schema
            
        Returns:
            Tool metadata dictionary
        """
        # Validate name
        if not name.isidentifier():
            raise ValueError(f"Invalid tool name: {name}")

        # If no code provided, generate using AI
        if code is None:
            code = self._generate_code_with_ai(name, description)
        
        # Validate the code
        validation = self.validate_tool_code(code)
        if not validation["valid"]:
            raise ValueError(f"Generated code is invalid: {validation['error']}")
        
        # Additional safety checks
        safety_issues = self._check_code_safety(code)
        if safety_issues:
            raise ValueError(f"Code failed safety checks: {', '.join(safety_issues)}")

        # Create tool file
        tool_path = self.tools_dir / f"{name}.py"
        
        # Wrap code in proper module structure
        tool_code = self._wrap_tool_code(name, description, code, parameters or {})
        
        # Write tool file
        tool_path.write_text(tool_code)
        
        # Register tool
        metadata = {
            "name": name,
            "description": description,
            "path": str(tool_path),
            "parameters": parameters or {},
            "created_at": self._get_timestamp(),
            "status": "active"
        }
        
        self._registry[name] = metadata
        
        # Save registry
        self._save_registry()
        
        # Log the creation
        self.scribe.log_action(
            f"Created tool: {name}",
            f"Description: {description}",
            "tool_created"
        )
        
        return metadata

    def _generate_code_with_ai(self, name: str, description: str) -> str:
        """
        Use the AI to generate tool code based on description.
        
        Args:
            name: Tool name
            description: What the tool should do
            
        Returns:
            Generated Python code
        """
        # Use router for code generation
        prompt = f"""
Create a Python tool named '{name}' that does the following: {description}

Requirements:
1. The tool should be a single function named 'execute' that takes keyword arguments (**kwargs)
2. The function should return a result dictionary
3. Include proper docstrings
4. The code should be safe, well-documented, and follow best practices
5. Do NOT include any markdown formatting, just pure Python code
6. Do NOT use input(), system calls, or file system operations that could be dangerous

Provide only the Python code for the execute function:
"""
        
        # Use router to get appropriate model for coding
        # First try to get a coding-capable model
        try:
            model_name, model_info = self.router.route_request("coding", "high")
        except Exception:
            # Fallback: try general request
            model_name, model_info = self.router.route_request("general", "medium")
        
        # Call the model
        response = self.router.call_model(
            model_name, 
            prompt, 
            system_prompt="You are a code generation assistant. Generate clean, safe, well-documented Python code. Return only the code, no markdown or explanations."
        )
        
        # Extract code from response (remove any markdown formatting)
        code = self._extract_code_from_response(response)
        
        # Log the generation attempt
        self.scribe.log_action(
            f"AI generated code for tool: {name}",
            f"Model: {model_name}, Description: {description}",
            "code_generated"
        )
        
        return code

    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract clean Python code from AI response.
        Removes markdown formatting if present.
        """
        # Remove markdown code blocks
        code = response.strip()
        
        # Remove ```python and ``` markers
        code = re.sub(r'^```python\s*', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\s*', '', code, flags=re.MULTILINE)
        code = re.sub(r'```$', '', code, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        return code

    def _check_code_safety(self, code: str) -> List[str]:
        """
        Perform basic safety checks on generated code.
        
        Returns:
            List of safety issues found (empty if safe)
        """
        issues = []
        
        # Check for dangerous imports/operations
        dangerous_patterns = [
            (r'\bimport\s+os\s*;', "os module import"),
            (r'\bimport\s+subprocess', "subprocess module import"),
            (r'\bimport\s+sys\s*;', "sys module import"),
            (r'\bimport\s+shutil', "shutil module import"),
            (r'\beval\s*\(', "eval() usage"),
            (r'\bexec\s*\(', "exec() usage"),
            (r'\b__import__\s*\(', "dynamic import"),
            (r'\bopen\s*\(', "file open (requires review)"),
            (r'\bos\.system\s*\(', "os.system call"),
            (r'\bos\.popen\s*\(', "os.popen call"),
        ]
        
        for pattern, issue in dangerous_patterns:
            if re.search(pattern, code):
                issues.append(issue)
        
        return issues

    def _wrap_tool_code(
        self,
        name: str,
        description: str,
        code: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Wrap user code in proper tool structure with metadata."""
        params_json = json.dumps(parameters, indent=2)
        
        wrapped = f'''"""
Tool: {name}
Description: {description}
Parameters: {params_json}
Auto-generated by Forge
"""

def execute(**kwargs):
    """Main execution function for this tool."""
{self._indent_code(code, 4)}
    return result


# Tool execution entry point
if __name__ == "__main__":
    import json
    import sys
    
    # Read input from stdin (JSON)
    stdin_input = sys.stdin.read()
    input_data = json.loads(stdin_input) if stdin_input else {{}}
    result = execute(**input_data)
    print(json.dumps(result))
'''
        return wrapped

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces."""
        indent = " " * spaces
        lines = code.split("\n")
        return "\n".join(indent + line if line.strip() else line for line in lines)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def _save_registry(self):
        """Save tool registry to JSON file."""
        registry_path = self.tools_dir / "_registry.json"
        registry_path.write_text(json.dumps(self._registry, indent=2))

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return list(self._registry.values())

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool."""
        return self._registry.get(name)

    def delete_tool(self, name: str) -> bool:
        """Delete a tool and its file."""
        if name not in self._registry:
            return False
        
        tool_path = Path(self._registry[name]["path"])
        if tool_path.exists():
            tool_path.unlink()
        
        del self._registry[name]
        self._save_registry()
        
        # Log deletion
        self.scribe.log_action(
            f"Deleted tool: {name}",
            "Tool removed from registry",
            "tool_deleted"
        )
        
        return True

    def validate_tool_code(self, code: str) -> Dict[str, Any]:
        """
        Validate tool code without executing it.
        
        Returns:
            Dictionary with validation results
        """
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Check for execute function
            has_execute = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "execute":
                    has_execute = True
                    break
            
            return {
                "valid": True,
                "has_execute": has_execute,
                "ast": tree
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e)
            }

    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name with given parameters.
        
        Note: This is a basic implementation. In production,
        consider using subprocess isolation for security.
        """
        if name not in self._registry:
            raise ValueError(f"Tool not found: {name}")
        
        tool_path = Path(self._registry[name]["path"])
        
        # Dynamic import and execution
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module.execute(**kwargs)


# Example tool templates (as fallback)
TOOL_TEMPLATES = {
    "data_processor": '''def execute(data: list, operation: str = "sum"):
    """Process data with specified operation."""
    result = None
    
    if operation == "sum":
        result = sum(data)
    elif operation == "avg":
        result = sum(data) / len(data) if data else 0
    elif operation == "max":
        result = max(data) if data else None
    elif operation == "min":
        result = min(data) if data else None
    
    return {"result": result, "operation": operation}
''',
    "file_searcher": '''def execute(directory: str, pattern: str = "*", recursive: bool = True):
    """Search for files matching pattern."""
    from pathlib import Path
    
    path = Path(directory)
    if recursive:
        files = list(path.rglob(pattern))
    else:
        files = list(path.glob(pattern))
    
    return {"files": [str(f) for f in files], "count": len(files)}
''',
    "web_fetcher": '''def execute(url: str, method: str = "GET"):
    """Fetch content from a URL."""
    import urllib.request
    
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode("utf-8")
    
    return {"url": url, "status": response.status, "content": content[:1000]}
'''
}
