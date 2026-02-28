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
          sqlite3
          # Add your other Python dependencies here
        ]);
        
      in
      {
        # The AAIA package
        packages.aaia = pkgs.python3Packages.buildPythonApplication {
          pname = "aaia";
          version = "0.1.0";
          
          src = ./packages;
          
          propagatedBuildInputs = with pkgs.python3Packages; [
            requests
            psutil
            sqlite3
          ];
          
          # Install main.py as executable
          installPhase = ''
            mkdir -p $out/bin
            cp -r modules $out/lib/aaia/
            cp main.py $out/lib/aaia/
            
            cat > $out/bin/aaia << 'EOF'
#!/bin/sh
exec ${pythonEnv}/bin/python $out/lib/aaia/main.py "$@"
EOF
            chmod +x $out/bin/aaia
          '';
        };
        
        # NixOS module that creates users and services
        nixosModules.aaia = { config, pkgs, ... }: {
          # Create aaia user
          users.users.aaia = {
            isSystemUser = true;
            group = "aaia";
            description = "AAIA Autonomous AI Agent";
          };
          
          users.groups.aaia = {};
          
          # Create systemd service
          systemd.services.aaia = {
            description = "AAIA Autonomous AI Agent";
            wantedBy = [ "multi-user.target" ];
            after = [ "network.target" ];
            
            serviceConfig = {
              Type = "simple";
              User = "aaia";
              Group = "aaia";
              ExecStart = "${self.packages.${system}.aaia}/bin/aaia";
              Restart = "on-failure";
              RestartSec = 5;
              
              # State directory
              StateDirectory = "aaia";
              StateDirectoryMode = "0755";
            };
            
            # Environment variables
            environment = {
              PYTHONPATH = "${self.packages.${system}.aaia}/lib/aaia";
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