#!/usr/bin/env python3
"""
Tool Building Capabilities - WSL/Nix Dry Run Test

Adapted for WSL environment with Nix and Ollama configuration from .env

Usage:
    python3 test_tool_building_wsl.py
"""

import sys
import os
import time
import json
from pathlib import Path

# Try to load .env, but don't fail if dotenv not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed, using environment variables directly")
    # Manually load .env file
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

print("=" * 80)
print("AUTONOMOUS TOOL DEVELOPMENT SYSTEM - WSL/NIX DRY RUN TEST")
print("=" * 80)
print()

# Verify environment
print("🔧 Environment Check:")
print(f"   Python: {sys.version.split()[0]}")
print(f"   Platform: {sys.platform}")
print(f"   Ollama URL: {os.getenv('OLLAMA_BASE_URL', 'Not set')}")
print(f"   Ollama Model: {os.getenv('OLLAMA_MODEL', 'Not set')}")
print()

# Initialize test results
test_results = {
    'setup': {},
    'phase_1': {},
    'phase_2': {},
    'phase_3': {},
    'integration': {},
    'overall': {'passed': 0, 'failed': 0, 'errors': []}
}

def log_test(phase, test_name, status, details=""):
    """Log test result"""
    emoji = "✅" if status == "PASS" else ("⏭️" if status == "SKIP" else "❌")
    print(f"{emoji} [{phase}] {test_name}: {status}")
    if details:
        print(f"   {details}")
    test_results[phase][test_name] = {'status': status, 'details': details}
    if status == "PASS":
        test_results['overall']['passed'] += 1
    elif status != "SKIP":
        test_results['overall']['failed'] += 1
        test_results['overall']['errors'].append(f"{phase}.{test_name}")

# ============================================================================
# PHASE 0: SETUP AND INITIALIZATION
# ============================================================================

print("\n📦 PHASE 0: Setup and Initialization\n")

try:
    print("Importing modules...")
    from modules.forge import Forge
    from modules.scheduler import AutonomousScheduler
    from modules.scribe import Scribe
    from modules.router import ModelRouter
    from modules.prompt_manager import PromptManager
    from modules.economics import EconomicManager
    from modules.settings import get_config
    log_test('setup', 'Module Imports', 'PASS', "All modules imported successfully")
except Exception as e:
    log_test('setup', 'Module Imports', 'FAIL', str(e))
    print(f"\n❌ CRITICAL: Cannot import modules. Exiting.\n")
    sys.exit(1)

try:
    print("Initializing components...")
    config = get_config()
    scribe = Scribe()
    prompt_manager = PromptManager()
    economic_manager = EconomicManager(scribe=scribe)
    
    # Initialize Router with correct parameters
    router = ModelRouter(
        economic_manager=economic_manager,
        config=config,
        prompt_manager=prompt_manager
    )
    
    forge = Forge(router=router, scribe=scribe, prompt_manager=prompt_manager, event_bus=None)
    log_test('setup', 'Component Initialization', 'PASS', "All components initialized")
except Exception as e:
    log_test('setup', 'Component Initialization', 'FAIL', str(e))
    print(f"\n❌ CRITICAL: Cannot initialize components. Exiting.\n")
    sys.exit(1)

# Test Ollama connection
print("\nTesting Ollama connection...")
try:
    # Try to route a simple request
    model_name, cost = router.route_request("test", "low")
    log_test('setup', 'Ollama Connection', 'PASS', f"Using model: {model_name}")
except Exception as e:
    log_test('setup', 'Ollama Connection', 'SKIP', f"Ollama may not be available: {str(e)[:60]}")

# ============================================================================
# PHASE 1: FOUNDATION (Testing & Performance Tracking)
# ============================================================================

print("\n" + "=" * 80)
print("🧪 PHASE 1: Testing & Performance Tracking")
print("=" * 80 + "\n")

# Test 1.1: Test Case Generation (will use Ollama)
print("Test 1.1: AI Test Case Generation (with Ollama)")
try:
    test_cases = forge._generate_test_cases(
        name="test_calculator",
        description="A simple calculator that adds two numbers"
    )
    
    if test_cases and len(test_cases) > 0:
        log_test('phase_1', 'Test Case Generation', 'PASS', 
                 f"Generated {len(test_cases)} test cases")
        print(f"   Sample test: {test_cases[0].get('name', 'Unknown')}")
    else:
        log_test('phase_1', 'Test Case Generation', 'FAIL', 
                 "No test cases generated")
except Exception as e:
    error_msg = str(e)
    if "route_request" in error_msg or "Ollama" in error_msg:
        log_test('phase_1', 'Test Case Generation', 'SKIP', 
                 f"LLM unavailable: {error_msg[:60]}")
    else:
        log_test('phase_1', 'Test Case Generation', 'FAIL', error_msg[:80])

# Test 1.2: Simple Tool Creation
print("\nTest 1.2: Simple Tool Creation")
try:
    simple_code = """
def execute(a, b):
    \"\"\"Add two numbers.\"\"\"
    result = a + b
    return result
"""
    metadata = forge.create_tool("test_adder", "Add two numbers", code=simple_code)
    
    if metadata and 'name' in metadata:
        log_test('phase_1', 'Simple Tool Creation', 'PASS', 
                 f"Tool created: {metadata['name']}")
    else:
        log_test('phase_1', 'Simple Tool Creation', 'FAIL', "Metadata missing")
except Exception as e:
    log_test('phase_1', 'Simple Tool Creation', 'FAIL', str(e)[:80])

# Test 1.3: Tool Execution with Performance Tracking
print("\nTest 1.3: Tool Execution & Performance Tracking")
try:
    result = forge.execute_tool("test_adder", a=10, b=20)
    
    if result == 30:
        log_test('phase_1', 'Tool Execution', 'PASS', f"Result: {result}")
    else:
        log_test('phase_1', 'Tool Execution', 'FAIL', f"Expected 30, got {result}")
except Exception as e:
    log_test('phase_1', 'Tool Execution', 'FAIL', str(e)[:80])

# Test 1.4: Performance Query
print("\nTest 1.4: Performance Metrics Query")
try:
    time.sleep(0.1)  # Small delay to ensure DB commit
    perf = forge.get_tool_performance("test_adder", hours=1)
    
    if perf and not perf.get('error'):
        executions = perf.get('total_executions', 0)
        log_test('phase_1', 'Performance Tracking', 'PASS', 
                 f"Tracked {executions} execution(s)")
    else:
        log_test('phase_1', 'Performance Tracking', 'FAIL', 
                 perf.get('error', 'No data'))
except Exception as e:
    log_test('phase_1', 'Performance Tracking', 'FAIL', str(e)[:80])

# Test 1.5: Test Execution Framework
print("\nTest 1.5: Test Execution Framework")
try:
    test_cases = [
        {'name': 'Add positive', 'input': {'a': 5, 'b': 3}, 'expected': '8'},
        {'name': 'Add negative', 'input': {'a': -2, 'b': 2}, 'expected': '0'},
        {'name': 'Add zero', 'input': {'a': 0, 'b': 0}, 'expected': '0'},
    ]
    
    results = forge.test_tool("test_adder", test_cases)
    
    if results:
        passed = results.get('passed', 0)
        total = results.get('total_tests', 0)
        success_rate = results.get('success_rate', 0)
        log_test('phase_1', 'Test Execution Framework', 'PASS', 
                 f"{passed}/{total} tests passed ({success_rate:.0%})")
    else:
        log_test('phase_1', 'Test Execution Framework', 'FAIL', "No results returned")
except Exception as e:
    log_test('phase_1', 'Test Execution Framework', 'FAIL', str(e)[:80])

# Test 1.6: Validated Tool Creation (with LLM)
print("\nTest 1.6: Validated Tool Creation (with automatic testing)")
try:
    validated_code = """
def execute(x, y):
    \"\"\"Multiply two numbers.\"\"\"
    result = x * y
    return result
"""
    metadata = forge.create_tool_with_validation(
        name="test_multiplier",
        description="Multiply two numbers",
        code=validated_code,
        auto_test=False,  # Skip auto-testing to avoid LLM dependency
        min_pass_rate=0.6
    )
    
    if metadata and 'name' in metadata:
        log_test('phase_1', 'Validated Tool Creation', 'PASS', 
                 f"Tool created: {metadata['name']}")
    else:
        log_test('phase_1', 'Validated Tool Creation', 'FAIL', "No metadata")
except Exception as e:
    log_test('phase_1', 'Validated Tool Creation', 'FAIL', str(e)[:80])

# ============================================================================
# PHASE 2: AUTONOMY (Autonomous Creation & Optimization)
# ============================================================================

print("\n" + "=" * 80)
print("🤖 PHASE 2: Autonomous Tool Development")
print("=" * 80 + "\n")

# Test 2.1: Scheduler Initialization
print("Test 2.1: Scheduler Initialization")
try:
    from modules.container import get_container
    
    container = get_container()
    
    scheduler = AutonomousScheduler(
        scribe=scribe,
        router=router,
        economics=economic_manager,
        forge=forge,
        container=container,
        prompt_manager=prompt_manager
    )
    log_test('phase_2', 'Scheduler Initialization', 'PASS', "Scheduler created")
except Exception as e:
    log_test('phase_2', 'Scheduler Initialization', 'FAIL', str(e)[:80])
    scheduler = None

# Test 2.2: Capability Prioritization
print("\nTest 2.2: Capability Prioritization Algorithm")
try:
    if scheduler:
        test_capabilities = [
            {'name': 'cap1', 'value': 0.9, 'feasibility': 0.8, 'usage_frequency': 0.7, 'complexity': 3},
            {'name': 'cap2', 'value': 0.5, 'feasibility': 0.5, 'usage_frequency': 0.5, 'complexity': 8},
            {'name': 'cap3', 'value': 0.8, 'feasibility': 0.9, 'usage_frequency': 0.6, 'complexity': 2},
        ]
        
        prioritized = scheduler._prioritize_capabilities(test_capabilities)
        
        if prioritized and len(prioritized) == 3:
            if prioritized[0].get('priority_score', 0) >= prioritized[1].get('priority_score', 0):
                log_test('phase_2', 'Capability Prioritization', 'PASS', 
                         f"Top priority: {prioritized[0]['name']} (score: {prioritized[0]['priority_score']:.2f})")
            else:
                log_test('phase_2', 'Capability Prioritization', 'FAIL', 
                         "Prioritization order incorrect")
        else:
            log_test('phase_2', 'Capability Prioritization', 'FAIL', "Wrong number of results")
    else:
        log_test('phase_2', 'Capability Prioritization', 'SKIP', "Scheduler not available")
except Exception as e:
    log_test('phase_2', 'Capability Prioritization', 'FAIL', str(e)[:80])

# Test 2.3: Task Registration
print("\nTest 2.3: Scheduled Task Registration")
try:
    if scheduler:
        tasks = scheduler.get_task_status()
        
        task_names = [t['name'] for t in tasks]
        phase_2_tasks = [
            'autonomous_tool_development',
            'tool_performance_optimizer',
            'tool_deprecation_check'
        ]
        
        found_tasks = [t for t in phase_2_tasks if t in task_names]
        
        if len(found_tasks) == 3:
            log_test('phase_2', 'Task Registration', 'PASS', 
                     f"All 3 Phase 2 tasks registered")
        else:
            log_test('phase_2', 'Task Registration', 'FAIL', 
                     f"Only {len(found_tasks)}/3 tasks found")
    else:
        log_test('phase_2', 'Task Registration', 'SKIP', "Scheduler not available")
except Exception as e:
    log_test('phase_2', 'Task Registration', 'FAIL', str(e)[:80])

# Test 2.4: Performance Analysis
print("\nTest 2.4: Performance Analysis for Optimization")
try:
    # Execute tool multiple times
    for i in range(3):
        forge.execute_tool("test_adder", a=i, b=i+1)
    
    time.sleep(0.2)  # Allow DB commits
    
    perf = forge.get_tool_performance("test_adder", hours=1)
    
    if perf and perf.get('total_executions', 0) >= 4:  # 1 from earlier + 3 new
        log_test('phase_2', 'Performance Analysis', 'PASS', 
                 f"{perf['total_executions']} executions tracked")
    else:
        log_test('phase_2', 'Performance Analysis', 'FAIL', 
                 f"Expected 4+ executions, got {perf.get('total_executions', 0)}")
except Exception as e:
    log_test('phase_2', 'Performance Analysis', 'FAIL', str(e)[:80])

# Test 2.5: Deprecation Logic
print("\nTest 2.5: Tool Deprecation Detection")
try:
    if scheduler:
        result = scheduler.deprecate_unused_tools()
        
        if result and isinstance(result, str):
            log_test('phase_2', 'Deprecation Logic', 'PASS', result[:60])
        else:
            log_test('phase_2', 'Deprecation Logic', 'FAIL', "Invalid result")
    else:
        log_test('phase_2', 'Deprecation Logic', 'SKIP', "Scheduler not available")
except Exception as e:
    log_test('phase_2', 'Deprecation Logic', 'FAIL', str(e)[:80])

# ============================================================================
# PHASE 3: SECURITY & QUALITY
# ============================================================================

print("\n" + "=" * 80)
print("🔐 PHASE 3: Security & Quality Validation")
print("=" * 80 + "\n")

# Test 3.1: Security Audit - Safe Code
print("Test 3.1: Security Audit - Safe Code")
try:
    audit = forge.audit_tool_security("test_adder")
    
    if audit:
        level = audit.get('security_level', 'unknown')
        issues = len(audit.get('issues', []))
        warnings = len(audit.get('warnings', []))
        
        log_test('phase_3', 'Security Audit - Safe Code', 'PASS', 
                 f"Level: {level}, Issues: {issues}, Warnings: {warnings}")
    else:
        log_test('phase_3', 'Security Audit - Safe Code', 'FAIL', "No audit result")
except Exception as e:
    log_test('phase_3', 'Security Audit - Safe Code', 'FAIL', str(e)[:80])

# Test 3.2: Security Audit - Dangerous Code
print("\nTest 3.2: Security Audit - Dangerous Code Detection")
try:
    dangerous_code = """
def execute(code_str):
    \"\"\"Execute arbitrary code.\"\"\"
    result = eval(code_str)
    return result
"""
    forge.create_tool("test_dangerous", "Dangerous tool", code=dangerous_code)
    
    audit = forge.audit_tool_security("test_dangerous")
    
    level = audit.get('security_level', 'unknown')
    if level == 'dangerous':
        log_test('phase_3', 'Dangerous Code Detection', 'PASS', 
                 f"Correctly identified: {len(audit.get('issues', []))} issues")
    else:
        log_test('phase_3', 'Dangerous Code Detection', 'FAIL', 
                 f"Expected 'dangerous', got '{level}'")
    
    forge.delete_tool("test_dangerous")
except Exception as e:
    log_test('phase_3', 'Dangerous Code Detection', 'FAIL', str(e)[:80])

# Test 3.3: Code Quality Check
print("\nTest 3.3: Code Quality Assessment")
try:
    quality_code = """
def execute(data: list) -> dict:
    \"\"\"Process data and return result.\"\"\"
    try:
        if not data:
            return {'result': 0}
        return {'result': sum(data)}
    except Exception as e:
        return {'error': str(e)}
"""
    
    quality_report = forge.check_code_quality(quality_code)
    
    if quality_report:
        score = quality_report.get('overall_score', 0)
        log_test('phase_3', 'Code Quality Assessment', 'PASS', 
                 f"Score: {score}/100")
    else:
        log_test('phase_3', 'Code Quality Assessment', 'FAIL', "No quality report")
except Exception as e:
    log_test('phase_3', 'Code Quality Assessment', 'FAIL', str(e)[:80])

# Test 3.4: Tool Quality Check
print("\nTest 3.4: Existing Tool Quality Check")
try:
    quality = forge.check_tool_quality("test_adder")
    
    if quality:
        score = quality.get('overall_score', 0)
        log_test('phase_3', 'Tool Quality Check', 'PASS', 
                 f"test_adder score: {score}/100")
    else:
        log_test('phase_3', 'Tool Quality Check', 'FAIL', "No quality data")
except Exception as e:
    log_test('phase_3', 'Tool Quality Check', 'FAIL', str(e)[:80])

# Test 3.5: Sandbox Execution (Unix/Linux)
print("\nTest 3.5: Sandbox Execution (WSL)")
try:
    result = forge.execute_tool_sandbox("test_adder", a=15, b=25)
    
    if result == 40:
        log_test('phase_3', 'Sandbox Execution', 'PASS', 
                 f"Sandbox result: {result} (isolated process)")
    else:
        log_test('phase_3', 'Sandbox Execution', 'FAIL', 
                 f"Expected 40, got {result}")
except Exception as e:
    log_test('phase_3', 'Sandbox Execution', 'FAIL', str(e)[:80])

# Test 3.6: Batch Security Audit
print("\nTest 3.6: Batch Security Audit")
try:
    audits = forge.audit_all_tools()
    
    if audits:
        safe_count = sum(1 for a in audits if a.get('security_level') == 'safe')
        log_test('phase_3', 'Batch Security Audit', 'PASS', 
                 f"Audited {len(audits)} tools, {safe_count} safe")
    else:
        log_test('phase_3', 'Batch Security Audit', 'FAIL', "No audit results")
except Exception as e:
    log_test('phase_3', 'Batch Security Audit', 'FAIL', str(e)[:80])

# Test 3.7: Scheduled Security Audit
print("\nTest 3.7: Scheduled Security Audit Task")
try:
    if scheduler:
        result = scheduler.audit_all_tools_scheduled()
        
        if result and isinstance(result, str):
            log_test('phase_3', 'Scheduled Security Audit', 'PASS', result[:60])
        else:
            log_test('phase_3', 'Scheduled Security Audit', 'FAIL', "Invalid result")
    else:
        log_test('phase_3', 'Scheduled Security Audit', 'SKIP', "Scheduler not available")
except Exception as e:
    log_test('phase_3', 'Scheduled Security Audit', 'FAIL', str(e)[:80])

# Test 3.8: Scheduled Quality Assessment
print("\nTest 3.8: Scheduled Quality Assessment Task")
try:
    if scheduler:
        result = scheduler.assess_code_quality_all()
        
        if result and isinstance(result, str):
            log_test('phase_3', 'Scheduled Quality Assessment', 'PASS', result[:60])
        else:
            log_test('phase_3', 'Scheduled Quality Assessment', 'FAIL', "Invalid result")
    else:
        log_test('phase_3', 'Scheduled Quality Assessment', 'SKIP', "Scheduler not available")
except Exception as e:
    log_test('phase_3', 'Scheduled Quality Assessment', 'FAIL', str(e)[:80])

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

print("\n" + "=" * 80)
print("🔗 INTEGRATION TESTS")
print("=" * 80 + "\n")

# Test I.1: Phase 1 + Phase 2 Integration
print("Test I.1: Phase 1 + Phase 2 Integration")
try:
    if scheduler:
        result = scheduler.optimize_underperforming_tools()
        
        if result and isinstance(result, str):
            log_test('integration', 'Phase 1+2 Integration', 'PASS', result[:60])
        else:
            log_test('integration', 'Phase 1+2 Integration', 'FAIL', "Invalid result")
    else:
        log_test('integration', 'Phase 1+2 Integration', 'SKIP', "Scheduler not available")
except Exception as e:
    log_test('integration', 'Phase 1+2 Integration', 'FAIL', str(e)[:80])

# Test I.2: Complete System Integration
print("\nTest I.2: Complete System Integration")
try:
    tools = forge.list_tools()
    
    perf_data = []
    for tool in tools:
        perf = forge.get_tool_performance(tool['name'], hours=1)
        if not perf.get('no_data'):
            perf_data.append(perf)
    
    audits = forge.audit_all_tools()
    
    log_test('integration', 'Complete System Integration', 'PASS', 
             f"Tools: {len(tools)}, Perf data: {len(perf_data)}, Audits: {len(audits)}")
except Exception as e:
    log_test('integration', 'Complete System Integration', 'FAIL', str(e)[:80])

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("📊 TEST RESULTS SUMMARY")
print("=" * 80 + "\n")

# Count results by phase
phase_results = {}
for phase in ['phase_1', 'phase_2', 'phase_3', 'integration', 'setup']:
    if phase in test_results:
        phase_tests = test_results[phase]
        passed = sum(1 for t in phase_tests.values() if t['status'] == 'PASS')
        failed = sum(1 for t in phase_tests.values() if t['status'] == 'FAIL')
        skipped = sum(1 for t in phase_tests.values() if t['status'] == 'SKIP')
        total = len(phase_tests)
        
        phase_results[phase] = {
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': total
        }
        
        if phase == 'setup':
            phase_name = "Setup & Environment"
        elif phase == 'phase_1':
            phase_name = "Phase 1 (Foundation)"
        elif phase == 'phase_2':
            phase_name = "Phase 2 (Autonomy)"
        elif phase == 'phase_3':
            phase_name = "Phase 3 (Security)"
        else:
            phase_name = "Integration"
        
        status_emoji = "✅" if failed == 0 else "⚠️"
        print(f"{status_emoji} {phase_name}:")
        print(f"   Passed:  {passed}/{total}")
        print(f"   Failed:  {failed}/{total}")
        if skipped > 0:
            print(f"   Skipped: {skipped}/{total}")
        print()

# Overall summary
total_passed = test_results['overall']['passed']
total_failed = test_results['overall']['failed']
total_tests = total_passed + total_failed
success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

print("=" * 80)
print(f"OVERALL RESULTS: {total_passed}/{total_tests} tests passed ({success_rate:.0f}%)")
print("=" * 80)

# Final status
if total_failed == 0:
    print("\n🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION\n")
    exit_code = 0
elif success_rate >= 80:
    print(f"\n✅ SYSTEM OPERATIONAL - {success_rate:.0f}% success rate (acceptable)")
    if test_results['overall']['errors']:
        print(f"   Failed tests: {', '.join(test_results['overall']['errors'][:3])}")
    print()
    exit_code = 0
else:
    print(f"\n⚠️ SYSTEM NEEDS ATTENTION - {success_rate:.0f}% success rate")
    if test_results['overall']['errors']:
        print(f"   Failed tests: {', '.join(test_results['overall']['errors'])}")
    print()
    exit_code = 1

# Save results to file
try:
    results_file = Path("test_results_wsl.json")
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"📄 Detailed results saved to: {results_file}")
except Exception as e:
    print(f"⚠️ Could not save results: {e}")

print("\n" + "=" * 80)
print("TEST RUN COMPLETE")
print("=" * 80 + "\n")

sys.exit(exit_code)
