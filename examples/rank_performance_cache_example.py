#!/usr/bin/env python
"""
Example demonstrating caching with the EnhancedRankPerformanceAPI.

This example shows how to:
1. Use the EnhancedRankPerformanceAPI for automatic caching
2. Compare performance between cached and non-cached API calls
3. Demonstrate how to bypass the cache when needed
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from p123api_client import RankPerformanceAPI, CachedRankPerformanceAPI
from p123api_client.rank_performance import RankPerformanceAPIRequest

# Load environment variables from .env file
load_dotenv()

# Set up a custom cache path in the examples directory
CACHE_PATH = Path(__file__).parent / "rank_performance_cache_example.db"
os.environ["P123_CACHE_PATH"] = str(CACHE_PATH)

def print_separator(title):
    """Print a section separator with title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, " "))
    print("=" * 80 + "\n")

def main():
    """Run the example script."""
    print_separator("Rank Performance Caching Example")
    print("This example demonstrates caching with the EnhancedRankPerformanceAPI.")
    
    # Create a regular API instance (no caching)
    regular_api = RankPerformanceAPI()
    
    # Define rank performance request
    request = RankPerformanceAPIRequest(
        ranking_system_id=1,  # Use a simple ranking system ID
        universe="SP500",
        start_date="2023-01-01",
        end_date="2023-12-31",
        rebalance_frequency="monthly"
    )
    
    # First call with regular API (no caching)
    print_separator("Regular API Call (No Caching)")
    start_time = time.time()
    result1 = regular_api.run_rank_performance([request])
    regular_call_time = time.time() - start_time
    
    # Print results
    print(f"Regular API call execution time: {regular_call_time:.2f} seconds")
    print(f"Result contains {len(result1)} response(s)")
    if result1:
        print(f"First response has {len(result1[0].performance_data)} data points")
    
    # Now create a cached API with caching
    print_separator("Creating Cached API with Caching")
    print("Now creating a CachedRankPerformanceAPI with built-in caching:")
    print("api = CachedRankPerformanceAPI()  # That's it! No configuration needed")
    
    # Create a cached API with caching - using default configuration
    cached_api = CachedRankPerformanceAPI()
    
    # First call with cached API (should hit the API)
    print_separator("First Cached API Call (Cache Miss)")
    start_time = time.time()
    result2 = cached_api.run_rank_performance([request])
    first_cached_call_time = time.time() - start_time
    
    # Print results
    print(f"First cached call execution time: {first_cached_call_time:.2f} seconds")
    print(f"Result contains {len(result2)} response(s)")
    if result2:
        print(f"First response has {len(result2[0].performance_data)} data points")
    
    # Second call with cached API (should use cache)
    print_separator("Second Cached API Call (Cache Hit)")
    start_time = time.time()
    result3 = cached_api.run_rank_performance([request])
    second_cached_call_time = time.time() - start_time
    
    # Print results and performance comparison
    print(f"Second cached call execution time: {second_cached_call_time:.2f} seconds")
    print(f"Result contains {len(result3)} response(s)")
    if result3:
        print(f"First response has {len(result3[0].performance_data)} data points")
    
    if first_cached_call_time > 0:
        print(f"Speed improvement: {first_cached_call_time / max(second_cached_call_time, 0.001):.1f}x faster")
    
    # Bypass cache
    print_separator("Bypassing Cache")
    start_time = time.time()
    result4 = cached_api.run_rank_performance([request], bypass_cache=True)
    bypass_call_time = time.time() - start_time
    
    # Print results
    print(f"Bypass cache call execution time: {bypass_call_time:.2f} seconds")
    print(f"Result contains {len(result4)} response(s)")
    
    # Print cache file information
    print_separator("Cache Information")
    print(f"Cache file: {CACHE_PATH}")
    if CACHE_PATH.exists():
        print(f"Cache file size: {CACHE_PATH.stat().st_size / 1024:.1f} KB")
    else:
        print("Cache file does not exist yet")
    
    print_separator("Summary")
    print("The CachedRankPerformanceAPI provides a simple way to use caching with the P123 API.")
    print("Just use CachedRankPerformanceAPI instead of RankPerformanceAPI for automatic caching!")
    print("No configuration needed - it just works with sensible defaults.")

if __name__ == "__main__":
    main()
