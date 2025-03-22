from __future__ import annotations

import logging
from datetime import date
from typing import Any

from ..common.api_client import APIClient
from .schemas import BacktestRequest, BacktestResponse

logger = logging.getLogger(__name__)


class ScreenBacktestAPI(APIClient[BacktestResponse]):
    """API client for screen backtest endpoints."""

    def make_request(
        self,
        method: str,
        params: dict[str, Any],
        as_dataframe: bool = False
    ) -> BacktestResponse:
        """Make HTTP request to API.

        Override parent method to handle BacktestResponse conversion.
        """
        raw_response = super().make_request(method, params, as_dataframe)
        if isinstance(raw_response, dict):
            return BacktestResponse(**raw_response)
        return raw_response

    def run_backtest(
        self,
        start_date: date,
        end_date: date,
        formula: str,
        **kwargs: Any
    ) -> BacktestResponse:
        """Run a backtest for a screen.

        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            formula: Screen formula to test
            **kwargs: Additional parameters to pass to API

        Returns:
            BacktestResponse object with results
        """
        request = BacktestRequest(
            start_date=start_date,
            end_date=end_date,
            formula=formula
        )

        params = {
            **request.model_dump(),
            **kwargs
        }
        return self.make_request("backtest", params)
