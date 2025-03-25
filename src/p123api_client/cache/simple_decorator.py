"""Simple cache decorator for P123 API.

This module provides a simple decorator that can be applied to API instances
to enable caching with minimal code changes.
"""

import base64
import functools
import inspect
import json
import logging
import pickle
from typing import TypeVar

from .config import CacheConfig
from .manager import CacheManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


def enable_cache(api_instance: T, config: CacheConfig | None = None) -> T:
    """Enable caching for an API instance with a single function call.

    This function adds a cache manager to the API instance and decorates
    its methods with the cached_api_call decorator.

    Args:
        api_instance: The API instance to enable caching for
        config: Optional cache configuration (uses default if None)

    Returns:
        The same API instance with caching enabled

    Example:
        ```python
        from p123api_client import ScreenRunAPI
        from p123api_client.cache import enable_cache

        # Create a regular API instance
        api = ScreenRunAPI(api_id="your_id", api_key="your_key")

        # Enable caching with a single line
        api = enable_cache(api)

        # Now all API calls will be cached
        result = api.run_simple_screen("SP500", "PRICE > 200")
        ```
    """
    # Create a cache manager with the provided or default config
    if config is None:
        config = CacheConfig()

    # Add cache manager to the instance
    api_instance.cache_manager = CacheManager(config)

    # List of method names to decorate (can be expanded)
    methods_to_cache = [
        "run_simple_screen",
        "run_screen",
        "get_universe_list",
        "get_universe",
        "get_ranking_system_list",
        "get_ranking_system",
    ]

    # Custom wrapper to avoid parameter conflicts
    def create_wrapper(func, endpoint):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract bypass_cache if present
            bypass_cache = kwargs.pop("bypass_cache", False)

            # Skip cache if requested
            if bypass_cache:
                return func(*args, **kwargs)

            # Get the instance (self) from args
            self = args[0]
            remaining_args = args[1:]

            # Build params dict from args and kwargs
            params = {}

            # Get parameter names from function signature
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())[1:]  # Skip 'self'

            # Add positional args with their parameter names
            for i, arg in enumerate(remaining_args):
                if i < len(param_names):
                    params[param_names[i]] = arg

            # Add keyword args
            params.update(kwargs)

            # Normalize parameters for consistent cache keys
            try:
                serialized = json.dumps(
                    params, default=lambda o: o.__dict__ if hasattr(o, "__dict__") else str(o)
                )
                normalized_params = json.loads(serialized)
            except (TypeError, ValueError) as e:
                logger.warning(f"Could not normalize parameters for caching: {e}")
                normalized_params = params

            # Try to get from cache first
            cached_result = self.cache_manager.get(endpoint, normalized_params)
            if cached_result is not None:
                logger.debug(f"Cache hit for {endpoint}")
                # Handle serialized objects
                if isinstance(cached_result, dict) and cached_result.get("__serialized__") == True:
                    try:
                        serialized_data = cached_result.get("data")
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
            result = func(*args, **kwargs)

            # Store result in cache - handle special types like DataFrames
            try:
                import pandas as pd

                if isinstance(result, pd.DataFrame):
                    # Serialize DataFrame
                    logger.debug("Serializing DataFrame result for caching")
                    serialized_data = pickle.dumps(result)
                    encoded_data = base64.b64encode(serialized_data).decode("ascii")
                    serialized_result = {
                        "__serialized__": True,
                        "type": "pandas.DataFrame",
                        "data": encoded_data,
                    }
                    self.cache_manager.put(endpoint, normalized_params, serialized_result)
                else:
                    self.cache_manager.put(endpoint, normalized_params, result)
            except Exception as e:
                logger.warning(f"Failed to serialize result for caching: {e}")
                # Still store the original result even if serialization fails
                self.cache_manager.put(endpoint, normalized_params, result)

            return result

        return wrapper

    # Decorate each method
    for method_name in methods_to_cache:
        if hasattr(api_instance, method_name):
            original_method = getattr(api_instance, method_name)

            # Skip if already decorated
            if hasattr(original_method, "_is_cached"):
                continue

            # Create endpoint name from method name
            endpoint = f"api/{method_name}"

            # Create and apply the wrapper
            wrapper = create_wrapper(original_method, endpoint)
            wrapper._is_cached = True

            # Replace the original method with the wrapped one
            setattr(api_instance, method_name, wrapper)

            logger.debug(f"Enabled caching for {method_name}")

    return api_instance
