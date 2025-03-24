"""Cached API client for P123 screen run endpoint with caching support."""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ..cache import CacheManager, CacheConfig, cached_api_call
from .screen_run_api import ScreenRunAPI
from .schemas import ScreenRunResponse

logger = logging.getLogger(__name__)


def normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize parameters for consistent cache keys.
    
    This function ensures that parameters with the same semantic meaning
    but different representations (e.g., different order, different case)
    will generate the same cache key.
    
    Args:
        params: Dictionary of parameters to normalize
        
    Returns:
        Normalized parameters dictionary
    """
    if not params:
        return {}
        
    # Create a copy to avoid modifying the original
    normalized = {}
    
    # Convert all keys to lowercase
    for key, value in params.items():
        normalized_key = key.lower()
        
        # Handle special cases
        if isinstance(value, list):
            # Sort lists to ensure consistent order
            normalized[normalized_key] = sorted(value) if all(isinstance(x, str) for x in value) else value
        elif isinstance(value, dict):
            # Recursively normalize nested dictionaries
            normalized[normalized_key] = normalize_params(value)
        else:
            normalized[normalized_key] = value
            
    return normalized


class CachedScreenRunAPI(ScreenRunAPI):
    """Cached Screen run API client with built-in caching support.
    
    This class automatically enables caching for all API calls with sensible defaults.
    No additional configuration is needed - just use this class instead of ScreenRunAPI.
    
    Example:
        ```python
        from p123api_client import CachedScreenRunAPI
        
        # Create API with caching enabled (credentials from environment variables)
        api = CachedScreenRunAPI()
        
        # All API calls are automatically cached
        result = api.run_simple_screen("SP500", "PRICE > 200")
        ```
    """
    
    def __init__(
        self,
        api_id: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_config: Optional[CacheConfig] = None
    ):
        """Initialize with caching support.
        
        Args:
            api_id: Portfolio123 API ID (from P123_API_ID env var if None)
            api_key: Portfolio123 API key (from P123_API_KEY env var if None)
            cache_config: Optional cache configuration
        """
        super().__init__(api_id=api_id, api_key=api_key)
        # Initialize the cache manager with provided or default config
        self.cache_manager = CacheManager(cache_config or CacheConfig())
        # Initialize logger
        self.logger = logger
    
    @cached_api_call("screen_run")
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
        bypass_cache: bool = False,
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
            bypass_cache: Whether to bypass the cache and force a fresh API call

        Returns:
            ScreenRunResponse object or pandas DataFrame with results
        """
        # The decorator will handle caching, we just call the parent method
        return super().run_screen(
            universe=universe,
            rules=rules,
            ranking=ranking,
            as_of_date=as_of_date,
            end_date=end_date,
            screen_type=screen_type,
            max_results=max_results,
            method=method,
            vendor=vendor,
            pit_method=pit_method,
            precision=precision,
            as_dataframe=as_dataframe
        )
    
    @cached_api_call("screen_run/simple")
    def run_simple_screen(
        self, 
        universe: str, 
        formula: str, 
        as_dataframe: bool = True,
        bypass_cache: bool = False
    ) -> Union[ScreenRunResponse, pd.DataFrame]:
        """Run a simple screen with a single formula.
        
        Convenience method for quick, simple screens.
        
        Args:
            universe: Universe to screen (e.g., "SP500")
            formula: Single screen formula
            as_dataframe: Whether to return as DataFrame (default: True)
            bypass_cache: Whether to bypass the cache (default: False)
            
        Returns:
            Screen results as ScreenRunResponse or DataFrame
        """
        return self.run_screen(
            universe=universe,
            rules=[formula],
            as_dataframe=as_dataframe,
            bypass_cache=bypass_cache
        )
        
    def run_screen_by_id(
        self,
        screen_id: int,
        as_of_date: Optional[date] = None,
        end_date: Optional[date] = None,
        vendor: Optional[str] = None,
        pit_method: Optional[str] = None,
        precision: Optional[int] = None,
        max_results: Optional[int] = None,
        as_dataframe: bool = True,
        bypass_cache: bool = False,
    ) -> Union[ScreenRunResponse, pd.DataFrame]:
        """Run a screen by its ID with caching support.
        
        Args:
            screen_id: ID of the screen to run
            as_of_date: Optional specific date to run screen for (default: today)
            end_date: Optional end date for historical screening
            vendor: Optional data vendor specification
            pit_method: Optional point-in-time method ("Prelim" or "Complete")
            precision: Optional result precision
            max_results: Optional maximum number of results
            as_dataframe: Whether to return results as pandas DataFrame (default: True)
            bypass_cache: Whether to bypass the cache (default: False)
            
        Returns:
            ScreenRunResponse object or pandas DataFrame with results
        """
        self.logger.debug(f"run_screen_by_id() called - screen_id: {screen_id}")
        self.logger.debug(f"Caching parameters - bypass_cache: {bypass_cache}, as_dataframe: {as_dataframe}")
        
        # Check cache first if not bypassed
        cached_response = None
        if not bypass_cache and self.cache_manager.config.enabled:
            # Build parameters dictionary
            params = {"screen": screen_id}
            
            # Add optional parameters if specified
            if as_of_date:
                params["asOfDt"] = as_of_date
            if end_date:
                params["endDt"] = end_date
            if vendor:
                params["vendor"] = vendor
            if pit_method:
                params["pitMethod"] = pit_method
            if precision:
                params["precision"] = precision
            if max_results is not None:
                params["screen"] = {
                    "id": screen_id,
                    "maxResults": max_results
                }
                
            # Normalize parameters for consistent cache key generation
            cache_params = normalize_params(params)
            self.logger.debug(f"Cache key params: {cache_params}")
            
            # Try to get from cache
            cached_response = self.cache_manager.get("screen_run", cache_params, bypass_cache)
            
            if cached_response is not None:
                self.logger.debug("Cache hit for screen run by ID")
                # Deserialize from cached dictionary to ScreenRunResponse
                if isinstance(cached_response, dict):
                    response = ScreenRunResponse(**cached_response)
                    
                    # Convert to DataFrame if requested
                    if as_dataframe:
                        self.logger.debug("Converting cached response to DataFrame")
                        df = pd.DataFrame(response.rows, columns=response.columns)
                        df.attrs["cost"] = response.cost
                        df.attrs["quota_remaining"] = response.quotaRemaining
                        return df
                    
                    return response
                
                # If already the right format, just return it
                return cached_response
        
        # If we get here, it's a cache miss or bypass - call super implementation
        response = super().run_screen_by_id(
            screen_id=screen_id,
            as_of_date=as_of_date,
            end_date=end_date,
            vendor=vendor,
            pit_method=pit_method,
            precision=precision,
            max_results=max_results,
            as_dataframe=False  # Always get the object first, we'll convert later
        )
        
        # Store in cache if not bypassed
        if not bypass_cache and isinstance(response, ScreenRunResponse):
            # Normalize parameters for consistent cache key generation
            params = {"screen": screen_id}
            
            # Add optional parameters if specified
            if as_of_date:
                params["asOfDt"] = as_of_date
            if end_date:
                params["endDt"] = end_date
            if vendor:
                params["vendor"] = vendor
            if pit_method:
                params["pitMethod"] = pit_method
            if precision:
                params["precision"] = precision
            if max_results is not None:
                params["screen"] = {
                    "id": screen_id,
                    "maxResults": max_results
                }
                
            cache_params = normalize_params(params)
            self.logger.debug("Storing response in cache")
            
            # Convert to dictionary for caching
            cache_data = response.model_dump()
            result = self.cache_manager.put("screen_run", cache_params, cache_data)
            self.logger.debug(f"Cache storage result: {result}")
        
        # Convert to DataFrame if requested
        if as_dataframe and isinstance(response, ScreenRunResponse):
            self.logger.debug("Converting response to DataFrame")
            df = pd.DataFrame(response.rows, columns=response.columns)
            df.attrs["cost"] = response.cost
            df.attrs["quota_remaining"] = response.quotaRemaining
            return df
            
        return response
