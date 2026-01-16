"""Tests for the MCP Dead Man's Snitch server."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_deadmansnitch.client import DeadMansSnitchError
from mcp_deadmansnitch.server import (
    _validate_params,
    add_tags_impl,
    delete_snitch_impl,
    remove_tag_impl,
    snitch_impl,
    update_snitch_impl,
)
from mcp_deadmansnitch.server import (
    check_in_impl as check_in,
)
from mcp_deadmansnitch.server import (
    create_snitch_impl as create_snitch,
)
from mcp_deadmansnitch.server import (
    get_snitch_impl as get_snitch,
)
from mcp_deadmansnitch.server import (
    list_snitches_impl as list_snitches,
)
from mcp_deadmansnitch.server import (
    pause_snitch_impl as pause_snitch,
)
from mcp_deadmansnitch.server import (
    unpause_snitch_impl as unpause_snitch,
)


@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    with patch("mcp_deadmansnitch.server.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        yield mock_client


class TestListSnitches:
    """Tests for list_snitches tool."""

    async def test_list_snitches_success(self, mock_client):
        """Test successful listing of snitches."""
        mock_snitches = [
            {"token": "abc123", "name": "Test Snitch 1", "status": "healthy"},
            {"token": "def456", "name": "Test Snitch 2", "status": "pending"},
        ]
        mock_client.list_snitches = AsyncMock(return_value=mock_snitches)

        result = await list_snitches(tags=["production"])

        assert result["success"] is True
        assert result["count"] == 2
        assert result["snitches"] == mock_snitches
        mock_client.list_snitches.assert_called_once_with(tags=["production"])

    async def test_list_snitches_no_tags(self, mock_client):
        """Test listing snitches without tag filter."""
        mock_snitches = []
        mock_client.list_snitches = AsyncMock(return_value=mock_snitches)

        result = await list_snitches()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["snitches"] == []
        mock_client.list_snitches.assert_called_once_with(tags=None)

    async def test_list_snitches_error(self, mock_client):
        """Test error handling in list_snitches."""
        mock_client.list_snitches = AsyncMock(
            side_effect=DeadMansSnitchError("API error")
        )

        result = await list_snitches()

        assert result["success"] is False
        assert result["error"] == "API error"


class TestGetSnitch:
    """Tests for get_snitch tool."""

    async def test_get_snitch_success(self, mock_client):
        """Test successful retrieval of a snitch."""
        mock_snitch = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "healthy",
            "interval": "daily",
        }
        mock_client.get_snitch = AsyncMock(return_value=mock_snitch)

        result = await get_snitch(token="abc123")

        assert result["success"] is True
        assert result["snitch"] == mock_snitch
        mock_client.get_snitch.assert_called_once_with("abc123")

    async def test_get_snitch_error(self, mock_client):
        """Test error handling in get_snitch."""
        mock_client.get_snitch = AsyncMock(
            side_effect=DeadMansSnitchError("Snitch not found")
        )

        result = await get_snitch(token="invalid")

        assert result["success"] is False
        assert result["error"] == "Snitch not found"


class TestCheckIn:
    """Tests for check_in tool."""

    async def test_check_in_success(self, mock_client):
        """Test successful check-in."""
        mock_response = {"status": "ok", "checked_in_at": "2025-01-24T12:00:00Z"}
        mock_client.check_in = AsyncMock(return_value=mock_response)

        result = await check_in(token="abc123", message="All systems operational")

        assert result["success"] is True
        assert result["message"] == "Check-in successful"
        assert result["result"] == mock_response
        mock_client.check_in.assert_called_once_with(
            "abc123", "All systems operational"
        )

    async def test_check_in_no_message(self, mock_client):
        """Test check-in without message."""
        mock_response = {"status": "ok"}
        mock_client.check_in = AsyncMock(return_value=mock_response)

        result = await check_in(token="abc123")

        assert result["success"] is True
        mock_client.check_in.assert_called_once_with("abc123", None)

    async def test_check_in_error(self, mock_client):
        """Test error handling in check_in."""
        mock_client.check_in = AsyncMock(
            side_effect=DeadMansSnitchError("Check-in failed")
        )

        result = await check_in(token="abc123")

        assert result["success"] is False
        assert result["error"] == "Check-in failed"


class TestCreateSnitch:
    """Tests for create_snitch tool."""

    async def test_create_snitch_success(self, mock_client):
        """Test successful snitch creation."""
        mock_snitch = {
            "token": "new123",
            "name": "New Snitch",
            "interval": "hourly",
            "check_in_url": "https://nosnch.in/new123",
        }
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        result = await create_snitch(
            name="New Snitch",
            interval="hourly",
            notes="Test notes",
            tags=["test", "dev"],
            alert_type="smart",
        )

        assert result["success"] is True
        assert result["message"] == "Snitch created successfully"
        assert result["snitch"] == mock_snitch
        mock_client.create_snitch.assert_called_once_with(
            name="New Snitch",
            interval="hourly",
            notes="Test notes",
            tags=["test", "dev"],
            alert_type="smart",
            alert_email=None,
        )

    async def test_create_snitch_minimal(self, mock_client):
        """Test creating snitch with minimal parameters."""
        mock_snitch = {"token": "new123", "name": "Basic Snitch"}
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        result = await create_snitch(name="Basic Snitch", interval="daily")

        assert result["success"] is True
        mock_client.create_snitch.assert_called_once_with(
            name="Basic Snitch",
            interval="daily",
            notes=None,
            tags=None,
            alert_type="basic",
            alert_email=None,
        )

    async def test_create_snitch_error(self, mock_client):
        """Test error handling in create_snitch."""
        mock_client.create_snitch = AsyncMock(
            side_effect=DeadMansSnitchError("Invalid interval")
        )

        result = await create_snitch(name="Bad Snitch", interval="invalid")

        assert result["success"] is False
        assert result["error"] == "Invalid interval"


class TestPauseSnitch:
    """Tests for pause_snitch tool."""

    async def test_pause_snitch_success(self, mock_client):
        """Test successful snitch pausing."""
        mock_snitch = {"token": "abc123", "name": "Test Snitch", "status": "paused"}
        mock_client.pause_snitch = AsyncMock(return_value=mock_snitch)

        result = await pause_snitch(token="abc123")

        assert result["success"] is True
        assert result["message"] == "Snitch paused successfully"
        assert result["snitch"] == mock_snitch
        mock_client.pause_snitch.assert_called_once_with("abc123", None)

    async def test_pause_snitch_error(self, mock_client):
        """Test error handling in pause_snitch."""
        mock_client.pause_snitch = AsyncMock(
            side_effect=DeadMansSnitchError("Already paused")
        )

        result = await pause_snitch(token="abc123")

        assert result["success"] is False
        assert result["error"] == "Already paused"


class TestUnpauseSnitch:
    """Tests for unpause_snitch tool."""

    async def test_unpause_snitch_success(self, mock_client):
        """Test successful snitch unpausing."""
        mock_snitch = {"token": "abc123", "name": "Test Snitch", "status": "healthy"}
        mock_client.unpause_snitch = AsyncMock(return_value=mock_snitch)

        result = await unpause_snitch(token="abc123")

        assert result["success"] is True
        assert result["message"] == "Snitch unpaused successfully"
        assert result["snitch"] == mock_snitch
        mock_client.unpause_snitch.assert_called_once_with("abc123")

    async def test_unpause_snitch_error(self, mock_client):
        """Test error handling in unpause_snitch."""
        mock_client.unpause_snitch = AsyncMock(
            side_effect=DeadMansSnitchError("Not paused")
        )

        result = await unpause_snitch(token="abc123")

        assert result["success"] is False
        assert result["error"] == "Not paused"


# Tests for new MCP tools moved from test_new_features.py
class TestNewMCPTools:
    """Test new MCP tool implementations."""

    @pytest.fixture
    def mock_client(self):
        """Mock the Dead Man's Snitch client."""
        with patch("mcp_deadmansnitch.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            yield mock_client

    async def test_update_snitch_tool(self, mock_client):
        """Test update_snitch MCP tool."""
        # Setup
        mock_snitch = {
            "token": "abc123",
            "name": "Updated via Tool",
            "interval": "15_minute",
        }
        mock_client.update_snitch = AsyncMock(return_value=mock_snitch)

        # Execute
        result = await update_snitch_impl(
            token="abc123", name="Updated via Tool", interval="15_minute"
        )

        # Verify
        assert result["success"] is True
        assert result["message"] == "Snitch updated successfully"
        assert result["snitch"] == mock_snitch
        mock_client.update_snitch.assert_called_once_with(
            token="abc123",
            name="Updated via Tool",
            interval="15_minute",
            notes=None,
            tags=None,
            alert_type=None,
            alert_email=None,
        )

    async def test_delete_snitch_tool(self, mock_client):
        """Test delete_snitch MCP tool."""
        # Setup
        mock_client.delete_snitch = AsyncMock(
            return_value={"status": "deleted", "token": "abc123"}
        )

        # Execute
        result = await delete_snitch_impl(token="abc123")

        # Verify
        assert result["success"] is True
        assert result["message"] == "Snitch deleted successfully"
        assert result["result"]["status"] == "deleted"

    async def test_add_tags_tool(self, mock_client):
        """Test add_tags MCP tool."""
        # Setup
        mock_snitch = {"token": "abc123", "tags": ["old", "new1", "new2"]}
        mock_client.add_tags = AsyncMock(return_value=mock_snitch)

        # Execute
        result = await add_tags_impl(token="abc123", tags=["new1", "new2"])

        # Verify
        assert result["success"] is True
        assert result["message"] == "Added 2 tags successfully"
        assert result["snitch"] == mock_snitch

    async def test_remove_tag_tool(self, mock_client):
        """Test remove_tag MCP tool."""
        # Setup
        mock_snitch = {"token": "abc123", "tags": ["tag1", "tag3"]}
        mock_client.remove_tag = AsyncMock(return_value=mock_snitch)

        # Execute
        result = await remove_tag_impl(token="abc123", tag="tag2")

        # Verify
        assert result["success"] is True
        assert result["message"] == "Tag 'tag2' removed successfully"
        assert result["snitch"] == mock_snitch

    async def test_error_handling_consistency(self, mock_client):
        """Test error handling is consistent across new tools."""
        error_msg = "Network timeout"

        # Test each new tool
        tools_and_args = [
            (
                update_snitch_impl,
                {"token": "abc", "name": "Test"},
                "update_snitch",
            ),
            (delete_snitch_impl, {"token": "abc"}, "delete_snitch"),
            (add_tags_impl, {"token": "abc", "tags": ["t1"]}, "add_tags"),
            (remove_tag_impl, {"token": "abc", "tag": "t1"}, "remove_tag"),
        ]

        for tool_func, kwargs, method_name in tools_and_args:
            # Setup mock to raise error
            getattr(mock_client, method_name).side_effect = DeadMansSnitchError(
                error_msg
            )

            # Execute
            result = await tool_func(**kwargs)

            # Verify consistent error format
            assert result["success"] is False
            assert result["error"] == error_msg
            assert len(result) == 2  # Only success and error fields


class TestValidateParams:
    """Tests for _validate_params function."""

    def test_valid_list_action(self):
        """Test valid list action with no required params."""
        result = _validate_params("list", {})
        assert result is None

    def test_valid_list_action_with_tags(self):
        """Test valid list action with optional tags."""
        result = _validate_params("list", {"tags": ["prod"]})
        assert result is None

    def test_valid_get_action(self):
        """Test valid get action with required token."""
        result = _validate_params("get", {"token": "abc123"})
        assert result is None

    def test_missing_required_param(self):
        """Test that missing required params are caught."""
        result = _validate_params("get", {})
        assert result is not None
        assert "requires" in result
        assert "token" in result

    def test_missing_required_param_with_none(self):
        """Test that None values for required params are caught."""
        result = _validate_params("get", {"token": None})
        assert result is not None
        assert "requires" in result

    def test_unknown_action(self):
        """Test that unknown actions are rejected."""
        result = _validate_params("unknown_action", {})
        assert result is not None
        assert "Unknown action" in result
        assert "unknown_action" in result

    def test_create_requires_name_and_interval(self):
        """Test create action requires both name and interval."""
        result = _validate_params("create", {"name": "Test"})
        assert result is not None
        assert "interval" in result

        result = _validate_params("create", {"interval": "daily"})
        assert result is not None
        assert "name" in result

        result = _validate_params("create", {"name": "Test", "interval": "daily"})
        assert result is None

    def test_add_tags_requires_token_and_tags(self):
        """Test add_tags action requires both token and tags."""
        result = _validate_params("add_tags", {"token": "abc"})
        assert result is not None
        assert "tags" in result

        result = _validate_params("add_tags", {"token": "abc", "tags": ["t1"]})
        assert result is None

    def test_update_requires_at_least_one_field(self):
        """Test update action requires at least one field to change."""
        # Only token provided - should fail
        result = _validate_params("update", {"token": "abc123"})
        assert result is not None
        assert "at least one field" in result
        assert "update" in result

    def test_update_with_one_field_passes(self):
        """Test update action passes with token and any one mutable field."""
        # Each optional field should pass validation
        optional_fields = [
            {"token": "abc", "name": "New Name"},
            {"token": "abc", "interval": "daily"},
            {"token": "abc", "notes": "New notes"},
            {"token": "abc", "tags": ["tag1"]},
            {"token": "abc", "alert_type": "smart"},
            {"token": "abc", "alert_email": ["test@example.com"]},
        ]
        for params in optional_fields:
            result = _validate_params("update", params)
            assert result is None, f"Failed for params: {params}"


class TestUnifiedSnitchTool:
    """Tests for the unified snitch_impl dispatcher."""

    @pytest.fixture
    def mock_client(self):
        """Mock the Dead Man's Snitch client."""
        with patch("mcp_deadmansnitch.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            yield mock_client

    async def test_snitch_list_action(self, mock_client):
        """Test snitch tool with list action."""
        mock_snitches = [{"token": "abc123", "name": "Test"}]
        mock_client.list_snitches = AsyncMock(return_value=mock_snitches)

        result = await snitch_impl(action="list")

        assert result["success"] is True
        assert result["count"] == 1
        mock_client.list_snitches.assert_called_once_with(tags=None)

    async def test_snitch_list_with_tags(self, mock_client):
        """Test snitch tool with list action and tags filter."""
        mock_client.list_snitches = AsyncMock(return_value=[])

        result = await snitch_impl(action="list", tags=["prod"])

        assert result["success"] is True
        mock_client.list_snitches.assert_called_once_with(tags=["prod"])

    async def test_snitch_get_action(self, mock_client):
        """Test snitch tool with get action."""
        mock_snitch = {"token": "abc123", "name": "Test"}
        mock_client.get_snitch = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(action="get", token="abc123")

        assert result["success"] is True
        assert result["snitch"] == mock_snitch
        mock_client.get_snitch.assert_called_once_with("abc123")

    async def test_snitch_get_missing_token(self, mock_client):
        """Test snitch tool with get action but missing token."""
        result = await snitch_impl(action="get")

        assert result["success"] is False
        assert "requires" in result["error"]
        assert "token" in result["error"]

    async def test_snitch_create_action(self, mock_client):
        """Test snitch tool with create action."""
        mock_snitch = {"token": "new123", "name": "New"}
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(
            action="create",
            name="New",
            interval="daily",
            notes="Test notes",
        )

        assert result["success"] is True
        assert result["snitch"] == mock_snitch
        mock_client.create_snitch.assert_called_once()

    async def test_snitch_create_missing_params(self, mock_client):
        """Test snitch tool with create action but missing required params."""
        result = await snitch_impl(action="create", name="Test")

        assert result["success"] is False
        assert "requires" in result["error"]
        assert "interval" in result["error"]

    async def test_snitch_update_action(self, mock_client):
        """Test snitch tool with update action."""
        mock_snitch = {"token": "abc123", "name": "Updated"}
        mock_client.update_snitch = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(action="update", token="abc123", name="Updated")

        assert result["success"] is True
        mock_client.update_snitch.assert_called_once()

    async def test_snitch_delete_action(self, mock_client):
        """Test snitch tool with delete action."""
        mock_client.delete_snitch = AsyncMock(return_value={"status": "deleted"})

        result = await snitch_impl(action="delete", token="abc123")

        assert result["success"] is True
        mock_client.delete_snitch.assert_called_once_with("abc123")

    async def test_snitch_pause_action(self, mock_client):
        """Test snitch tool with pause action."""
        mock_snitch = {"token": "abc123", "status": "paused"}
        mock_client.pause_snitch = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(action="pause", token="abc123")

        assert result["success"] is True
        mock_client.pause_snitch.assert_called_once_with("abc123", None)

    async def test_snitch_pause_with_until(self, mock_client):
        """Test snitch tool with pause action and until parameter."""
        mock_snitch = {"token": "abc123", "status": "paused"}
        mock_client.pause_snitch = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(
            action="pause", token="abc123", until="2025-01-25T12:00:00Z"
        )

        assert result["success"] is True
        mock_client.pause_snitch.assert_called_once_with(
            "abc123", "2025-01-25T12:00:00Z"
        )

    async def test_snitch_unpause_action(self, mock_client):
        """Test snitch tool with unpause action."""
        mock_snitch = {"token": "abc123", "status": "healthy"}
        mock_client.unpause_snitch = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(action="unpause", token="abc123")

        assert result["success"] is True
        mock_client.unpause_snitch.assert_called_once_with("abc123")

    async def test_snitch_check_in_action(self, mock_client):
        """Test snitch tool with check_in action."""
        mock_client.check_in = AsyncMock(return_value={"status": "ok"})

        result = await snitch_impl(
            action="check_in", token="abc123", message="All good"
        )

        assert result["success"] is True
        mock_client.check_in.assert_called_once_with("abc123", "All good")

    async def test_snitch_add_tags_action(self, mock_client):
        """Test snitch tool with add_tags action."""
        mock_snitch = {"token": "abc123", "tags": ["new"]}
        mock_client.add_tags = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(action="add_tags", token="abc123", tags=["new"])

        assert result["success"] is True
        mock_client.add_tags.assert_called_once_with("abc123", ["new"])

    async def test_snitch_remove_tag_action(self, mock_client):
        """Test snitch tool with remove_tag action."""
        mock_snitch = {"token": "abc123", "tags": []}
        mock_client.remove_tag = AsyncMock(return_value=mock_snitch)

        result = await snitch_impl(action="remove_tag", token="abc123", tag="old")

        assert result["success"] is True
        mock_client.remove_tag.assert_called_once_with("abc123", "old")

    async def test_snitch_unknown_action(self, mock_client):
        """Test snitch tool with unknown action."""
        result = await snitch_impl(action="invalid")

        assert result["success"] is False
        assert "Unknown action" in result["error"]
