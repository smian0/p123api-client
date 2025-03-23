#!/usr/bin/env python
"""
Example demonstrating the simplified caching approach with enable_cache.

This example shows how to:
1. Enable caching on an existing API instance with a single line
2. Compare performance between cached and non-cached API calls
3. Demonstrate how to bypass the cache when needed
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from p123api_client import ScreenRunAPI, CachedScreenRunAPI
from p123api_client.cache import CacheConfig

# Load environment variables from .env file
load_dotenv()

# API credentials will be automatically read from environment variables
# P123_API_ID and P123_API_KEY

# Set up a custom cache path in the examples directory
CACHE_PATH = Path(__file__).parent / "easy_cache_example.db"

def print_separator(title):
    """Print a section separator with title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, " "))
    print("=" * 80 + "\n")

def main():
    """Run the example script."""
    print_separator("Easy Caching Example")
    print("This example demonstrates how to enable caching with a single line of code.")
    
    # Create a regular API instance (no caching)
    regular_api = ScreenRunAPI()
    
    # Define screen parameters
    universe = "SP500"
    formula = "PRICE > 200"
    
    # First call with regular API (no caching)
    print_separator("Regular API Call (No Caching)")
    start_time = time.time()
    result1 = regular_api.run_simple_screen(
        universe=universe,
        formula=formula,
        as_dataframe=True
    )
    regular_call_time = time.time() - start_time
    
    # Print results
    print(f"Found {len(result1)} stocks matching criteria")
    print(f"Regular API call execution time: {regular_call_time:.2f} seconds")
    print("\nSample results:")
    print(result1.head())
    
    # Now create a cached API with caching
    print_separator("Creating Cached API with Caching")
    print("Now creating a CachedScreenRunAPI with built-in caching:")
    print("api = CachedScreenRunAPI()  # That's it! No configuration needed")
    
    # Create a cached API with caching - using default configuration
    cached_api = CachedScreenRunAPI()
    
    # First call with cached API (should hit the API)
    print_separator("First Cached API Call (Cache Miss)")
    start_time = time.time()
    result2 = cached_api.run_simple_screen(
        universe=universe,
        formula=formula,
        as_dataframe=True
    )
    first_cached_call_time = time.time() - start_time
    
    # Print results
    print(f"Found {len(result2)} stocks matching criteria")
    print(f"First cached call execution time: {first_cached_call_time:.2f} seconds")
    
    # Second call with cached API (should use cache)
    print_separator("Second Cached API Call (Cache Hit)")
    start_time = time.time()
    result3 = cached_api.run_simple_screen(
        universe=universe,
        formula=formula,
        as_dataframe=True
    )
    second_cached_call_time = time.time() - start_time
    
    # Print results and performance comparison
    print(f"Found {len(result3)} stocks matching criteria")
    print(f"Second cached call execution time: {second_cached_call_time:.2f} seconds")
    print(f"Speed improvement: {first_cached_call_time / max(second_cached_call_time, 0.001):.1f}x faster")
    
    # Verify results are the same
    columns_match = set(result2.columns) == set(result3.columns)
    shape_match = result2.shape == result3.shape
    print(f"\nResults match: {columns_match and shape_match}")
    
    # Bypass cache
    print_separator("Bypassing Cache")
    start_time = time.time()
    result4 = cached_api.run_simple_screen(
        universe=universe,
        formula=formula,
        as_dataframe=True,
        bypass_cache=True  # Force a fresh API call
    )
    bypass_call_time = time.time() - start_time
    
    # Print results
    print(f"Found {len(result4)} stocks matching criteria")
    print(f"Bypass cache call execution time: {bypass_call_time:.2f} seconds")
    
    # Print cache file information
    print_separator("Cache Information")
    print(f"Cache file: {CACHE_PATH}")
    print(f"Cache file size: {CACHE_PATH.stat().st_size / 1024:.1f} KB")
    
    print_separator("Summary")
    print("The CachedScreenRunAPI provides a simple way to use caching with the P123 API.")
    print("Just use CachedScreenRunAPI instead of ScreenRunAPI for automatic caching!")
    print("No configuration needed - it just works with sensible defaults.")

if __name__ == "__main__":
    main()
