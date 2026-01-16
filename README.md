# MCP Dead Man's Snitch

[![PyPI version](https://img.shields.io/pypi/v/mcp-deadmansnitch.svg)](https://pypi.org/project/mcp-deadmansnitch/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-deadmansnitch.svg)](https://pypi.org/project/mcp-deadmansnitch/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/jamesbrink/mcp-deadmansnitch/actions/workflows/ci.yml/badge.svg)](https://github.com/jamesbrink/mcp-deadmansnitch/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jamesbrink/mcp-deadmansnitch/graph/badge.svg)](https://codecov.io/gh/jamesbrink/mcp-deadmansnitch)
[![FlakeHub](https://img.shields.io/endpoint?url=https://flakehub.com/f/jamesbrink/mcp-deadmansnitch/badge)](https://flakehub.com/flake/jamesbrink/mcp-deadmansnitch)
[![Nix Flake](https://img.shields.io/badge/Nix-flake-blue?logo=nixos)](https://nixos.org)

A Model Context Protocol (MCP) server for [Dead Man's Snitch](https://deadmanssnitch.com/) monitoring service. This server enables AI assistants like Claude to interact with Dead Man's Snitch to monitor scheduled tasks and cron jobs.

## What it does

This MCP server provides tools to:

- List and search your monitoring snitches
- Check in (ping) snitches to confirm tasks are running
- Create new monitors for your scheduled jobs
- Update, pause, or delete existing monitors
- Manage tags for organizing your snitches

## Installation & Setup

1. Get your API key from [Dead Man's Snitch account settings](https://deadmanssnitch.com/account/integrations)

2. Configure your MCP client by adding this to your settings:

```json
{
  "mcpServers": {
    "deadmansnitch": {
      "command": "uvx",
      "args": ["mcp-deadmansnitch"],
      "env": {
        "DEADMANSNITCH_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Nix / NixOS

For Nix users, this project provides a flake with packages, overlays, and a development shell:

```bash
# Run directly
nix run github:jamesbrink/mcp-deadmansnitch

# Build the package
nix build github:jamesbrink/mcp-deadmansnitch
```

See [NIX.md](NIX.md) for detailed NixOS configuration and declarative usage.

### Docker

A Docker image can be built from the Nix flake:

```bash
# Build and load the image
nix build github:jamesbrink/mcp-deadmansnitch#docker
docker load < result

# Run the server
docker run --rm -e DEADMANSNITCH_API_KEY="your_api_key" mcp-deadmansnitch:latest
```

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

## Available Tools

This MCP server exposes a single unified `snitch` tool with an `action` parameter to reduce context usage when connecting to LLMs.

### `snitch`

Manage Dead Man's Snitch monitors with the following actions:

| Action | Description | Required Params | Optional Params |
|--------|-------------|-----------------|-----------------|
| `list` | List all snitches | - | `tags` (filter) |
| `get` | Get snitch details | `token` | - |
| `create` | Create new snitch | `name`, `interval` | `notes`, `tags`, `alert_type`, `alert_email` |
| `update` | Update snitch | `token` | `name`, `interval`, `notes`, `tags`, `alert_type`, `alert_email` |
| `delete` | Delete snitch | `token` | - |
| `pause` | Pause monitoring | `token` | `until` (ISO 8601) |
| `unpause` | Resume monitoring | `token` | - |
| `check_in` | Send check-in | `token` | `message` |
| `add_tags` | Add tags | `token`, `tags` | - |
| `remove_tag` | Remove a tag | `token`, `tag` | - |

**Valid intervals**: `15_minute`, `hourly`, `daily`, `weekly`, `monthly`

**Valid alert_types**: `basic`, `smart`

## Example Usage in Claude

Once configured, you can ask Claude:

- "List all my Dead Man's Snitch monitors"
- "Create a daily monitor called 'Database Backup'"
- "Check in the backup-job snitch"
- "Pause the deployment monitor for 2 hours"
- "Show me all snitches tagged with 'production'"

## Support

- [GitHub Issues](https://github.com/jamesbrink/mcp-deadmansnitch/issues)
- [Dead Man's Snitch API Docs](https://deadmanssnitch.com/docs/api/v1)
- [MCP Documentation](https://modelcontextprotocol.io/)

## License

MIT License - see [LICENSE](LICENSE) file for details.
