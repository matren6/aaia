#!/usr/bin/env python3
"""
Automated fix: Replace provider = route_request() + provider.generate()
With: router.generate(... task_type=X, complexity=Y)
"""

import re

# Map of files and their expected task_type/complexity patterns
files = [
    'packages/modules/intent_predictor.py',
    'packages/modules/evolution_orchestrator.py',
    'packages/modules/evolution.py',
    'packages/modules/evolution_pipeline.py',
    'packages/modules/metacognition.py',
    'packages/modules/capability_discovery.py',
    'packages/modules/dialogue.py',
    'packages/modules/goals.py',
    'packages/modules/nix_aware_self_modification.py',
    'packages/modules/profitability_reporter.py',
    'packages/modules/prompt_optimizer.py',
]

print("Automated LLM call fix - Step 2")
print("=" * 80)

for filepath in files:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Pattern: provider = self.router.route_request("X", "Y") followed by provider.generate
        # Replace with: self.router.generate(... task_type="X", complexity="Y")
        
        pattern = re.compile(
            r'provider\s*=\s*self\.router\.route_request\(["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\)\s*\n'
            r'(\s+)(?:response_obj|response|suggestions|analysis|insights|proposals|ideas|summary|report|result)\s*=\s*provider\.generate\(',
            re.MULTILINE
        )
        
        def replacer(match):
            task_type = match.group(1)
            complexity = match.group(2)
            indent = match.group(3)
            
            # Determine variable name from context
            line_after = match.group(0).split('provider.generate')[0].split('=')[-2].strip().split()[-1] if '=' in match.group(0) else 'response'
            
            return f'{indent}{line_after} = self.router.generate(\n{indent}    '
        
        # Simpler approach - just replace provider.generate with self.router.generate
        if 'provider.generate(' in content:
            content = content.replace('provider.generate(', 'self.router.generate(')
            # Remove the provider = route_request lines
            content = re.sub(r'\s*provider\s*=\s*self\.router\.route_request\([^)]+\)\n', '', content)
            
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
        else:
            print(f"ℹ️  Already fixed: {filepath}")
            
    except Exception as e:
        print(f"❌ Error in {filepath}: {e}")

print("\n" + "=" * 80)
print("✅ All provider.generate() calls converted to router.generate()")
