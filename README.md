# MCP Dead Man's Snitch

[![PyPI version](https://img.shields.io/pypi/v/mcp-deadmansnitch.svg)](https://pypi.org/project/mcp-deadmansnitch/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-deadmansnitch.svg)](https://pypi.org/project/mcp-deadmansnitch/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/jamesbrink/mcp-deadmansnitch/actions/workflows/ci.yml/badge.svg)](https://github.com/jamesbrink/mcp-deadmansnitch/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jamesbrink/mcp-deadmansnitch/graph/badge.svg)](https://codecov.io/gh/jamesbrink/mcp-deadmansnitch)

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

## Available Tools

### `list_snitches`
List all snitches, optionally filtered by tags.

### `get_snitch`
Get details about a specific snitch using its token.

### `check_in`
Send a check-in to confirm a task completed successfully.

### `create_snitch`
Create a new snitch monitor with intervals: 15_minute, hourly, daily, weekly, or monthly.

**Note on array parameters**: When using MCP tools through Claude, pass arrays directly without JSON encoding:
- ✅ Correct: `tags: ["test", "production"]`
- ❌ Incorrect: `tags: "[\"test\", \"production\"]"`

### `update_snitch`
Update snitch configuration including name, interval, notes, tags, and alert settings.

### `delete_snitch`
Permanently delete a snitch.

### `pause_snitch`
Temporarily pause monitoring (optionally until a specific time).

### `unpause_snitch`
Resume monitoring for a paused snitch.

### `add_tags` / `remove_tag`
Manage tags for organizing snitches.

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