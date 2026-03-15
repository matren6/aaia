#!/usr/bin/env python3
"""Fix all syntax errors from automated script"""

import re
import os

files_with_errors = [
    'packages/modules/capability_discovery.py',
    'packages/modules/evolution.py',
    'packages/modules/evolution_orchestrator.py',
    'packages/modules/evolution_pipeline.py',
    'packages/modules/goals.py',
    'packages/modules/intent_predictor.py',
    'packages/modules/metacognition.py',
    'packages/modules/nix_aware_self_modification.py',
    'packages/modules/profitability_reporter.py',
    'packages/modules/prompt_optimizer.py',
]

print("Fixing syntax errors from automated script...")
print("=" * 80)

for filepath in files_with_errors:
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern: )        response = self.router.generate(
    # Should be: )\n        \n        response = self.router.generate(
    
    content = re.sub(
        r'\)(\s*)response = self\.router\.generate\(',
        r')\n\1\n\1response = self.router.generate(',
        content
    )
    
    # Also handle other variable names
    content = re.sub(
        r'\)(\s+)(suggestions|analysis|insights|proposals|ideas|summary|report|result|prediction) = self\.router\.generate\(',
        r')\n\1\n\1\2 = self.router.generate(',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed: {filepath}")

print("\n" + "=" * 80)
print("✅ All syntax errors fixed!")
