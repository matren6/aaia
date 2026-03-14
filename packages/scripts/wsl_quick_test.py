#!/usr/bin/env python3
"""
WSL Integration Test - Simplified version that works in WSL
"""

import subprocess
import sys
from pathlib import Path

def run_wsl_test(description, command):
    """Run a test in WSL"""
    print(f"Testing: {description}")
    try:
        result = subprocess.run(
            f'wsl -d Ubuntu-24.04 -e bash -c "{command}"',
            shell=True,
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"  ✅ PASS")
            return True
        else:
            error = result.stderr.decode()[:100]
            print(f"  ❌ FAIL: {error}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ TIMEOUT")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def main():
    print("="*60)
    print("AAIA WSL INTEGRATION TEST")
    print("="*60)
    print()
    
    tests = [
        ("Python 3 installed", "python3 --version"),
        ("Python sqlite3 module", "python3 -c 'import sqlite3; print(\"OK\")'"),
        ("Project files exist", "test -f /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia/packages/main.py && echo OK"),
        ("Modules directory", "test -d /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia/packages/modules && echo OK"),
        ("Database directory", "mkdir -p ~/.local/share/aaia && echo OK"),
        ("Prompts directory", "test -d /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia/packages/prompts && echo OK"),
    ]
    
    passed = 0
    failed = 0
    
    for desc, cmd in tests:
        if run_wsl_test(desc, cmd):
            passed += 1
        else:
            failed += 1
    
    print()
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
