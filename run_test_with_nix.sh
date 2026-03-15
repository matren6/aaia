#!/usr/bin/env bash
#
# Run Tool Building Tests in Nix Flake Environment
# Uses the AAIA flake.nix development environment
#

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  AAIA Tool Building Capabilities - Nix Flake Test"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if we're in WSL
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo "✅ Running in WSL"
else
    echo "⚠️  Not running in WSL (continuing anyway)"
fi

# Check if nix is available
if ! command -v nix &> /dev/null; then
    echo "❌ ERROR: Nix is not installed or not in PATH"
    echo ""
    echo "Please install Nix with flakes support:"
    echo "  curl -L https://nixos.org/nix/install | sh"
    echo "  mkdir -p ~/.config/nix"
    echo '  echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf'
    echo ""
    exit 1
fi

echo "✅ Nix available: $(nix --version | head -1)"

# Check for .env file
if [ -f .env ]; then
    echo "✅ Found .env configuration"
    OLLAMA_URL=$(grep OLLAMA_BASE_URL .env | cut -d= -f2 || echo "Not set")
    OLLAMA_MODEL=$(grep OLLAMA_MODEL .env | cut -d= -f2 || echo "Not set")
    echo "   Ollama URL: $OLLAMA_URL"
    echo "   Ollama Model: $OLLAMA_MODEL"
else
    echo "⚠️  No .env file found - using defaults"
fi

echo ""
echo "🔧 Entering Nix development shell (flake)..."
echo ""

# Use nix develop with flakes (as per copilot-instructions-testing.md)
nix develop \
    --extra-experimental-features 'nix-command flakes' \
    --command bash -c "
        echo '✅ Inside Nix development environment'
        echo '   Python: '\$(python3 --version)
        echo '   PYTHONPATH: packages'
        echo ''
        echo '🧪 Running tool building capability tests...'
        echo ''
        PYTHONPATH=packages python3 test_tool_building_wsl.py
    "

EXIT_CODE=$?

echo ""
echo "════════════════════════════════════════════════════════════════"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Tests completed successfully!"
else
    echo "⚠️  Tests completed with exit code: $EXIT_CODE"
fi
echo "════════════════════════════════════════════════════════════════"

exit $EXIT_CODE
