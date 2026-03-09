#!/bin/bash
# WSL test script for main.py startup (uses Nix environment)

set -e

echo "================================"
echo "WSL AAIA Test Suite (Nix)"
echo "================================"
echo ""

# Enable Nix experimental features
NIX_FLAGS="--extra-experimental-features nix-command --extra-experimental-features flakes"

cd /mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia

echo "Test 1: Check Nix Python version..."
nix $NIX_FLAGS develop -c python --version
echo ""

echo "Test 2: Check dependencies available..."
nix $NIX_FLAGS develop -c python -c "import psutil; import requests; import dotenv; print('✓ All dependencies available')"
echo ""

echo "Test 3: Import test (LLMConfig)..."
nix $NIX_FLAGS develop -c python -c "import sys; sys.path.insert(0, 'packages'); from modules.settings import LLMConfig; print('✓ LLMConfig imported')"
echo ""

echo "Test 4: ModelInfo test..."
nix $NIX_FLAGS develop -c python -c "import sys; sys.path.insert(0, 'packages'); from modules.llm.base_provider import ModelInfo; m = ModelInfo('id', 'name', 'test', {}, 4096, 0.1, 0.2, 'USD'); print(f'✓ ModelInfo working, cost: {m.total_cost_per_1k}')"
echo ""

echo "Test 5: Run full verification..."
nix $NIX_FLAGS develop -c python verify_build.py
echo ""

echo "================================"
echo "✓ WSL Test Complete!"
echo "================================"
