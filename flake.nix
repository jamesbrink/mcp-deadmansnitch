{
  description = "MCP server for Dead Man's Snitch monitoring service";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = inputs @ {
    self,
    flake-parts,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = ["x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin"];

      flake = {
        # Overlay for use in NixOS configurations or other flakes
        overlays.default = final: prev: {
          mcp-deadmansnitch = final.callPackage ./nix/package.nix {src = self;};
        };
      };

      perSystem = {
        pkgs,
        system,
        self',
        ...
      }: let
        # Import the package with self as source
        mcp-deadmansnitch = pkgs.callPackage ./nix/package.nix {src = self;};
      in {
        # Packages
        packages = {
          default = mcp-deadmansnitch;
          mcp-deadmansnitch = mcp-deadmansnitch;
        };

        # Apps for `nix run`
        apps = {
          default = {
            type = "app";
            program = "${mcp-deadmansnitch}/bin/mcp-deadmansnitch";
            meta.description = "Run the MCP Dead Man's Snitch server";
          };
          mcp-deadmansnitch = {
            type = "app";
            program = "${mcp-deadmansnitch}/bin/mcp-deadmansnitch";
            meta.description = "Run the MCP Dead Man's Snitch server";
          };
        };

        # Development shell
        devShells.default = pkgs.mkShell {
          name = "mcp-deadmansnitch";

          packages = with pkgs; [
            # Python
            python312

            # Package management
            uv

            # Development tools (provided via uv, but useful to have natively)
            ruff

            # For building native extensions if needed
            gcc
            gnumake
          ];

          shellHook = ''
            echo "mcp-deadmansnitch development environment"
            echo "Python: $(python --version)"
            echo "uv: $(uv --version)"
            echo ""
            echo "Run 'uv sync' to install dependencies"
          '';

          # Ensure proper locale
          LANG = "en_US.UTF-8";
          LC_ALL = "en_US.UTF-8";
        };

        # Formatter for nix files
        formatter = pkgs.alejandra;

        # Checks
        checks = {
          package = mcp-deadmansnitch;
        };
      };
    };
}
