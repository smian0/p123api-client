"""Rank performance API module."""
import logging
from typing import Any

from p123api_client.common.api_client import APIClient

from .schemas import RankPerformanceAPIRequest, RankPerformanceResponse

logger = logging.getLogger(__name__)


class RankPerformanceAPI(APIClient):
    """API client for rank performance endpoints."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize RankPerformanceAPI client.

        Args:
            config: Configuration dictionary for rank performance API.
            **kwargs: Additional keyword arguments for APIClient.
        """
        super().__init__(**kwargs)
        self.config = config or {}

    def run_rank_performance(
        self,
        requests: list[RankPerformanceAPIRequest],
    ) -> list[RankPerformanceResponse]:
        """Run rank performance analysis for multiple requests.

        Args:
            requests: List of RankPerformanceAPIRequest objects containing
                ranking system definitions and performance parameters.

        Returns:
            List of RankPerformanceResponse objects.
        """
        all_results = []

        for request in requests:
            try:
                # Convert request to API parameters
                params = request.to_api_params()

                # Make API request
                response = self.make_request(
                    "rank_performance",
                    params,
                    as_dataframe=True,
                )

                # Convert response to RankPerformanceResponse
                result = RankPerformanceResponse(
                    request=request,
                    response=response,
                )

                all_results.append(result)
                logger.info(
                    "Successfully ran performance analysis for period: "
                    f"{request.start_dt} to {request.end_dt}"
                )

            except Exception as e:
                logger.error(
                    "Failed to run performance analysis for period: "
                    f"{request.start_dt} to {request.end_dt}"
                )
                logger.error(f"Error: {e}")
                raise

        return all_results
