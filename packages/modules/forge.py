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

from modules.container import DependencyError


class Forge:
    """Dynamic tool creation system for extending AI capabilities."""

    def __init__(self, router, scribe, tools_dir: str = None, event_bus=None, prompt_manager=None, tools_config=None):
        """
        Initialize the Forge with router and scribe dependencies.
        
        Args:
            router: Model router for AI code generation
            scribe: Scribe instance for logging
            tools_dir: Directory to store tools (defaults to config)
            event_bus: Optional EventBus for publishing events
        """

        self.router = router
        self.scribe = scribe
        self.event_bus = event_bus
        self.prompt_manager = prompt_manager

        # Load tools configuration (prefer explicit tools_config, then global config)
        if tools_config is not None:
            self.config = tools_config
        else:
            try:
                from modules.settings import get_config
                self.config = get_config().tools
            except Exception:
                # Fallback to minimal config shape
                class _Fallback:
                    tools_dir = tools_dir or "tools"
                    backup_dir = "backups"
                    auto_discover = True
                    max_tool_size_kb = 500
                    sandbox_mode = True
                    execution_timeout = 30
                self.config = _Fallback()

        # Ensure tools directory exists
        self.tools_dir = Path(self.config.tools_dir)
        self.backup_dir = Path(self.config.backup_dir)
        self.execution_timeout = getattr(self.config, 'execution_timeout', 30)
        self.max_tool_size = getattr(self.config, 'max_tool_size_kb', 500) * 1024
        self.sandbox_mode = getattr(self.config, 'sandbox_mode', True)

        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_existing_tools()
        self._init_performance_tracking()

    def _init_performance_tracking(self):
        """Initialize performance tracking table"""
        try:
            # Create performance tracking table
            self.scribe.db.execute('''
                CREATE TABLE IF NOT EXISTS tool_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    execution_timestamp TEXT NOT NULL,
                    execution_time_ms INTEGER,
                    success INTEGER DEFAULT 1,
                    error TEXT,
                    input_size INTEGER,
                    output_size INTEGER,
                    memory_mb REAL,
                    cpu_percent REAL
                )
            ''')

            # Create index for efficient queries
            self.scribe.db.execute('''
                CREATE INDEX IF NOT EXISTS idx_tool_performance_name 
                ON tool_performance(tool_name, execution_timestamp DESC)
            ''')
        except Exception as e:
            print(f"[WARNING] Performance tracking init failed: {e}")

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
        
        # Publish tool created event
        if self.event_bus is not None:
            try:
                from modules.bus import Event, EventType
                self.event_bus.publish(Event(
                    type=EventType.TOOL_CREATED,
                    data={
                        'name': name,
                        'description': description,
                        'path': str(tool_path)
                    },
                    source='Forge'
                ))
            except ImportError:
                pass
        
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
        # Require centralized prompt template for forge code generation
        if not self.prompt_manager:
            raise DependencyError("PromptManager is required to generate tool code via centralized templates")

        try:
            # Ensure prompt exists
            self.prompt_manager.get_prompt_raw("forge_code_generation")
        except Exception:
            raise DependencyError("Required prompt 'forge_code_generation' not registered in PromptManager")

        pm_prompt = self.prompt_manager.get_prompt(
            "forge_code_generation",
            name=name,
            description=description
        )
        model_name, model_info = self.router.route_request("coding", "high")
        response = self.router.call_model(
            model_name,
            pm_prompt.get("prompt", ""),
            pm_prompt.get("system_prompt", "You are a code generation assistant. Generate clean, safe, well-documented Python code. Return only the code, no markdown or explanations.")
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
        code = re.sub(r'```\$', '', code, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        code = code.strip()

        return code

    def _generate_test_cases(self, name: str, description: str) -> List[Dict]:
        """
        Generate test cases for a tool using AI.

        Args:
            name: Tool name
            description: Tool description

        Returns:
            List of test case dictionaries
        """
        try:
            # Use PromptManager for test generation
            if not self.prompt_manager:
                raise DependencyError("PromptManager required for test generation")

            prompt_data = self.prompt_manager.get_prompt(
                "tool_test_generation",
                tool_name=name,
                tool_description=description
            )

            model_name, _ = self.router.route_request("coding", "medium")
            response = self.router.call_model(
                model_name,
                prompt_data["prompt"],
                system_prompt=prompt_data.get("system_prompt", "You are a test engineer specializing in Python unit tests.")
            )

            # Parse response into test cases
            test_cases = self._parse_test_cases(response)

            # Log generation
            self.scribe.log_action(
                f"Generated test cases for: {name}",
                f"Generated {len(test_cases)} test cases",
                "test_generation_complete"
            )

            return test_cases

        except Exception as e:
            self.scribe.log_action(
                f"Test generation failed for: {name}",
                reasoning=str(e),
                outcome="error"
            )
            return []

    def _parse_test_cases(self, response: str) -> List[Dict]:
        """Parse AI response into structured test cases"""
        test_cases = []
        current_test = {}

        for line in response.split('\n'):
            line = line.strip()
            if not line:
                if current_test and 'name' in current_test:
                    test_cases.append(current_test)
                    current_test = {}
                continue

            if line.upper().startswith('TEST:'):
                if current_test and 'name' in current_test:
                    test_cases.append(current_test)
                current_test = {'name': line.split(':', 1)[1].strip()}
            elif line.upper().startswith('INPUT:'):
                current_test['input'] = self._parse_json_safe(line.split(':', 1)[1].strip())
            elif line.upper().startswith('EXPECTED:'):
                current_test['expected'] = line.split(':', 1)[1].strip()
            elif line.upper().startswith('TYPE:'):
                current_test['type'] = line.split(':', 1)[1].strip().lower()

        if current_test and 'name' in current_test:
            test_cases.append(current_test)

        return test_cases

    def _parse_json_safe(self, text: str) -> Any:
        """Safely parse JSON or return string"""
        try:
            return json.loads(text)
        except:
            return text

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
            (r'\beval\s*$$', "eval() usage"),
            (r'\bexec\s*$$', "exec() usage"),
            (r'\b__import__\s*$$', "dynamic import"),
            (r'\bopen\s*$$', "file open (requires review)"),
            (r'\bos\.system\s*$$', "os.system call"),
            (r'\bos\.popen\s*$$', "os.popen call"),
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

    def _log_tool_execution(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: str = None,
        input_data: Any = None,
        output_data: Any = None
    ):
        """Log tool execution for performance tracking"""
        try:
            import sys
            from datetime import datetime

            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / (1024 * 1024)
                cpu_percent = process.cpu_percent()
            except:
                memory_mb = 0
                cpu_percent = 0

            # Calculate data sizes
            input_size = sys.getsizeof(input_data) if input_data else 0
            output_size = sys.getsizeof(output_data) if output_data else 0

            # Log to database
            self.scribe.db.execute('''
                INSERT INTO tool_performance (
                    tool_name, execution_timestamp, execution_time_ms,
                    success, error, input_size, output_size,
                    memory_mb, cpu_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tool_name,
                datetime.now().isoformat(),
                int(duration_ms * 1000),
                1 if success else 0,
                error[:500] if error else None,
                input_size,
                output_size,
                memory_mb,
                cpu_percent
            ))

        except Exception as e:
            print(f"[WARNING] Performance logging failed: {e}")

    def get_tool_performance(self, tool_name: str, hours: int = 24) -> Dict:
        """
        Get performance statistics for a tool.

        Args:
            tool_name: Tool name
            hours: Hours of history to analyze

        Returns:
            Dict with performance metrics
        """
        from datetime import datetime, timedelta

        since = (datetime.now() - timedelta(hours=hours)).isoformat()

        try:
            rows = self.scribe.db.query('''
                SELECT 
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    AVG(execution_time_ms) as avg_time_ms,
                    MAX(execution_time_ms) as max_time_ms,
                    MIN(execution_time_ms) as min_time_ms,
                    AVG(memory_mb) as avg_memory_mb,
                    AVG(cpu_percent) as avg_cpu_percent
                FROM tool_performance
                WHERE tool_name = ? AND execution_timestamp > ?
            ''', (tool_name, since))

            if not rows:
                return {
                    'tool_name': tool_name,
                    'no_data': True
                }

            row = rows[0]

            return {
                'tool_name': tool_name,
                'period_hours': hours,
                'total_executions': row['total_executions'] or 0,
                'successful': row['successful'] or 0,
                'failed': (row['total_executions'] or 0) - (row['successful'] or 0),
                'success_rate': (row['successful'] / row['total_executions']) if row['total_executions'] else 0,
                'avg_execution_time_ms': row['avg_time_ms'] or 0,
                'max_execution_time_ms': row['max_time_ms'] or 0,
                'min_execution_time_ms': row['min_time_ms'] or 0,
                'avg_memory_mb': row['avg_memory_mb'] or 0,
                'avg_cpu_percent': row['avg_cpu_percent'] or 0
            }
        except Exception as e:
            print(f"[WARNING] Performance query failed: {e}")
            return {'tool_name': tool_name, 'error': str(e)}

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return list(self._registry.values())

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool."""
        return self._registry.get(name)

    def test_tool(self, name: str, test_cases: List[Dict]) -> Dict:
        """
        Test a tool with provided test cases.

        Args:
            name: Tool name
            test_cases: List of test case dictionaries

        Returns:
            Dict with test results
        """
        if name not in self._registry:
            raise ValueError(f"Tool not found: {name}")

        results = {
            'tool': name,
            'total_tests': len(test_cases),
            'passed': 0,
            'failed': 0,
            'errors': [],
            'test_details': []
        }

        for i, test_case in enumerate(test_cases):
            test_name = test_case.get('name', f'Test {i+1}')
            test_input = test_case.get('input', {})
            expected = test_case.get('expected')

            test_result = {
                'name': test_name,
                'status': 'pending',
                'actual_output': None,
                'error': None,
                'execution_time': 0
            }

            try:
                import time
                start_time = time.time()

                # Execute tool with test input
                if isinstance(test_input, dict):
                    actual_output = self.execute_tool(name, **test_input)
                else:
                    actual_output = self.execute_tool(name, input=test_input)

                test_result['execution_time'] = time.time() - start_time
                test_result['actual_output'] = actual_output

                # Validate output
                if self._validate_output(actual_output, expected):
                    test_result['status'] = 'passed'
                    results['passed'] += 1
                else:
                    test_result['status'] = 'failed'
                    test_result['error'] = f"Expected: {expected}, Got: {actual_output}"
                    results['failed'] += 1
                    results['errors'].append(test_result['error'])

            except Exception as e:
                test_result['status'] = 'error'
                test_result['error'] = str(e)
                results['failed'] += 1
                results['errors'].append(f"{test_name}: {str(e)}")

            results['test_details'].append(test_result)

        # Calculate success rate
        results['success_rate'] = results['passed'] / results['total_tests'] if results['total_tests'] > 0 else 0

        # Log test results
        self.scribe.log_action(
            f"Tool testing: {name}",
            reasoning=f"Ran {results['total_tests']} tests",
            outcome=f"Passed: {results['passed']}/{results['total_tests']} ({results['success_rate']:.0%})"
        )

        return results

    def _validate_output(self, actual: Any, expected: Any) -> bool:
        """Validate actual output against expected"""
        if expected is None:
            return True  # No expected output specified

        # String comparison (flexible)
        if isinstance(expected, str):
            actual_str = str(actual)
            return expected.lower() in actual_str.lower()

        # Exact match
        return actual == expected

    def create_tool_with_validation(
        self,
        name: str,
        description: str,
        code: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        auto_test: bool = True,
        min_pass_rate: float = 0.8
    ) -> Dict[str, Any]:
        """
        Create and validate a tool.

        Args:
            name: Tool name
            description: Tool description
            code: Optional pre-written code
            parameters: Optional parameter schema
            auto_test: Whether to automatically test (default: True)
            min_pass_rate: Minimum test pass rate (default: 80%)

        Returns:
            Tool metadata with test results

        Raises:
            ValueError: If tool fails validation
        """
        # Create the tool first
        metadata = self.create_tool(name, description, code, parameters)

        if not auto_test:
            return metadata

        # Generate and run tests
        try:
            test_cases = self._generate_test_cases(name, description)

            if not test_cases:
                # No tests generated - log warning but allow
                self.scribe.log_action(
                    f"Tool created without tests: {name}",
                    reasoning="AI failed to generate test cases",
                    outcome="warning"
                )
                return metadata

            test_results = self.test_tool(name, test_cases)

            # Validate pass rate
            if test_results['success_rate'] < min_pass_rate:
                # Tool failed tests - remove it
                self.delete_tool(name)

                error_summary = f"Tool failed tests: {test_results['passed']}/{test_results['total_tests']} passed ({test_results['success_rate']:.0%})"
                if test_results['errors']:
                    error_summary += f"\nErrors: {'; '.join(test_results['errors'][:3])}"

                raise ValueError(error_summary)

            # Tool passed - add test results to metadata
            metadata['test_results'] = test_results
            metadata['validated'] = True
            metadata['validation_date'] = self._get_timestamp()

            # Update registry
            self._registry[name] = metadata
            self._save_registry()

            return metadata

        except Exception as e:
            # If testing fails, remove the tool
            if name in self._registry:
                self.delete_tool(name)
            raise

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
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name with given parameters and track performance.

        Note: This is a basic implementation. In production,
        consider using subprocess isolation for security.
        """
        if name not in self._registry:
            raise ValueError(f"Tool not found: {name}")

        tool_path = Path(self._registry[name]["path"])

        # Publish tool loaded event
        if self.event_bus is not None:
            try:
                from modules.bus import Event, EventType
                self.event_bus.publish(Event(
                    type=EventType.TOOL_LOADED,
                    data={'name': name, 'parameters': kwargs},
                    source='Forge'
                ))
            except ImportError:
                pass

        # Track execution time
        import time
        start_time = time.time()
        error = None
        result = None

        try:
            # Dynamic import and execution
            import importlib.util
            import signal

            spec = importlib.util.spec_from_file_location(name, tool_path)
            module = importlib.util.module_from_spec(spec)

            def _timeout_handler(signum, frame):
                raise TimeoutError(f"Tool execution exceeded {self.execution_timeout}s")

            # Set alarm if sandboxed and platform supports it
            use_alarm = getattr(self, 'sandbox_mode', True) and hasattr(signal, 'SIGALRM')
            try:
                if use_alarm:
                    signal.signal(signal.SIGALRM, _timeout_handler)
                    signal.alarm(int(self.execution_timeout))

                spec.loader.exec_module(module)
                result = module.execute(**kwargs)
                return result
            finally:
                if use_alarm:
                    try:
                        signal.alarm(0)
                    except Exception:
                        pass

        except Exception as e:
            error = str(e)
            raise

        finally:
            # Log performance
            duration = time.time() - start_time
            self._log_tool_execution(
                tool_name=name,
                duration_ms=duration,
                success=(error is None),
                error=error,
                input_data=kwargs,
                output_data=result
            )

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

    # PHASE 3: SECURITY & QUALITY VALIDATION (NEW)

    def audit_tool_security(self, name: str) -> Dict:
        """
        Perform security audit on a tool.

        Checks for:
        - Dangerous imports (os, subprocess, etc.)
        - File system access
        - Network access
        - System calls
        - Code injection risks

        Returns:
            Dict with audit results
        """
        if name not in self._registry:
            raise ValueError(f"Tool not found: {name}")

        tool_path = Path(self._registry[name]["path"])
        code = tool_path.read_text()

        audit_results = {
            'tool': name,
            'audit_timestamp': self._get_timestamp(),
            'security_level': 'safe',  # safe, warning, dangerous
            'issues': [],
            'warnings': [],
            'recommendations': []
        }

        # Check for dangerous imports
        dangerous_imports = {
            'os': 'File system access',
            'subprocess': 'Process execution',
            'socket': 'Network access',
            'urllib': 'HTTP requests',
            'requests': 'HTTP requests',
            'eval': 'Code execution',
            'exec': 'Code execution',
            '__import__': 'Dynamic imports',
            'pickle': 'Arbitrary code execution',
            'shelve': 'File system access'
        }

        for import_name, risk in dangerous_imports.items():
            if import_name in code:
                if import_name in ['eval', 'exec', 'pickle']:
                    audit_results['security_level'] = 'dangerous'
                    audit_results['issues'].append(f"Uses {import_name}: {risk}")
                else:
                    if audit_results['security_level'] == 'safe':
                        audit_results['security_level'] = 'warning'
                    audit_results['warnings'].append(f"Uses {import_name}: {risk}")

        # Check for file operations
        if 'open(' in code or 'file' in code.lower():
            if audit_results['security_level'] == 'safe':
                audit_results['security_level'] = 'warning'
            audit_results['warnings'].append("File I/O operations detected")

        # AST analysis for deeper inspection
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # Check for eval/exec calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec']:
                            audit_results['security_level'] = 'dangerous'
                            audit_results['issues'].append(f"Direct call to {node.func.id}()")
        except:
            audit_results['warnings'].append("AST parsing failed - manual review required")

        # Recommendations
        if audit_results['security_level'] == 'dangerous':
            audit_results['recommendations'].append("CRITICAL: Review and rewrite without dangerous operations")
            audit_results['recommendations'].append("Consider using restricted execution environment")
        elif audit_results['security_level'] == 'warning':
            audit_results['recommendations'].append("Run in sandboxed environment only")
            audit_results['recommendations'].append("Audit file/network access patterns")
        else:
            audit_results['recommendations'].append("Safe for general use")

        # Log audit
        self.scribe.log_action(
            f"Security audit: {name}",
            reasoning=f"Level: {audit_results['security_level']}",
            outcome=f"{len(audit_results['issues'])} issues, {len(audit_results['warnings'])} warnings"
        )

        return audit_results

    def audit_all_tools(self) -> List[Dict]:
        """Run security audit on all tools"""
        tools = self.list_tools()
        audits = []

        for tool in tools:
            try:
                audit = self.audit_tool_security(tool['name'])
                audits.append(audit)
            except Exception as e:
                audits.append({
                    'tool': tool['name'],
                    'error': str(e)
                })

        return audits

    def check_code_quality(self, code: str) -> Dict:
        """
        Check code quality using multiple metrics.

        Checks:
        - Code complexity (cyclomatic complexity)
        - Code style (PEP 8 compliance)
        - Documentation (docstrings)
        - Error handling
        - Type hints

        Returns:
            Dict with quality metrics
        """
        quality_report = {
            'overall_score': 0,  # 0-100
            'metrics': {},
            'issues': [],
            'recommendations': []
        }

        # 1. Complexity check
        try:
            tree = ast.parse(code)

            complexity_scores = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    complexity_scores.append(complexity)

                    if complexity > 10:
                        quality_report['issues'].append(
                            f"Function '{node.name}' has high complexity: {complexity}"
                        )

            avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
            quality_report['metrics']['avg_complexity'] = avg_complexity
            quality_report['metrics']['max_complexity'] = max(complexity_scores) if complexity_scores else 0

        except Exception as e:
            quality_report['issues'].append(f"Complexity analysis failed: {e}")

        # 2. Documentation check
        has_module_docstring = '"""' in code[:200] or "'''" in code[:200]
        quality_report['metrics']['has_module_docstring'] = has_module_docstring

        if not has_module_docstring:
            quality_report['issues'].append("Missing module docstring")

        # Count functions with docstrings
        try:
            tree = ast.parse(code)
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            documented = [f for f in functions if ast.get_docstring(f)]

            doc_ratio = len(documented) / len(functions) if functions else 0
            quality_report['metrics']['documentation_ratio'] = doc_ratio

            if doc_ratio < 0.8:
                quality_report['recommendations'].append(
                    f"Only {doc_ratio:.0%} of functions have docstrings"
                )
        except:
            pass

        # 3. Error handling check
        has_try_except = 'try:' in code
        quality_report['metrics']['has_error_handling'] = has_try_except

        if not has_try_except:
            quality_report['recommendations'].append("Consider adding error handling")

        # 4. Type hints check
        has_type_hints = '->' in code or ': ' in code
        quality_report['metrics']['has_type_hints'] = has_type_hints

        if not has_type_hints:
            quality_report['recommendations'].append("Consider adding type hints")

        # 5. Calculate overall score
        score = 100

        # Complexity penalty
        if quality_report['metrics'].get('max_complexity', 0) > 10:
            score -= 20
        elif quality_report['metrics'].get('avg_complexity', 0) > 7:
            score -= 10

        # Documentation bonus/penalty
        if quality_report['metrics'].get('documentation_ratio', 0) >= 0.8:
            score += 0  # No bonus, this is expected
        else:
            score -= 15

        if not has_module_docstring:
            score -= 10

        # Error handling
        if not has_try_except:
            score -= 10

        # Type hints
        if not has_type_hints:
            score -= 5

        quality_report['overall_score'] = max(0, min(100, score))

        return quality_report

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Each decision point adds 1
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or operators
                complexity += len(child.values) - 1

        return complexity

    def check_tool_quality(self, name: str) -> Dict:
        """Check quality of an existing tool"""
        if name not in self._registry:
            raise ValueError(f"Tool not found: {name}")

        tool_path = Path(self._registry[name]["path"])
        code = tool_path.read_text()

        quality = self.check_code_quality(code)
        quality['tool'] = name
        quality['check_timestamp'] = self._get_timestamp()

        # Log quality check
        self.scribe.log_action(
            f"Quality check: {name}",
            reasoning=f"Overall score: {quality['overall_score']}/100",
            outcome=f"{len(quality['issues'])} issues found"
        )

        return quality

    def execute_tool_sandbox(self, name: str, **kwargs) -> Any:
        """
        Execute tool in isolated subprocess for enhanced security.

        This provides:
        - Process isolation
        - Resource limits
        - Timeout enforcement
        - Memory limits

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: Tool not found
            TimeoutError: Execution exceeded timeout
            RuntimeError: Tool execution failed
        """
        if name not in self._registry:
            raise ValueError(f"Tool not found: {name}")

        tool_path = Path(self._registry[name]["path"])

        import subprocess
        import tempfile

        # Prepare input as JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(kwargs, f)
            input_file = f.name

        # Prepare output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name

        try:
            # Build sandbox command
            sandbox_script = self._create_sandbox_script(tool_path, input_file, output_file)

            # Execute in subprocess with limits
            try:
                import resource
                has_resource_limits = True
            except ImportError:
                has_resource_limits = False

            # Determine if we can use preexec_fn (Unix only)
            preexec_fn = None
            if has_resource_limits and hasattr(os, 'setrlimit'):
                preexec_fn = self._set_resource_limits

            proc = subprocess.Popen(
                ['python3', sandbox_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=preexec_fn
            )

            # Wait with timeout
            try:
                stdout, stderr = proc.communicate(timeout=self.execution_timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise TimeoutError(f"Tool execution exceeded {self.execution_timeout}s timeout")

            # Check return code
            if proc.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                raise RuntimeError(f"Tool execution failed: {error_msg}")

            # Read result
            with open(output_file, 'r') as f:
                result = json.load(f)

            return result.get('output')

        finally:
            # Cleanup temp files
            for f in [input_file, output_file]:
                try:
                    os.unlink(f)
                except:
                    pass
            try:
                os.unlink(sandbox_script)
            except:
                pass

    def _create_sandbox_script(self, tool_path: Path, input_file: str, output_file: str) -> str:
        """Create temporary Python script for sandboxed execution"""
        import tempfile

        script_content = f'''
import json
import sys
import traceback

try:
    # Load input
    with open("{input_file}", "r") as f:
        kwargs = json.load(f)

    # Import and execute tool
    sys.path.insert(0, "{tool_path.parent}")
    import {tool_path.stem} as tool_module

    result = tool_module.execute(**kwargs)

    # Save output
    with open("{output_file}", "w") as f:
        json.dump({{"output": result, "success": True}}, f)

    sys.exit(0)

except Exception as e:
    # Save error
    with open("{output_file}", "w") as f:
        json.dump({{
            "output": None,
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }}, f)
    sys.exit(1)
'''

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            return f.name

    def _set_resource_limits(self):
        """Set resource limits for subprocess (Unix only)"""
        try:
            import resource

            # Limit memory to 512MB
            memory_limit = 512 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

            # Limit CPU time to 30 seconds
            resource.setrlimit(resource.RLIMIT_CPU, (30, 30))

            # Limit number of processes
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
        except Exception as e:
            print(f"[WARNING] Failed to set resource limits: {e}")


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