"""Dead Man's Snitch API client."""

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Load .env: try CWD first, then project root (for local development)
load_dotenv()  # CWD
load_dotenv(
    Path(__file__).parent.parent.parent / ".env"
)  # Project root if developing locally


class DeadMansSnitchError(Exception):
    """Base exception for Dead Man's Snitch API errors."""

    pass


class DeadMansSnitchClient:
    """Async client for Dead Man's Snitch API."""

    def __init__(self, api_key: str | None = None):
        """Initialize the client with API key.

        Args:
            api_key: Dead Man's Snitch API key. If not provided, will attempt
                    to load from DEADMANSNITCH_API_KEY environment variable.

        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or os.getenv("DEADMANSNITCH_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set in "
                "DEADMANSNITCH_API_KEY environment variable"
            )

        self.base_url = "https://api.deadmanssnitch.com/v1"
        self.auth = (self.api_key, "")  # HTTP Basic Auth with API key as username
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def list_snitches(
        self, tags: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """List all snitches, optionally filtered by tags.

        Args:
            tags: Optional list of tags to filter snitches.

        Returns:
            List of snitch dictionaries.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches"
        params = {}
        if tags:
            params["tags"] = ",".join(tags)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, auth=self.auth, headers=self.headers, params=params
                )
                response.raise_for_status()
                data: list[dict[str, Any]] = response.json()
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise DeadMansSnitchError(
                        "Authentication failed: Invalid API key. "
                        "Please check your DEADMANSNITCH_API_KEY."
                    ) from e
                raise DeadMansSnitchError(
                    f"Failed to list snitches: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to list snitches: {str(e)}") from e

    async def get_snitch(self, token: str) -> dict[str, Any]:
        """Get details of a specific snitch.

        Args:
            token: The snitch token.

        Returns:
            Snitch details dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches/{token}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, auth=self.auth, headers=self.headers)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise DeadMansSnitchError(
                        "Authentication failed: Invalid API key. "
                        "Please check your DEADMANSNITCH_API_KEY."
                    ) from e
                raise DeadMansSnitchError(
                    f"Failed to get snitch: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to get snitch: {str(e)}") from e

    async def check_in(self, token: str, message: str | None = None) -> dict[str, Any]:
        """Check in (ping) a snitch.

        Args:
            token: The snitch token.
            message: Optional message to include with check-in.

        Returns:
            Check-in response dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        # First get the snitch details to get the check_in_url
        snitch = await self.get_snitch(token)
        check_in_url = snitch.get("check_in_url")

        if not check_in_url:
            raise DeadMansSnitchError("No check_in_url found for snitch")

        async with httpx.AsyncClient() as client:
            try:
                # Check-ins don't require authentication
                if message:
                    # Send as form data or query parameter
                    response = await client.post(
                        check_in_url,
                        data={"m": message},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                else:
                    response = await client.post(check_in_url)

                response.raise_for_status()

                # Check-in responses may be empty or minimal
                return {
                    "status": "ok",
                    "checked_in_at": response.headers.get("Date", ""),
                }
            except httpx.HTTPStatusError as e:
                raise DeadMansSnitchError(
                    f"Failed to check in: {e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to check in: {str(e)}") from e

    async def create_snitch(
        self,
        name: str,
        interval: str,
        notes: str | None = None,
        tags: list[str] | None = None,
        alert_type: str = "basic",
        alert_email: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new snitch.

        Args:
            name: Name of the snitch.
            interval: Check-in interval (e.g., "15_minute", "hourly", "daily",
                    "weekly", "monthly").
            notes: Optional notes about the snitch.
            tags: Optional list of tags.
            alert_type: Alert type ("basic" or "smart").
            alert_email: Optional list of email addresses for alerts.

        Returns:
            Created snitch details dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches"
        data: dict[str, Any] = {
            "name": name,
            "interval": interval,
            "alert_type": alert_type,
        }
        if notes:
            data["notes"] = notes
        if tags:
            data["tags"] = tags
        if alert_email:
            data["alert_email"] = alert_email

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, auth=self.auth, headers=self.headers, json=data
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise DeadMansSnitchError(
                        "Authentication failed: Invalid API key. "
                        "Please check your DEADMANSNITCH_API_KEY."
                    ) from e
                raise DeadMansSnitchError(
                    f"Failed to create snitch: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to create snitch: {str(e)}") from e

    async def pause_snitch(
        self, token: str, until: str | None = None
    ) -> dict[str, Any]:
        """Pause a snitch.

        Args:
            token: The snitch token.
            until: Optional ISO 8601 timestamp to pause until
                  (e.g., "2025-01-25T12:00:00Z").

        Returns:
            Updated snitch details dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches/{token}/pause"
        data: dict[str, Any] = {}
        if until:
            data["until"] = until

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    json=data if data else None,
                )
                response.raise_for_status()

                # Pause endpoint returns 204 No Content
                if response.status_code == 204:
                    # Fetch the updated snitch details
                    return await self.get_snitch(token)

                result: dict[str, Any] = response.json()
                return result
            except httpx.HTTPStatusError as e:
                raise DeadMansSnitchError(
                    f"Failed to pause snitch: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to pause snitch: {str(e)}") from e

    async def unpause_snitch(self, token: str) -> dict[str, Any]:
        """Unpause (resume) a snitch.

        Args:
            token: The snitch token.

        Returns:
            Updated snitch details dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches/{token}/unpause"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, auth=self.auth, headers=self.headers)
                response.raise_for_status()

                # Unpause endpoint returns 204 No Content
                if response.status_code == 204:
                    # Fetch the updated snitch details
                    return await self.get_snitch(token)

                result: dict[str, Any] = response.json()
                return result
            except httpx.HTTPStatusError as e:
                raise DeadMansSnitchError(
                    f"Failed to unpause snitch: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to unpause snitch: {str(e)}") from e

    async def update_snitch(
        self,
        token: str,
        name: str | None = None,
        interval: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
        alert_type: str | None = None,
        alert_email: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update an existing snitch.

        Args:
            token: The snitch token.
            name: New name for the snitch.
            interval: New check-in interval.
            notes: New notes for the snitch.
            tags: New tags for the snitch.
            alert_type: New alert type ("basic" or "smart").
            alert_email: List of email addresses for alerts.

        Returns:
            Updated snitch details dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches/{token}"
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if interval is not None:
            data["interval"] = interval
        if notes is not None:
            data["notes"] = notes
        if tags is not None:
            data["tags"] = tags
        if alert_type is not None:
            data["alert_type"] = alert_type
        if alert_email is not None:
            data["alert_email"] = alert_email

        if not data:
            raise ValueError("At least one field must be provided to update")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    url, auth=self.auth, headers=self.headers, json=data
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
            except httpx.HTTPStatusError as e:
                raise DeadMansSnitchError(
                    f"Failed to update snitch: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to update snitch: {str(e)}") from e

    async def delete_snitch(self, token: str) -> dict[str, Any]:
        """Delete a snitch.

        Args:
            token: The snitch token.

        Returns:
            Confirmation dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches/{token}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    url, auth=self.auth, headers=self.headers
                )
                response.raise_for_status()
                return {"status": "deleted", "token": token}
            except httpx.HTTPStatusError as e:
                raise DeadMansSnitchError(
                    f"Failed to delete snitch: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to delete snitch: {str(e)}") from e

    async def add_tags(self, token: str, tags: list[str]) -> dict[str, Any]:
        """Add tags to a snitch.

        Args:
            token: The snitch token.
            tags: List of tags to add.

        Returns:
            Updated snitch details dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches/{token}/tags"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, auth=self.auth, headers=self.headers, json=tags
                )
                response.raise_for_status()
                # API returns array of tags, need to get full snitch details
                response.json()  # Consume response body

                # Fetch full snitch details with updated tags
                snitch = await self.get_snitch(token)
                return snitch
            except httpx.HTTPStatusError as e:
                raise DeadMansSnitchError(
                    f"Failed to add tags: {e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to add tags: {str(e)}") from e

    async def remove_tag(self, token: str, tag: str) -> dict[str, Any]:
        """Remove a tag from a snitch.

        Args:
            token: The snitch token.
            tag: The tag to remove.

        Returns:
            Updated snitch details dictionary.

        Raises:
            DeadMansSnitchError: If the API request fails.
        """
        url = f"{self.base_url}/snitches/{token}/tags/{tag}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    url, auth=self.auth, headers=self.headers
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
            except httpx.HTTPStatusError as e:
                raise DeadMansSnitchError(
                    f"Failed to remove tag: "
                    f"{e.response.status_code} - {e.response.text}"
                ) from e
            except Exception as e:
                raise DeadMansSnitchError(f"Failed to remove tag: {str(e)}") from e
