# Epic-7-caching: Implement P123 API Result Caching System
# Story-2: Integrate Caching with Screen Run API

## Story

**As a** quantitative researcher
**I want** screen run API calls to use the caching system
**so that** I can perform repeated screening operations without consuming my API quota

## Status

Draft

## Context

Part of Epic-7-caching which implements a caching system for P123 API responses. This story focuses on integrating the comprehensive caching solution from Story-Combined with the existing Screen Run API functionality.

The Screen Run API is one of the most frequently used P123 endpoints and often involves repeated calls with identical parameters during model development and testing. Since P123 data only updates once daily, caching these responses will significantly reduce API quota usage and improve application performance without sacrificing data freshness.

This implementation will apply the SQLite-based caching system to the ScreenRunAPI client, ensuring proper cache key generation, storage, retrieval, and invalidation for all screening operations.

## Estimation

**Story Points**: 3

**Implementation Time Estimates**:
- **Human Development**: 3 days
- **AI-Assisted Development**: 0.05 days (~30 minutes)

## Tasks

1. - [ ] Write Screen Run Caching Tests
   1. - [ ] Write tests for screen run parameter normalization
   2. - [ ] Write tests for screen run cache key generation
   3. - [ ] Write tests for screen run cache hits/misses
   4. - [ ] Write tests for historical date parameter handling
   5. - [ ] Write tests for different screen types (standard/custom)
   6. - [ ] Write tests for DataFrame conversion with cached results

2. - [ ] Implement Cache Integration
   1. - [ ] Create cached version of ScreenRunAPI class
   2. - [ ] Implement parameter normalization for screen run requests
   3. - [ ] Apply cache lookup before API calls
   4. - [ ] Add cache storage after successful API calls
   5. - [ ] Implement cache bypass option for force refresh

3. - [ ] Handle Special Cases
   1. - [ ] Implement historical date parameter normalization
   2. - [ ] Create screen definition hash function
   3. - [ ] Handle screen filter variations
   4. - [ ] Manage cached DataFrame conversion

4. - [ ] Add Performance Monitoring
   1. - [ ] Implement cache hit/miss tracking
   2. - [ ] Add quota usage metrics
   3. - [ ] Create response time comparison (cached vs. direct)
   4. - [ ] Implement detailed logging for cache operations

5. - [ ] Create Documentation and Examples
   1. - [ ] Update ScreenRunAPI documentation with caching details
   2. - [ ] Create usage examples for cached screen runs
   3. - [ ] Document performance expectations and benefits
   4. - [ ] Add troubleshooting guide for cache-related issues

## Implementation Details

### CachedScreenRunAPI Class

```python
from p123api_client.clients.screen_run_api import ScreenRunAPI
from p123api_client.cache.cache_manager import CacheManager, CacheConfig
from p123api_client.clients.base import generate_cache_key
from datetime import datetime
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Union

class CachedScreenRunAPI(ScreenRunAPI):
    """ScreenRunAPI client with caching capabilities."""
    
    def __init__(self, client, cache_config: Optional[CacheConfig] = None):
        """Initialize with caching support."""
        super().__init__(client)
        self.cache_manager = CacheManager(cache_config)
        self.logger = logging.getLogger(__name__)
    
    def run_screen(self, screen_id: int, universe_id: Optional[int] = None, 
                   as_of_date: Optional[Union[str, datetime]] = None, 
                   bypass_cache: bool = False, **kwargs) -> Dict[str, Any]:
        """Run a screen with caching support."""
        if bypass_cache or not self.cache_manager.config.enabled:
            return super().run_screen(screen_id, universe_id, as_of_date, **kwargs)
        
        # Generate cache key
        params = self._normalize_screen_params(screen_id, universe_id, as_of_date, kwargs)
        cache_key = generate_cache_key("screen_run", params)
        
        # Try to get from cache
        cached_response = self.cache_manager.get(cache_key)
        if cached_response is not None:
            self.logger.debug(f"Cache hit for screen_run: {screen_id}")
            return cached_response
        
        # Make actual API request
        response = super().run_screen(screen_id, universe_id, as_of_date, **kwargs)
        
        # Store in cache
        self.cache_manager.put(cache_key, response, "screen_run")
        
        return response
    
    def run_screen_custom(self, screen_definition: Dict[str, Any], universe_id: Optional[int] = None,
                         as_of_date: Optional[Union[str, datetime]] = None,
                         bypass_cache: bool = False, **kwargs) -> Dict[str, Any]:
        """Run a custom screen definition with caching support."""
        if bypass_cache or not self.cache_manager.config.enabled:
            return super().run_screen_custom(screen_definition, universe_id, as_of_date, **kwargs)
        
        # Generate cache key
        params = self._normalize_custom_screen_params(screen_definition, universe_id, as_of_date, kwargs)
        cache_key = generate_cache_key("screen_run_custom", params)
        
        # Try to get from cache
        cached_response = self.cache_manager.get(cache_key)
        if cached_response is not None:
            self.logger.debug(f"Cache hit for screen_run_custom")
            return cached_response
        
        # Make actual API request
        response = super().run_screen_custom(screen_definition, universe_id, as_of_date, **kwargs)
        
        # Store in cache
        self.cache_manager.put(cache_key, response, "screen_run_custom")
        
        return response
    
    def _normalize_screen_params(self, screen_id: int, universe_id: Optional[int],
                               as_of_date: Optional[Union[str, datetime]],
                               kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize screen parameters for consistent cache keys."""
        params = {"screen_id": screen_id}
        
        if universe_id is not None:
            params["universe_id"] = universe_id
            
        if as_of_date is not None:
            if isinstance(as_of_date, datetime):
                params["as_of_date"] = as_of_date.isoformat()
            else:
                params["as_of_date"] = as_of_date
                
        # Add any additional kwargs
        params.update(kwargs)
        
        return params
    
    def _normalize_custom_screen_params(self, screen_definition: Dict[str, Any],
                                      universe_id: Optional[int],
                                      as_of_date: Optional[Union[str, datetime]],
                                      kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize custom screen parameters for consistent cache keys."""
        # Sort and serialize screen definition for consistent hashing
        sorted_definition = json.dumps(screen_definition, sort_keys=True)
        definition_hash = hashlib.sha256(sorted_definition.encode()).hexdigest()
        
        params = {"screen_definition_hash": definition_hash}
        
        if universe_id is not None:
            params["universe_id"] = universe_id
            
        if as_of_date is not None:
            if isinstance(as_of_date, datetime):
                params["as_of_date"] = as_of_date.isoformat()
            else:
                params["as_of_date"] = as_of_date
                
        # Add any additional kwargs
        params.update(kwargs)
        
        return params
    
    def clear_screen_cache(self, screen_id: Optional[int] = None):
        """Clear cache for specific screen or all screens."""
        # Implementation would depend on how cache is structured
        # For now, just invalidate the entire cache for simplicity
        self.cache_manager.force_refresh_after_update()
```

### Screen Run Parameter Handling

The key challenge for caching screen run API calls is proper normalization of parameters, especially:

1. **Screen Definitions**:
   - Custom screen definitions need to be serialized consistently
   - Must handle different filter combinations that produce the same logical filter
   - Sort parameters to ensure identical definitions produce the same cache key

2. **Date Parameters**:
   - Handle both string and datetime objects for as_of_date
   - Normalize to ISO format for consistency

3. **Universe IDs**:
   - Handle None values properly
   - Account for default universe behavior

### DataFrame Conversion

When the to_dataframe() method is called on cached results, ensure that:

1. The conversion happens with the cached data
2. DataFrame conversion doesn't bypass the cache
3. Cached results are properly formatted for DataFrame conversion

## Dev Notes

- Ensure all screen run endpoints use the caching system
- Add proper logging for debugging cache issues
- Consider adding cache warming for frequently used screens
- Implement clear error messages for cache-related failures
- Add configuration examples in documentation
- Use test fixtures to verify correct caching behavior
- Consider adding cache statistics specifically for screen run operations
- Test with large screen results to ensure performance remains good

## Change Log

| Date | Change | Description |
|------|--------|-------------|
| 2023-03-22 | Creation | Initial draft of Screen Run API caching integration story | 