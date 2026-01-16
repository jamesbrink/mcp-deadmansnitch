"""FastMCP server for Dead Man's Snitch."""

from collections.abc import Callable
from functools import wraps
from typing import Any, Literal, TypeVar

from fastmcp import FastMCP

from .client import DeadMansSnitchClient, DeadMansSnitchError

# Initialize FastMCP server
mcp = FastMCP("mcp-deadmansnitch")

# Type variable for decorator
T = TypeVar("T")


def handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle common errors in tool implementations."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return await func(*args, **kwargs)  # type: ignore[no-any-return]
        except ValueError as e:
            # Handle missing API key or other validation errors
            return {
                "success": False,
                "error": str(e),
            }
        except DeadMansSnitchError as e:
            # Handle Dead Man's Snitch API errors
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            # Handle unexpected errors
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }

    return wrapper


# Client instance (created lazily)
_client: DeadMansSnitchClient | None = None


def get_client() -> DeadMansSnitchClient:
    """Get or create the client instance.

    Raises:
        ValueError: If no API key is configured.
    """
    global _client
    if _client is None:
        try:
            _client = DeadMansSnitchClient()
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(
                "Dead Man's Snitch API key not configured. "
                "Please set the DEADMANSNITCH_API_KEY environment variable."
            ) from e
    return _client


# Parameter requirements per action: (required_params, optional_params)
ACTION_REQUIREMENTS: dict[str, tuple[set[str], set[str]]] = {
    "list": (set(), {"tags"}),
    "get": ({"token"}, set()),
    "create": ({"name", "interval"}, {"notes", "tags", "alert_type", "alert_email"}),
    "update": (
        {"token"},
        {"name", "interval", "notes", "tags", "alert_type", "alert_email"},
    ),
    "delete": ({"token"}, set()),
    "pause": ({"token"}, {"until"}),
    "unpause": ({"token"}, set()),
    "check_in": ({"token"}, {"message"}),
    "add_tags": ({"token", "tags"}, set()),
    "remove_tag": ({"token", "tag"}, set()),
}


def _validate_params(action: str, params: dict[str, Any]) -> str | None:
    """Return error message if validation fails, None if OK."""
    if action not in ACTION_REQUIREMENTS:
        valid_actions = ", ".join(sorted(ACTION_REQUIREMENTS.keys()))
        return f"Unknown action: {action}. Valid actions: {valid_actions}"
    required, optional = ACTION_REQUIREMENTS[action]
    missing = required - {k for k, v in params.items() if v is not None}
    if missing:
        return f"Action '{action}' requires: {', '.join(sorted(missing))}"

    # Special case: update requires at least one field to change
    if action == "update":
        provided_optional = {
            k for k, v in params.items() if v is not None and k in optional
        }
        if not provided_optional:
            fields = ", ".join(sorted(optional))
            return f"Action 'update' requires at least one field to change: {fields}"

    return None


@handle_errors
async def list_snitches_impl(tags: list[str] | None = None) -> dict[str, Any]:
    """List all snitches with optional tag filtering.

    Returns a list of all snitches in your Dead Man's Snitch account.
    You can optionally filter by tags to see only snitches with specific tags.
    """
    snitches = await get_client().list_snitches(tags=tags)
    return {
        "success": True,
        "count": len(snitches),
        "snitches": snitches,
    }


@handle_errors
async def get_snitch_impl(token: str) -> dict[str, Any]:
    """Get details of a specific snitch by token.

    Retrieves comprehensive information about a single snitch including
    its status, check-in history, and configuration.
    """
    snitch = await get_client().get_snitch(token)
    return {
        "success": True,
        "snitch": snitch,
    }


@handle_errors
async def check_in_impl(token: str, message: str | None = None) -> dict[str, Any]:
    """Check in (ping) a snitch.

    Sends a check-in signal to a snitch to indicate that the monitored
    task is still running. You can optionally include a message with
    the check-in for logging purposes.
    """
    result = await get_client().check_in(token, message)
    return {
        "success": True,
        "message": "Check-in successful",
        "result": result,
    }


@handle_errors
async def create_snitch_impl(
    name: str,
    interval: str,
    notes: str | None = None,
    tags: list[str] | None = None,
    alert_type: str = "basic",
    alert_email: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new snitch.

    Creates a new Dead Man's Snitch monitor with the specified configuration.
    The interval determines how often the snitch expects to receive check-ins.

    Valid intervals:
    - '15_minute': Every 15 minutes
    - 'hourly': Every hour
    - 'daily': Every day
    - 'weekly': Every week
    - 'monthly': Every month
    """
    snitch = await get_client().create_snitch(
        name=name,
        interval=interval,
        notes=notes,
        tags=tags,
        alert_type=alert_type,
        alert_email=alert_email,
    )
    return {
        "success": True,
        "message": "Snitch created successfully",
        "snitch": snitch,
    }


@handle_errors
async def pause_snitch_impl(token: str, until: str | None = None) -> dict[str, Any]:
    """Pause a snitch.

    Temporarily disables monitoring for a snitch. While paused, the snitch
    will not send alerts if check-ins are missed. This is useful during
    maintenance windows or when temporarily disabling a monitored task.
    """
    snitch = await get_client().pause_snitch(token, until)
    return {
        "success": True,
        "message": "Snitch paused successfully",
        "snitch": snitch,
    }


@handle_errors
async def unpause_snitch_impl(token: str) -> dict[str, Any]:
    """Unpause (resume) a snitch.

    Re-enables monitoring for a previously paused snitch. The snitch will
    resume sending alerts if check-ins are missed according to its configured
    interval.
    """
    snitch = await get_client().unpause_snitch(token)
    return {
        "success": True,
        "message": "Snitch unpaused successfully",
        "snitch": snitch,
    }


@handle_errors
async def update_snitch_impl(
    token: str,
    name: str | None = None,
    interval: str | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
    alert_type: str | None = None,
    alert_email: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing snitch."""
    snitch = await get_client().update_snitch(
        token=token,
        name=name,
        interval=interval,
        notes=notes,
        tags=tags,
        alert_type=alert_type,
        alert_email=alert_email,
    )
    return {
        "success": True,
        "message": "Snitch updated successfully",
        "snitch": snitch,
    }


@handle_errors
async def delete_snitch_impl(token: str) -> dict[str, Any]:
    """Delete a snitch."""
    result = await get_client().delete_snitch(token)
    return {
        "success": True,
        "message": "Snitch deleted successfully",
        "result": result,
    }


@handle_errors
async def add_tags_impl(token: str, tags: list[str]) -> dict[str, Any]:
    """Add tags to a snitch."""
    snitch = await get_client().add_tags(token, tags)
    return {
        "success": True,
        "message": f"Added {len(tags)} tags successfully",
        "snitch": snitch,
    }


@handle_errors
async def remove_tag_impl(token: str, tag: str) -> dict[str, Any]:
    """Remove a tag from a snitch."""
    snitch = await get_client().remove_tag(token, tag)
    return {
        "success": True,
        "message": f"Tag '{tag}' removed successfully",
        "snitch": snitch,
    }


async def snitch_impl(
    action: str,
    token: str | None = None,
    name: str | None = None,
    interval: str | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
    alert_type: str | None = None,
    alert_email: list[str] | None = None,
    until: str | None = None,
    message: str | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """Dispatch to appropriate handler based on action."""
    params = {
        "token": token,
        "name": name,
        "interval": interval,
        "notes": notes,
        "tags": tags,
        "alert_type": alert_type,
        "alert_email": alert_email,
        "until": until,
        "message": message,
        "tag": tag,
    }

    if error := _validate_params(action, params):
        return {"success": False, "error": error}

    # Dispatch to existing _impl functions
    # Note: type ignores needed because @handle_errors decorator returns
    # Callable[..., Any] and validation ensures required params are not None
    if action == "list":
        result: dict[str, Any] = await list_snitches_impl(tags=tags)
        return result
    elif action == "get":
        assert token is not None  # Validated above
        return await get_snitch_impl(token)  # type: ignore[no-any-return]
    elif action == "create":
        assert name is not None and interval is not None  # Validated above
        return await create_snitch_impl(  # type: ignore[no-any-return]
            name=name,
            interval=interval,
            notes=notes,
            tags=tags,
            alert_type=alert_type if alert_type is not None else "basic",
            alert_email=alert_email,
        )
    elif action == "update":
        assert token is not None  # Validated above
        return await update_snitch_impl(  # type: ignore[no-any-return]
            token=token,
            name=name,
            interval=interval,
            notes=notes,
            tags=tags,
            alert_type=alert_type,
            alert_email=alert_email,
        )
    elif action == "delete":
        assert token is not None  # Validated above
        return await delete_snitch_impl(token)  # type: ignore[no-any-return]
    elif action == "pause":
        assert token is not None  # Validated above
        return await pause_snitch_impl(token, until)  # type: ignore[no-any-return]
    elif action == "unpause":
        assert token is not None  # Validated above
        return await unpause_snitch_impl(token)  # type: ignore[no-any-return]
    elif action == "check_in":
        assert token is not None  # Validated above
        return await check_in_impl(token, message)  # type: ignore[no-any-return]
    elif action == "add_tags":
        assert token is not None and tags is not None  # Validated above
        return await add_tags_impl(token, tags)  # type: ignore[no-any-return]
    elif action == "remove_tag":
        assert token is not None and tag is not None  # Validated above
        return await remove_tag_impl(token, tag)  # type: ignore[no-any-return]

    return {"success": False, "error": f"Unhandled action: {action}"}


@mcp.tool()
async def snitch(
    action: Literal[
        "list",
        "get",
        "create",
        "update",
        "delete",
        "pause",
        "unpause",
        "check_in",
        "add_tags",
        "remove_tag",
    ],
    token: str | None = None,
    name: str | None = None,
    interval: str | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
    alert_type: str | None = None,
    alert_email: list[str] | None = None,
    until: str | None = None,
    message: str | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """Manage Dead Man's Snitch monitors.

    Actions:
      list       - List snitches. Optional: tags (filter)
      get        - Get snitch. Required: token
      create     - Create snitch. Required: name, interval
      update     - Update snitch. Required: token + at least one field
      delete     - Delete snitch. Required: token
      pause      - Pause monitoring. Required: token. Optional: until
      unpause    - Resume monitoring. Required: token
      check_in   - Send check-in. Required: token. Optional: message
      add_tags   - Add tags. Required: token, tags
      remove_tag - Remove tag. Required: token, tag

    Optional params for create/update: notes, tags, alert_type, alert_email

    Valid intervals: 15_minute, hourly, daily, weekly, monthly
    Valid alert_types: basic, smart
    """
    return await snitch_impl(
        action=action,
        token=token,
        name=name,
        interval=interval,
        notes=notes,
        tags=tags,
        alert_type=alert_type,
        alert_email=alert_email,
        until=until,
        message=message,
        tag=tag,
    )


def main() -> None:
    """Run the MCP server."""
    import sys

    try:
        mcp.run()
    except KeyboardInterrupt:
        # Exit cleanly on Ctrl+C
        sys.exit(0)


if __name__ == "__main__":
    main()
