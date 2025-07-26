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
        assert "Authentication failed: Invalid API key" in str(exc_info.value)

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

    # Client initialization tests moved from test_server.py
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

    # Bug fix regression tests moved from test_bug_fixes.py
    # These tests ensure that pause_snitch, unpause_snitch, and add_tags
    # properly handle 204 No Content responses
    async def test_pause_snitch_handles_204_no_content(self, client, mock_async_client):
        """Test pause_snitch correctly handles 204 No Content response.

        Regression test for bug fix: pause_snitch was not handling
        204 No Content properly.
        """
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
        """Test pause_snitch with until parameter handles 204 No Content.

        Regression test for bug fix: pause_snitch with until parameter
        was not handling 204 No Content properly.
        """
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
        """Test unpause_snitch correctly handles 204 No Content response.

        Regression test for bug fix: unpause_snitch was not handling
        204 No Content properly.
        """
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
        """Test add_tags returns the full updated snitch details.

        Regression test for bug fix: add_tags was not returning full
        snitch details.
        """
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
        """Test complete workflow: add tags and verify response shows all tags.

        Regression test for bug fix: ensuring complete add_tags workflow
        works correctly.
        """
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


# Tests for new client features moved from test_new_features.py
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
