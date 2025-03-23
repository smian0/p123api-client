#!/usr/bin/env python
"""
Test script for the enhanced decorator-based caching API.

This script demonstrates how to use the new EnhancedScreenRunAPI
which uses the decorator-based caching approach.
"""

import logging
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tabulate import tabulate

from p123api_client import EnhancedScreenRunAPI, CacheConfig


def setup_logging():
    """Configure logging for the test script."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Reduce noise from other loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def print_result_summary(result):
    """Print a summary of the screen run result."""
    if isinstance(result, pd.DataFrame):
        cost = result.attrs.get("cost", "N/A")
        quota = result.attrs.get("quota_remaining", "N/A")
        rows = len(result)
        columns = list(result.columns)
    else:
        cost = getattr(result, "cost", "N/A")
        quota = getattr(result, "quotaRemaining", "N/A")
        rows = len(getattr(result, "rows", []))
        columns = getattr(result, "columns", [])
    
    print(f"Result summary:")
    print(f"  - API quota cost: {cost}")
    print(f"  - Quota remaining: {quota}")
    print(f"  - Result rows: {rows}")
    print(f"  - Result columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
    
    if isinstance(result, pd.DataFrame) and not result.empty:
        print("\nSample data:")
        print(tabulate(result.head(5), headers="keys", tablefmt="grid"))


def test_basic_caching():
    """Test the decorator-based caching functionality."""
    print_section("Testing EnhancedScreenRunAPI with Decorator-Based Caching")
    
    # Load environment variables
    env_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded environment variables from {env_path}")
    
    api_id = os.environ.get("P123_API_ID")
    api_key = os.environ.get("P123_API_KEY")
    
    if not api_id or not api_key:
        raise ValueError(
            "API credentials are required. Provide them via P123_API_ID and P123_API_KEY environment variables."
        )
    
    # Create a custom cache configuration with a unique test path to avoid conflicts
    test_cache_path = os.path.expanduser("~/.p123cache/test_decorator_cache.db")
    print(f"Using test cache at: {test_cache_path}")
    
    # Remove existing test cache if it exists
    if os.path.exists(test_cache_path):
        os.remove(test_cache_path)
        print("Removed existing test cache file")
    
    cache_config = CacheConfig(
        db_path=test_cache_path,
        max_cache_size_mb=100
    )
    
    # Initialize the enhanced API with caching
    api = EnhancedScreenRunAPI(
        api_id=api_id,
        api_key=api_key,
        cache_config=cache_config
    )
    
    print("Running a simple screen for the first time...")
    
    # First call - should make an API request
    start_time = time.time()
    result1 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE > 100",
        as_dataframe=True
    )
    first_call_time = time.time() - start_time
    
    print_result_summary(result1)
    print(f"First call execution time: {first_call_time:.2f} seconds")
    
    print("\nRunning the same screen again (should use cache)...")
    
    # Second call - should use cache
    start_time = time.time()
    result2 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE > 100",
        as_dataframe=True
    )
    second_call_time = time.time() - start_time
    
    print_result_summary(result2)
    print(f"Second call execution time: {second_call_time:.2f} seconds")
    print(f"Speed improvement: {first_call_time / max(second_call_time, 0.001):.1f}x faster")
    
    # Test bypassing the cache with a different formula to ensure a fresh API call
    print("\nRunning a different screen with bypass_cache=True (should make a fresh API call)...")
    
    start_time = time.time()
    result3 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE > 200",  # Different formula to ensure it's a new request
        as_dataframe=True,
        bypass_cache=True
    )
    bypass_call_time = time.time() - start_time
    
    print_result_summary(result3)
    print(f"Fresh API call execution time: {bypass_call_time:.2f} seconds")
    
    # Now test the bypass_cache parameter with the original formula
    print("\nRunning the original screen with bypass_cache=True (should skip cache)...")
    
    start_time = time.time()
    result4 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE > 100",
        as_dataframe=True,
        bypass_cache=True
    )
    bypass_cache_time = time.time() - start_time
    
    print_result_summary(result4)
    print(f"Bypass cache execution time: {bypass_cache_time:.2f} seconds")
    
    # Check if results are identical
    if isinstance(result1, pd.DataFrame) and isinstance(result2, pd.DataFrame):
        if result1.equals(result2):
            print("\n✅ Results are identical - caching is working correctly!")
        else:
            print("\n❌ Results differ - caching might not be working correctly!")
    
    return result1, result2, result3


if __name__ == "__main__":
    setup_logging()
    test_basic_caching()
