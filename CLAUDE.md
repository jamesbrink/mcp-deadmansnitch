# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dead Man's Snitch MCP Server

This MCP server provides tools to interact with Dead Man's Snitch, a monitoring service for scheduled tasks and cron jobs.

## Essential Commands

```bash
# Run tests
uv run pytest -v
uv run pytest tests/test_client.py::TestClass::test_method  # Run single test

# Type checking and linting
uv run mypy src/
uv run ruff check
uv run ruff format

# Run server
uv run mcp-deadmansnitch
```

## Architecture Overview

The codebase follows a standard MCP server structure:

- **`src/mcp_deadmansnitch/server.py`**: Main MCP server implementation using the `mcp` framework. Handles tool registration and request routing.
- **`src/mcp_deadmansnitch/client.py`**: HTTP client for Dead Man's Snitch API. Implements all API interactions with proper authentication and error handling.
- **`main.py`**: Entry point that starts the server with stdio transport.

### Key Design Patterns

1. **API Authentication**: Uses HTTP Basic Auth with API key as username (no password)
2. **Response Format**: All tools return consistent `{"success": bool, "data": ..., "error": ...}` format
3. **Error Handling**: API errors are caught and wrapped with context
4. **Check-in URLs**: Check-ins use separate URLs (https://nosnch.in/{token}) not the main API

### Available Tools

- `list_snitches`: Get all snitches with optional tag filtering
- `get_snitch`: Get details for a specific snitch by token
- `create_snitch`: Create new snitch (required: name, interval)
- `update_snitch`: Update snitch configuration
- `delete_snitch`: Delete a snitch
- `pause_snitch`: Temporarily pause monitoring
- `check_in`: Send check-in signal to snitch URL
- `add_tags`/`remove_tags`: Manage snitch tags

### Valid Intervals

`15_minute`, `hourly`, `daily`, `weekly`, `monthly`

## Testing Strategy

- **Unit tests** (`test_client.py`): Test individual client methods with mocked API responses
- **Integration tests** (`test_integration.py`): Test server tool handlers
- **All API calls should be mocked** to avoid rate limits and dependency on external service

## API Endpoints

- Base URL: `https://api.deadmanssnitch.com/v1/`
- Authentication: Basic Auth with API key
- Check-in URL: `https://nosnch.in/{token}` (separate from API)