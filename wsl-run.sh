#!/usr/bin/env bash
# Helper script for GitHub Copilot to run AAIA commands in WSL
# Usage: ./wsl-run.sh <command>

WSL_DIST="Ubuntu-24.04"
AAIA_PATH="/mnt/c/Users/Marcelo.Trenkenchu/source/repos/matren6/aaia"

case "${1:-help}" in
    build)
        wsl -d "$WSL_DIST" -e bash -c "cd $AAIA_PATH && nix build .#aaia"
        ;;
    run)
        wsl -d "$WSL_DIST" -e bash -c "cd $AAIA_PATH && ./result/bin/aaia"
        ;;
    test)
        wsl -d "$WSL_DIST" -e bash -c "cd $AAIA_PATH && ./wsl-test.sh"
        ;;
    dev)
        wsl -d "$WSL_DIST" -e bash -c "cd $AAIA_PATH && nix develop"
        ;;
    python)
        wsl -d "$WSL_DIST" -e bash -c "cd $AAIA_PATH && nix develop -c python packages/main.py"
        ;;
    check)
        wsl -d "$WSL_DIST" -e bash -c "cd $AAIA_PATH && nix flake check"
        ;;
    *)
        echo "GitHub Copilot WSL Helper"
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  build   - Build AAIA package"
        echo "  run     - Run AAIA"
        echo "  test    - Run test script"
        echo "  dev     - Enter development shell"
        echo "  python  - Run from Python"
        echo "  check   - Check flake"
        ;;
esac
