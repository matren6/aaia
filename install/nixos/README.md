# NixOS AAIA Automated Installation

Complete automated installation system for deploying AAIA on NixOS.

## 🚀 Quick Start

Boot NixOS installation ISO and run:

```bash
nix-shell -p git
git clone https://github.com/matren6/aaia.git /tmp/aaia
cd /tmp/aaia/install/nixos
bash check-iso.sh              # Check environment (optional)
bash install-nixos.sh          # Install
```

After installation, reboot and login at **192.168.178.105** as **admin:changeme**.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Network Setup](#network-setup)
6. [Post-Installation](#post-installation)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

---

## Overview

### What This Does

The installation script automatically:
- ✅ Partitions disk (512MB EFI + ext4 root)
- ✅ Installs NixOS 24.05 with UEFI boot
- ✅ Configures static IP (192.168.178.105)
- ✅ Sets up German keyboard layout
- ✅ Installs and enables AAIA service
- ✅ Creates admin user with sudo access
- ✅ Enables SSH server

### What You Get

| Component | Details |
|-----------|---------|
| **OS** | NixOS 24.05 |
| **IP Address** | 192.168.178.105/24 |
| **Gateway** | 192.168.178.1 |
| **DNS** | 192.168.178.1, 8.8.8.8 |
| **Hostname** | nixos-aaia |
| **Keyboard** | German (console + X11) |
| **Timezone** | Europe/Berlin |
| **User** | admin (password: changeme) |
| **Root** | password: changeme |
| **SSH** | Enabled (port 22) |
| **AAIA GUI** | http://192.168.178.105:5080 |

---

## Prerequisites

### Required

- ✅ NixOS installation ISO (minimal or graphical)
- ✅ Target machine with at least 4GB disk space
- ✅ Network connectivity
- ✅ Internet access (for downloading packages)

### Important Notes

⚠️ **ALL DATA on target disk will be ERASED!**  
⚠️ **Backup important data before proceeding!**

---

## Installation Steps

### 1. Boot NixOS Installation ISO

Boot your target machine from the NixOS installation ISO. You'll see a command prompt.

### 2. Optional: Enable SSH for Remote Installation

If you want to install remotely via SSH:

```bash
# Set root password
passwd
# Enter password (e.g., 123)

# Start SSH service
systemctl start sshd

# Find IP address
ip a

# From another machine, connect:
# ssh root@<ip-address>
```

### 3. Clone the Repository

```bash
# Install git temporarily
nix-shell -p git

# Clone AAIA repository
cd /tmp
git clone https://github.com/matren6/aaia.git
cd aaia/install/nixos
```

### 4. Check Your Environment (Recommended)

```bash
bash check-iso.sh
```

This will check:
- NixOS installation tools availability
- Available disks
- Network interface names **← IMPORTANT!**
- Network connectivity
- Memory availability

**Pay attention to the network interface name!** If it's not `enp0s3`, you need to edit `configuration.nix`.

### 5. Edit Configuration (If Needed)

#### Change Network Interface

If your interface is NOT `enp0s3`:

```bash
vim configuration.nix
```

Find and change:
```nix
networking.interfaces.enp0s3 = {  # ← Change this
```

Common interface names:
- `enp0s3` - VirtualBox, some physical systems
- `ens18` - Proxmox VMs
- `ens33` - VMware VMs
- `eth0` - Older systems
- `enp2s0` - Various physical systems

#### Other Customizations

You can also customize:
- IP address (default: 192.168.178.105)
- Gateway (default: 192.168.178.1)
- Hostname (default: nixos-aaia)
- Timezone (default: Europe/Berlin)

### 6. Run the Installation

For standard disk `/dev/sda`:
```bash
bash install-nixos.sh
```

For other disks (NVMe, VirtIO, etc.):
```bash
bash install-nixos.sh /dev/nvme0n1  # NVMe
bash install-nixos.sh /dev/vda      # VirtIO
```

The script will:
1. Confirm disk erasure
2. Partition and format disk
3. Mount filesystems
4. Generate hardware configuration
5. Copy AAIA repository to `/mnt/root/aaia`
6. Copy configuration to `/mnt/etc/nixos/`
7. Install NixOS (this takes 5-15 minutes)
8. Set root password to "changeme"

### 7. Reboot

```bash
reboot
```

Remove the installation ISO when prompted.

---

## Configuration

### File Structure

```
install/nixos/
├── install-nixos.sh      # Main installation script
├── check-iso.sh          # Environment check script
├── configuration.nix     # NixOS configuration
└── README.md            # This file
```

### Configuration Details

#### configuration.nix

This file contains the complete NixOS configuration including:

```nix
{
  # Boot loader (UEFI + systemd-boot)
  boot.loader.systemd-boot.enable = true;
  
  # Static network configuration
  networking.interfaces.enp0s3 = {
    ipv4.addresses = [{
      address = "192.168.178.105";
      prefixLength = 24;
    }];
  };
  networking.defaultGateway = "192.168.178.1";
  
  # German keyboard
  console.keyMap = "de";
  services.xserver.xkb.layout = "de";
  
  # AAIA service
  services.aaia.enable = true;
  
  # More configuration...
}
```

After installation, the system imports the AAIA flake from `/root/aaia` to enable the AAIA service.

---

## Network Setup

### Static IP Configuration

The system is configured with a static IP by default:

- **IP**: 192.168.178.105
- **Netmask**: 255.255.255.0 (/24)
- **Gateway**: 192.168.178.1
- **DNS**: 192.168.178.1, 8.8.8.8

### Network Interface

**IMPORTANT**: The default configuration uses `enp0s3`. You must check your actual interface name with:

```bash
ip link
```

If your interface is different, edit `configuration.nix` before installation.

### Common Interface Names

| Interface | Typically Found On |
|-----------|-------------------|
| `enp0s3` | VirtualBox VMs, some physical systems |
| `ens18` | Proxmox VMs |
| `ens33` | VMware VMs |
| `eth0` | Older systems, cloud VMs |
| `enp2s0` | Various physical systems |
| `wlan0` | Wireless adapters |

### Change to DHCP (Optional)

If you prefer DHCP instead of static IP, edit `configuration.nix`:

```nix
# Replace the static IP section with:
networking.useDHCP = true;
# Or use NetworkManager:
# networking.networkmanager.enable = true;
```

---

## Post-Installation

### First Login

After reboot, the system will be available at:
- **SSH**: `ssh admin@192.168.178.105`
- **Password**: `changeme`

### Essential First Steps

1. **Change passwords immediately!**
   ```bash
   passwd              # Change admin password
   sudo passwd root    # Change root password
   ```

2. **Verify AAIA is running**
   ```bash
   systemctl status aaia
   ```

3. **Check logs**
   ```bash
   journalctl -u aaia -f
   ```

4. **Test AAIA command**
   ```bash
   aaia --help
   ```

5. **Access Web GUI**
   Open browser: `http://192.168.178.105:5080`

### Network Verification

```bash
# Check IP configuration
ip addr show

# Test gateway connectivity
ping 192.168.178.1

# Test DNS resolution
ping google.com
```

### Update System Configuration

If you need to modify the system configuration after installation:

```bash
# Edit configuration
sudo vim /etc/nixos/configuration.nix

# Rebuild system
sudo nixos-rebuild switch
```

### Update AAIA

The AAIA repository is located at `/root/aaia`:

```bash
# Update AAIA from git
cd /root/aaia
sudo git pull

# Rebuild system to apply changes
sudo nixos-rebuild switch
```

---

## Troubleshooting

### Installation Issues

#### Problem: Network interface not found after install

**Cause**: Wrong interface name in configuration.nix

**Solution**:
1. Boot from ISO again, or login to broken system
2. Check interface: `ip link`
3. Edit: `sudo vim /etc/nixos/configuration.nix`
4. Change `networking.interfaces.enp0s3` to your interface
5. Rebuild: `sudo nixos-rebuild switch`

#### Problem: No network connectivity after boot

**Solution**:
```bash
# Check interface status
ip addr show

# Check routing
ip route show

# Manually set IP (temporary)
sudo ip addr add 192.168.178.105/24 dev enp0s3
sudo ip route add default via 192.168.178.1

# Then fix configuration.nix and rebuild
```

#### Problem: Cannot find git during installation

**Solution**:
```bash
# Use nix-shell to get git temporarily
nix-shell -p git

# Then clone the repository
```

#### Problem: Disk not /dev/sda

**Check available disks**:
```bash
lsblk
```

**Use correct disk**:
```bash
bash install-nixos.sh /dev/nvme0n1  # For NVMe
bash install-nixos.sh /dev/vda      # For VirtIO
```

#### Problem: Installation fails with flake error

**Cause**: No internet connection or flake evaluation issues

**Solution**:
1. Verify network: `ping nixos.org`
2. Check DNS: `cat /etc/resolv.conf`
3. If needed, set DNS manually:
   ```bash
   echo "nameserver 8.8.8.8" > /etc/resolv.conf
   ```

### Post-Installation Issues

#### Problem: Cannot SSH into system

**Check**:
```bash
# From the system console:
sudo systemctl status sshd
sudo systemctl start sshd

# Check firewall
sudo iptables -L -n | grep 22
```

#### Problem: AAIA service not running

**Check**:
```bash
# Service status
systemctl status aaia

# View logs
journalctl -u aaia -n 50

# Restart service
sudo systemctl restart aaia
```

#### Problem: Web GUI not accessible

**Check**:
```bash
# Verify AAIA is running
systemctl status aaia

# Check port is listening
sudo ss -tlnp | grep 5080

# Check firewall
sudo iptables -L -n | grep 5080
```

---

## Advanced Usage

### Manual Installation

If the automated script doesn't work, you can install manually:

#### 1. Partition Disk

```bash
parted /dev/sda -- mklabel gpt
parted /dev/sda -- mkpart ESP fat32 1MiB 513MiB
parted /dev/sda -- set 1 esp on
parted /dev/sda -- mkpart primary ext4 513MiB 100%
```

#### 2. Format Partitions

```bash
mkfs.fat -F 32 -n BOOT /dev/sda1
mkfs.ext4 -L nixos /dev/sda2
```

#### 3. Mount Filesystems

```bash
mount /dev/sda2 /mnt
mkdir -p /mnt/boot
mount /dev/sda1 /mnt/boot
```

#### 4. Generate Configuration

```bash
nixos-generate-config --root /mnt
```

#### 5. Copy AAIA Files

```bash
mkdir -p /mnt/root
cp -r /tmp/aaia /mnt/root/
cp /tmp/aaia/install/nixos/configuration.nix /mnt/etc/nixos/
```

#### 6. Install

```bash
nixos-install
```

### Customization Examples

#### Change IP Address

Edit `configuration.nix`:
```nix
networking.interfaces.enp0s3 = {
  ipv4.addresses = [{
    address = "192.168.1.100";  # Your IP
    prefixLength = 24;
  }];
};
networking.defaultGateway = "192.168.1.1";  # Your gateway
```

#### Change Hostname

```nix
networking.hostName = "my-aaia-server";
```

#### Add More Users

```nix
users.users.john = {
  isNormalUser = true;
  description = "John Doe";
  extraGroups = [ "wheel" ];
  initialPassword = "temppass";
};
```

#### Enable Automatic Updates

```nix
system.autoUpgrade = {
  enable = true;
  dates = "04:00";
  allowReboot = false;
};
```

#### Add More Firewall Ports

```nix
networking.firewall.allowedTCPPorts = [ 22 5080 8080 443 ];
```

### Updating Configuration After Installation

1. Edit configuration:
   ```bash
   sudo vim /etc/nixos/configuration.nix
   ```

2. Test configuration:
   ```bash
   sudo nixos-rebuild dry-build
   ```

3. Apply changes:
   ```bash
   sudo nixos-rebuild switch
   ```

4. Or just test without persisting:
   ```bash
   sudo nixos-rebuild test
   ```

---

## Files Reference

### Scripts

- **install-nixos.sh**: Main installation script
  - Partitions disk
  - Formats filesystems
  - Installs NixOS with AAIA
  - Usage: `bash install-nixos.sh [disk]`

- **check-iso.sh**: Environment validation script
  - Checks NixOS tools
  - Lists disks
  - Shows network interfaces
  - Tests connectivity

### Configuration

- **configuration.nix**: Complete NixOS configuration
  - Bootloader setup
  - Network configuration (static IP)
  - German keyboard layout
  - AAIA service integration
  - Users, SSH, firewall

---

## Security Notes

### Default Credentials

⚠️ **CHANGE IMMEDIATELY AFTER INSTALLATION!**

- **admin user**: `changeme`
- **root user**: `changeme`

### Recommended Security Steps

1. Change all passwords
2. Disable root SSH login:
   ```nix
   services.openssh.settings.PermitRootLogin = "no";
   ```
3. Use SSH keys instead of passwords
4. Configure proper firewall rules
5. Keep system updated

---

## Support

### Documentation

- **NixOS Manual**: https://nixos.org/manual/nixos/stable/
- **NixOS Options**: https://search.nixos.org/options
- **Flakes**: https://nixos.wiki/wiki/Flakes

### Getting Help

1. Check this README thoroughly
2. Review troubleshooting section
3. Check AAIA repository documentation
4. NixOS Discourse: https://discourse.nixos.org/

---

## Summary

This installation system provides a fully automated way to deploy AAIA on NixOS with:
- One-command installation from ISO
- Static IP networking
- German keyboard layout
- Secure SSH access
- AAIA service running automatically
- Comprehensive documentation

**Ready to install?** Boot the ISO and run:
```bash
cd /tmp/aaia/install/nixos && bash install-nixos.sh
```
