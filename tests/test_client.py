"""Comprehensive tests for the Dead Man's Snitch API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp_deadmansnitch.client import DeadMansSnitchClient, DeadMansSnitchError


class TestDeadMansSnitchClient:
    """Test the Dead Man's Snitch API client."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return DeadMansSnitchClient(api_key="test_api_key")

    @pytest.fixture
    def mock_async_client(self):
        """Create a mock httpx.AsyncClient."""
        with patch("httpx.AsyncClient") as mock:
            yield mock

    async def test_list_snitches_no_tags(self, client, mock_async_client):
        """Test listing snitches without tags."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"token": "abc123", "name": "Test Snitch", "status": "healthy"}
        ]
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.list_snitches()

        # Verify
        assert len(result) == 1
        assert result[0]["token"] == "abc123"
        mock_instance.get.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            params={},
        )

    async def test_list_snitches_with_tags(self, client, mock_async_client):
        """Test listing snitches with tag filtering."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.list_snitches(tags=["production", "critical"])

        # Verify
        assert result == []
        mock_instance.get.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            params={"tags": "production,critical"},
        )

    async def test_list_snitches_http_error(self, client, mock_async_client):
        """Test list_snitches with HTTP error."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.list_snitches()
        assert "Failed to list snitches: 401 - Unauthorized" in str(exc_info.value)

    async def test_get_snitch_success(self, client, mock_async_client):
        """Test successfully getting a snitch."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "healthy",
            "check_in_url": "https://nosnch.in/abc123",
        }
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.get_snitch("abc123")

        # Verify
        assert result["token"] == "abc123"
        assert result["check_in_url"] == "https://nosnch.in/abc123"
        mock_instance.get.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    async def test_check_in_without_message(self, client, mock_async_client):
        """Test check-in without a message."""
        # Setup mock for get_snitch
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "check_in_url": "https://nosnch.in/abc123",
        }
        mock_get_response.raise_for_status = MagicMock()

        # Setup mock for check_in
        mock_post_response = MagicMock()
        mock_post_response.raise_for_status = MagicMock()
        mock_post_response.headers = {"Date": "2025-01-24T12:00:00Z"}

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_get_response
        mock_instance.post.return_value = mock_post_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.check_in("abc123")

        # Verify
        assert result["status"] == "ok"
        assert result["checked_in_at"] == "2025-01-24T12:00:00Z"
        mock_instance.post.assert_called_once_with("https://nosnch.in/abc123")

    async def test_check_in_with_message(self, client, mock_async_client):
        """Test check-in with a message."""
        # Setup mock for get_snitch
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "check_in_url": "https://nosnch.in/abc123",
        }
        mock_get_response.raise_for_status = MagicMock()

        # Setup mock for check_in
        mock_post_response = MagicMock()
        mock_post_response.raise_for_status = MagicMock()
        mock_post_response.headers = {"Date": "2025-01-24T12:00:00Z"}

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_get_response
        mock_instance.post.return_value = mock_post_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.check_in("abc123", "Test message")

        # Verify
        assert result["status"] == "ok"
        mock_instance.post.assert_called_once_with(
            "https://nosnch.in/abc123",
            data={"m": "Test message"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    async def test_check_in_no_url(self, client, mock_async_client):
        """Test check-in when snitch has no check_in_url."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "abc123", "name": "Test"}
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.check_in("abc123")
        assert "No check_in_url found for snitch" in str(exc_info.value)

    async def test_create_snitch_minimal(self, client, mock_async_client):
        """Test creating a snitch with minimal parameters."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token": "new123",
            "name": "New Snitch",
            "interval": "daily",
        }
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.create_snitch(name="New Snitch", interval="daily")

        # Verify
        assert result["token"] == "new123"
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={"name": "New Snitch", "interval": "daily", "alert_type": "basic"},
        )

    async def test_create_snitch_full(self, client, mock_async_client):
        """Test creating a snitch with all parameters."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "token": "new123",
            "name": "Full Snitch",
            "interval": "hourly",
        }
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.create_snitch(
            name="Full Snitch",
            interval="hourly",
            notes="Test notes",
            tags=["test", "dev"],
            alert_type="smart",
        )

        # Verify
        assert result["token"] == "new123"
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={
                "name": "Full Snitch",
                "interval": "hourly",
                "alert_type": "smart",
                "notes": "Test notes",
                "tags": ["test", "dev"],
            },
        )

    async def test_pause_snitch_success(self, client, mock_async_client):
        """Test pausing a snitch."""
        # Setup mock for pause (204 No Content)
        mock_pause_response = MagicMock()
        mock_pause_response.status_code = 204
        mock_pause_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "paused",
        }
        mock_get_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_pause_response
        mock_instance.get.return_value = mock_get_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.pause_snitch("abc123")

        # Verify
        assert result["status"] == "paused"
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/pause",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=None,
        )

    async def test_unpause_snitch_success(self, client, mock_async_client):
        """Test unpausing a snitch."""
        # Setup mock for unpause (204 No Content)
        mock_unpause_response = MagicMock()
        mock_unpause_response.status_code = 204
        mock_unpause_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "healthy",
        }
        mock_get_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_unpause_response
        mock_instance.get.return_value = mock_get_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.unpause_snitch("abc123")

        # Verify
        assert result["status"] == "healthy"
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/unpause",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    async def test_generic_exception_handling(self, client, mock_async_client):
        """Test handling of generic exceptions."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.get.side_effect = Exception("Network error")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.list_snitches()
        assert "Failed to list snitches: Network error" in str(exc_info.value)
