"""Test edge cases and specific behaviors identified during testing."""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_deadmansnitch.server import (
    create_snitch_impl,
    pause_snitch_impl,
    remove_tag_impl,
)


class TestEdgeCases:
    """Test edge cases and specific behaviors."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        with patch("mcp_deadmansnitch.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            yield mock_client

    async def test_create_snitch_with_array_parameters(self, mock_client):
        """Test that create_snitch properly handles array parameters."""
        # Setup
        mock_snitch = {
            "token": "test123",
            "name": "Test Snitch",
            "tags": ["tag1", "tag2"],
            "alert_email": ["email1@example.com", "email2@example.com"],
        }
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        # Execute - test with array parameters
        result = await create_snitch_impl(
            name="Test Snitch",
            interval="hourly",
            tags=["tag1", "tag2"],
            alert_email=["email1@example.com", "email2@example.com"],
        )

        # Verify
        assert result["success"] is True
        assert result["snitch"]["tags"] == ["tag1", "tag2"]
        assert result["snitch"]["alert_email"] == [
            "email1@example.com",
            "email2@example.com",
        ]

        # Verify the client was called with the correct array parameters
        mock_client.create_snitch.assert_called_once_with(
            name="Test Snitch",
            interval="hourly",
            notes=None,
            tags=["tag1", "tag2"],
            alert_type="basic",
            alert_email=["email1@example.com", "email2@example.com"],
        )

    async def test_pause_snitch_with_iso_timestamp(self, mock_client):
        """Test pause_snitch with ISO 8601 timestamp format."""
        # Setup
        mock_snitch = {
            "token": "abc123",
            "status": "paused",
            "paused_until": "2025-01-25T12:00:00Z",
        }
        mock_client.pause_snitch = AsyncMock(return_value=mock_snitch)

        # Execute with ISO timestamp
        result = await pause_snitch_impl(token="abc123", until="2025-01-25T12:00:00Z")

        # Verify
        assert result["success"] is True
        assert result["snitch"]["paused_until"] == "2025-01-25T12:00:00Z"
        mock_client.pause_snitch.assert_called_once_with(
            "abc123", "2025-01-25T12:00:00Z"
        )

    async def test_pause_snitch_with_invalid_duration_format(self, mock_client):
        """Test that pause_snitch handles invalid duration formats gracefully."""
        # The API will reject non-ISO formats like "1h"
        # This test documents the expected behavior
        from mcp_deadmansnitch.client import DeadMansSnitchError

        mock_client.pause_snitch = AsyncMock(
            side_effect=DeadMansSnitchError(
                "Failed to pause snitch: 400 - Invalid 'until' format"
            )
        )

        # Execute with relative duration (which the API doesn't support)
        result = await pause_snitch_impl(token="abc123", until="1h")

        # Verify error handling
        assert result["success"] is False
        assert "Invalid 'until' format" in result["error"]

    async def test_remove_tag_non_existent(self, mock_client):
        """Test remove_tag behavior when tag doesn't exist."""
        # The Dead Man's Snitch API returns success even for non-existent tags
        # This test documents this behavior
        mock_snitch = {"token": "abc123", "tags": ["existing-tag"]}
        mock_client.remove_tag = AsyncMock(return_value=mock_snitch)

        # Execute - try to remove a tag that doesn't exist
        result = await remove_tag_impl(token="abc123", tag="non-existent-tag")

        # Verify - the operation succeeds (this is API behavior)
        assert result["success"] is True
        assert result["message"] == "Tag 'non-existent-tag' removed successfully"
        mock_client.remove_tag.assert_called_once_with("abc123", "non-existent-tag")

    async def test_create_snitch_empty_arrays(self, mock_client):
        """Test create_snitch with empty arrays."""
        # Setup
        mock_snitch = {"token": "test123", "name": "Test Snitch", "tags": []}
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        # Execute with empty arrays
        result = await create_snitch_impl(
            name="Test Snitch", interval="daily", tags=[], alert_email=[]
        )

        # Verify
        assert result["success"] is True
        mock_client.create_snitch.assert_called_once_with(
            name="Test Snitch",
            interval="daily",
            notes=None,
            tags=[],
            alert_type="basic",
            alert_email=[],
        )

    async def test_create_snitch_none_vs_empty_arrays(self, mock_client):
        """Test the difference between None and empty arrays in create_snitch."""
        mock_snitch = {"token": "test123", "name": "Test Snitch"}
        mock_client.create_snitch = AsyncMock(return_value=mock_snitch)

        # Test 1: with None (default)
        await create_snitch_impl(name="Test Snitch", interval="weekly")
        mock_client.create_snitch.assert_called_with(
            name="Test Snitch",
            interval="weekly",
            notes=None,
            tags=None,  # None means "don't set tags"
            alert_type="basic",
            alert_email=None,  # None means "don't set alert_email"
        )

        # Test 2: with empty arrays
        await create_snitch_impl(
            name="Test Snitch", interval="weekly", tags=[], alert_email=[]
        )
        mock_client.create_snitch.assert_called_with(
            name="Test Snitch",
            interval="weekly",
            notes=None,
            tags=[],  # Empty array means "set tags to empty"
            alert_type="basic",
            alert_email=[],  # Empty array means "set alert_email to empty"
        )
