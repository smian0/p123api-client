"""Base API client module."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Generic, TypeVar, cast

import requests
from p123api import Client
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class APIClient(Generic[ResponseT]):
    """Base API client for P123 API interactions."""

    def __init__(
        self,
        api_id: str | None = None,
        api_key: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize API client with credentials.

        Args:
            api_id: Portfolio123 API ID. If not provided, will read from P123_API_ID env var.
            api_key: Portfolio123 API key. If not provided, will read from P123_API_KEY env var.
            session: Optional requests session for connection reuse.

        Raises:
            ValueError: If credentials are not provided and not found in environment.
        """
        self.api_id = api_id or os.getenv("P123_API_ID")
        self.api_key = api_key or os.getenv("P123_API_KEY")
        self.base_url = "https://api.portfolio123.com/rest"

        # In CI, use dummy values if not provided (tests use VCR cassettes)
        ci_env = os.getenv("CI", "").lower() == "true"
        if (not self.api_id or not self.api_key) and ci_env:
            logger.debug(
                "Running in CI environment with missing credentials, using dummy values for tests"
            )
            self.api_id = self.api_id or "dummy_api_id_for_ci"
            self.api_key = self.api_key or "dummy_api_key_for_ci"
        elif not self.api_id or not self.api_key:
            raise ValueError(
                "API credentials must be provided either through constructor arguments "
                "or environment variables (P123_API_ID, P123_API_KEY)"
            )

        self._client: Client | None = None
        self._session = session
        logger.debug(f"Initialized API client with ID: {self.api_id[:4]}...")

    @property
    def client(self) -> Client:
        """Lazy initialization of P123 API client."""
        if self._client is None:
            self._client = Client(api_id=self.api_id, api_key=self.api_key)
            if self._session:
                self._client.session = self._session
        return self._client

    def make_request(
        self, method: str, params: dict[str, Any], as_dataframe: bool = False
    ) -> ResponseT:
        """Make an API request with rate limiting and error handling.

        Args:
            method: API method name to call
            params: Parameters to pass to the method
            as_dataframe: Whether to return response as DataFrame

        Returns:
            API response object of type ResponseT

        Raises:
            Exception: If the API call fails
        """
        try:
            # Get the method from the client
            api_method = getattr(self.client, method)

            # Log the exact parameters being sent to the API
            import json

            logging.info(f"API request to {method} with params: {json.dumps(params, default=str)}")

            # Remove any 'factors' parameter that might be causing issues
            if method == "screen_backtest" and "factors" in params:
                logging.warning("Removing 'factors' parameter from request")
                del params["factors"]

            # Also check if it's nested in the screen object
            if (
                method == "screen_backtest"
                and "screen" in params
                and isinstance(params["screen"], dict)
                and "factors" in params["screen"]
            ):
                logging.warning("Removing 'factors' parameter from screen object")
                del params["screen"]["factors"]

            # Make the API call
            if method == "rank_update":
                # For rank_update, we need to pass the XML content in the correct format
                response = api_method(
                    {
                        "nodes": params["nodes"],
                        "type": "stock",  # Required parameter according to docs
                    }
                )
            elif method in ["screen", "backtest"]:  # Methods that support as_dataframe
                response = api_method(params, as_dataframe)
            else:
                response = api_method(params)

            # Basic rate limiting
            time.sleep(1)

            return cast(ResponseT, response)

        except Exception as e:
            self.handle_api_error(e, method)
            raise

    def handle_api_error(self, error: Exception, context: str) -> None:
        """Common error handling for API calls."""
        logger.error(f"API error in {context}: {str(error)}", exc_info=True)
        raise error
