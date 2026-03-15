#!/usr/bin/env python3
"""Fix all concatenated lines from bad regex replacement"""

import re

files = [
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

print("Fixing concatenated lines...")
print("=" * 80)

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Fix pattern: )        SOMETHING = ...
    # Should be: )\n        \n        SOMETHING = ...
    content = re.sub(
        r'\)(\s{4,8})([a-z_]+)\s*=\s*self\.',
        r')\n\1\n\1\2 = self.',
        content
    )
    
    # Also handle prompt_data specifically
    content = re.sub(
        r'\)(\s{4,8})(prompt_data)\s*=\s*self\.',
        r')\n\1\n\1\2 = self.',
        content
    )
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")

print("\n✅ All concatenated lines fixed!")
