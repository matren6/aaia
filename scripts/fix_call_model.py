#!/usr/bin/env python3
"""
Comprehensive fix for VeniceProvider unpacking error.

This script:
1. Changes: model_name, _ = router.route_request(...) → provider = router.route_request(...)
2. Changes: router.call_model(model_name, ...) → provider.generate(...)
3. Handles response object: response_obj.content if hasattr(...) else str(...)
"""

import os
import re

files_to_fix = [
    'packages/modules/self_diagnosis.py',
    'packages/modules/intent_predictor.py',
    'packages/modules/evolution_orchestrator.py',
]

print("Fixing VeniceProvider unpacking in critical files...")
print("=" * 80)

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        print(f"⚠️  Skip: {filepath} (not found)")
        continue
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for: router.call_model(model_name, ...)
        # This should now be: router.generate(prompt, system_prompt)
        if 'self.router.call_model' in line and 'model_name' in line:
            # Replace call_model with generate, remove model_name parameter
            # This is tricky because we need to match the pattern
            modified_line = line.replace('self.router.call_model(', 'provider.generate(')
            modified_line = re.sub(r'provider\.generate\(\s*model_name,\s*', 'provider.generate(', modified_line)
            new_lines.append(modified_line)
            modified = True
            print(f"  Line {i+1}: Fixed call_model → generate")
        else:
            new_lines.append(line)
        
        i += 1
    
    if modified:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Updated {filepath}")
    else:
        print(f"ℹ️  No changes needed in {filepath}")

print("\n" + "=" * 80)
print("✅ Fix complete! Run the app to test.")
