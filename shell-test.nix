{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "aaia-test-environment";
  
  buildInputs = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.python-dotenv
    
    # System tools
    curl
    jq
  ];
  
  shellHook = ''
    echo "════════════════════════════════════════════════════════════════"
    echo "  AAIA Tool Building Capabilities - Nix Test Environment"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "🔧 Environment:"
    echo "   Python: $(python3 --version)"
    echo "   Nix:    $(nix --version | head -1)"
    echo "   PWD:    $PWD"
    echo ""
    
    # Set up Python path
    export PYTHONPATH="$PWD/packages:$PYTHONPATH"
    
    # Load environment variables
    if [ -f .env ]; then
      set -a
      source .env
      set +a
      echo "✅ Environment Configuration:"
      echo "   Ollama URL:   $OLLAMA_BASE_URL"
      echo "   Ollama Model: $OLLAMA_MODEL"
      echo "   LLM Provider: $LLM_DEFAULT_PROVIDER"
    else
      echo "⚠️  No .env file found"
    fi
    
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "🚀 Ready to run tests!"
    echo ""
    echo "   Run: python3 test_tool_building_wsl.py"
    echo "   Or:  ./run_test_with_nix.sh"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
  '';
}
