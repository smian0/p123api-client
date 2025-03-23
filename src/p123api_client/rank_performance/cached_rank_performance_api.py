"""Cached API client for P123 rank performance endpoint with caching support."""
from __future__ import annotations

import logging
from typing import Any, List

import pandas as pd

from ..cache import CacheManager, CacheConfig, cached_api_call
from .rank_performance_api import RankPerformanceAPI
from .schemas import RankPerformanceAPIRequest, RankPerformanceResponse

logger = logging.getLogger(__name__)


class CachedRankPerformanceAPI(RankPerformanceAPI):
    """Cached Rank Performance API client with built-in caching support.
    
    This class automatically enables caching for all API calls with sensible defaults.
    No additional configuration is needed - just use this class instead of RankPerformanceAPI.
    
    Example:
        ```python
        from p123api_client import CachedRankPerformanceAPI
        
        # Create API with caching enabled (credentials from environment variables)
        api = CachedRankPerformanceAPI()
        
        # All API calls are automatically cached
        results = api.run_rank_performance(requests)
        ```
    """
    
    def __init__(
        self,
        api_id: str | None = None,
        api_key: str | None = None,
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Initialize with caching support.
        
        Args:
            api_id: Portfolio123 API ID (from P123_API_ID env var if None)
            api_key: Portfolio123 API key (from P123_API_KEY env var if None)
            config: Configuration dictionary for rank performance API
            **kwargs: Additional keyword arguments for APIClient
        """
        super().__init__(api_id=api_id, api_key=api_key, config=config, **kwargs)
        # Use default cache configuration for simplicity
        self.cache_manager = CacheManager(CacheConfig())
    
    @cached_api_call("rank/performance")
    def run_rank_performance(
        self,
        requests: List[RankPerformanceAPIRequest],
        bypass_cache: bool = False,
    ) -> pd.DataFrame:
        """Run rank performance analysis for multiple requests with caching.

        Args:
            requests: List of RankPerformanceAPIRequest objects containing
                ranking system definitions and performance parameters.
            bypass_cache: If True, bypass the cache and force a fresh API call.

        Returns:
            DataFrame containing rank performance results.
        """
        # The cached_api_call decorator will handle caching
        return super().run_rank_performance(requests)
