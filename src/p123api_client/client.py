"""Client module for Portfolio123 API."""

from __future__ import annotations

import os
from typing import TypedDict

import requests


class APICredentials(TypedDict):
    api_id: str
    api_key: str


def get_credentials() -> APICredentials:
    """Get API credentials from environment.

    Returns:
        Dictionary containing api_id and api_key
    """
    api_id = os.environ.get("P123_API_ID")
    api_key = os.environ.get("P123_API_KEY")

    if not api_id or not api_key:
        raise ValueError("Missing required environment variables: P123_API_ID, P123_API_KEY")

    return {"api_id": api_id, "api_key": api_key}


class Client:
    """Client for the Portfolio123 API."""

    def __init__(self, api_key: str, base_url: str) -> None:
        """Initialize the client.

        Args:
            api_key: The API key to use for authentication.
            base_url: The base URL of the API.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    def update_rank_from_single_factor(
        self,
        factor_id: int,
        universe_id: int,
        ascending: bool = True,
    ) -> dict:
        """Update rank from a single factor.

        Args:
            factor_id: The ID of the factor to use.
            universe_id: The ID of the universe to use.
            ascending: Whether to sort in ascending order.

        Returns:
            The response from the API.
        """
        response = self.session.post(
            f"{self.base_url}/rank/update",
            json={
                "factorId": factor_id,
                "universeId": universe_id,
                "ascending": ascending,
            },
        )
        response.raise_for_status()
        return response.json()
