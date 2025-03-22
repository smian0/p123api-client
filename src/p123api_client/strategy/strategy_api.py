import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from p123api_client.common.api_client import APIClient

from .schemas import Holding, StrategyRequest, StrategyResponse, Summary

logger = logging.getLogger(__name__)


class StrategyAPIError(Exception):
    """Base exception for strategy API errors"""

    pass


class StrategyAPI(APIClient):
    """API client for retrieving strategy details"""

    def __init__(self, api_id: str, api_key: str):
        """Initialize strategy API client

        Args:
            api_id: Portfolio123 API ID
            api_key: Portfolio123 API key
        """
        super().__init__(api_id=api_id, api_key=api_key)
        logger.info("Initialized StrategyAPI")

    def save_json_response(self, response: dict[str, Any], filename: str) -> None:
        """Save the JSON response to a file."""
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / filename, "w") as f:
            json.dump(response, f, indent=4)

    def get_strategy(self, strategy_id: int) -> StrategyResponse:
        """Get strategy details including summary, holdings and statistics

        Args:
            strategy_id: ID of the strategy/book to retrieve

        Returns:
            StrategyResponse containing strategy details

        Raises:
            StrategyAPIError: If the API call fails
        """
        try:
            # Create request object
            request = StrategyRequest(strategy_id=strategy_id)

            # Make API call
            response = self.client.strategy(strategy_id=request.strategy_id)

            # Save the full JSON response to a file
            self.save_json_response(response, f"strategy_{strategy_id}_response.json")
            logger.debug(f"Raw API response for strategy {strategy_id}:")
            logger.debug(f"Response content: {response}")

            # Check for specific fields in the response
            holdings_df = pd.DataFrame(response.get("holdings", []))
            if not holdings_df.empty:
                logger.debug(f"Holdings summary:\n{holdings_df.describe()}")
                logger.debug(
                    f"Holdings by sector:\n{holdings_df.groupby('sector')['weight'].sum()}"
                )

            # Create StrategyResponse object
            strategy_response = StrategyResponse(
                summary=Summary(**response.get("summary", {})),
                holdings=[Holding(**holding) for holding in response.get("holdings", [])],
                stats=response.get("stats", {}),
                trading=response.get("trading", {}),
                riskMeasurements=response.get("riskMeasurements", {}),
            )

            # Save the full response data as CSV files
            strategy_response.save_full_response_as_csv(Path(__file__).parent / "output")

            return strategy_response

        except Exception as e:
            logger.error(f"Error getting strategy {strategy_id}: {str(e)}")
            raise StrategyAPIError(f"Failed to get strategy: {str(e)}") from e
