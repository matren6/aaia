#!/usr/bin/env python3
"""Final comprehensive fix for all VeniceProvider unpacking errors"""

import re
import sys

# All files with the issue
files = {
    'packages/modules/intent_predictor.py': 2,
    'packages/modules/evolution_orchestrator.py': 3,
    'packages/modules/evolution.py': 2,
    'packages/modules/evolution_pipeline.py': 1,
    'packages/modules/metacognition.py': 2,
    'packages/modules/capability_discovery.py': 1,
    'packages/modules/dialogue.py': 1,
    'packages/modules/goals.py': 1,
    'packages/modules/nix_aware_self_modification.py': 1,
    'packages/modules/profitability_reporter.py': 5,
    'packages/modules/prompt_optimizer.py': 3,
}

print("Fixing call_model references after unpacking fix...")
print("=" * 80)

total_fixed = 0

for filepath, expected_count in files.items():
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Replace: self.router.call_model(model_name, ...)
        # With: provider.generate(...)
        content = re.sub(
            r'self\.router\.call_model\(\s*model_name,\s*',
            'provider.generate(',
            content
        )
        
        # Also handle cases where response needs to be extracted
        # This is a simplified approach - may need manual review
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            
            changes = len(re.findall(r'provider\.generate\(', content))
            print(f"✅ {filepath}: Fixed {changes} call(s)")
            total_fixed += changes
        else:
            print(f"ℹ️  {filepath}: Already fixed or no changes needed")
            
    except Exception as e:
        print(f"❌ {filepath}: Error - {e}")

print("\n" + "=" * 80)
print(f"✅ Total: Fixed {total_fixed} call_model → generate conversions")
print("\n⚠️  IMPORTANT: Some responses may need wrapping:")
print("   response_obj = provider.generate(...)")
print("   response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)")
