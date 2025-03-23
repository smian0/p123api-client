#!/usr/bin/env python
"""
Example script demonstrating the EnhancedScreenRunAPI with decorator-based caching.

This script shows how to use the EnhancedScreenRunAPI to run screens with automatic caching,
and demonstrates the performance benefits of caching API calls.
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from p123api_client import EnhancedScreenRunAPI
from p123api_client.cache import CacheConfig

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
API_ID = os.environ.get("P123_API_ID")
API_KEY = os.environ.get("P123_API_KEY")

# Set up a custom cache path in the examples directory
CACHE_PATH = Path(__file__).parent / "enhanced_api_cache.db"

def print_separator(title):
    """Print a section separator with title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, " "))
    print("=" * 80 + "\n")

def main():
    """Run the example script."""
    # Create cache config
    cache_config = CacheConfig(
        enabled=True,
        db_path=str(CACHE_PATH),
        max_cache_size_mb=10,  # Small size for example
        enable_statistics=True,
        auto_cleanup=True
    )

    # Initialize the enhanced API with caching
    api = EnhancedScreenRunAPI(
        api_id=API_ID,
        api_key=API_KEY,
        cache_config=cache_config
    )

    # Define screen parameters
    universe = "SP500"
    formula = "PRICE > 200"

    # First call - should hit the API
    print_separator("First API Call (Cache Miss)")
    start_time = time.time()
    result1 = api.run_simple_screen(
        universe=universe,
        formula=formula,
        as_dataframe=True
    )
    first_call_time = time.time() - start_time

    # Print results
    print(f"Found {len(result1)} stocks matching criteria")
    print(f"First call execution time: {first_call_time:.2f} seconds")
    print("\nSample results:")
    print(result1.head())

    # Second call with same parameters - should use cache
    print_separator("Second API Call (Cache Hit)")
    start_time = time.time()
    result2 = api.run_simple_screen(
        universe=universe,
        formula=formula,
        as_dataframe=True
    )
    second_call_time = time.time() - start_time

    # Print results and performance comparison
    print(f"Found {len(result2)} stocks matching criteria")
    print(f"Second call execution time: {second_call_time:.2f} seconds")
    print(f"Speed improvement: {first_call_time / max(second_call_time, 0.001):.1f}x faster")
    
    # Verify results are the same
    columns_match = set(result1.columns) == set(result2.columns)
    shape_match = result1.shape == result2.shape
    print(f"\nResults match: {columns_match and shape_match}")

    # Third call with bypass_cache=True - should hit the API again
    print_separator("Third API Call (Bypass Cache)")
    start_time = time.time()
    result3 = api.run_simple_screen(
        universe=universe,
        formula=formula,
        as_dataframe=True,
        bypass_cache=True
    )
    third_call_time = time.time() - start_time

    # Print results
    print(f"Found {len(result3)} stocks matching criteria")
    print(f"Third call execution time (bypassing cache): {third_call_time:.2f} seconds")
    print("\nSample results:")
    print(result3.head())

    # Print cache file information
    print_separator("Cache Information")
    print(f"Cache file: {CACHE_PATH}")
    print(f"Cache file size: {CACHE_PATH.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
