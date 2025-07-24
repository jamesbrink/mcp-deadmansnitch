"""Tests for the MCP Dead Man's Snitch server."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_deadmansnitch.client import DeadMansSnitchClient, DeadMansSnitchError
from mcp_deadmansnitch.server import (
    CheckInParams,
    CreateSnitchParams,
    GetSnitchParams,
    ListSnitchesParams,
    PauseSnitchParams,
    UnpauseSnitchParams,
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

        params = ListSnitchesParams(tags=["production"])
        result = await list_snitches(params)

        assert result["success"] is True
        assert result["count"] == 2
        assert result["snitches"] == mock_snitches
        mock_client.list_snitches.assert_called_once_with(tags=["production"])

    async def test_list_snitches_no_tags(self, mock_client):
        """Test listing snitches without tag filter."""
        mock_snitches = []
        mock_client.list_snitches = AsyncMock(return_value=mock_snitches)

        params = ListSnitchesParams()
        result = await list_snitches(params)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["snitches"] == []
        mock_client.list_snitches.assert_called_once_with(tags=None)

    async def test_list_snitches_error(self, mock_client):
        """Test error handling in list_snitches."""
        mock_client.list_snitches = AsyncMock(
            side_effect=DeadMansSnitchError("API error")
        )

        params = ListSnitchesParams()
        result = await list_snitches(params)

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

        params = GetSnitchParams(token="abc123")
        result = await get_snitch(params)

        assert result["success"] is True
        assert result["snitch"] == mock_snitch
        mock_client.get_snitch.assert_called_once_with("abc123")

    async def test_get_snitch_error(self, mock_client):
        """Test error handling in get_snitch."""
        mock_client.get_snitch = AsyncMock(
            side_effect=DeadMansSnitchError("Snitch not found")
        )

        params = GetSnitchParams(token="invalid")
        result = await get_snitch(params)

        assert result["success"] is False
        assert result["error"] == "Snitch not found"


class TestCheckIn:
    """Tests for check_in tool."""

    async def test_check_in_success(self, mock_client):
        """Test successful check-in."""
        mock_response = {"status": "ok", "checked_in_at": "2025-01-24T12:00:00Z"}
        mock_client.check_in = AsyncMock(return_value=mock_response)

        params = CheckInParams(token="abc123", message="All systems operational")
        result = await check_in(params)

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

        params = CheckInParams(token="abc123")
        result = await check_in(params)

        assert result["success"] is True
        mock_client.check_in.assert_called_once_with("abc123", None)

    async def test_check_in_error(self, mock_client):
        """Test error handling in check_in."""
        mock_client.check_in = AsyncMock(
            side_effect=DeadMansSnitchError("Check-in failed")
        )

        params = CheckInParams(token="abc123")
        result = await check_in(params)

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

        params = CreateSnitchParams(
            name="New Snitch",
            interval="hourly",
            notes="Test notes",
            tags=["test", "dev"],
            alert_type="smart",
        )
        result = await create_snitch(params)

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

        params = CreateSnitchParams(name="Basic Snitch", interval="daily")
        result = await create_snitch(params)

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

        params = CreateSnitchParams(name="Bad Snitch", interval="invalid")
        result = await create_snitch(params)

        assert result["success"] is False
        assert result["error"] == "Invalid interval"


class TestPauseSnitch:
    """Tests for pause_snitch tool."""

    async def test_pause_snitch_success(self, mock_client):
        """Test successful snitch pausing."""
        mock_snitch = {"token": "abc123", "name": "Test Snitch", "status": "paused"}
        mock_client.pause_snitch = AsyncMock(return_value=mock_snitch)

        params = PauseSnitchParams(token="abc123")
        result = await pause_snitch(params)

        assert result["success"] is True
        assert result["message"] == "Snitch paused successfully"
        assert result["snitch"] == mock_snitch
        mock_client.pause_snitch.assert_called_once_with("abc123", None)

    async def test_pause_snitch_error(self, mock_client):
        """Test error handling in pause_snitch."""
        mock_client.pause_snitch = AsyncMock(
            side_effect=DeadMansSnitchError("Already paused")
        )

        params = PauseSnitchParams(token="abc123")
        result = await pause_snitch(params)

        assert result["success"] is False
        assert result["error"] == "Already paused"


class TestUnpauseSnitch:
    """Tests for unpause_snitch tool."""

    async def test_unpause_snitch_success(self, mock_client):
        """Test successful snitch unpausing."""
        mock_snitch = {"token": "abc123", "name": "Test Snitch", "status": "healthy"}
        mock_client.unpause_snitch = AsyncMock(return_value=mock_snitch)

        params = UnpauseSnitchParams(token="abc123")
        result = await unpause_snitch(params)

        assert result["success"] is True
        assert result["message"] == "Snitch unpaused successfully"
        assert result["snitch"] == mock_snitch
        mock_client.unpause_snitch.assert_called_once_with("abc123")

    async def test_unpause_snitch_error(self, mock_client):
        """Test error handling in unpause_snitch."""
        mock_client.unpause_snitch = AsyncMock(
            side_effect=DeadMansSnitchError("Not paused")
        )

        params = UnpauseSnitchParams(token="abc123")
        result = await unpause_snitch(params)

        assert result["success"] is False
        assert result["error"] == "Not paused"


class TestDeadMansSnitchClient:
    """Tests for the DeadMansSnitchClient class."""

    def test_client_initialization_with_api_key(self):
        """Test client initialization with provided API key."""
        client = DeadMansSnitchClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.auth == ("test_key", "")  # HTTP Basic Auth

    def test_client_initialization_from_env(self, monkeypatch):
        """Test client initialization from environment variable."""
        monkeypatch.setenv("DEADMANSNITCH_API_KEY", "env_key")
        client = DeadMansSnitchClient()
        assert client.api_key == "env_key"
        assert client.auth == ("env_key", "")  # HTTP Basic Auth

    def test_client_initialization_no_key(self, monkeypatch):
        """Test client initialization without API key."""
        monkeypatch.delenv("DEADMANSNITCH_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key must be provided"):
            DeadMansSnitchClient()
