"""
Live Ollama Server Test Script

Tests the Ollama provider implementation against a real server.
Server: http://192.168.178.104:11434/
"""

import sys
sys.path.insert(0, 'packages')

import json
from modules.llm.ollama_provider import OllamaProvider, OllamaAPIClient
from modules.settings import OllamaConfig


def print_header(title):
    """Print a formatted header"""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()


def print_section(title):
    """Print a formatted section header"""
    print()
    print("-" * 70)
    print(title)
    print("-" * 70)


def test_server_connectivity(base_url):
    """Test basic connectivity to Ollama server"""
    print_section("TEST 1: Server Connectivity")
    
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ Server is ONLINE at {base_url}")
            print(f"✅ Response Status: {response.status_code}")
            print(f"✅ Found {len(models)} installed models")
            print()
            print("Installed models:")
            for model in models:
                print(f"  - {model['name']}")
            return True, models
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False, []


def test_api_client(base_url):
    """Test OllamaAPIClient class"""
    print_section("TEST 2: OllamaAPIClient")
    
    try:
        client = OllamaAPIClient(base_url)
        
        # Test list_models
        print("Testing list_models()...")
        models = client.list_models()
        print(f"✅ list_models() returned {len(models)} models")
        
        # Test caching
        print("Testing cache...")
        models2 = client.list_models()
        print(f"✅ Cache working (returned {len(models2)} models)")
        
        # Test get_model_details for first model
        if models:
            model_name = models[0]['name']
            print(f"Testing get_model_details('{model_name}')...")
            details = client.get_model_details(model_name)
            
            print(f"✅ Got model details")
            print(f"   Capabilities: {details.get('capabilities', [])}")
            print(f"   Family: {details.get('details', {}).get('family', 'Unknown')}")
            print(f"   Parameter size: {details.get('details', {}).get('parameter_size', 'Unknown')}")
            
            # Check for model_info
            model_info = details.get('model_info', {})
            context_keys = [k for k in model_info.keys() if 'context' in k.lower()]
            if context_keys:
                print(f"   Context length key: {context_keys[0]} = {model_info[context_keys[0]]}")
            
        return True
        
    except Exception as e:
        print(f"❌ OllamaAPIClient test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_capability_extraction(base_url):
    """Test capability extraction from real API responses"""
    print_section("TEST 3: Capability Extraction")
    
    try:
        from modules.llm.ollama_capabilities import (
            extract_capabilities_from_show,
            extract_context_window,
            calculate_speed_score,
            get_model_description
        )
        
        client = OllamaAPIClient(base_url)
        models = client.list_models()
        
        if not models:
            print("⚠️  No models available for testing")
            return False
        
        for model_entry in models[:2]:  # Test first 2 models
            model_name = model_entry['name']
            print(f"\nTesting capabilities for: {model_name}")
            
            details = client.get_model_details(model_name)
            
            # Extract capabilities
            capabilities = extract_capabilities_from_show(details)
            print(f"  Capabilities:")
            print(f"    - Code: {capabilities['code']}")
            print(f"    - Reasoning: {capabilities['reasoning']}")
            print(f"    - Vision: {capabilities['vision']}")
            print(f"    - Function Calling: {capabilities['function_calling']}")
            
            # Extract context window
            context = extract_context_window(details)
            print(f"  Context Window: {context} tokens")
            
            # Calculate speed score
            model_details = details.get('details', {})
            speed = calculate_speed_score(model_details)
            print(f"  Speed Score: {speed}")
            
            # Get description
            desc = get_model_description(model_details)
            print(f"  Description: {desc}")
        
        print("\n✅ Capability extraction working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Capability extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_discovery(base_url):
    """Test full provider discovery pipeline"""
    print_section("TEST 4: OllamaProvider Discovery")
    
    try:
        # Create config
        config = OllamaConfig()
        config.base_url = base_url
        
        # Initialize provider
        provider = OllamaProvider(config)
        
        print("Testing get_available_models()...")
        models = provider.get_available_models()
        
        print(f"✅ Discovery successful!")
        print(f"✅ Found {len(models)} models")
        print()
        
        for i, model in enumerate(models, 1):
            print(f"Model {i}: {model.id}")
            print(f"  Provider: {model.provider}")
            print(f"  Speed Score: {model.input_cost_per_1k}")
            print(f"  Context Window: {model.context_window} tokens")
            print(f"  Currency: {model.currency}")
            print(f"  Capabilities:")
            print(f"    - Code: {model.capabilities['code']}")
            print(f"    - Reasoning: {model.capabilities['reasoning']}")
            print(f"    - Vision: {model.capabilities['vision']}")
            print(f"    - Function Calling: {model.capabilities['function_calling']}")
            print(f"  Description: {model.description}")
            print(f"  Parameters: {model.parameter_count}")
            print()
        
        # Verify sorting
        print("Verifying model sorting (by speed score)...")
        is_sorted = True
        for i in range(len(models) - 1):
            if models[i].input_cost_per_1k > models[i+1].input_cost_per_1k:
                print(f"  ❌ SORTING ERROR: {models[i].id} ({models[i].input_cost_per_1k}) > {models[i+1].id} ({models[i+1].input_cost_per_1k})")
                is_sorted = False
            else:
                print(f"  ✅ {models[i].id} ({models[i].input_cost_per_1k}) <= {models[i+1].id} ({models[i+1].input_cost_per_1k})")
        
        if is_sorted:
            print("\n✅ Models correctly sorted by speed!")
        
        return True, models
        
    except Exception as e:
        print(f"❌ Provider discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_model_selection(models):
    """Test model selection logic"""
    print_section("TEST 5: Model Selection Logic")
    
    if not models:
        print("⚠️  No models available for selection testing")
        return False
    
    try:
        print("Testing model filtering by capabilities...")
        
        # Find fastest model
        fastest = models[0]
        print(f"✅ Fastest model: {fastest.id} (speed: {fastest.input_cost_per_1k})")
        
        # Find code-capable models
        code_models = [m for m in models if m.capabilities['code']]
        if code_models:
            print(f"✅ Code-capable models: {len(code_models)}")
            for m in code_models:
                print(f"   - {m.id}")
        else:
            print("⚠️  No code-capable models found")
        
        # Find vision-capable models
        vision_models = [m for m in models if m.capabilities['vision']]
        if vision_models:
            print(f"✅ Vision-capable models: {len(vision_models)}")
            for m in vision_models:
                print(f"   - {m.id}")
        else:
            print("ℹ️  No vision-capable models found (expected for most setups)")
        
        # Test context window filtering
        large_context = [m for m in models if m.context_window >= 8192]
        if large_context:
            print(f"✅ Large context models (≥8K): {len(large_context)}")
            for m in large_context:
                print(f"   - {m.id}: {m.context_window} tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ Model selection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print_header("OLLAMA PROVIDER - LIVE SERVER TEST")
    
    base_url = "http://192.168.178.104:11434"
    print(f"Server: {base_url}")
    
    results = []
    
    # Test 1: Connectivity
    success, raw_models = test_server_connectivity(base_url)
    results.append(("Server Connectivity", success))
    
    if not success:
        print("\n❌ Cannot connect to server. Aborting tests.")
        return
    
    # Test 2: API Client
    success = test_api_client(base_url)
    results.append(("API Client", success))
    
    # Test 3: Capability Extraction
    success = test_capability_extraction(base_url)
    results.append(("Capability Extraction", success))
    
    # Test 4: Provider Discovery
    success, models = test_provider_discovery(base_url)
    results.append(("Provider Discovery", success))
    
    # Test 5: Model Selection
    if models:
        success = test_model_selection(models)
        results.append(("Model Selection", success))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Implementation is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
