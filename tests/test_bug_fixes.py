"""Tests to verify the bug fixes for pause_snitch, unpause_snitch, and add_tags."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_deadmansnitch.client import DeadMansSnitchClient


class TestBugFixes:
    """Verify the bug fixes work correctly."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return DeadMansSnitchClient(api_key="test_api_key")

    @pytest.fixture
    def mock_async_client(self):
        """Create a mock httpx.AsyncClient."""
        with patch("httpx.AsyncClient") as mock:
            yield mock

    async def test_pause_snitch_handles_204_no_content(self, client, mock_async_client):
        """Test pause_snitch correctly handles 204 No Content response."""
        # Setup mock for pause request (204 No Content)
        mock_pause_response = MagicMock()
        mock_pause_response.status_code = 204
        mock_pause_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch request (returns updated snitch)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "paused",
            "paused_until": None,
        }
        mock_get_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        # First call is pause, second is get_snitch
        mock_instance.post.return_value = mock_pause_response
        mock_instance.get.return_value = mock_get_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.pause_snitch("abc123")

        # Verify
        assert result["status"] == "paused"
        assert result["token"] == "abc123"
        # Verify pause was called with correct params
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/pause",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=None,
        )
        # Verify get_snitch was called
        mock_instance.get.assert_called_once()

    async def test_pause_snitch_with_until_handles_204(self, client, mock_async_client):
        """Test pause_snitch with until parameter handles 204 No Content."""
        # Setup mock for pause request (204 No Content)
        mock_pause_response = MagicMock()
        mock_pause_response.status_code = 204
        mock_pause_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch request
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
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
        assert result["paused_until"] == "2025-01-25T12:00:00Z"
        # Verify pause was called with until parameter
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/pause",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={"until": "2025-01-25T12:00:00Z"},
        )

    async def test_unpause_snitch_handles_204_no_content(
        self, client, mock_async_client
    ):
        """Test unpause_snitch correctly handles 204 No Content response."""
        # Setup mock for unpause request (204 No Content)
        mock_unpause_response = MagicMock()
        mock_unpause_response.status_code = 204
        mock_unpause_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch request
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "healthy",
            "paused_until": None,
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
        assert result["token"] == "abc123"
        # Verify unpause was called
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/unpause",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    async def test_add_tags_returns_updated_snitch(self, client, mock_async_client):
        """Test add_tags returns the full updated snitch details."""
        # Setup mock for add_tags request (returns array of tags)
        mock_tags_response = MagicMock()
        mock_tags_response.json.return_value = ["original", "test", "new1", "new2"]
        mock_tags_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch request (returns full snitch details)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
            "status": "healthy",
            "tags": ["original", "test", "new1", "new2"],
            "interval": "daily",
        }
        mock_get_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_tags_response
        mock_instance.get.return_value = mock_get_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.add_tags("abc123", ["new1", "new2"])

        # Verify
        assert result["tags"] == ["original", "test", "new1", "new2"]
        assert result["token"] == "abc123"
        assert result["name"] == "Test Snitch"
        # Verify add_tags was called with tags array directly (not wrapped in object)
        mock_instance.post.assert_called_once_with(
            "https://api.deadmanssnitch.com/v1/snitches/abc123/tags",
            auth=("test_api_key", ""),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=["new1", "new2"],  # Tags sent as array, not object
        )
        # Verify get_snitch was called
        mock_instance.get.assert_called_once()

    async def test_add_tags_integration_workflow(self, client, mock_async_client):
        """Test complete workflow: add tags and verify response shows all tags."""
        # Initial snitch has two tags
        initial_tags = ["original", "test"]
        new_tags = ["new1", "new2"]
        all_tags = initial_tags + new_tags

        # Setup mock for add_tags request
        mock_tags_response = MagicMock()
        mock_tags_response.json.return_value = all_tags
        mock_tags_response.raise_for_status = MagicMock()

        # Setup mock for get_snitch request
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "name": "Test Snitch",
            "tags": all_tags,
        }
        mock_get_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_tags_response
        mock_instance.get.return_value = mock_get_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.add_tags("abc123", new_tags)

        # Verify the result contains all tags (old + new)
        assert set(result["tags"]) == set(all_tags)
        assert len(result["tags"]) == 4
