"""Tests targeting uncovered error handling paths to improve code coverage."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mcp_deadmansnitch.client import DeadMansSnitchClient, DeadMansSnitchError


class TestHTTPErrorHandling:
    """Test HTTP error handling paths that are not covered."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return DeadMansSnitchClient(api_key="test_api_key")

    @pytest.fixture
    def mock_async_client(self):
        """Create a mock httpx.AsyncClient."""
        with patch("httpx.AsyncClient") as mock:
            yield mock

    async def test_list_snitches_non_401_http_error(self, client, mock_async_client):
        """Test list_snitches with non-401 HTTP error (line 78)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.list_snitches()
        assert "Failed to list snitches: 500 - Internal Server Error" in str(
            exc_info.value
        )

    async def test_get_snitch_401_error(self, client, mock_async_client):
        """Test get_snitch with 401 authentication error (line 107)."""
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
            await client.get_snitch("abc123")
        assert "Authentication failed: Invalid API key" in str(exc_info.value)

    async def test_get_snitch_generic_exception(self, client, mock_async_client):
        """Test get_snitch with generic exception (lines 115-116)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.get.side_effect = Exception("Connection timeout")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.get_snitch("abc123")
        assert "Failed to get snitch: Connection timeout" in str(exc_info.value)

    async def test_check_in_http_error(self, client, mock_async_client):
        """Test check_in with HTTP error (lines 158-161)."""
        # Setup mock for get_snitch
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "check_in_url": "https://nosnch.in/abc123",
        }
        mock_get_response.raise_for_status = MagicMock()

        # Setup mock for check_in failure
        mock_post_response = MagicMock()
        mock_post_response.status_code = 503
        mock_post_response.text = "Service Unavailable"
        mock_post_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable", request=MagicMock(), response=mock_post_response
        )

        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_get_response
        mock_instance.post.return_value = mock_post_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.check_in("abc123")
        assert "Failed to check in: 503 - Service Unavailable" in str(exc_info.value)

    async def test_check_in_generic_exception(self, client, mock_async_client):
        """Test check_in with generic exception (lines 162-163)."""
        # Setup mock for get_snitch
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = {
            "token": "abc123",
            "check_in_url": "https://nosnch.in/abc123",
        }
        mock_get_response.raise_for_status = MagicMock()

        # Setup mock for check_in failure
        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_get_response
        mock_instance.post.side_effect = Exception("Network error")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.check_in("abc123")
        assert "Failed to check in: Network error" in str(exc_info.value)

    async def test_create_snitch_401_error(self, client, mock_async_client):
        """Test create_snitch with 401 authentication error (lines 212-217)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.create_snitch("Test", "daily")
        assert "Authentication failed: Invalid API key" in str(exc_info.value)

    async def test_create_snitch_non_401_http_error(self, client, mock_async_client):
        """Test create_snitch with non-401 HTTP error (lines 218-221)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Invalid interval"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "422 Unprocessable Entity", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.create_snitch("Test", "invalid_interval")
        assert "Failed to create snitch: 422 - Invalid interval" in str(exc_info.value)

    async def test_create_snitch_generic_exception(self, client, mock_async_client):
        """Test create_snitch with generic exception (lines 222-223)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.post.side_effect = Exception("Connection refused")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.create_snitch("Test", "daily")
        assert "Failed to create snitch: Connection refused" in str(exc_info.value)

    async def test_pause_snitch_returns_json_response(self, client, mock_async_client):
        """Test pause_snitch when API returns JSON instead of 204 (lines 261-262)."""
        # Setup mock - API returns 200 with JSON body instead of 204
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "abc123",
            "status": "paused",
            "paused_until": None,
        }
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.pause_snitch("abc123")

        # Verify - should return the JSON response directly
        assert result["token"] == "abc123"
        assert result["status"] == "paused"

    async def test_pause_snitch_http_error(self, client, mock_async_client):
        """Test pause_snitch with HTTP error (lines 264-267)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Snitch not found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.pause_snitch("abc123")
        assert "Failed to pause snitch: 404 - Snitch not found" in str(exc_info.value)

    async def test_pause_snitch_generic_exception(self, client, mock_async_client):
        """Test pause_snitch with generic exception (lines 268-269)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.post.side_effect = Exception("Network timeout")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.pause_snitch("abc123")
        assert "Failed to pause snitch: Network timeout" in str(exc_info.value)

    async def test_unpause_snitch_returns_json_response(
        self, client, mock_async_client
    ):
        """Test unpause_snitch when API returns JSON instead of 204 (lines 295-296)."""
        # Setup mock - API returns 200 with JSON body instead of 204
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "abc123",
            "status": "healthy",
            "paused_until": None,
        }
        mock_response.raise_for_status = MagicMock()

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute
        result = await client.unpause_snitch("abc123")

        # Verify - should return the JSON response directly
        assert result["token"] == "abc123"
        assert result["status"] == "healthy"

    async def test_unpause_snitch_http_error(self, client, mock_async_client):
        """Test unpause_snitch with HTTP error (lines 298-301)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.text = "Snitch is not paused"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "409 Conflict", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.unpause_snitch("abc123")
        assert "Failed to unpause snitch: 409 - Snitch is not paused" in str(
            exc_info.value
        )

    async def test_unpause_snitch_generic_exception(self, client, mock_async_client):
        """Test unpause_snitch with generic exception (lines 302-303)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.post.side_effect = Exception("SSL error")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.unpause_snitch("abc123")
        assert "Failed to unpause snitch: SSL error" in str(exc_info.value)

    async def test_update_snitch_http_error(self, client, mock_async_client):
        """Test update_snitch with HTTP error (lines 358-362)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid parameters"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.patch.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.update_snitch("abc123", name="New Name")
        assert "Failed to update snitch: 400 - Invalid parameters" in str(
            exc_info.value
        )

    async def test_update_snitch_generic_exception(self, client, mock_async_client):
        """Test update_snitch with generic exception (lines 363-364)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.patch.side_effect = Exception("Database error")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.update_snitch("abc123", name="New Name")
        assert "Failed to update snitch: Database error" in str(exc_info.value)

    async def test_delete_snitch_http_error(self, client, mock_async_client):
        """Test delete_snitch with HTTP error (lines 387-391)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Snitch not found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.delete.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.delete_snitch("abc123")
        assert "Failed to delete snitch: 404 - Snitch not found" in str(exc_info.value)

    async def test_delete_snitch_generic_exception(self, client, mock_async_client):
        """Test delete_snitch with generic exception (lines 392-393)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.delete.side_effect = Exception("Permission denied")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.delete_snitch("abc123")
        assert "Failed to delete snitch: Permission denied" in str(exc_info.value)

    async def test_add_tags_http_error(self, client, mock_async_client):
        """Test add_tags with HTTP error (lines 422-425)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Invalid tags"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "422 Unprocessable Entity", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.add_tags("abc123", ["invalid tag!"])
        assert "Failed to add tags: 422 - Invalid tags" in str(exc_info.value)

    async def test_add_tags_generic_exception(self, client, mock_async_client):
        """Test add_tags with generic exception (lines 426-427)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.post.side_effect = Exception("Memory error")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.add_tags("abc123", ["tag1", "tag2"])
        assert "Failed to add tags: Memory error" in str(exc_info.value)

    async def test_remove_tag_http_error(self, client, mock_async_client):
        """Test remove_tag with HTTP error (lines 452-456)."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Tag not found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=mock_response
        )

        mock_instance = AsyncMock()
        mock_instance.delete.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.remove_tag("abc123", "nonexistent")
        assert "Failed to remove tag: 404 - Tag not found" in str(exc_info.value)

    async def test_remove_tag_generic_exception(self, client, mock_async_client):
        """Test remove_tag with generic exception (lines 457-458)."""
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.delete.side_effect = Exception("IO error")
        mock_async_client.return_value.__aenter__.return_value = mock_instance

        # Execute and verify
        with pytest.raises(DeadMansSnitchError) as exc_info:
            await client.remove_tag("abc123", "tag1")
        assert "Failed to remove tag: IO error" in str(exc_info.value)


class TestServerTypeignores:
    """Test to ensure server type ignores are necessary (they just return values)."""

    async def test_server_functions_return_correctly(self):
        """Verify that the server functions with type ignores work correctly."""
        # Import the server module
        from mcp_deadmansnitch.server import (
            add_tags_impl,
            check_in_impl,
            create_snitch_impl,
            delete_snitch_impl,
            get_snitch_impl,
            list_snitches_impl,
            pause_snitch_impl,
            remove_tag_impl,
            unpause_snitch_impl,
            update_snitch_impl,
        )

        # Mock the get_client function
        with patch("mcp_deadmansnitch.server.get_client") as mock_get_client:
            mock_client = AsyncMock()

            # Test list_snitches_impl
            mock_client.list_snitches.return_value = []
            mock_get_client.return_value = mock_client
            result = await list_snitches_impl()
            assert result["success"] is True
            assert result["count"] == 0

            # Test get_snitch_impl
            mock_client.get_snitch.return_value = {"token": "abc123"}
            result = await get_snitch_impl("abc123")
            assert result["success"] is True
            assert result["snitch"]["token"] == "abc123"

            # Test check_in_impl
            mock_client.check_in.return_value = {"status": "ok"}
            result = await check_in_impl("abc123")
            assert result["success"] is True
            assert result["message"] == "Check-in successful"

            # Test create_snitch_impl
            mock_client.create_snitch.return_value = {"token": "new123"}
            result = await create_snitch_impl("Test", "daily")
            assert result["success"] is True
            assert result["message"] == "Snitch created successfully"

            # Test pause_snitch_impl
            mock_client.pause_snitch.return_value = {"status": "paused"}
            result = await pause_snitch_impl("abc123")
            assert result["success"] is True
            assert result["message"] == "Snitch paused successfully"

            # Test unpause_snitch_impl
            mock_client.unpause_snitch.return_value = {"status": "healthy"}
            result = await unpause_snitch_impl("abc123")
            assert result["success"] is True
            assert result["message"] == "Snitch unpaused successfully"

            # Test update_snitch_impl
            mock_client.update_snitch.return_value = {"token": "abc123"}
            result = await update_snitch_impl("abc123", name="New Name")
            assert result["success"] is True
            assert result["message"] == "Snitch updated successfully"

            # Test delete_snitch_impl
            mock_client.delete_snitch.return_value = {"status": "deleted"}
            result = await delete_snitch_impl("abc123")
            assert result["success"] is True
            assert result["message"] == "Snitch deleted successfully"

            # Test add_tags_impl
            mock_client.add_tags.return_value = {"tags": ["tag1", "tag2"]}
            result = await add_tags_impl("abc123", ["tag1", "tag2"])
            assert result["success"] is True
            assert result["message"] == "Added 2 tags successfully"

            # Test remove_tag_impl
            mock_client.remove_tag.return_value = {"tags": ["tag1"]}
            result = await remove_tag_impl("abc123", "tag2")
            assert result["success"] is True
            assert result["message"] == "Tag 'tag2' removed successfully"

    async def test_main_function(self):
        """Test the main function (lines 437, 441)."""
        from mcp_deadmansnitch.server import main

        with patch("mcp_deadmansnitch.server.mcp") as mock_mcp:
            mock_mcp.run = MagicMock()
            main()
            mock_mcp.run.assert_called_once()
