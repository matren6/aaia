#!/usr/bin/env bash
# WSL Testing Helper Script
# Runs AAIA in WSL with proper Nix environment and .env configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "============================================"
echo "AAIA WSL Test Runner"
echo "============================================"
echo ""

# Check if we're in WSL
if ! grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
    echo "⚠️  Warning: Not running in WSL"
fi

# Check if Nix is available
if ! command -v nix &> /dev/null; then
    echo "❌ Error: Nix is not available"
    echo "   Please ensure Nix is installed and in PATH"
    exit 1
fi

echo "✅ Nix available"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Using default configuration"
    echo ""
fi

# Run with Nix development environment
echo "Running AAIA with Nix environment..."
echo "This ensures python-dotenv and all dependencies are available"
echo ""

if [ $# -eq 0 ]; then
    # Interactive mode
    nix develop --extra-experimental-features "nix-command flakes" --command python3 packages/main.py
else
    # Pass through all arguments
    nix develop --extra-experimental-features "nix-command flakes" --command python3 packages/main.py "$@"
fi
