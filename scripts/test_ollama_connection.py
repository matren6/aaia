#!/usr/bin/env python3
"""Test Ollama connectivity from AAIA"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from modules.settings import get_config

def test_ollama():
    """Test connection to Ollama server"""
    config = get_config()
    
    print("=" * 70)
    print("OLLAMA CONNECTIVITY TEST")
    print("=" * 70)
    print()
    
    print("Configuration:")
    print(f"  Enabled: {config.llm.ollama.enabled}")
    print(f"  Base URL: {config.llm.ollama.base_url}")
    print(f"  Default Model: {config.llm.ollama.default_model}")
    print(f"  Timeout: {config.llm.ollama.timeout}s")
    print()
    
    if not config.llm.ollama.enabled:
        print("❌ Ollama is disabled in configuration")
        return False
    
    print("=" * 70)
    print("Testing Connection...")
    print("=" * 70)
    print()
    
    # Test 1: Basic connectivity to /api/tags
    print("1. Testing /api/tags endpoint...")
    try:
        url = f"{config.llm.ollama.base_url}/api/tags"
        request = urllib.request.Request(url, method='GET')
        response = urllib.request.urlopen(request, timeout=config.llm.ollama.timeout)
        data = json.loads(response.read().decode())
        
        models = data.get('models', [])
        print(f"   ✅ Success! ({response.status})")
        print(f"   Available Models: {len(models)}")
        
        if models:
            for model in models:
                name = model.get('name', 'unknown')
                size = model.get('size', 0)
                size_gb = size / (1024**3)
                print(f"     - {name} ({size_gb:.2f} GB)")
        else:
            print("     (No models available)")
        
    except urllib.error.URLError as e:
        print(f"   ❌ Connection Failed: {e.reason}")
        if hasattr(e, 'args'):
            print(f"      Details: {e.args}")
        return False
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return False
    
    # Test 2: Check if default model is available
    print()
    print(f"2. Checking if default model '{config.llm.ollama.default_model}' is available...")
    try:
        default_model = config.llm.ollama.default_model
        if models:
            model_names = [m.get('name', '').split(':')[0] for m in models]
            if any(default_model in name for name in model_names):
                print(f"   ✅ Model '{default_model}' is available")
            else:
                print(f"   ⚠️  Model '{default_model}' not found")
                print(f"      Available: {', '.join(model_names)}")
        else:
            print(f"   ⚠️  No models loaded (but server is running)")
    except Exception as e:
        print(f"   ⚠️  Could not verify: {e}")
    
    # Test 3: Test a generate request (lightweight)
    print()
    print("3. Testing generate endpoint with a simple prompt...")
    try:
        url = f"{config.llm.ollama.base_url}/api/generate"
        payload = {
            'model': config.llm.ollama.default_model,
            'prompt': 'say hello',
            'stream': False
        }
        
        data = json.dumps(payload).encode()
        request = urllib.request.Request(url, data=data, method='POST')
        request.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(request, timeout=config.llm.ollama.timeout)
        result = json.loads(response.read().decode())
        
        print(f"   ✅ Success! ({response.status})")
        response_text = result.get('response', '')
        print(f"   Response preview: {response_text[:100]}...")
        
    except urllib.error.URLError as e:
        print(f"   ❌ Connection Failed: {e.reason}")
        return False
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error {e.code}: {e.reason}")
        try:
            error_data = json.loads(e.read().decode())
            print(f"      Details: {error_data}")
        except:
            pass
        return False
    except Exception as e:
        print(f"   ⚠️  Error (may be expected): {type(e).__name__}: {e}")
    
    print()
    print("=" * 70)
    print("✅ OLLAMA SERVER IS ACCESSIBLE")
    print("=" * 70)
    return True

if __name__ == '__main__':
    try:
        success = test_ollama()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ FATAL ERROR: {e}")
        print("=" * 70)
        sys.exit(1)
