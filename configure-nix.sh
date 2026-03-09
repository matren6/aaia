#!/usr/bin/env bash
# Configure Nix to enable experimental features permanently
# Run this once: ./configure-nix.sh

set -e

echo "Configuring Nix to enable experimental features..."
echo ""

# Create nix config directory if it doesn't exist
mkdir -p ~/.config/nix

# Create or update nix.conf
CONFIG_FILE="$HOME/.config/nix/nix.conf"

echo "Creating $CONFIG_FILE..."

cat > "$CONFIG_FILE" << 'EOF'
# Enable experimental features
experimental-features = nix-command flakes
EOF

echo ""
echo "✓ Nix configuration updated!"
echo ""
echo "Configuration written to: $CONFIG_FILE"
echo ""
echo "Enabled features:"
echo "  - nix-command (new Nix CLI)"
echo "  - flakes (Nix flakes support)"
echo ""
echo "You can now run Nix commands without --extra-experimental-features flags."
echo ""
echo "Try running: ./wsl-local.sh build"
