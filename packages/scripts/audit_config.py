#!/usr/bin/env python3
"""
Configuration Audit Script

Finds hardcoded values that should be in config:
- Timeouts
- Retry counts  
- Intervals
- Paths
- Limits/thresholds
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Patterns to find
PATTERNS = {
    'timeout': [
        (r'timeout\s*=\s*(\d+)', 'Hardcoded timeout'),
        (r'TIMEOUT\s*=\s*(\d+)', 'Hardcoded timeout constant'),
    ],
    'retry': [
        (r'max_retries\s*=\s*(\d+)', 'Hardcoded max retries'),
        (r'retries\s*=\s*(\d+)', 'Hardcoded retries'),
        (r'MAX_RETRIES\s*=\s*(\d+)', 'Hardcoded retry constant'),
    ],
    'interval': [
        (r'interval\s*=\s*(\d+)', 'Hardcoded interval'),
        (r'INTERVAL\s*=\s*(\d+)', 'Hardcoded interval constant'),
        (r'sleep\((\d+)\)', 'Hardcoded sleep'),
    ],
    'path': [
        (r'["\']tools["\']', 'Hardcoded tools path'),
        (r'["\']backups?["\']', 'Hardcoded backup path'),
        (r'["\']data["\']', 'Hardcoded data path'),
    ],
    'limit': [
        (r'limit\s*=\s*(\d+)', 'Hardcoded limit'),
        (r'max_\w+\s*=\s*(\d+)', 'Hardcoded max value'),
    ]
}

# Files to ignore
IGNORE_FILES = {
    '__pycache__',
    '.pyc',
    'test_',
    'audit_config.py',
    'settings.py'  # Config file itself
}


def should_check_file(filepath: Path) -> bool:
    """Check if file should be audited"""
    if not filepath.suffix == '.py':
        return False
    
    for ignore in IGNORE_FILES:
        if ignore in str(filepath):
            return False
    
    return True


def audit_file(filepath: Path) -> List[Tuple[int, str, str, str]]:
    """
    Audit a single file for hardcoded values.
    
    Returns:
        List of (line_num, category, pattern, line_content)
    """
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip comments
                if line.strip().startswith('#'):
                    continue
                
                # Check each pattern
                for category, patterns in PATTERNS.items():
                    for pattern, description in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append((
                                line_num,
                                category,
                                description,
                                line.strip()
                            ))
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return findings


def audit_directory(directory: Path) -> Dict[str, List]:
    """Audit all Python files in directory"""
    results = {}
    
    for filepath in directory.rglob('*.py'):
        if should_check_file(filepath):
            findings = audit_file(filepath)
            if findings:
                results[str(filepath.relative_to(directory))] = findings
    
    return results


def print_results(results: Dict[str, List]):
    """Print audit results"""
    total_findings = sum(len(findings) for findings in results.values())
    
    print(f"\n{'='*70}")
    print(f"Configuration Audit Report")
    print(f"{'='*70}")
    print(f"Total files with findings: {len(results)}")
    print(f"Total hardcoded values: {total_findings}")
    print(f"{'='*70}\n")
    
    # Group by category
    by_category = {}
    for filepath, findings in results.items():
        for line_num, category, desc, line in findings:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((filepath, line_num, line))
    
    # Print by category
    for category, items in sorted(by_category.items()):
        print(f"\n{category.upper()} ({len(items)} findings)")
        print("-" * 70)
        for filepath, line_num, line in items[:10]:  # Show first 10
            print(f"{filepath}:{line_num}")
            print(f"  {line}")
        if len(items) > 10:
            print(f"  ... and {len(items) - 10} more")
    
    # Recommendations
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print("="*70)
    
    if 'timeout' in by_category:
        print("\n1. Timeouts:")
        print("   - Add to LLMConfig or specific provider config")
        print("   - Example: config.llm.ollama.timeout")
    
    if 'interval' in by_category:
        print("\n2. Intervals:")
        print("   - Add to SchedulerConfig")
        print("   - Example: config.scheduler.diagnosis_interval")
    
    if 'path' in by_category:
        print("\n3. Paths:")
        print("   - Add to ToolsConfig or DatabaseConfig")
        print("   - Example: config.tools.tools_dir")
    
    if 'retry' in by_category:
        print("\n4. Retries:")
        print("   - Add to ProviderConfig or EvolutionConfig")
        print("   - Example: config.llm.ollama.max_retries")


def main():
    """Main entry point"""
    # Get packages directory
    script_dir = Path(__file__).parent
    packages_dir = script_dir.parent
    
    print(f"Auditing directory: {packages_dir}")
    
    # Run audit
    results = audit_directory(packages_dir)
    
    # Print results
    print_results(results)
    
    # Save detailed report
    report_path = packages_dir.parent / "docs" / "config_audit_report.txt"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("Configuration Audit Detailed Report\n")
        f.write("=" * 70 + "\n\n")
        
        for filepath, findings in sorted(results.items()):
            f.write(f"\n{filepath}\n")
            f.write("-" * 70 + "\n")
            for line_num, category, desc, line in findings:
                f.write(f"Line {line_num} [{category}]: {desc}\n")
                f.write(f"  {line}\n")
    
    print(f"\n\nDetailed report saved to: {report_path}")


if __name__ == '__main__':
    main()
