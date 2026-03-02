#!/usr/bin/env python3
"""
Prompt Migration Analyzer

Scans the AAIA codebase to identify hardcoded AI prompts that should be
migrated to use the PromptManager class.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PromptIssue:
    """Represents a hardcoded prompt found in the code."""
    file_path: str
    line_number: int
    issue_type: str  # 'inline', 'multiline', 'f-string', 'variable'
    context: str
    snippet: str
    suggested_prompt_name: str
    priority: str  # 'high', 'medium', 'low'


class PromptAnalyzer:
    """Analyzes codebase for hardcoded prompts."""

    def __init__(self, base_path: str = "packages/modules"):
        self.base_path = Path(base_path)
        self.issues: List[PromptIssue] = []
        self.prompt_manager_patterns = self._load_prompt_manager_patterns()
        self.excluded_files = {
            'prompt_optimizer.py',
            'setup.py'
        }
        
    def _load_prompt_manager_patterns(self) -> Dict[str, str]:
        """Load patterns of existing prompts from PromptManager files."""
        patterns = {}
        prompts_dir = Path("packages/prompts")
        
        if prompts_dir.exists():
            for prompt_file in prompts_dir.rglob("*.json"):
                try:
                    import json
                    with open(prompt_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                if 'name' in item and 'template' in item:
                                    patterns[item['name']] = item['template']
                        elif 'name' in data and 'template' in data:
                            patterns[data['name']] = data['template']
                except Exception:
                    pass
        
        return patterns

    def analyze(self) -> List[PromptIssue]:
        """Analyze all Python files in the codebase."""
        if not self.base_path.exists():
            print(f"Error: Base path {self.base_path} does not exist")
            return []
        
        print(f"Scanning {self.base_path} for hardcoded prompts...")
        print(f"Excluded files: {self.excluded_files}")
        print()
        
        for py_file in self.base_path.rglob("*.py"):
            if py_file.name in self.excluded_files:
                continue
            
            self._analyze_file(py_file)
        
        # Sort issues by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        self.issues.sort(key=lambda x: priority_order[x.priority])
        
        return self.issues

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return

        # Check if file already uses PromptManager
        uses_prompt_manager = self._check_prompt_manager_usage(content)
        
        # Analyze AST for string literals
        tree = ast.parse(content, filename=str(file_path))
        
        # Find potential prompt strings in the AST
        self._find_string_literals(file_path, tree, lines, uses_prompt_manager)
        
        # Find router.call_model calls
        self._find_router_calls(file_path, tree, lines)

    def _check_prompt_manager_usage(self, content: str) -> bool:
        """Check if file already uses PromptManager."""
        indicators = [
            'from prompts import',
            'from prompts.manager import',
            'PromptManager',
            'get_prompt_manager',
            'prompt_manager.get_prompt'
        ]
        
        for indicator in indicators:
            if indicator in content:
                return True
        return False

    def _find_string_literals(self, file_path: Path, tree: ast.AST, lines: List[str], uses_pm: bool):
        """Find string literals that might be prompts."""
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Str):  # Python 3.7 and earlier
                self._check_string_node(file_path, node, node.s, lines, uses_pm)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):  # Python 3.8+
                self._check_string_node(file_path, node, node.value, lines, uses_pm)

    def _check_string_node(self, file_path: Path, node: ast.AST, string_value: str, lines: List[str], uses_pm: bool):
        """Check if a string node contains a prompt."""
        if not string_value or len(string_value) < 50:
            return
            
        line_num = getattr(node, 'lineno', 0)
        if line_num <= 0:
            return
        
        line_content = lines[line_num - 1]
        context = self._get_context(lines, line_num - 1)
        
        # Check for prompt indicators
        prompt_indicators = [
            'Analyze this',
            'As an AI',
            'You are a',
            'Based on this',
            'Suggest',
            'Generate',
            'Provide',
            'Identify',
            'Response format',
            'Consider',
            'Analyze the following'
        ]
        
        # Calculate score
        indicator_count = sum(1 for indicator in prompt_indicators if indicator.lower() in string_value.lower())
        
        # Check for multi-line prompt structure
        has_newlines = '\n\n' in string_value
        has_structure = ':' in string_value and len(string_value.split('\n')) > 2
        
        # Determine if this is likely a prompt
        score = indicator_count + (2 if has_newlines else 0) + (1 if has_structure else 0)
        
        if score >= 2:
            # Determine issue type
            issue_type = 'multiline' if has_newlines else 'inline'
            
            # Determine priority
            if not uses_pm and indicator_count >= 2:
                priority = 'high'
            elif not uses_pm:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Suggest prompt name
            suggested_name = self._suggest_prompt_name(file_path.name, line_num, string_value)
            
            self.issues.append(PromptIssue(
                file_path=str(file_path.relative_to(self.base_path.parent)),
                line_number=line_num,
                issue_type=issue_type,
                context=context,
                snippet=string_value[:100] + '...' if len(string_value) > 100 else string_value,
                suggested_prompt_name=suggested_name,
                priority=priority
            ))

    def _find_router_calls(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Find router.call_model calls with inline prompts."""
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's a call to router.call_model
                if self._is_router_call(node):
                    # Get the prompt argument (usually second argument)
                    prompt_arg = self._get_prompt_argument(node)
                    if prompt_arg:
                        line_num = getattr(node, 'lineno', 0)
                        if line_num > 0:
                            context = self._get_context(lines, line_num - 1)
                            
                            # Get the actual prompt string if available
                            prompt_string = self._extract_string_from_arg(prompt_arg, lines)
                            
                            if prompt_string and len(prompt_string) > 50:
                                suggested_name = self._suggest_prompt_name(file_path.name, line_num, prompt_string)
                                
                                self.issues.append(PromptIssue(
                                    file_path=str(file_path.relative_to(self.base_path.parent)),
                                    line_number=line_num,
                                    issue_type='router_call',
                                    context=context,
                                    snippet=prompt_string[:100] + '...' if len(prompt_string) > 100 else prompt_string,
                                    suggested_prompt_name=suggested_name,
                                    priority='high'
                                ))

    def _is_router_call(self, node: ast.Call) -> bool:
        """Check if a call node is calling router.call_model."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'call_model'
        return False

    def _get_prompt_argument(self, node: ast.Call) -> ast.AST:
        """Get the prompt argument from a router.call_model call."""
        # Typically: router.call_model(model_name, prompt, system_prompt)
        # So prompt is the second argument (index 1)
        args = node.args
        if len(args) >= 2:
            return args[1]
        return None

    def _extract_string_from_arg(self, arg: ast.AST, lines: List[str]) -> str:
        """Extract the actual string value from an argument node."""
        if isinstance(arg, ast.Str):
            return arg.s
        elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        elif isinstance(arg, ast.JoinedStr):  # f-string
            # Reconstruct f-string from lines
            line_num = getattr(arg, 'lineno', 0)
            if 0 < line_num <= len(lines):
                return lines[line_num - 1].strip()
        return ''

    def _get_context(self, lines: List[str], line_idx: int, context_lines: int = 2) -> str:
        """Get surrounding context for a line."""
        start = max(0, line_idx - context_lines)
        end = min(len(lines), line_idx + context_lines + 1)
        return '\n'.join(lines[start:end])

    def _suggest_prompt_name(self, filename: str, line_num: int, prompt_content: str) -> str:
        """Suggest a name for the prompt based on context."""
        # Extract filename base
        module_name = filename.replace('.py', '')
        
        # Look for keywords in prompt
        keywords = {
            'analyze': 'analysis',
            'suggest': 'suggestion',
            'generate': 'generation',
            'optimize': 'optimization',
            'reflect': 'reflection',
            'predict': 'prediction',
            'diagnose': 'diagnosis',
            'improve': 'improvement',
            'create': 'creation',
            'plan': 'planning',
            'review': 'review',
            'strategy': 'strategy'
        }
        
        prompt_lower = prompt_content.lower()
        for keyword, suffix in keywords.items():
            if keyword in prompt_lower:
                return f"{module_name}_{suffix}"
        
        # Default: use module name with line number
        return f"{module_name}_prompt_{line_num}"

    def generate_report(self) -> str:
        """Generate a comprehensive migration report."""
        if not self.issues:
            return "✓ No hardcoded prompts found! All modules appear to use PromptManager."
        
        # Group by file
        issues_by_file = defaultdict(list)
        for issue in self.issues:
            issues_by_file[issue.file_path].append(issue)
        
        report_lines = [
            "# Prompt Migration Analysis Report",
            "",
            f"Found {len(self.issues)} hardcoded prompts that should be migrated to PromptManager",
            f"Files affected: {len(issues_by_file)}",
            "",
            "## Issues by Priority",
            "",
        ]
        
        # Count by priority
        priority_counts = defaultdict(int)
        for issue in self.issues:
            priority_counts[issue.priority] += 1
        
        for priority in ['high', 'medium', 'low']:
            count = priority_counts[priority]
            if count > 0:
                report_lines.append(f"- {priority.upper()}: {count} issues")
        
        report_lines.extend([
            "",
            "## Issues by File",
            ""
        ])
        
        # List issues by file
        for file_path in sorted(issues_by_file.keys()):
            issues = issues_by_file[file_path]
            report_lines.append(f"### {file_path}")
            report_lines.append(f"Total issues: {len(issues)}")
            report_lines.append("")
            
            for issue in issues:
                report_lines.append(f"- Line {issue.line_number} [{issue.priority.upper()}]")
                report_lines.append(f"  Type: {issue.issue_type}")
                report_lines.append(f"  Suggested prompt: `{issue.suggested_prompt_name}`")
                report_lines.append(f"  Context:")
                for context_line in issue.context.split('\n'):
                    report_lines.append(f"    {context_line}")
                report_lines.append(f"  Snippet: `{issue.snippet}`")
                report_lines.append("")
        
        report_lines.extend([
            "",
            "## Migration Recommendations",
            "",
            "1. **High Priority Issues**: These are likely router.call_model calls with inline prompts",
            "   - Extract the prompt template to a JSON file in packages/prompts/",
            "   - Replace inline prompt with pm.get_prompt('prompt_name', **params)",
            "",
            "2. **Medium Priority Issues**: These are multi-line prompts not in router calls",
            "   - Extract to PromptManager if they're complex or reused",
            "   - Consider parameterizing dynamic parts",
            "",
            "3. **Low Priority Issues**: These are already using PromptManager or are simple strings",
            "   - Review to ensure they're properly parameterized",
            "   - May not need migration if they're one-time use",
            "",
            "## Example Migration",
            "",
            "Before:",
            "```python",
            "prompt = '''",
            "Analyze this Python module for improvement opportunities:",
            "Module: {module_name}",
            "Lines: {lines_of_code}",
            "```",
            "response = self.router.call_model(model_name, prompt, system_prompt)",
            "```",
            "",
            "After:",
            "```python",
            "from prompts import get_prompt_manager",
            "",
            "pm = get_prompt_manager()",
            "prompt_data = pm.get_prompt(",
            "    'code_improvement_analysis',",
            "    module_name=module_name,",
            "    lines_of_code=lines_of_code",
            "    function_count=function_count,",
            "    complex_functions=[c['function'] for c in complexities]",
            ")",
            "response = self.router.call_model(",
            "    model_name,",
            "    prompt_data['prompt'],",
            "    prompt_data['system_prompt']",
            ")",
            "```"
        ])
        
        return '\n'.join(report_lines)

    def generate_summary(self) -> str:
        """Generate a brief summary of findings."""
        if not self.issues:
            return "✓ No hardcoded prompts found!"
        
        # Count by priority
        priority_counts = defaultdict(int)
        file_counts = defaultdict(int)
        
        for issue in self.issues:
            priority_counts[issue.priority] += 1
            file_counts[issue.file_path] += 1
        
        lines = [
            f"Found {len(self.issues)} hardcoded prompts across {len(file_counts)} files:",
            ""
        ]
        
        for priority in ['high', 'medium', 'low']:
            count = priority_counts[priority]
            if count > 0:
                lines.append(f"  {priority.upper()}: {count}")
        
        lines.extend([
            "",
            "Files with the most issues:",
            ""
        ])
        
        # Sort files by issue count
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        for file_path, count in sorted_files[:5]:
            lines.append(f"  {file_path}: {count} issues")
        
        return '\n'.join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze codebase for hardcoded AI prompts needing migration to PromptManager"
    )
    parser.add_argument(
        "--path",
        default="packages/modules",
        help="Path to analyze (default: packages/modules)"
    )
    parser.add_argument(
        "--output",
        help="Output file for the report (default: stdout)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only a brief summary"
    )
    
    args = parser.parse_args()
    
    analyzer = PromptAnalyzer(base_path=args.path)
    analyzer.analyze()
    
    if args.summary:
        report = analyzer.generate_summary()
    else:
        report = analyzer.generate_report()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()