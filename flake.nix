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

          # Docker image (Linux only)
          docker = let
            # Format git commit date as ISO 8601 (YYYYMMDDHHMMSS -> YYYY-MM-DDTHH:MM:SSZ)
            d = self.lastModifiedDate;
            createdDate = "${builtins.substring 0 4 d}-${builtins.substring 4 2 d}-${builtins.substring 6 2 d}T${builtins.substring 8 2 d}:${builtins.substring 10 2 d}:${builtins.substring 12 2 d}Z";
            version = mcp-deadmansnitch.version;
            rev = self.rev or self.dirtyRev or "unknown";
          in
            pkgs.dockerTools.buildLayeredImage {
              name = "mcp-deadmansnitch";
              tag = "latest";
              created = createdDate;

              contents = [
                mcp-deadmansnitch
                pkgs.cacert # For HTTPS
              ];

              config = {
                Entrypoint = ["${mcp-deadmansnitch}/bin/mcp-deadmansnitch"];
                Env = [
                  "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                ];
                Labels = {
                  "org.opencontainers.image.title" = "mcp-deadmansnitch";
                  "org.opencontainers.image.description" = "MCP server for Dead Man's Snitch monitoring service";
                  "org.opencontainers.image.version" = version;
                  "org.opencontainers.image.revision" = rev;
                  "org.opencontainers.image.created" = createdDate;
                  "org.opencontainers.image.source" = "https://github.com/jamesbrink/mcp-deadmansnitch";
                  "org.opencontainers.image.url" = "https://github.com/jamesbrink/mcp-deadmansnitch";
                  "org.opencontainers.image.documentation" = "https://github.com/jamesbrink/mcp-deadmansnitch#readme";
                  "org.opencontainers.image.licenses" = "MIT";
                  "org.opencontainers.image.authors" = "James Brink <james@jamesbrink.net>";
                };
              };
            };
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
