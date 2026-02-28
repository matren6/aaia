{ config, pkgs, ... }:

let
  # Import your flake
  aaiaFlake = builtins.getFlake (builtins.toString ./.);
  
in
{
  imports = [
    aaiaFlake.nixosModules.aaia
  ];
  
  # Base system configuration
  system.stateVersion = "23.11";
  
  # Enable networking
  networking.hostName = "aaia";
  
  # Your AAIA package will be available as aaiaFlake.packages.x86_64-linux.aaia
  environment.systemPackages = [
    aaiaFlake.packages.x86_64-linux.aaia
  ];
}