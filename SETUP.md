# AAIA NixOS Deployment Guide

Complete guide for deploying AAIA (Autonomous AI Agent) on NixOS systems.

## 📋 Prerequisites

- NixOS VM with internet connectivity
- Git installed (usually available by default)
- Root/sudo access

## 🚀 Quick Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/matren6/aaia.git
cd aaia
```

### Step 2: Run Automated Installation

```bash
chmod +x install.sh
sudo ./install.sh
```

The script automatically:
- ✅ Enables Nix flakes (if needed)
- ✅ Builds the AAIA package
- ✅ Configures the NixOS system
- ✅ Creates system user and directories
- ✅ Starts the AAIA service
- ✅ Verifies the installation

### Step 3: Verify Installation

```bash
chmod +x test-installation.sh
./test-installation.sh
```

Check service status:
```bash
systemctl status aaia
journalctl -u aaia -f
```

## 📁 Deployment Files

- **`configuration.nix`** - NixOS system configuration for AAIA
- **`flake.nix`** - Nix flake with package and module definitions
- **`install.sh`** - Automated installation script
- **`test-installation.sh`** - Installation verification script

## ⚙️ Configuration

### Environment Variables

Edit `configuration.nix` to customize environment variables:

```nix
systemd.services.aaia.environment = {
  AAIA_LOG_LEVEL = "DEBUG";  # Change log level
  # Add your custom variables:
  # AAIA_API_KEY = "your-api-key";
  # AAIA_CONFIG_FILE = "/var/lib/aaia/config.json";
};
```

After changes, rebuild the system:
```bash
sudo nixos-rebuild switch
sudo systemctl restart aaia
```

### Resource Limits

Default limits (configured in `flake.nix`):
- **Memory**: 2GB max, 1.5GB high watermark
- **CPU**: 200% (up to 2 cores)

To modify, edit the `nixosModules.aaia` section in `flake.nix`.

### Data Directory

AAIA stores data in `/var/lib/aaia/` with subdirectories:
- `/var/lib/aaia/logs` - Application logs
- `/var/lib/aaia/data` - Runtime data
- `/var/lib/aaia/config` - Configuration files

All directories are owned by the `aaia` system user.

## 🔧 Manual Installation

If the automated script fails, you can install manually:

### 1. Enable Nix Flakes

Edit `/etc/nixos/configuration.nix` and add:
```nix
{
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
}
```

Rebuild:
```bash
sudo nixos-rebuild switch
```

### 2. Build AAIA Package

```bash
cd /path/to/aaia
nix build .#aaia
```

### 3. Install Configuration

```bash
# Copy AAIA configuration
sudo cp configuration.nix /etc/nixos/aaia.nix

# Update path in the configuration
sudo sed -i "s|builtins.getFlake.*|builtins.getFlake \"$(pwd)\"|" /etc/nixos/aaia.nix

# Add import to main configuration
echo 'imports = [ ./aaia.nix ];' | sudo tee -a /etc/nixos/configuration.nix

# Or manually edit /etc/nixos/configuration.nix to add:
# imports = [ ./aaia.nix ];
```

### 4. Rebuild System

```bash
sudo nixos-rebuild switch
```

### 5. Manage Service

```bash
# Start service
sudo systemctl start aaia

# Enable auto-start on boot
sudo systemctl enable aaia

# Check status
systemctl status aaia
```

## 🛠️ Service Management

### Common Commands

```bash
# Start the service
sudo systemctl start aaia

# Stop the service
sudo systemctl stop aaia

# Restart the service
sudo systemctl restart aaia

# Enable auto-start on boot
sudo systemctl enable aaia

# Disable auto-start
sudo systemctl disable aaia

# View status
systemctl status aaia

# View logs (follow mode)
journalctl -u aaia -f

# View last 100 log lines
journalctl -u aaia -n 100

# View logs from today
journalctl -u aaia --since today
```

### Service Details

The AAIA service runs with:
- **User/Group**: `aaia` (dedicated system user)
- **Working Directory**: `/var/lib/aaia`
- **Auto-restart**: Enabled (5-second delay on failure)
- **Security**: Protected system/home, private tmp, no new privileges

## 🔍 Troubleshooting

### Service Won't Start

1. Check detailed logs:
   ```bash
   journalctl -u aaia -xe
   ```

2. Test manual execution:
   ```bash
   sudo -u aaia aaia
   ```

3. Verify package exists:
   ```bash
   which aaia
   ls -la $(which aaia)
   ```

### Build Failures

1. Check flake structure:
   ```bash
   nix flake show
   ```

2. Build with verbose output:
   ```bash
   nix build .#aaia --verbose
   ```

3. Verify internet connectivity:
   ```bash
   ping nixos.org
   ```

4. Clear Nix cache if needed:
   ```bash
   nix-collect-garbage
   ```

### Permission Issues

Fix directory ownership:
```bash
sudo chown -R aaia:aaia /var/lib/aaia
sudo chmod 755 /var/lib/aaia
```

### Configuration Errors

If `nixos-rebuild` fails:

1. Check syntax:
   ```bash
   nix-instantiate --parse /etc/nixos/aaia.nix
   ```

2. Review the error message carefully

3. Restore from backup if needed:
   ```bash
   sudo cp /etc/nixos/configuration.nix.backup.<timestamp> /etc/nixos/configuration.nix
   ```

### Service Keeps Restarting

1. Check for errors in logs:
   ```bash
   journalctl -u aaia --since "5 minutes ago"
   ```

2. Verify Python dependencies:
   ```bash
   nix develop
   python -c "import requests, psutil"
   ```

3. Check available resources:
   ```bash
   free -h  # Memory
   df -h    # Disk space
   ```

## 🔄 Updating AAIA

To update to the latest version:

```bash
cd /path/to/aaia
git pull origin main
sudo ./install.sh
```

Or manually:
```bash
git pull origin main
nix build .#aaia
sudo nixos-rebuild switch
sudo systemctl restart aaia
```

## 👨‍💻 Development

### Enter Development Shell

```bash
nix develop
```

This provides:
- Python environment with all dependencies
- Development tools (git, debugpy, etc.)
- Proper PYTHONPATH configuration

### Test Changes Without Installing

```bash
# Build package
nix build .#aaia

# Run from build result
./result/bin/aaia

# Or run directly with nix
nix run .#aaia
```

### Modify and Test

1. Make code changes
2. Test in development shell:
   ```bash
   nix develop
   cd packages
   python main.py
   ```
3. Build and test package:
   ```bash
   nix build .#aaia
   ./result/bin/aaia
   ```

## 🔒 Security Considerations

The AAIA service is configured with security hardening:

- **Dedicated User**: Runs as `aaia` system user (not root)
- **Protected Directories**: Cannot write to system or home directories
- **Private Temporary**: Uses isolated temporary directories
- **No New Privileges**: Cannot escalate privileges
- **Resource Limits**: Memory and CPU limits prevent resource exhaustion
- **Logging**: All activity logged to systemd journal

### Additional Security Recommendations

1. **Review Code**: Audit the source code before production deployment
2. **Network Isolation**: Consider firewall rules or network namespaces
3. **Secrets Management**: Store API keys in environment variables or secret managers
4. **Regular Updates**: Keep NixOS and AAIA updated
5. **Monitoring**: Set up monitoring and alerting for the service

## 📊 Monitoring

### Check Resource Usage

```bash
# Memory usage
systemctl status aaia | grep Memory

# Full resource stats
systemd-cgtop

# Process details
ps aux | grep aaia
```

### Log Analysis

```bash
# Count error messages
journalctl -u aaia | grep -i error | wc -l

# Find specific patterns
journalctl -u aaia | grep "pattern"

# Export logs
journalctl -u aaia --since "2024-01-01" > aaia-logs.txt
```

## 🆘 Getting Help

1. **Check logs first**: `journalctl -u aaia -f`
2. **Run test script**: `./test-installation.sh`
3. **Review this guide**: Look through troubleshooting section
4. **GitHub Issues**: Open an issue at https://github.com/matren6/aaia/issues

## 📝 Quick Reference

```bash
# Installation
git clone https://github.com/matren6/aaia.git && cd aaia
chmod +x install.sh && sudo ./install.sh

# Verification
./test-installation.sh

# Service control
sudo systemctl {start|stop|restart|status} aaia

# Logs
journalctl -u aaia -f

# Update
git pull && sudo ./install.sh

# Development
nix develop
```

---

**Ready to deploy!** Start with `sudo ./install.sh` and AAIA will be running on your NixOS system.