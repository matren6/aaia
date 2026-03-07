{ config, pkgs, ... }:

let
  # Import the AAIA flake from the current directory
  aaiaFlake = builtins.getFlake (builtins.toString ./.);

in
{
  # Import the AAIA NixOS module
  imports = [
    aaiaFlake.nixosModules.aaia
  ];

  # Enable AAIA service
  services.aaia = {
    enable = true;
    # You can customize other options here:
    # user = "aaia";
    # group = "aaia"; 
    # dataDir = "/var/lib/aaia";
  };

  # Enable experimental features for flakes
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  # System packages
  environment.systemPackages = with pkgs; [
    # Add the AAIA package to system packages
    aaiaFlake.packages.${pkgs.system}.aaia

    # Useful utilities for managing AAIA
    git
    htop
    curl
    wget
  ];

  # Network configuration for the service
  networking.firewall.allowedTCPPorts = [ 
    # Add any ports that AAIA needs to expose
    # 8080  # Example: if AAIA runs a web interface
  ];

  # Logging configuration
  services.journald = {
    # Keep more logs for AAIA debugging
    extraConfig = ''
      SystemMaxUse=1G
      RuntimeMaxUse=100M
    '';
  };

  # Optional: Configure automatic updates for the system
  system.autoUpgrade = {
    enable = false;  # Set to true if you want automatic system updates
    dates = "04:00";
    allowReboot = false;
  };

  # Override service configuration if needed
  systemd.services.aaia.environment = {
    # Custom environment variables for AAIA
    AAIA_LOG_LEVEL = "INFO";

    # Add any other environment variables AAIA needs
    # AAIA_API_KEY = "your-api-key";
    # AAIA_CONFIG_FILE = "/var/lib/aaia/config.json";
  };

  # Create additional directories if needed
  systemd.tmpfiles.rules = [
    "d /var/lib/aaia/logs 0755 aaia aaia -"
    "d /var/lib/aaia/data 0755 aaia aaia -"
    "d /var/lib/aaia/config 0755 aaia aaia -"
  ];
}