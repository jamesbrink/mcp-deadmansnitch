"""FastMCP server for Dead Man's Snitch."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastmcp import FastMCP

from .client import DeadMansSnitchClient, DeadMansSnitchError

# Initialize FastMCP server
mcp = FastMCP("mcp-deadmansnitch")  # type: ignore[var-annotated]

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


@mcp.tool()
async def list_snitches(tags: list[str] | None = None) -> dict[str, Any]:
    """List all snitches with optional tag filtering.

    Returns a list of all snitches in your Dead Man's Snitch account.
    You can optionally filter by tags to see only snitches with specific tags.

    Args:
        tags: Optional list of tags to filter snitches
    """
    return await list_snitches_impl(tags=tags)  # type: ignore[no-any-return]


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


@mcp.tool()
async def get_snitch(token: str) -> dict[str, Any]:
    """Get details of a specific snitch by token.

    Retrieves comprehensive information about a single snitch including
    its status, check-in history, and configuration.

    Args:
        token: The snitch token
    """
    return await get_snitch_impl(token)  # type: ignore[no-any-return]


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


@mcp.tool()
async def check_in(token: str, message: str | None = None) -> dict[str, Any]:
    """Check in (ping) a snitch.

    Sends a check-in signal to a snitch to indicate that the monitored
    task is still running. You can optionally include a message with
    the check-in for logging purposes.

    Args:
        token: The snitch token
        message: Optional message to include with check-in
    """
    return await check_in_impl(token, message)  # type: ignore[no-any-return]


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


@mcp.tool()
async def create_snitch(
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

    Args:
        name: Name of the snitch
        interval: Check-in interval ('15_minute', 'hourly', 'daily',
            'weekly', 'monthly')
        notes: Optional notes about the snitch
        tags: Optional list of tags
        alert_type: Alert type ('basic' or 'smart')
        alert_email: Optional list of email addresses for alerts
    """
    return await create_snitch_impl(  # type: ignore[no-any-return]
        name=name,
        interval=interval,
        notes=notes,
        tags=tags,
        alert_type=alert_type,
        alert_email=alert_email,
    )


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


@mcp.tool()
async def pause_snitch(token: str, until: str | None = None) -> dict[str, Any]:
    """Pause a snitch.

    Temporarily disables monitoring for a snitch. While paused, the snitch
    will not send alerts if check-ins are missed. This is useful during
    maintenance windows or when temporarily disabling a monitored task.

    Args:
        token: The snitch token
        until: Optional ISO 8601 timestamp to pause until
            (e.g., '2025-01-25T12:00:00Z')
    """
    return await pause_snitch_impl(token, until)  # type: ignore[no-any-return]


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


@mcp.tool()
async def unpause_snitch(token: str) -> dict[str, Any]:
    """Unpause (resume) a snitch.

    Re-enables monitoring for a previously paused snitch. The snitch will
    resume sending alerts if check-ins are missed according to its configured
    interval.

    Args:
        token: The snitch token
    """
    return await unpause_snitch_impl(token)  # type: ignore[no-any-return]


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


@mcp.tool()
async def update_snitch(
    token: str,
    name: str | None = None,
    interval: str | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
    alert_type: str | None = None,
    alert_email: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing snitch.

    Modifies one or more attributes of an existing Dead Man's Snitch monitor.
    All parameters except the token are optional - only provide the fields
    you want to update.

    Note: Tags provided will replace all existing tags, not append to them.
    Use add_tags/remove_tag for incremental tag management.

    Args:
        token: The snitch token
        name: New name for the snitch
        interval: New check-in interval ('15_minute', 'hourly', 'daily',
            'weekly', 'monthly')
        notes: New notes for the snitch
        tags: New tags for the snitch (replaces existing tags)
        alert_type: New alert type ('basic' or 'smart')
        alert_email: New list of email addresses for alerts
    """
    return await update_snitch_impl(  # type: ignore[no-any-return]
        token=token,
        name=name,
        interval=interval,
        notes=notes,
        tags=tags,
        alert_type=alert_type,
        alert_email=alert_email,
    )


@handle_errors
async def delete_snitch_impl(token: str) -> dict[str, Any]:
    """Delete a snitch."""
    result = await get_client().delete_snitch(token)
    return {
        "success": True,
        "message": "Snitch deleted successfully",
        "result": result,
    }


@mcp.tool()
async def delete_snitch(token: str) -> dict[str, Any]:
    """Delete a snitch permanently.

    WARNING: This action cannot be undone. The snitch and all its
    check-in history will be permanently deleted.

    Args:
        token: The snitch token
    """
    return await delete_snitch_impl(token)  # type: ignore[no-any-return]


@handle_errors
async def add_tags_impl(token: str, tags: list[str]) -> dict[str, Any]:
    """Add tags to a snitch."""
    snitch = await get_client().add_tags(token, tags)
    return {
        "success": True,
        "message": f"Added {len(tags)} tags successfully",
        "snitch": snitch,
    }


@mcp.tool()
async def add_tags(token: str, tags: list[str]) -> dict[str, Any]:
    """Add tags to a snitch.

    Appends one or more tags to an existing snitch without affecting
    its current tags. Use this for incremental tag management.

    Args:
        token: The snitch token
        tags: List of tags to add
    """
    return await add_tags_impl(token, tags)  # type: ignore[no-any-return]


@handle_errors
async def remove_tag_impl(token: str, tag: str) -> dict[str, Any]:
    """Remove a tag from a snitch."""
    snitch = await get_client().remove_tag(token, tag)
    return {
        "success": True,
        "message": f"Tag '{tag}' removed successfully",
        "snitch": snitch,
    }


@mcp.tool()
async def remove_tag(token: str, tag: str) -> dict[str, Any]:
    """Remove a specific tag from a snitch.

    Removes a single tag from a snitch without affecting other tags.
    If the tag doesn't exist, the operation will fail.

    Args:
        token: The snitch token
        tag: The tag to remove
    """
    return await remove_tag_impl(token, tag)  # type: ignore[no-any-return]


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
