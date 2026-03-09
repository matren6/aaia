#!/usr/bin/env bash
# Script to run AAIA commands from INSIDE WSL
# Usage: ./wsl-local.sh <command>

set -e

AAIA_PATH="$(pwd)"

# Enable Nix experimental features
NIX_FLAGS="--extra-experimental-features nix-command --extra-experimental-features flakes"

case "${1:-help}" in
    build)
        echo "Building AAIA with Nix..."
        nix $NIX_FLAGS build .#aaia
        ;;
    run)
        echo "Running AAIA..."
        ./result/bin/aaia
        ;;
    test)
        echo "Running tests..."
        if [ -f "./wsl-test.sh" ]; then
            ./wsl-test.sh
        else
            echo "Error: wsl-test.sh not found"
            exit 1
        fi
        ;;
    dev)
        echo "Entering development shell..."
        nix $NIX_FLAGS develop
        ;;
    python)
        echo "Running Python from Nix environment..."
        nix $NIX_FLAGS develop -c python packages/main.py
        ;;
    check)
        echo "Checking Nix flake..."
        nix $NIX_FLAGS flake check
        ;;
    verify)
        echo "Running build verification..."
        nix $NIX_FLAGS develop -c python verify_build.py
        ;;
    pytest)
        echo "Running unit tests..."
        nix $NIX_FLAGS develop -c python -m pytest tests/test_model_info.py -v
        ;;
    shell)
        echo "Entering Nix development shell with all dependencies..."
        echo "Run 'exit' to leave the shell"
        nix $NIX_FLAGS develop
        ;;
    deps)
        echo "Checking dependencies in Nix environment..."
        nix $NIX_FLAGS develop -c python -c "import psutil; import requests; import dotenv; print('✓ All dependencies available')"
        ;;
    quick-test)
        echo "Quick verification (using Nix environment)..."
        nix $NIX_FLAGS develop -c python -c "import sys; sys.path.insert(0, 'packages'); from modules.llm.base_provider import ModelInfo; print('✓ ModelInfo imported successfully')"
        ;;
    *)
        echo "AAIA WSL Local Helper (run from INSIDE WSL)"
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  build       - Build AAIA package with Nix"
        echo "  run         - Run AAIA from build"
        echo "  test        - Run wsl-test.sh script"
        echo "  dev         - Enter Nix development shell"
        echo "  shell       - Enter Nix shell with all dependencies"
        echo "  python      - Run from Python (with Nix env)"
        echo "  check       - Check Nix flake"
        echo "  verify      - Run build verification script"
        echo "  pytest      - Run pytest unit tests"
        echo "  deps        - Check if dependencies are available"
        echo "  quick-test  - Quick import test"
        echo ""
        echo "Note: Run this script FROM INSIDE WSL, not from Windows"
        echo "      For Windows, use wsl-run.sh instead"
        echo ""
        echo "Important: All Python commands run through Nix environment"
        echo "           which includes all required dependencies (psutil, etc.)"
        ;;
esac
