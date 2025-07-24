# Dead Man's Snitch MCP Server - Claude Instructions

This MCP server provides tools to interact with Dead Man's Snitch, a monitoring service for scheduled tasks and cron jobs.

## Key Information

- **API Authentication**: The server uses HTTP Basic Authentication with the API key as the username
- **Check-ins**: Check-ins are sent to a unique URL for each snitch (not through the API)
- **Intervals**: Valid intervals are `15_minute`, `hourly`, `daily`, `weekly`, `monthly`
- **Alert Types**: Can be `basic` or `smart`

## Important Commands

When working with this codebase:

1. **Run tests**: `uv run pytest -v`
2. **Type checking**: `uv run mypy src/`
3. **Linting**: `uv run ruff check`
4. **Format code**: `uv run ruff format`
5. **Run server**: `uv run mcp-deadmansnitch`

## Tool Usage Examples

### Listing Snitches
```
Use list_snitches to see all monitoring tasks
- Filter by tags: list_snitches(tags=["production", "critical"])
- Returns: Array of snitches with their status
```

### Creating a Snitch
```
Use create_snitch to set up new monitoring
- Required: name and interval
- Optional: notes, tags, alert_type, alert_email
- Example: create_snitch(name="Daily Backup", interval="daily", tags=["backup"])
```

### Checking In
```
Use check_in to signal task completion
- Requires: token (from snitch details)
- Optional: message about the check-in
- Example: check_in(token="abc123", message="Backup completed: 5GB")
```

### Managing Snitches
```
- Pause during maintenance: pause_snitch(token="abc123", until="2h")
- Update configuration: update_snitch(token="abc123", interval="hourly")
- Manage tags: add_tags(token="abc123", tags=["new-tag"])
- Delete when no longer needed: delete_snitch(token="abc123")
```

## Best Practices

1. **Tag Organization**: Use consistent tags like `production`, `staging`, `critical`, `backup`
2. **Interval Selection**: Choose intervals that match your task frequency with some buffer
3. **Alert Emails**: Keep alert email lists updated when team members change
4. **Pause vs Delete**: Pause snitches during known maintenance windows instead of deleting
5. **Check-in Messages**: Include useful context in check-in messages for debugging

## Common Workflows

### Setting up monitoring for a new cron job
1. Create snitch with appropriate interval
2. Note the check-in URL from the response
3. Add curl command to end of cron job: `curl https://nosnch.in/TOKEN`

### Investigating missed check-ins
1. Get snitch details to see last check-in time
2. Check snitch status (healthy, pending, or failed)
3. Review any check-in messages for context

### Bulk operations
1. List snitches with specific tags
2. Update multiple snitches using loops
3. Pause all snitches with a specific tag during deployment

## Error Handling

The server returns consistent error responses:
- `success: false` indicates an error occurred
- `error` field contains the error message
- HTTP errors from the API are wrapped with context

## Testing

When adding new features:
1. Add unit tests to `test_client.py`
2. Add integration tests to `test_integration.py`
3. Ensure all tools follow the same response format
4. Mock external API calls to avoid rate limits