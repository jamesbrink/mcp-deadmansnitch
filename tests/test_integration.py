"""Integration tests for MCP server tools."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_deadmansnitch.client import DeadMansSnitchError
from mcp_deadmansnitch.server import (
    CheckInParams,
    CreateSnitchParams,
    GetSnitchParams,
    ListSnitchesParams,
    PauseSnitchParams,
    UnpauseSnitchParams,
    check_in_impl,
    create_snitch_impl,
    get_snitch_impl,
    list_snitches_impl,
    pause_snitch_impl,
    unpause_snitch_impl,
)


class TestMCPToolIntegration:
    """Integration tests for MCP tools."""

    @pytest.fixture
    def mock_client(self):
        """Mock the Dead Man's Snitch client."""
        with patch("mcp_deadmansnitch.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            yield mock_client

    async def test_list_snitches_tool_success(self, mock_client):
        """Test list_snitches tool returns proper MCP response format."""
        # Setup
        mock_snitches = [
            {"token": "abc", "name": "Test 1"},
            {"token": "def", "name": "Test 2"},
        ]
        mock_client.list_snitches = AsyncMock(return_value=mock_snitches)

        # Execute
        params = ListSnitchesParams(tags=["prod"])
        result = await list_snitches_impl(params)

        # Verify MCP response format
        assert result["success"] is True
        assert result["count"] == 2
        assert result["snitches"] == mock_snitches
        assert "error" not in result

    async def test_list_snitches_tool_error(self, mock_client):
        """Test list_snitches tool error handling."""
        # Setup
        mock_client.list_snitches = AsyncMock(
            side_effect=DeadMansSnitchError("Connection failed")
        )

        # Execute
        params = ListSnitchesParams()
        result = await list_snitches_impl(params)

        # Verify error response format
        assert result["success"] is False
        assert result["error"] == "Connection failed"
        assert "snitches" not in result
        assert "count" not in result

    async def test_get_snitch_tool_success(self, mock_client):
        """Test get_snitch tool returns proper format."""
        # Setup
        mock_snitch = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "healthy",
            "check_in_url": "https://nosnch.in/abc123",
        }
        mock_client.get_snitch = AsyncMock(return_value=mock_snitch)

        # Execute
        params = GetSnitchParams(token="abc123")
        result = await get_snitch_impl(params)

        # Verify
        assert result["success"] is True
        assert result["snitch"] == mock_snitch
        assert "error" not in result

    async def test_check_in_tool_with_message(self, mock_client):
        """Test check_in tool with message parameter."""
        # Setup
        mock_response = {"status": "ok", "checked_in_at": "2025-01-24T12:00:00Z"}
        mock_client.check_in = AsyncMock(return_value=mock_response)

        # Execute
        params = CheckInParams(token="abc123", message="Backup completed")
        result = await check_in_impl(params)

        # Verify
        assert result["success"] is True
        assert result["message"] == "Check-in successful"
        assert result["result"] == mock_response
        mock_client.check_in.assert_called_once_with("abc123", "Backup completed")

    async def test_check_in_tool_without_message(self, mock_client):
        """Test check_in tool without message parameter."""
        # Setup
        mock_response = {"status": "ok"}
        mock_client.check_in = AsyncMock(return_value=mock_response)

        # Execute
        params = CheckInParams(token="abc123")
        result = await check_in_impl(params)

        # Verify
        assert result["success"] is True
        mock_client.check_in.assert_called_once_with("abc123", None)

    async def test_create_snitch_tool_all_params(self, mock_client):
        """Test create_snitch tool with all parameters."""
        # Setup
        mock_snitch = {
            "token": "new123",
            "name": "New Monitor",
            "interval": "15_minute",
        }
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        # Execute
        params = CreateSnitchParams(
            name="New Monitor",
            interval="15_minute",
            notes="Critical service monitor",
            tags=["critical", "production"],
            alert_type="smart",
        )
        result = await create_snitch_impl(params)

        # Verify
        assert result["success"] is True
        assert result["message"] == "Snitch created successfully"
        assert result["snitch"] == mock_snitch
        mock_client.create_snitch.assert_called_once_with(
            name="New Monitor",
            interval="15_minute",
            notes="Critical service monitor",
            tags=["critical", "production"],
            alert_type="smart",
            alert_email=None,
        )

    async def test_create_snitch_tool_minimal_params(self, mock_client):
        """Test create_snitch tool with minimal parameters."""
        # Setup
        mock_snitch = {"token": "new123", "name": "Basic Monitor"}
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        # Execute
        params = CreateSnitchParams(name="Basic Monitor", interval="daily")
        await create_snitch_impl(params)

        # Verify defaults are used
        mock_client.create_snitch.assert_called_once_with(
            name="Basic Monitor",
            interval="daily",
            notes=None,
            tags=None,
            alert_type="basic",  # Default value
            alert_email=None,
        )

    async def test_pause_snitch_tool(self, mock_client):
        """Test pause_snitch tool."""
        # Setup
        mock_snitch = {"token": "abc123", "status": "paused"}
        mock_client.pause_snitch = AsyncMock(return_value=mock_snitch)

        # Execute
        params = PauseSnitchParams(token="abc123")
        result = await pause_snitch_impl(params)

        # Verify
        assert result["success"] is True
        assert result["message"] == "Snitch paused successfully"
        assert result["snitch"] == mock_snitch

    async def test_unpause_snitch_tool(self, mock_client):
        """Test unpause_snitch tool."""
        # Setup
        mock_snitch = {"token": "abc123", "status": "healthy"}
        mock_client.unpause_snitch = AsyncMock(return_value=mock_snitch)

        # Execute
        params = UnpauseSnitchParams(token="abc123")
        result = await unpause_snitch_impl(params)

        # Verify
        assert result["success"] is True
        assert result["message"] == "Snitch unpaused successfully"
        assert result["snitch"] == mock_snitch

    async def test_error_consistency_across_tools(self, mock_client):
        """Test that all tools handle errors consistently."""
        error_msg = "API rate limit exceeded"

        # Test each tool's error handling
        tools_and_params = [
            (list_snitches_impl, ListSnitchesParams(), "list_snitches"),
            (get_snitch_impl, GetSnitchParams(token="abc"), "get_snitch"),
            (check_in_impl, CheckInParams(token="abc"), "check_in"),
            (
                create_snitch_impl,
                CreateSnitchParams(name="Test", interval="daily"),
                "create_snitch",
            ),
            (pause_snitch_impl, PauseSnitchParams(token="abc"), "pause_snitch"),
            (unpause_snitch_impl, UnpauseSnitchParams(token="abc"), "unpause_snitch"),
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
