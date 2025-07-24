"""FastMCP server for Dead Man's Snitch."""

from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .client import DeadMansSnitchClient, DeadMansSnitchError

# Initialize FastMCP server
mcp = FastMCP("mcp-deadmansnitch")  # type: ignore[var-annotated]


# Pydantic models for tool parameters
class ListSnitchesParams(BaseModel):
    """Parameters for listing snitches."""

    tags: list[str] | None = Field(
        None,
        description="Optional list of tags to filter snitches",
    )


class GetSnitchParams(BaseModel):
    """Parameters for getting a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )


class CheckInParams(BaseModel):
    """Parameters for checking in a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )
    message: str | None = Field(
        None,
        description="Optional message to include with check-in",
    )


class CreateSnitchParams(BaseModel):
    """Parameters for creating a snitch."""

    name: str = Field(
        ...,
        description="Name of the snitch",
    )
    interval: str = Field(
        ...,
        description="Check-in interval (e.g., '15_minute', 'hourly', 'daily', "
        "'weekly', 'monthly')",
    )
    notes: str | None = Field(
        None,
        description="Optional notes about the snitch",
    )
    tags: list[str] | None = Field(
        None,
        description="Optional list of tags",
    )
    alert_type: str = Field(
        "basic",
        description="Alert type ('basic' or 'smart')",
    )
    alert_email: list[str] | None = Field(
        None,
        description="Optional list of email addresses for alerts",
    )


class PauseSnitchParams(BaseModel):
    """Parameters for pausing a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )
    until: str | None = Field(
        None,
        description="Optional timestamp or duration to pause until "
        "(e.g., '2025-01-25T12:00:00Z' or '24h')",
    )


class UnpauseSnitchParams(BaseModel):
    """Parameters for unpausing a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )


# Client instance (created lazily)
_client: DeadMansSnitchClient | None = None


def get_client() -> DeadMansSnitchClient:
    """Get or create the client instance."""
    global _client
    if _client is None:
        _client = DeadMansSnitchClient()
    return _client


async def list_snitches_impl(params: ListSnitchesParams) -> dict[str, Any]:
    """List all snitches with optional tag filtering.

    Returns a list of all snitches in your Dead Man's Snitch account.
    You can optionally filter by tags to see only snitches with specific tags.
    """
    try:
        snitches = await get_client().list_snitches(tags=params.tags)
        return {
            "success": True,
            "count": len(snitches),
            "snitches": snitches,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def list_snitches(params: ListSnitchesParams) -> dict[str, Any]:
    """List all snitches with optional tag filtering.

    Returns a list of all snitches in your Dead Man's Snitch account.
    You can optionally filter by tags to see only snitches with specific tags.
    """
    return await list_snitches_impl(params)


async def get_snitch_impl(params: GetSnitchParams) -> dict[str, Any]:
    """Get details of a specific snitch by token.

    Retrieves comprehensive information about a single snitch including
    its status, check-in history, and configuration.
    """
    try:
        snitch = await get_client().get_snitch(params.token)
        return {
            "success": True,
            "snitch": snitch,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def get_snitch(params: GetSnitchParams) -> dict[str, Any]:
    """Get details of a specific snitch by token.

    Retrieves comprehensive information about a single snitch including
    its status, check-in history, and configuration.
    """
    return await get_snitch_impl(params)


async def check_in_impl(params: CheckInParams) -> dict[str, Any]:
    """Check in (ping) a snitch.

    Sends a check-in signal to a snitch to indicate that the monitored
    task is still running. You can optionally include a message with
    the check-in for logging purposes.
    """
    try:
        result = await get_client().check_in(params.token, params.message)
        return {
            "success": True,
            "message": "Check-in successful",
            "result": result,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def check_in(params: CheckInParams) -> dict[str, Any]:
    """Check in (ping) a snitch.

    Sends a check-in signal to a snitch to indicate that the monitored
    task is still running. You can optionally include a message with
    the check-in for logging purposes.
    """
    return await check_in_impl(params)


async def create_snitch_impl(params: CreateSnitchParams) -> dict[str, Any]:
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
    try:
        snitch = await get_client().create_snitch(
            name=params.name,
            interval=params.interval,
            notes=params.notes,
            tags=params.tags,
            alert_type=params.alert_type,
            alert_email=params.alert_email,
        )
        return {
            "success": True,
            "message": "Snitch created successfully",
            "snitch": snitch,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def create_snitch(params: CreateSnitchParams) -> dict[str, Any]:
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
    return await create_snitch_impl(params)


async def pause_snitch_impl(params: PauseSnitchParams) -> dict[str, Any]:
    """Pause a snitch.

    Temporarily disables monitoring for a snitch. While paused, the snitch
    will not send alerts if check-ins are missed. This is useful during
    maintenance windows or when temporarily disabling a monitored task.
    """
    try:
        snitch = await get_client().pause_snitch(params.token, params.until)
        return {
            "success": True,
            "message": "Snitch paused successfully",
            "snitch": snitch,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def pause_snitch(params: PauseSnitchParams) -> dict[str, Any]:
    """Pause a snitch.

    Temporarily disables monitoring for a snitch. While paused, the snitch
    will not send alerts if check-ins are missed. This is useful during
    maintenance windows or when temporarily disabling a monitored task.
    """
    return await pause_snitch_impl(params)


async def unpause_snitch_impl(params: UnpauseSnitchParams) -> dict[str, Any]:
    """Unpause (resume) a snitch.

    Re-enables monitoring for a previously paused snitch. The snitch will
    resume sending alerts if check-ins are missed according to its configured
    interval.
    """
    try:
        snitch = await get_client().unpause_snitch(params.token)
        return {
            "success": True,
            "message": "Snitch unpaused successfully",
            "snitch": snitch,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def unpause_snitch(params: UnpauseSnitchParams) -> dict[str, Any]:
    """Unpause (resume) a snitch.

    Re-enables monitoring for a previously paused snitch. The snitch will
    resume sending alerts if check-ins are missed according to its configured
    interval.
    """
    return await unpause_snitch_impl(params)


# Pydantic models for new tool parameters
class UpdateSnitchParams(BaseModel):
    """Parameters for updating a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )
    name: str | None = Field(
        None,
        description="New name for the snitch",
    )
    interval: str | None = Field(
        None,
        description="New check-in interval (e.g., '15_minute', 'hourly', 'daily', "
        "'weekly', 'monthly')",
    )
    notes: str | None = Field(
        None,
        description="New notes for the snitch",
    )
    tags: list[str] | None = Field(
        None,
        description="New tags for the snitch (replaces existing tags)",
    )
    alert_type: str | None = Field(
        None,
        description="New alert type ('basic' or 'smart')",
    )
    alert_email: list[str] | None = Field(
        None,
        description="New list of email addresses for alerts",
    )


class DeleteSnitchParams(BaseModel):
    """Parameters for deleting a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )


class AddTagsParams(BaseModel):
    """Parameters for adding tags to a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )
    tags: list[str] = Field(
        ...,
        description="List of tags to add",
    )


class RemoveTagParams(BaseModel):
    """Parameters for removing a tag from a snitch."""

    token: str = Field(
        ...,
        description="The snitch token",
    )
    tag: str = Field(
        ...,
        description="The tag to remove",
    )


async def update_snitch_impl(params: UpdateSnitchParams) -> dict[str, Any]:
    """Update an existing snitch."""
    try:
        snitch = await get_client().update_snitch(
            token=params.token,
            name=params.name,
            interval=params.interval,
            notes=params.notes,
            tags=params.tags,
            alert_type=params.alert_type,
            alert_email=params.alert_email,
        )
        return {
            "success": True,
            "message": "Snitch updated successfully",
            "snitch": snitch,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def update_snitch(params: UpdateSnitchParams) -> dict[str, Any]:
    """Update an existing snitch.

    Modifies one or more attributes of an existing Dead Man's Snitch monitor.
    All parameters except the token are optional - only provide the fields
    you want to update.

    Note: Tags provided will replace all existing tags, not append to them.
    Use add_tags/remove_tag for incremental tag management.
    """
    return await update_snitch_impl(params)


async def delete_snitch_impl(params: DeleteSnitchParams) -> dict[str, Any]:
    """Delete a snitch."""
    try:
        result = await get_client().delete_snitch(params.token)
        return {
            "success": True,
            "message": "Snitch deleted successfully",
            "result": result,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def delete_snitch(params: DeleteSnitchParams) -> dict[str, Any]:
    """Delete a snitch permanently.

    WARNING: This action cannot be undone. The snitch and all its
    check-in history will be permanently deleted.
    """
    return await delete_snitch_impl(params)


async def add_tags_impl(params: AddTagsParams) -> dict[str, Any]:
    """Add tags to a snitch."""
    try:
        snitch = await get_client().add_tags(params.token, params.tags)
        return {
            "success": True,
            "message": f"Added {len(params.tags)} tags successfully",
            "snitch": snitch,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def add_tags(params: AddTagsParams) -> dict[str, Any]:
    """Add tags to a snitch.

    Appends one or more tags to an existing snitch without affecting
    its current tags. Use this for incremental tag management.
    """
    return await add_tags_impl(params)


async def remove_tag_impl(params: RemoveTagParams) -> dict[str, Any]:
    """Remove a tag from a snitch."""
    try:
        snitch = await get_client().remove_tag(params.token, params.tag)
        return {
            "success": True,
            "message": f"Tag '{params.tag}' removed successfully",
            "snitch": snitch,
        }
    except DeadMansSnitchError as e:
        return {
            "success": False,
            "error": str(e),
        }


@mcp.tool()
async def remove_tag(params: RemoveTagParams) -> dict[str, Any]:
    """Remove a specific tag from a snitch.

    Removes a single tag from a snitch without affecting other tags.
    If the tag doesn't exist, the operation will fail.
    """
    return await remove_tag_impl(params)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
