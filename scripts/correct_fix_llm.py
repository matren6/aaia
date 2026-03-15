#!/usr/bin/env python3
"""
CORRECT FIX for VeniceProvider unpacking error

The issue: Code unpacks route_request() which now returns single provider.
The solution: Use router.generate() instead of route_request() + call_model()

router.generate() properly:
1. Publishes LLM_REQUEST and LLM_RESPONSE events
2. Tracks costs automatically
3. Handles fallbacks
"""

import re

files_to_fix = [
    'packages/modules/self_diagnosis.py',
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

print("CORRECT FIX: Replace route_request + call_model with router.generate")
print("=" * 80)

for filepath in files_to_fix:
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern 1: Remove unpacking assignment entirely
    # provider = router.route_request(...) → (remove line, will use router.generate instead)
    
    # Pattern 2: Replace provider.generate(...) with router.generate(...)
    content = re.sub(
        r'provider\s*=\s*self\.router\.route_request\([^)]+\)\s*\n\s*response',
        'response',
        content
    )
    
    # Also replace standalone provider.generate with router.generate  
    content = content.replace('provider.generate(', 'self.router.generate(')
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed: {filepath}")

print("\n✅ All files updated to use router.generate() for proper event publishing")
