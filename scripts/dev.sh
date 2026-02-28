#!/bin/bash
# Development environment setup

set -e

echo "Starting AAIA development environment..."

# Enter nix develop
nix develop

# You can also add commands here:
# echo "Running tests..."
# python -m pytest tests/