#!/usr/bin/env bash
# NixOS AAIA Installation Script
# Run this script FROM the NixOS installation ISO after cloning the repo
# Usage: bash install-nixos.sh [disk]
# Example: bash install-nixos.sh /dev/sda

set -e

DISK="${1:-/dev/sda}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "==========================================="
echo "NixOS AAIA Installation"
echo "==========================================="
echo "Repository: $REPO_DIR"
echo "Install script: $SCRIPT_DIR"
echo "Target disk: $DISK"
echo ""
echo "This will:"
echo "  1. Partition $DISK (512MB EFI + rest ext4)"
echo "  2. Format and mount filesystems"
echo "  3. Install NixOS with AAIA configuration"
echo ""
echo "⚠️  WARNING: ALL DATA ON $DISK WILL BE ERASED!"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Installation cancelled."
    exit 0
fi

echo ""
echo "Step 1: Partitioning disk $DISK..."

# Unmount any existing partitions
umount ${DISK}* 2>/dev/null || true

# Wipe partition table
wipefs -a "$DISK"

# Create GPT partition table
parted "$DISK" --script -- mklabel gpt

# Create EFI partition (512MB)
parted "$DISK" --script -- mkpart ESP fat32 1MiB 513MiB
parted "$DISK" --script -- set 1 esp on

# Create root partition (rest of disk)
parted "$DISK" --script -- mkpart primary ext4 513MiB 100%

# Determine partition names
if [[ $DISK == *"nvme"* ]] || [[ $DISK == *"mmcblk"* ]]; then
    BOOT_PART="${DISK}p1"
    ROOT_PART="${DISK}p2"
else
    BOOT_PART="${DISK}1"
    ROOT_PART="${DISK}2"
fi

# Wait for kernel to recognize partitions
sleep 2

echo ""
echo "Step 2: Formatting partitions..."

# Format EFI partition
mkfs.fat -F 32 -n BOOT "$BOOT_PART"

# Format root partition
mkfs.ext4 -L nixos "$ROOT_PART"

echo ""
echo "Step 3: Mounting filesystems..."

# Mount root
mount "$ROOT_PART" /mnt

# Create and mount boot
mkdir -p /mnt/boot
mount "$BOOT_PART" /mnt/boot

echo ""
echo "Step 4: Generating hardware configuration..."

# Generate hardware config
nixos-generate-config --root /mnt

echo ""
echo "Step 5: Copying AAIA repository and configuration..."

# Copy the entire AAIA repo to /mnt/root/aaia
mkdir -p /mnt/root
cp -r "$REPO_DIR" /mnt/root/aaia

# Copy the configuration.nix from install/nixos/ to /mnt/etc/nixos/
cp "$SCRIPT_DIR/configuration.nix" /mnt/etc/nixos/configuration.nix

echo "Configuration copied from repository."
echo ""
echo "Step 6: Installing NixOS..."
echo "This will take several minutes..."
echo ""

# Install NixOS
nixos-install --no-root-passwd

echo ""
echo "Step 7: Setting root password..."
# Set root password via nixos-enter
nixos-enter --root /mnt -c 'echo "root:changeme" | chpasswd'

echo ""
echo "==========================================="
echo "Installation Complete!"
echo "==========================================="
echo ""
echo "Next steps:"
echo "  1. Reboot: reboot"
echo "  2. System will be available at: 192.168.178.105"
echo "  3. Login as: admin (password: changeme)"
echo "  4. Change passwords: passwd && sudo passwd root"
echo "  5. Check AAIA: systemctl status aaia"
echo "  6. Access Web GUI: http://192.168.178.105:5080"
echo ""
echo "⚠️  IMPORTANT: Change default passwords immediately!"
echo ""
