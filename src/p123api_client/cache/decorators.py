"""API caching decorators.

This module provides decorators for adding caching functionality to API methods.
"""
import functools
import inspect
import json
import logging
import pickle
import base64
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from .manager import CacheManager

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def cached_api_call(endpoint: str) -> Callable[[F], F]:
    """Decorator to add caching to API methods.
    
    This decorator can be applied to methods of API classes that have a
    cache_manager attribute. It will check the cache before making the API call
    and store the result in the cache after the call.
    
    Args:
        endpoint: The API endpoint for this method (used as part of the cache key)
        
    Returns:
        Decorated function with caching capabilities
        
    Example:
        ```python
        class MyAPI:
            def __init__(self):
                self.cache_manager = CacheManager()
                
            @cached_api_call("my/endpoint")
            def get_data(self, param1, param2=None, bypass_cache=False):
                # Make API call...
                return result
        ```
    
    Note:
        The decorated method can accept a `bypass_cache` parameter which, when True,
        will bypass the cache and make a fresh API call.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self, *args, bypass_cache: bool = False, **kwargs):
            # Create a copy of kwargs without bypass_cache to pass to the original function
            func_kwargs = {k: v for k, v in kwargs.items() if k != 'bypass_cache'}
            
            # Skip cache if requested or if no cache manager is available
            if bypass_cache or not hasattr(self, 'cache_manager'):
                logger.debug(f"Bypassing cache for {endpoint}")
                return func(self, *args, **func_kwargs)
            
            cache_manager = cast(CacheManager, self.cache_manager)
            
            # Extract parameter names from function signature
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())[1:]  # Skip 'self'
            
            # Build params dict from args and kwargs
            params: Dict[str, Any] = {}
            
            # Add positional args with their parameter names
            for i, arg in enumerate(args):
                if i < len(param_names):
                    # Skip 'bypass_cache' parameter
                    if param_names[i] != 'bypass_cache':
                        params[param_names[i]] = arg
            
            # Add keyword args (excluding bypass_cache)
            for key, value in kwargs.items():
                if key != 'bypass_cache':
                    params[key] = value
            
            # Normalize parameters for consistent cache keys
            try:
                # Convert complex objects to basic types for consistent serialization
                serialized = json.dumps(params, default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o))
                normalized_params = json.loads(serialized)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not normalize parameters for caching: {e}")
                normalized_params = params
            
            # Try to get from cache first
            cached_result = cache_manager.get(endpoint, normalized_params)
            if cached_result is not None:
                logger.debug(f"Cache hit for {endpoint}")
                # If the cached result is a serialized object, deserialize it
                if isinstance(cached_result, dict) and cached_result.get('__serialized__') == True:
                    try:
                        serialized_data = cached_result.get('data')
                        if serialized_data:
                            logger.debug("Deserializing cached result")
                            decoded_data = base64.b64decode(serialized_data)
                            deserialized_result = pickle.loads(decoded_data)
                            return deserialized_result
                    except Exception as e:
                        logger.warning(f"Failed to deserialize cached result: {e}")
                return cached_result
            
            # Call the original function if not in cache
            logger.debug(f"Cache miss for {endpoint}, calling API")
            result = func(self, *args, **func_kwargs)
            
            # Store result in cache - handle special types like DataFrames
            try:
                import pandas as pd
                if isinstance(result, pd.DataFrame):
                    # Serialize DataFrame to avoid string representation issues
                    logger.debug("Serializing DataFrame result for caching")
                    serialized_data = pickle.dumps(result)
                    encoded_data = base64.b64encode(serialized_data).decode('ascii')
                    serialized_result = {
                        '__serialized__': True,
                        'type': 'pandas.DataFrame',
                        'data': encoded_data
                    }
                    cache_manager.put(endpoint, normalized_params, serialized_result)
                else:
                    cache_manager.put(endpoint, normalized_params, result)
            except Exception as e:
                logger.warning(f"Failed to serialize result for caching: {e}")
                # Still store the original result even if serialization fails
                cache_manager.put(endpoint, normalized_params, result)
            
            return result
        
        # Cast to F to satisfy mypy
        return cast(F, wrapper)
    
    return decorator
