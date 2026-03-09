#!/usr/bin/env python3
"""Build verification test - ASCII only"""

import sys
import os
sys.path.insert(0, 'packages')

print("="*80)
print("BUILD VERIFICATION TEST")
print("="*80)
print()

errors = []
passed = 0
total = 0

# Test 1: Import core modules
total += 1
print("Test 1: Importing core modules...")
try:
    from modules.bus import EventBus, Event, EventType
    from modules.settings import SystemConfig, LLMConfig
    from modules.router import ModelRouter
    from modules.llm.base_provider import ModelInfo
    print("  [PASS] Core modules imported")
    passed += 1
except Exception as e:
    print(f"  [FAIL] Import failed: {e}")
    errors.append(f"Core imports: {e}")

# Test 2: Import all providers
total += 1
print("Test 2: Importing all providers...")
try:
    from modules.llm.venice_provider import VeniceProvider
    from modules.llm.openai_provider import OpenAIProvider
    from modules.llm.ollama_provider import OllamaProvider
    from modules.llm.github_provider import GitHubProvider
    from modules.llm.azure_provider import AzureOpenAIProvider
    print("  [PASS] All providers imported")
    passed += 1
except Exception as e:
    print(f"  [FAIL] Provider import failed: {e}")
    errors.append(f"Provider imports: {e}")

# Test 3: Create Event instance
total += 1
print("Test 3: Creating Event instance...")
try:
    event = Event(
        type=EventType.MODEL_INFERENCE,
        data={'test': 'data'},
        source='test'
    )
    print(f"  [PASS] Event created with type: {event.type.value}")
    passed += 1
except Exception as e:
    print(f"  [FAIL] Event creation failed: {e}")
    errors.append(f"Event creation: {e}")

# Test 4: Create ModelInfo instance
total += 1
print("Test 4: Creating ModelInfo instance...")
try:
    model = ModelInfo(
        id='test-model',
        name='Test Model',
        provider='test',
        capabilities={'code': True},
        context_window=8192,
        input_cost_per_1k=0.1,
        output_cost_per_1k=0.2,
        currency='USD'
    )
    print(f"  [PASS] ModelInfo created, total_cost: {model.total_cost_per_1k}")
    passed += 1
except Exception as e:
    print(f"  [FAIL] ModelInfo creation failed: {e}")
    errors.append(f"ModelInfo creation: {e}")

# Test 5: Create LLMConfig instance
total += 1
print("Test 5: Creating LLMConfig instance...")
try:
    config = LLMConfig()
    config.__post_init__()
    print(f"  [PASS] LLMConfig created with provider: {config.default_provider}")
    passed += 1
except Exception as e:
    print(f"  [FAIL] LLMConfig creation failed: {e}")
    errors.append(f"LLMConfig creation: {e}")

# Test 6: Test LLMConfig validation
total += 1
print("Test 6: Testing LLMConfig validation...")
try:
    bad_config = LLMConfig(default_provider="invalid")
    bad_config.__post_init__()
    # If we get here, validation FAILED to catch the error
    print("  [FAIL] Validation should have rejected invalid provider")
    errors.append("LLMConfig validation not working")
except ValueError as ve:
    # This is expected - validation should raise ValueError
    print(f"  [PASS] Validation correctly rejected: {str(ve)[:50]}...")
    passed += 1
except Exception as e:
    print(f"  [FAIL] Unexpected error: {e}")
    errors.append(f"Validation test: {e}")

# Test 7: Load SystemConfig
total += 1
print("Test 7: Loading SystemConfig from environment...")
try:
    sys_config = SystemConfig.from_env()
    print(f"  [PASS] SystemConfig loaded, LLM provider: {sys_config.llm.default_provider}")
    passed += 1
except Exception as e:
    print(f"  [FAIL] SystemConfig load failed: {e}")
    errors.append(f"SystemConfig load: {e}")

# Test 8: Verify OpenAI models table
total += 1
print("Test 8: Verifying OpenAI models table...")
try:
    if hasattr(OpenAIProvider, 'OPENAI_MODELS'):
        count = len(OpenAIProvider.OPENAI_MODELS)
        print(f"  [PASS] OpenAI models table exists ({count} models)")
        passed += 1
    else:
        print("  [FAIL] OpenAI models table not found")
        errors.append("OpenAI models table missing")
except Exception as e:
    print(f"  [FAIL] OpenAI table check failed: {e}")
    errors.append(f"OpenAI table check: {e}")

# Test 9: Test get_available_models
total += 1
print("Test 9: Testing get_available_models...")
try:
    provider = OpenAIProvider(sys_config.llm.openai)
    models = provider.get_available_models()
    print(f"  [PASS] get_available_models() returned {len(models)} models")
    passed += 1
except Exception as e:
    print(f"  [FAIL] get_available_models failed: {e}")
    errors.append(f"get_available_models: {e}")

# Test 10: Test ModelInfo meets_requirements
total += 1
print("Test 10: Testing ModelInfo.meets_requirements...")
try:
    test_model = ModelInfo('id', 'name', 'test', {'code': True}, 8192, 0.1, 0.2, 'USD')
    
    tests = [
        (test_model.meets_requirements(task_type='code'), True, "code capability"),
        (test_model.meets_requirements(task_type='vision'), False, "vision capability"),
        (test_model.meets_requirements(min_context=4096), True, "context 4096"),
        (test_model.meets_requirements(min_context=16384), False, "context 16384"),
        (test_model.meets_requirements(max_cost=0.5), True, "cost 0.5"),
        (test_model.meets_requirements(max_cost=0.2), False, "cost 0.2"),
    ]
    
    all_ok = all(result == expected for result, expected, _ in tests)
    if all_ok:
        print(f"  [PASS] All meets_requirements tests passed")
        passed += 1
    else:
        failed = [desc for result, expected, desc in tests if result != expected]
        print(f"  [FAIL] Failed tests: {', '.join(failed)}")
        errors.append(f"meets_requirements: {', '.join(failed)}")
except Exception as e:
    print(f"  [FAIL] meets_requirements test failed: {e}")
    errors.append(f"meets_requirements test: {e}")

# Summary
print()
print("="*80)
print("BUILD VERIFICATION SUMMARY")
print("="*80)
print(f"Tests run: {total}")
print(f"Passed: {passed}")
print(f"Failed: {total - passed}")
print()

if errors:
    print("ERRORS:")
    for error in errors:
        print(f"  - {error}")
    print()

if passed == total:
    print("*** BUILD VERIFICATION: PASSED ***")
    print()
    print("All components verified:")
    print("  [OK] All imports working")
    print("  [OK] Event system functional")
    print("  [OK] ModelInfo working")
    print("  [OK] LLMConfig with __post_init__")
    print("  [OK] Validation working")
    print("  [OK] SystemConfig loads")
    print("  [OK] Phase 2.5 components functional")
    print()
    sys.exit(0)
else:
    print("*** BUILD VERIFICATION: FAILED ***")
    print()
    sys.exit(1)
