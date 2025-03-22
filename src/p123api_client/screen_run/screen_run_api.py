"""API client for P123 screen run endpoint."""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ..common.api_client import APIClient
from .schemas import ScreenDefinition, ScreenRunRequest, ScreenRunResponse

logger = logging.getLogger(__name__)


class ScreenRunAPI(APIClient[ScreenRunResponse]):
    """API client for screen run endpoint."""

    def make_request(
        self,
        method: str,
        params: dict[str, Any],
        as_dataframe: bool = False
    ) -> ScreenRunResponse | pd.DataFrame:
        """Make HTTP request to API.

        Override parent method to handle ScreenRunResponse conversion.
        """
        raw_response = super().make_request(method, params, as_dataframe)
        
        if isinstance(raw_response, dict):
            response = ScreenRunResponse(**raw_response)
            
            # If dataframe requested, convert to pandas DataFrame
            if as_dataframe:
                df = pd.DataFrame(response.rows, columns=response.columns)
                # Store metadata in DataFrame attributes
                df.attrs["cost"] = response.cost
                df.attrs["quota_remaining"] = response.quotaRemaining
                return df
                
            return response
            
        return raw_response

    def run_screen(
        self,
        universe: str,
        rules: List[str],
        ranking: Optional[Union[str, int, Dict[str, Any]]] = None,
        as_of_date: Optional[date] = None,
        end_date: Optional[date] = None,
        screen_type: str = "stock",
        max_results: Optional[int] = None,
        method: Optional[str] = None,
        vendor: Optional[str] = None,
        pit_method: Optional[str] = None,
        precision: Optional[int] = None,
        as_dataframe: bool = False,
    ) -> ScreenRunResponse | pd.DataFrame:
        """Run a screen with the specified parameters.

        Args:
            universe: Universe name to screen (e.g., "SP500", "Russell3000")
            rules: List of screening rule formulas
            ranking: Optional ranking system (ID, name, or formula configuration)
            as_of_date: Optional specific date to run screen for (default: today)
            end_date: Optional end date for historical screening
            screen_type: Type of screen ("stock" or "etf")
            max_results: Optional maximum number of results to return
            method: Optional screen method ("long", "short", "long/short", "hedged")
            vendor: Optional data vendor specification
            pit_method: Optional point-in-time method ("Prelim" or "Complete")
            precision: Optional result precision
            as_dataframe: Whether to return results as pandas DataFrame (default: False)

        Returns:
            ScreenRunResponse object or pandas DataFrame with results
        """
        # Build screen definition
        screen_def = ScreenDefinition(
            type=screen_type,
            universe=universe,
            rules=rules,
            ranking=ranking,
            maxResults=max_results,
            method=method
        )

        # Create request object
        request = ScreenRunRequest(
            screen=screen_def,
            asOfDt=as_of_date,
            endDt=end_date,
            vendor=vendor,
            pitMethod=pit_method,
            precision=precision
        )

        # Convert to dict for API call, filtering out None values
        params = {k: v for k, v in request.model_dump().items() if v is not None}
        
        # Handle nested objects with None values
        if "screen" in params and isinstance(params["screen"], dict):
            params["screen"] = {k: v for k, v in params["screen"].items() if v is not None}
            
        return self.make_request("screen_run", params, as_dataframe)
    
    def run_simple_screen(
        self, 
        universe: str, 
        formula: str, 
        as_dataframe: bool = True
    ) -> ScreenRunResponse | pd.DataFrame:
        """Run a simple screen with a single formula.
        
        Convenience method for quick, simple screens.
        
        Args:
            universe: Universe to screen (e.g., "SP500")
            formula: Single screen formula
            as_dataframe: Whether to return as DataFrame (default: True)
            
        Returns:
            Screen results as ScreenRunResponse or DataFrame
        """
        return self.run_screen(
            universe=universe,
            rules=[formula],
            as_dataframe=as_dataframe
        ) 