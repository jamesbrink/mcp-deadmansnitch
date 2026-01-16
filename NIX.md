# Nix Usage

This project provides a Nix flake for reproducible builds and easy integration with NixOS systems.

## Quick Start

### Run directly with `nix run`

```bash
# Run the MCP server directly (requires API key in environment)
DEADMANSNITCH_API_KEY="your_api_key" nix run github:jamesbrink/mcp-deadmansnitch

# Or from a local checkout
DEADMANSNITCH_API_KEY="your_api_key" nix run .
```

### Build the package

```bash
# Build the package
nix build github:jamesbrink/mcp-deadmansnitch

# The binary will be at ./result/bin/mcp-deadmansnitch
```

## Docker

The flake includes a Docker image target, providing another deployment option.

### Build Docker Image

```bash
# Build the Docker image via Nix
nix build .#docker

# Load into Docker
docker load < result

# Run (requires API key)
docker run --rm -e DEADMANSNITCH_API_KEY="your_api_key" mcp-deadmansnitch:latest
```

### MCP Client Configuration (Docker)

Configure your MCP client to use Docker:

```json
{
  "mcpServers": {
    "deadmansnitch": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-e", "DEADMANSNITCH_API_KEY", "mcp-deadmansnitch:latest"],
      "env": {
        "DEADMANSNITCH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Note: The `-i` flag keeps stdin open, which is required for MCP's stdio transport.

## NixOS Configuration

### Using the Overlay

Add the flake to your NixOS configuration inputs and apply the overlay:

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    mcp-deadmansnitch.url = "github:jamesbrink/mcp-deadmansnitch";
  };

  outputs = { self, nixpkgs, mcp-deadmansnitch, ... }: {
    nixosConfigurations.your-hostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        # Apply the overlay
        {
          nixpkgs.overlays = [ mcp-deadmansnitch.overlays.default ];
        }
        ./configuration.nix
      ];
    };
  };
}
```

Then in your `configuration.nix`:

```nix
{ pkgs, ... }:
{
  # Install the package system-wide
  environment.systemPackages = [ pkgs.mcp-deadmansnitch ];
}
```

### Using Packages Directly (without overlay)

Alternatively, use the package directly without an overlay:

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    mcp-deadmansnitch.url = "github:jamesbrink/mcp-deadmansnitch";
  };

  outputs = { self, nixpkgs, mcp-deadmansnitch, ... }: {
    nixosConfigurations.your-hostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs = { inherit mcp-deadmansnitch; };
      modules = [ ./configuration.nix ];
    };
  };
}
```

```nix
# configuration.nix
{ pkgs, mcp-deadmansnitch, ... }:
{
  environment.systemPackages = [
    mcp-deadmansnitch.packages.${pkgs.system}.default
  ];
}
```

## Home Manager Configuration

For user-level installation with Home Manager:

```nix
# home.nix
{ pkgs, mcp-deadmansnitch, ... }:
{
  home.packages = [
    mcp-deadmansnitch.packages.${pkgs.system}.default
  ];

  # For API key management, see "Secrets Management" section below.
  # Note: home.sessionVariables are set at activation time, not runtime,
  # so command substitution like $(cat ...) won't work here.
}
```

## MCP Client Configuration

Configure your MCP client (e.g., Claude Desktop) to use the Nix-installed binary:

```json
{
  "mcpServers": {
    "deadmansnitch": {
      "command": "mcp-deadmansnitch",
      "env": {
        "DEADMANSNITCH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Or if using `nix run` directly:

```json
{
  "mcpServers": {
    "deadmansnitch": {
      "command": "nix",
      "args": ["run", "github:jamesbrink/mcp-deadmansnitch"],
      "env": {
        "DEADMANSNITCH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Secrets Management

For production NixOS systems, avoid hardcoding API keys. Instead use:

### sops-nix

```nix
{ config, pkgs, ... }:
{
  sops.secrets.deadmansnitch-api-key = {
    owner = "your-user";
  };

  # Use in a systemd service
  systemd.services.my-mcp-service = {
    environment = {
      DEADMANSNITCH_API_KEY_FILE = config.sops.secrets.deadmansnitch-api-key.path;
    };
  };
}
```

### agenix

```nix
{ config, pkgs, ... }:
{
  age.secrets.deadmansnitch-api-key.file = ./secrets/deadmansnitch-api-key.age;

  # Reference the secret path
  environment.variables.DEADMANSNITCH_API_KEY_FILE =
    config.age.secrets.deadmansnitch-api-key.path;
}
```

## Development Shell

Enter the development environment:

```bash
# From the repository root
nix develop

# Or with direnv (if .envrc is allowed)
direnv allow
```

The development shell provides:
- Python 3.12
- uv (Python package manager)
- ruff (linter/formatter)
- gcc/gnumake (for native extensions)

## Flake Outputs

| Output | Description |
|--------|-------------|
| `packages.<system>.default` | The mcp-deadmansnitch package |
| `packages.<system>.mcp-deadmansnitch` | Alias for the default package |
| `packages.<system>.docker` | Docker image (load with `docker load < result`) |
| `apps.<system>.default` | Run with `nix run` |
| `overlays.default` | Nixpkgs overlay adding `pkgs.mcp-deadmansnitch` |
| `devShells.<system>.default` | Development environment |

Supported systems: `x86_64-linux`, `aarch64-linux`, `x86_64-darwin`, `aarch64-darwin`
