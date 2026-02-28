#!/bin/bash
# Build AAIA

set -e

echo "Building AAIA..."
nix build .#aaia

echo "Build complete. Binary available at: ./result/bin/aaia"