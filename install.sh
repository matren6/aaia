#!/usr/bin/env bash
set -euo pipefail
export NIX_EXPERIMENTAL_FEATURES="nix-command flakes"

# AAIA NixOS Automated Installation Script
# This script automates the deployment of AAIA on NixOS

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;94m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to check if we're on NixOS
check_nixos() {
    if ! command -v nixos-rebuild &> /dev/null; then
        log_error "This script requires NixOS"
        exit 1
    fi
    log_success "NixOS detected"
}

# Function to backup existing configuration
backup_config() {
    if [[ -f /etc/nixos/configuration.nix ]]; then
        cp /etc/nixos/configuration.nix /etc/nixos/configuration.nix.backup.$(date +%s)
        log_info "Backed up existing configuration.nix"
    fi
}

# Function to enable nix flakes
enable_flakes() {
    log_info "Checking Nix flakes configuration..."
    
    # Check if flakes are already enabled
    if nix --experimental-features="nix-command flakes" config show | grep -q "experimental-features.*flakes"; then
        log_success "Nix flakes already enabled"
        return 0
    fi
    
    log_info "Enabling Nix flakes..."
    
    # Add flakes configuration if not present
    if ! grep -q "experimental-features.*flakes" /etc/nixos/configuration.nix; then
        # Create a temporary configuration that enables flakes
        cat > /tmp/flakes-config.nix << 'EOF'
# Temporary configuration to enable flakes
{
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
}
EOF
        
        # Add import to main configuration
        sed -i '/imports = \[/a\    /tmp/flakes-config.nix' /etc/nixos/configuration.nix
        
        log_info "Rebuilding NixOS with flakes enabled..."
        nixos-rebuild switch
        
        # Remove temporary config and update main config permanently
        rm /tmp/flakes-config.nix
        sed -i '/\/tmp\/flakes-config.nix/d' /etc/nixos/configuration.nix
        
        # Add permanent flakes configuration
        if ! grep -q "nix.settings.experimental-features" /etc/nixos/configuration.nix; then
            sed -i '/^{/a\  nix.settings.experimental-features = [ "nix-command" "flakes" ];' /etc/nixos/configuration.nix
        fi
        
        log_success "Nix flakes enabled successfully"
    fi
}

# Function to build AAIA package
build_aaia() {
    log_info "Building AAIA package..."
    
    cd "$REPO_DIR"
    
    # Verify flake structure
    if ! nix flake show 2>/dev/null; then
        log_error "Invalid flake structure. Please check flake.nix"
        exit 1
    fi
    
    # Build the package
    if nix build .#aaia; then
        log_success "AAIA package built successfully"
    else
        log_error "Failed to build AAIA package"
        exit 1
    fi
}

# Function to install AAIA configuration
install_aaia_config() {
    log_info "Installing AAIA NixOS configuration..."

    # Copy the NixOS configuration to system location
    cp "$REPO_DIR/configuration.nix" /etc/nixos/aaia.nix

    # Add import to main configuration if not already present
    if ! grep -q "aaia.nix" /etc/nixos/configuration.nix; then
        # Find the imports line and add our configuration
        if grep -q "imports = \[" /etc/nixos/configuration.nix; then
            sed -i '/imports = \[/a\    ./aaia.nix' /etc/nixos/configuration.nix
        else
            # Add imports section if it doesn't exist
            sed -i '/^{/a\  imports = [\n    ./aaia.nix\n  ];' /etc/nixos/configuration.nix
        fi
        log_info "Added AAIA configuration import to system configuration"
    fi

    # Update system configuration to use local flake
    sed -i "s|builtins.getFlake.*|builtins.getFlake \"$REPO_DIR\"|" /etc/nixos/aaia.nix

    log_success "AAIA configuration installed"
}

# Function to rebuild NixOS with AAIA
rebuild_nixos() {
    log_info "Rebuilding NixOS with AAIA configuration..."
    
    if nixos-rebuild switch; then
        log_success "NixOS rebuilt successfully with AAIA"
    else
        log_error "Failed to rebuild NixOS"
        log_error "Check the configuration and try again"
        exit 1
    fi
}

# Function to start and enable AAIA service
setup_service() {
    log_info "Setting up AAIA service..."
    
    # Start the service
    if systemctl start aaia; then
        log_success "AAIA service started"
    else
        log_warning "Failed to start AAIA service immediately (this is normal on first install)"
    fi
    
    # Enable the service for auto-start
    if systemctl enable aaia; then
        log_success "AAIA service enabled for auto-start"
    else
        log_error "Failed to enable AAIA service"
        exit 1
    fi
    
    # Give the service a moment to start
    sleep 3
    
    # Check service status
    if systemctl is-active --quiet aaia; then
        log_success "AAIA service is running"
    else
        log_warning "AAIA service is not running. Check logs with: journalctl -u aaia"
    fi
}

# Function to verify installation
verify_installation() {
    log_info "Verifying AAIA installation..."
    
    # Check if aaia command is available
    if command -v aaia &> /dev/null; then
        log_success "AAIA command is available"
    else
        log_error "AAIA command not found in PATH"
        return 1
    fi
    
    # Check service status
    local service_status
    service_status=$(systemctl is-active aaia 2>/dev/null || echo "inactive")
    
    case $service_status in
        "active")
            log_success "AAIA service is active and running"
            ;;
        "inactive")
            log_warning "AAIA service is inactive"
            ;;
        "failed")
            log_error "AAIA service has failed"
            return 1
            ;;
        *)
            log_warning "AAIA service status: $service_status"
            ;;
    esac
    
    # Check data directory
    if [[ -d /var/lib/aaia ]]; then
        log_success "AAIA data directory exists"
    else
        log_warning "AAIA data directory not found"
    fi
    
    return 0
}

# Function to display post-installation information
show_post_install_info() {
    echo
    log_success "AAIA installation completed!"
    echo
    echo "Next steps:"
    echo "1. Check service status: systemctl status aaia"
    echo "2. View service logs: journalctl -u aaia -f"
    echo "3. Test AAIA command: aaia --help"
    echo "4. Data directory: /var/lib/aaia"
    echo
    echo "For more information, see SETUP.md"
    echo
}

# Main installation function
main() {
    log_info "Starting AAIA NixOS automated installation..."
    
    # Perform checks
    check_root
    check_nixos
    
    # Backup existing configuration
    backup_config
    
    # Installation steps
    enable_flakes
    build_aaia
    install_aaia_config
    rebuild_nixos
    setup_service
    
    # Verification
    if verify_installation; then
        show_post_install_info
    else
        log_error "Installation verification failed"
        log_error "Please check the logs and try manual installation steps"
        exit 1
    fi
}

# Handle script interruption
trap 'log_error "Installation interrupted"; exit 130' INT TERM

# Run main function
main "$@"