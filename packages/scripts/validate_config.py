#!/usr/bin/env python3
"""
Configuration Validation Tool

Validates that all modules use config correctly:
- No hardcoded values  
- Config values are accessed
- Required config exists
"""

import sys
from pathlib import Path
import ast
import inspect

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.settings import SystemConfig, get_config
from modules.container import get_container
from modules.setup import SystemBuilder


class ConfigUsageChecker(ast.NodeVisitor):
    """AST visitor to check config usage"""
    
    def __init__(self):
        self.hardcoded_values = []
        self.config_accesses = []
    
    def visit_Assign(self, node):
        """Check assignments for hardcoded values"""
        # Check for hardcoded numbers/strings being assigned
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.lower()
                
                # Check if looks like config value
                if any(keyword in var_name for keyword in ['timeout', 'interval', 'retry', 'max', 'limit']):
                    if isinstance(node.value, ast.Constant):
                        self.hardcoded_values.append({
                            'var': var_name,
                            'value': node.value.value,
                            'line': node.lineno
                        })
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Track config accesses"""
        # Check for self.config.something patterns
        if isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name):
                if node.value.value.id == 'self' and node.value.attr == 'config':
                    self.config_accesses.append({
                        'attribute': node.attr,
                        'line': node.lineno
                    })
        
        self.generic_visit(node)


def check_module_config_usage(module_path: Path) -> dict:
    """Check a module's config usage"""
    try:
        with open(module_path, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        checker = ConfigUsageChecker()
        checker.visit(tree)
        
        return {
            'path': str(module_path),
            'hardcoded': checker.hardcoded_values,
            'config_accesses': checker.config_accesses
        }
    
    except Exception as e:
        return {
            'path': str(module_path),
            'error': str(e)
        }


def validate_config_complete():
    """Validate that all required config values exist"""
    config = get_config()
    
    print("\n" + "="*70)
    print("Configuration Completeness Check")
    print("="*70)
    
    issues = []
    
    # Check LLM configs
    for provider_name in ['ollama', 'openai', 'github', 'azure', 'venice']:
        provider = getattr(config.llm, provider_name, None)
        if provider and provider.enabled:
            if not provider.timeout:
                issues.append(f"{provider_name}: Missing timeout")
            if not provider.max_retries:
                issues.append(f"{provider_name}: Missing max_retries")
    
    # Check scheduler config
    if config.scheduler.diagnosis_interval <= 0:
        issues.append("scheduler: Invalid diagnosis_interval")
    if config.scheduler.health_check_interval <= 0:
        issues.append("scheduler: Invalid health_check_interval")
    
    # Check tools config
    if not config.tools.tools_dir:
        issues.append("tools: Missing tools_dir")
    
    # Check evolution config
    if config.evolution.max_retries <= 0:
        issues.append("evolution: Invalid max_retries")
    
    if issues:
        print("\n❌ Configuration Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ Configuration is complete")
        return True


def validate_modules_use_config():
    """Validate modules use config instead of hardcoded values"""
    packages_dir = Path(__file__).parent.parent
    modules_dir = packages_dir / "packages" / "modules"
    
    print("\n" + "="*70)
    print("Module Configuration Usage Check")
    print("="*70)
    
    results = []
    
    for module_file in modules_dir.glob("*.py"):
        if module_file.name.startswith('_'):
            continue
        
        result = check_module_config_usage(module_file)
        if result.get('hardcoded') or result.get('error'):
            results.append(result)
    
    if results:
        print(f"\n⚠️  Found {len(results)} modules with potential issues:\n")
        
        for result in results:
            print(f"\n{result['path']}")
            print("-" * 70)
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
            
            if result.get('hardcoded'):
                print(f"  Hardcoded values:")
                for hc in result['hardcoded'][:5]:
                    print(f"    Line {hc['line']}: {hc['var']} = {hc['value']}")
            
            if result.get('config_accesses'):
                print(f"  Config accesses: {len(result['config_accesses'])}")
    else:
        print("\n✓ All modules use config correctly")
    
    return len(results) == 0


def print_config_summary():
    """Print summary of current configuration"""
    config = get_config()
    
    print("\n" + "="*70)
    print("Current Configuration Summary")
    print("="*70)
    
    print("\nLLM Providers:")
    print(f"  Default: {config.llm.default_provider}")
    print(f"  Fallback: {config.llm.fallback_provider or 'None'}")
    
    for provider_name in ['ollama', 'openai', 'github', 'azure', 'venice']:
        provider = getattr(config.llm, provider_name)
        status = "✓ Enabled" if provider.enabled else "✗ Disabled"
        print(f"  {provider_name}: {status}")
        if provider.enabled:
            print(f"    - Timeout: {provider.timeout}s")
            print(f"    - Max Retries: {provider.max_retries}")
    
    print("\nScheduler:")
    print(f"  Enabled: {config.scheduler.enabled}")
    print(f"  Diagnosis Interval: {config.scheduler.diagnosis_interval}s")
    print(f"  Health Check Interval: {config.scheduler.health_check_interval}s")
    
    print("\nTools:")
    print(f"  Tools Dir: {config.tools.tools_dir}")
    print(f"  Backup Dir: {config.tools.backup_dir}")
    print(f"  Auto Discover: {config.tools.auto_discover}")
    
    print("\nEvolution:")
    print(f"  Safety Mode: {config.evolution.safety_mode}")
    print(f"  Backup Before Modify: {config.evolution.backup_before_modify}")
    print(f"  Max Retries: {config.evolution.max_retries}")


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("AAIA Configuration Validation")
    print("="*70)
    
    # Print current config
    print_config_summary()
    
    # Validate completeness
    config_valid = validate_config_complete()
    
    # Validate module usage
    modules_valid = validate_modules_use_config()
    
    # Final summary
    print("\n" + "="*70)
    print("Validation Summary")
    print("="*70)
    
    if config_valid and modules_valid:
        print("\n✓ All validation checks passed")
        sys.exit(0)
    else:
        print("\n❌ Validation failed - see issues above")
        sys.exit(1)


if __name__ == '__main__':
    main()
