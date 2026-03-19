#!/usr/bin/env bash
# Quick check script - Run this from NixOS ISO to verify environment

echo "NixOS Installation Environment Check"
echo "====================================="
echo ""

echo "1. NixOS tools:"
if command -v nixos-install &> /dev/null; then
    echo "   ✓ nixos-install found"
else
    echo "   ✗ nixos-install NOT found (Are you on NixOS ISO?)"
fi

echo ""
echo "2. Available disks:"
lsblk -d -o NAME,SIZE,TYPE | grep disk | while read -r line; do
    echo "   /dev/$line"
done

echo ""
echo "3. Network interface:"
ip link show | grep -E '^[0-9]+: (en|eth|wlan)' | awk '{print "   " $2}' | sed 's/://g'

echo ""
echo "4. Network connectivity:"
if ping -c 1 -W 2 nixos.org &> /dev/null; then
    echo "   ✓ Network is working"
else
    echo "   ✗ No network connection"
    echo "   Try: systemctl start dhcpcd"
fi

echo ""
echo "5. Memory:"
free -h | grep Mem

echo ""
echo "====================================="
echo "Ready to install!"
echo ""
echo "IMPORTANT: Check your network interface name above."
echo "If it's NOT 'enp0s3', edit configuration.nix before installing!"
echo ""
echo "Run: bash install-nixos.sh [disk]"
echo "Example: bash install-nixos.sh /dev/sda"
