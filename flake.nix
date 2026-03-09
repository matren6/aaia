{
  description = "AAIA - Autonomous AI Agent";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python environment with all dependencies
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          requests
          psutil
          python-dotenv
          pytest
        ]);
        
      in
      {
        # The AAIA package
        packages.aaia = pkgs.stdenv.mkDerivation {
          pname = "aaia";
          version = "0.1.0";

          src = ./packages;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          installPhase = ''
            mkdir -p $out/bin $out/lib/aaia

            # Copy all source files
            cp -r modules $out/lib/aaia/
            cp -r prompts $out/lib/aaia/
            cp main.py $out/lib/aaia/

            # Create wrapper script
            makeWrapper ${pythonEnv}/bin/python $out/bin/aaia \
              --add-flags "$out/lib/aaia/main.py" \
              --set PYTHONPATH "$out/lib/aaia"
          '';

          meta = with pkgs.lib; {
            description = "AAIA - Autonomous AI Agent";
            homepage = "https://github.com/matren6/aaia";
            license = licenses.mit; # Adjust license as appropriate
            maintainers = [ ];
            platforms = platforms.linux;
          };
        };
        
        # NixOS module that creates users and services
        nixosModules.aaia = { config, lib, pkgs, ... }: 
        let
          cfg = config.services.aaia;
        in
        {
          options.services.aaia = {
            enable = lib.mkEnableOption "AAIA Autonomous AI Agent";

            user = lib.mkOption {
              type = lib.types.str;
              default = "aaia";
              description = "User to run AAIA as";
            };

            group = lib.mkOption {
              type = lib.types.str;
              default = "aaia";
              description = "Group for AAIA user";
            };

            dataDir = lib.mkOption {
              type = lib.types.path;
              default = "/var/lib/aaia";
              description = "Directory to store AAIA data";
            };

            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.system}.aaia;
              description = "AAIA package to use";
            };
          };

          config = lib.mkIf cfg.enable {
            # Create aaia user
            users.users.${cfg.user} = {
              isSystemUser = true;
              group = cfg.group;
              description = "AAIA Autonomous AI Agent";
              home = cfg.dataDir;
              createHome = true;
            };

            users.groups.${cfg.group} = {};

            # Create systemd service
            systemd.services.aaia = {
              description = "AAIA Autonomous AI Agent";
              wantedBy = [ "multi-user.target" ];
              after = [ "network.target" ];

              serviceConfig = {
                Type = "simple";
                User = cfg.user;
                Group = cfg.group;
                ExecStart = "${cfg.package}/bin/aaia";
                Restart = "on-failure";
                RestartSec = 5;

                # State directory
                StateDirectory = "aaia";
                StateDirectoryMode = "0755";
                WorkingDirectory = cfg.dataDir;

                # Security settings
                ProtectSystem = "strict";
                ProtectHome = true;
                NoNewPrivileges = true;
                PrivateTmp = true;

                # Resource limits
                MemoryMax = "2G";
                MemoryHigh = "1.5G";
              };

              # Environment variables
              environment = {
                PYTHONPATH = "${cfg.package}/lib/aaia";
                AAIA_LOG_LEVEL = "INFO";
                AAIA_DATA_DIR = cfg.dataDir;
              };
            };
          };
        };
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            python3Packages.debugpy
            nix
            git
          ];
          
          shellHook = ''
            echo "AAIA development environment ready"
            export PYTHONPATH=$(pwd)/packages:$PYTHONPATH
          '';
        };
        
        # Default app
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.aaia}/bin/aaia";
        };
      });
}