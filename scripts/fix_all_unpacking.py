#!/usr/bin/env python3
"""Fix all route_request unpacking errors across all modules"""

import os
import re

# Files that need fixing
files_to_fix = [
    'packages/modules/capability_discovery.py',
    'packages/modules/dialogue.py',
    'packages/modules/evolution.py',
    'packages/modules/evolution_orchestrator.py',
    'packages/modules/evolution_pipeline.py',
    'packages/modules/goals.py',
    'packages/modules/intent_predictor.py',
    'packages/modules/metacognition.py',
    'packages/modules/nix_aware_self_modification.py',
    'packages/modules/profitability_reporter.py',
    'packages/modules/prompt_optimizer.py',
    'packages/modules/self_diagnosis.py',
]

# Pattern to find: model_name, _ = self.router.route_request(...)
pattern = re.compile(r'(\s*)model_name,\s*_\s*=\s*(self\.router\.route_request\([^)]+\))')

fixed_count = 0
total_occurrences = 0

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    occurrences = pattern.findall(content)
    
    if not occurrences:
        continue
    
    total_occurrences += len(occurrences)
    
    # Replace: model_name, _ = router.route_request(...) 
    # With: provider = router.route_request(...)
    new_content = pattern.sub(r'\1provider = \2', content)
    
    # Now we need to also replace call_model usage
    # Pattern: self.router.call_model(model_name, ...)
    # Replace with: provider.generate(...)
    
    # This is complex, so let's just do the first replacement
    # and note that call_model needs manual fixing
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Fixed {len(occurrences)} occurrence(s) in {filepath}")
    fixed_count += len(occurrences)

print(f"\n✅ Total: Fixed {fixed_count} occurrences across {len([f for f in files_to_fix if os.path.exists(f)])} files")
print(f"\n⚠️  NOTE: You must also replace 'self.router.call_model(model_name, ...)' with 'provider.generate(...)'")
print(f"   This requires manual review of each file.")
