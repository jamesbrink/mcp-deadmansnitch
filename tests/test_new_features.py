"""Tests for new Dead Man's Snitch API features."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_deadmansnitch.client import DeadMansSnitchClient, DeadMansSnitchError
from mcp_deadmansnitch.server import (
    AddTagsParams,
    DeleteSnitchParams,
    RemoveTagParams,
    UpdateSnitchParams,
    add_tags_impl,
    delete_snitch_impl,
    remove_tag_impl,
    update_snitch_impl,
)


class TestNewClientFeatures:
    """Test new client API methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return DeadMansSnitchClient(api_key="test_api_key")

    @pytest.fixture
    def mock_async_client(self):
        """Create a mock httpx.AsyncClient."""
        with patch("httpx.AsyncClient") as mock:
            yield mock

    async def test_update_snitch_all_fields(self, client, mock_async_client):
        """Test updating a snitch with all fields."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "abc123", "name": "Updated Snitch"}
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.patch.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.update_snitch(
            token="abc123",
            name="Updated Snitch",
            interval="hourly",
            notes="New notes",
            tags=["tag1", "tag2"],
            alert_type="smart",
            alert_email=["test@example.com"],
        )

        # Verify
        assert result["name"] == "Updated Snitch"
        mock_instance.patch.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={
                "name": "Updated Snitch",
                "interval": "hourly",
                "notes": "New notes",
                "tags": ["tag1", "tag2"],
                "alert_type": "smart",
                "alert_email": ["test@example.com"],
            },
        )

    async def test_update_snitch_partial_fields(self, client, mock_async_client):
        """Test updating a snitch with only some fields."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "abc123"}
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.patch.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        await client.update_snitch(token="abc123", name="New Name")

        # Verify
        mock_instance.patch.assert_called_once()
        call_args = mock_instance.patch.call_args
        assert call_args[1]["json"] == {"name": "New Name"}

    async def test_update_snitch_no_fields_error(self, client):
        """Test updating a snitch with no fields raises error."""
        with pytest.raises(ValueError, match="At least one field must be provided"):
            await client.update_snitch(token="abc123")

    async def test_delete_snitch(self, client, mock_async_client):
        """Test deleting a snitch."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.delete.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.delete_snitch("abc123")

        # Verify
        assert result["status"] == "deleted"
        assert result["token"] == "abc123"
        mock_instance.delete.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    async def test_add_tags(self, client, mock_async_client):
        """Test adding tags to a snitch."""
        # Setup mock for add_tags request (returns array of tags)
        mock_tags_response = MagicMock()
        mock_tags_response.json.return_value = ["existing", "new1", "new2"]
        mock_tags_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch request (returns full snitch details)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "tags": ["existing", "new1", "new2"],
        }
        mock_get_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_tags_response
        mock_instance.get.return_value = mock_get_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.add_tags("abc123", ["new1", "new2"])

        # Verify
        assert result["tags"] == ["existing", "new1", "new2"]
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/tags",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=["new1", "new2"],  # Tags sent as array, not object
        )

    async def test_remove_tag(self, client, mock_async_client):
        """Test removing a tag from a snitch."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "abc123", "tags": ["tag1"]}
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.delete.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.remove_tag("abc123", "tag2")

        # Verify
        assert result["tags"] == ["tag1"]
        mock_instance.delete.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/tags/tag2",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    async def test_pause_snitch_with_until(self, client, mock_async_client):
        """Test pausing a snitch with until parameter."""
        # Setup mock for pause (204 No Content)
        mock_pause_response = MagicMock()
        mock_pause_response.status_code = 204
        mock_pause_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "status": "paused",
            "paused_until": "2025-01-25T12:00:00Z",
        }
        mock_get_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_pause_response
        mock_instance.get.return_value = mock_get_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.pause_snitch("abc123", until="2025-01-25T12:00:00Z")

        # Verify
        assert result["status"] == "paused"
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/pause",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={"until": "2025-01-25T12:00:00Z"},
        )

    async def test_create_snitch_with_alert_email(self, client, mock_async_client):
        """Test creating a snitch with alert_email."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token": "new123",
            "name": "Email Alerts Snitch",
            "alert_email": ["admin@example.com", "ops@example.com"],
        }
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.create_snitch(
            name="Email Alerts Snitch",
            interval="daily",
            alert_email=["admin@example.com", "ops@example.com"],
        )

        # Verify
        assert result["alert_email"] == ["admin@example.com", "ops@example.com"]
        call_args = mock_instance.post.call_args
        assert call_args[1]["json"]["alert_email"] == [
            "admin@example.com",
            "ops@example.com",
        ]


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
        params = UpdateSnitchParams(
            token="abc123", name="Updated via Tool", interval="15_minute"
        )
        result = await update_snitch_impl(params)

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
        params = DeleteSnitchParams(token="abc123")
        result = await delete_snitch_impl(params)

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
        params = AddTagsParams(token="abc123", tags=["new1", "new2"])
        result = await add_tags_impl(params)

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
        params = RemoveTagParams(token="abc123", tag="tag2")
        result = await remove_tag_impl(params)

        # Verify
        assert result["success"] is True
        assert result["message"] == "Tag 'tag2' removed successfully"
        assert result["snitch"] == mock_snitch

    async def test_error_handling_consistency(self, mock_client):
        """Test error handling is consistent across new tools."""
        error_msg = "Network timeout"

        # Test each new tool
        tools_and_params = [
            (
                update_snitch_impl,
                UpdateSnitchParams(token="abc", name="Test"),
                "update_snitch",
            ),
            (delete_snitch_impl, DeleteSnitchParams(token="abc"), "delete_snitch"),
            (add_tags_impl, AddTagsParams(token="abc", tags=["t1"]), "add_tags"),
            (remove_tag_impl, RemoveTagParams(token="abc", tag="t1"), "remove_tag"),
        ]

        for tool_func, params, method_name in tools_and_params:
            # Setup mock to raise error
            getattr(mock_client, method_name).side_effect = DeadMansSnitchError(
                error_msg
            )

            # Execute
            result = await tool_func(params)

            # Verify consistent error format
            assert result["success"] is False
            assert result["error"] == error_msg
            assert len(result) == 2  # Only success and error fields
