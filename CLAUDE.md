# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dead Man's Snitch MCP Server

This MCP server provides tools to interact with Dead Man's Snitch, a monitoring service for scheduled tasks and cron jobs.

## Essential Commands

```bash
# Run tests (uses pytest-asyncio in auto mode)
uv run pytest -v
uv run pytest tests/test_client.py::TestClass::test_method  # Run single test

# Type checking and linting
uv run mypy src/
uv run ruff check
uv run ruff format

# Run server (requires DEADMANSNITCH_API_KEY env var)
DEADMANSNITCH_API_KEY=your_key uv run mcp-deadmansnitch
```

## Nix Development

```bash
# Enter dev shell (provides Python 3.12, uv, ruff, gcc)
nix develop

# Run directly
nix run .

# Build package
nix build .
```

See `NIX.md` for NixOS/Home Manager integration and secrets management.

## Release Process

We use a beta release workflow to test on TestPyPI before production:

1. **Beta releases** (e.g., `v0.1.2-beta1`) publish to TestPyPI only for testing
2. **Production releases** (e.g., `v0.1.2`) require TestPyPI to succeed first, then publish to PyPI

See `RELEASING.md` for detailed release instructions.

## Architecture Overview

The codebase follows a standard MCP server structure:

- **`src/mcp_deadmansnitch/server.py`**: Main MCP server implementation using FastMCP. Handles tool registration and request routing. Entry point is `main()`.
- **`src/mcp_deadmansnitch/client.py`**: HTTP client for Dead Man's Snitch API using httpx. Implements all API interactions with proper authentication and error handling.

### Key Design Patterns

1. **API Authentication**: Uses HTTP Basic Auth with API key as username (no password)
2. **Response Format**: All tools return consistent `{"success": bool, "data": ..., "error": ...}` format
3. **Error Handling**: API errors are caught and wrapped with context via `@handle_errors` decorator
4. **Check-in URLs**: Check-ins use separate URLs (<https://nosnch.in/{token}>) not the main API
5. **Testability**: Each action has a separate `_impl` function (e.g., `list_snitches_impl`) that can be unit tested directly without FastMCP decorator overhead
6. **Unified Tool Design**: Single `snitch` tool with `action` parameter reduces context usage (10 actions → 1 tool definition)

### Unified Tool

The server exposes a single `snitch` tool with an `action` parameter:

```python
snitch(action="list")                    # List all snitches
snitch(action="get", token="abc123")     # Get snitch details
snitch(action="create", name="...", interval="daily")  # Create snitch
snitch(action="update", token="...", name="...")       # Update snitch
snitch(action="delete", token="...")     # Delete snitch
snitch(action="pause", token="...")      # Pause monitoring
snitch(action="unpause", token="...")    # Resume monitoring
snitch(action="check_in", token="...")   # Send check-in
snitch(action="add_tags", token="...", tags=["..."])   # Add tags
snitch(action="remove_tag", token="...", tag="...")    # Remove tag
```

Parameter validation is handled by `ACTION_REQUIREMENTS` dict and `_validate_params()` function. The `snitch_impl()` dispatcher routes to the appropriate `_impl` function.

### Valid Intervals

`15_minute`, `hourly`, `daily`, `weekly`, `monthly`

## Testing Strategy

- **Client tests** (`test_client.py`): Test individual client methods with mocked httpx responses
- **Server tests** (`test_server.py`, `test_integration.py`): Test tool handlers via `_impl` functions
- **Error coverage** (`test_auth_errors.py`, `test_error_coverage.py`, `test_edge_cases.py`): Edge cases and error paths
- **All API calls should be mocked** to avoid rate limits and dependency on external service

## API Endpoints

- Base URL: `https://api.deadmanssnitch.com/v1/`
- Authentication: Basic Auth with API key
- Check-in URL: `https://nosnch.in/{token}` (separate from API)