"""Tests for authentication error handling."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from mcp_deadmansnitch.client import DeadMansSnitchClient
from mcp_deadmansnitch.server import (
    add_tags_impl,
    check_in_impl,
    create_snitch_impl,
    delete_snitch_impl,
    get_snitch_impl,
    list_snitches_impl,
    pause_snitch_impl,
    remove_tag_impl,
    update_snitch_impl,
)


class TestAuthenticationErrors:
    """Test authentication error handling."""

    @pytest.fixture(autouse=True)
    def clear_env(self):
        """Clear the API key environment variable before each test."""
        # Save the original value
        original_key = os.environ.get("DEADMANSNITCH_API_KEY")

        # Clear the environment variable
        if "DEADMANSNITCH_API_KEY" in os.environ:
            del os.environ["DEADMANSNITCH_API_KEY"]

        # Clear the global client instance
        import mcp_deadmansnitch.server

        mcp_deadmansnitch.server._client = None

        yield

        # Restore the original value
        if original_key is not None:
            os.environ["DEADMANSNITCH_API_KEY"] = original_key
        elif "DEADMANSNITCH_API_KEY" in os.environ:
            del os.environ["DEADMANSNITCH_API_KEY"]

    def test_client_missing_api_key(self):
        """Test that client raises ValueError when API key is missing."""
        with pytest.raises(ValueError) as exc_info:
            DeadMansSnitchClient()

        assert "API key must be provided" in str(exc_info.value)
        assert "DEADMANSNITCH_API_KEY" in str(exc_info.value)

    def test_client_with_api_key_provided(self):
        """Test that client initializes correctly when API key is provided."""
        client = DeadMansSnitchClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.auth == ("test-api-key", "")

    def test_client_with_env_var(self):
        """Test that client initializes correctly from environment variable."""
        os.environ["DEADMANSNITCH_API_KEY"] = "env-api-key"
        client = DeadMansSnitchClient()
        assert client.api_key == "env-api-key"
        assert client.auth == ("env-api-key", "")

    @pytest.mark.asyncio
    async def test_list_snitches_missing_api_key(self):
        """Test list_snitches handles missing API key gracefully."""
        result = await list_snitches_impl()

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]
        assert "DEADMANSNITCH_API_KEY" in result["error"]

    @pytest.mark.asyncio
    async def test_get_snitch_missing_api_key(self):
        """Test get_snitch handles missing API key gracefully."""
        result = await get_snitch_impl(token="test-token")

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_check_in_missing_api_key(self):
        """Test check_in handles missing API key gracefully."""
        result = await check_in_impl(token="test-token")

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_create_snitch_missing_api_key(self):
        """Test create_snitch handles missing API key gracefully."""
        result = await create_snitch_impl(name="Test Snitch", interval="hourly")

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_pause_snitch_missing_api_key(self):
        """Test pause_snitch handles missing API key gracefully."""
        result = await pause_snitch_impl(token="test-token")

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_update_snitch_missing_api_key(self):
        """Test update_snitch handles missing API key gracefully."""
        result = await update_snitch_impl(token="test-token", name="Updated Name")

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_snitch_missing_api_key(self):
        """Test delete_snitch handles missing API key gracefully."""
        result = await delete_snitch_impl(token="test-token")

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_add_tags_missing_api_key(self):
        """Test add_tags handles missing API key gracefully."""
        result = await add_tags_impl(token="test-token", tags=["tag1", "tag2"])

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_remove_tag_missing_api_key(self):
        """Test remove_tag handles missing API key gracefully."""
        result = await remove_tag_impl(token="test-token", tag="tag1")

        assert result["success"] is False
        assert "Dead Man's Snitch API key not configured" in result["error"]


class TestAPIAuthenticationErrors:
    """Test handling of API authentication errors (401, 403)."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client with API key set."""
        os.environ["DEADMANSNITCH_API_KEY"] = "invalid-key"
        # Clear the global client instance
        import mcp_deadmansnitch.server

        mcp_deadmansnitch.server._client = None
        yield
        # Clean up
        del os.environ["DEADMANSNITCH_API_KEY"]
        mcp_deadmansnitch.server._client = None

    @pytest.mark.asyncio
    async def test_list_snitches_401_error(self, mock_client):
        """Test handling of 401 Unauthorized error."""
        from httpx import HTTPStatusError, Request, Response

        # Create a mock httpx client
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Create a real Request and Response object
            request = Request("GET", "https://api.deadmanssnitch.com/v1/snitches")
            response = Response(
                status_code=401,
                headers={},
                content=b"Unauthorized: Invalid API key",
                request=request,
            )

            # Create the HTTPStatusError
            error = HTTPStatusError(
                "401 Unauthorized", request=request, response=response
            )

            # Configure the mock to raise the error
            mock_client_instance.get.side_effect = error

            result = await list_snitches_impl()

            assert result["success"] is False
            assert "Authentication failed" in result["error"]
            assert "Invalid API key" in result["error"]

    @pytest.mark.asyncio
    async def test_get_snitch_403_error(self, mock_client):
        """Test handling of 403 Forbidden error."""
        from httpx import HTTPStatusError, Request, Response

        # Create a mock httpx client
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            # Create a real Request and Response object
            request = Request(
                "GET", "https://api.deadmanssnitch.com/v1/snitches/test-token"
            )
            response = Response(
                status_code=403,
                headers={},
                content=b"Forbidden: Access denied",
                request=request,
            )

            # Create the HTTPStatusError
            error = HTTPStatusError("403 Forbidden", request=request, response=response)

            # Configure the mock to raise the error
            mock_client_instance.get.side_effect = error

            result = await get_snitch_impl(token="test-token")

            assert result["success"] is False
            assert "403" in result["error"] or "Forbidden" in result["error"]


class TestUnexpectedErrors:
    """Test handling of unexpected errors."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client with API key set."""
        os.environ["DEADMANSNITCH_API_KEY"] = "test-key"
        # Clear the global client instance
        import mcp_deadmansnitch.server

        mcp_deadmansnitch.server._client = None
        yield
        # Clean up
        del os.environ["DEADMANSNITCH_API_KEY"]
        mcp_deadmansnitch.server._client = None

    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, mock_client):
        """Test handling of unexpected errors."""
        with patch(
            "mcp_deadmansnitch.client.DeadMansSnitchClient.list_snitches"
        ) as mock_list:
            # Make it raise an unexpected error
            mock_list.side_effect = RuntimeError("Unexpected error occurred")

            result = await list_snitches_impl()

            assert result["success"] is False
            assert "Unexpected error" in result["error"]
            assert "Unexpected error occurred" in result["error"]
