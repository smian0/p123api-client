"""Screen backtest application module."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from ..common.settings import Settings
from .models import BacktestRequest
from .screen_backtest_api import ScreenBacktestAPI


class ScreenBacktestApp:
    """Application class for running screen backtests."""

    def __init__(self, api_id: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the screen backtest app.
        
        Args:
            api_id: Optional API ID. If not provided, will use settings.
            api_key: Optional API key. If not provided, will use settings.
        """
        settings = Settings()
        self.api_id = api_id or settings.api_id
        self.api_key = api_key or settings.api_key
        self.api = ScreenBacktestAPI(api_id=self.api_id, api_key=self.api_key)

    def run_backtest(self, request: BacktestRequest) -> Dict[str, Any]:
        """Run a screen backtest.
        
        Args:
            request: The backtest request.
            
        Returns:
            The backtest response.
        """
        # Convert request to API parameters
        params = request.to_api_params()
        
        # Note: Factor handling is now done in the to_api_params method of the BacktestRequest class
        
        # Log the parameters being sent to the API
        import logging
        import json
        logging.basicConfig(level=logging.INFO)
        logging.info(f"Screen backtest parameters: {json.dumps(params, default=str)}")
        
        # Check for any 'factors' parameter that might be causing issues
        if "factors" in params:
            logging.warning(f"Found 'factors' parameter in request: {params['factors']}")
            del params["factors"]
            logging.info("Removed 'factors' parameter from request")
        
        # Also check if it's nested in the screen object
        if "screen" in params and isinstance(params["screen"], dict) and "factors" in params["screen"]:
            logging.warning(f"Found 'factors' parameter in screen object: {params['screen']['factors']}")
            del params["screen"]["factors"]
            logging.info("Removed 'factors' parameter from screen object")
        
        # Make the API request
        response = self.api.make_request("screen_backtest", params, as_dataframe=True)
        return response
