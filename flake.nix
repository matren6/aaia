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