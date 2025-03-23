"""Rank performance API module."""
import logging
from typing import Any

import pandas as pd

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
    ) -> pd.DataFrame:
        """Run rank performance analysis for multiple requests.

        Args:
            requests: List of RankPerformanceAPIRequest objects containing
                ranking system definitions and performance parameters.

        Returns:
            DataFrame containing rank performance results.
        """
        all_results = []

        for request in requests:
            try:
                # Convert request to API parameters
                params = request.to_api_params()

                # Make API request
                response = self.make_request(
                    "rank_perf",
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

        # Convert results to DataFrame
        if not all_results:
            return pd.DataFrame()
        
        # Create a list to store the data for each result
        data_rows = []
        
        for result in all_results:
            # Extract data from the response
            response_data = result.response
            
            # Create a base row with metadata
            row = {
                'benchmark_ann_ret': response_data.get('benchmarkAnnRet', None),
            }
            
            # Add bucket returns
            bucket_returns = response_data.get('bucketAnnRet', [])
            for i, ret in enumerate(bucket_returns, 1):
                row[f'bucket_ann_ret_{i}'] = ret
                
            # Add any additional metadata from the request
            if result.request.ranking_definition:
                row['description'] = result.request.ranking_definition.description
            elif result.request.xml_file_path:
                row['xml_file'] = result.request.xml_file_path
                
            data_rows.append(row)
        
        # Create DataFrame from the collected data
        return pd.DataFrame(data_rows)
