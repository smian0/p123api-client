"""Visual verification tests for screen run API caching.

This test file implements scenarios to verify the caching functionality
of the P123 API client and stores the cache database in the same directory
for easy visual inspection.
"""
import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv
from tabulate import tabulate

from p123api_client.cache import CacheConfig
from p123api_client.screen_run import CachedScreenRunAPI


# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Reduce noise from other loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)


# Get the directory of this test file
TEST_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
# Create a cache directory within the test directory
CACHE_DIR = TEST_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
# Set the cache database path
CACHE_DB_PATH = CACHE_DIR / "visual_cache.db"


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"{title.center(80)}")
    print("=" * 80 + "\n")


def print_result_summary(result):
    """Print a summary of the screen run result."""
    if not isinstance(result, pd.DataFrame):
        print("Result is not a DataFrame")
        return
    
    # Extract metadata from DataFrame attributes
    cost = result.attrs.get("cost", "N/A")
    quota_remaining = result.attrs.get("quotaRemaining", "N/A")
    
    # Print summary
    print("Result summary:")
    print(f"  - API quota cost: {cost}")
    print(f"  - Quota remaining: {quota_remaining}")
    print(f"  - Result rows: {len(result)}")
    print(f"  - Result columns: {', '.join(result.columns[:5])}...")
    
    # Print sample data
    print("\nSample data:")
    print(tabulate(result.head(5), headers="keys", tablefmt="grid"))


def view_cache_database(db_path):
    """View the contents of the cache database."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        print(f"Cache database not found at {db_path}")
        return
    
    print("\nCache entries:")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get cache entries
        cursor.execute("""
            SELECT key, endpoint, created_at, expires_at, access_count, size_bytes
            FROM cache_entries
            ORDER BY created_at DESC
        """)
        entries = cursor.fetchall()
        
        if entries:
            df = pd.DataFrame(entries, columns=[
                "key", "endpoint", "created_at", "expires_at", 
                "access_count", "size_bytes"
            ])
            print(tabulate(df, headers="keys", tablefmt="grid", showindex=True))
            
            # Calculate total size
            total_size = sum(entry[5] for entry in entries)
            print(f"\nTotal cache size: {total_size / 1024:.2f} KB")
            print(f"Total entries: {len(entries)}")
        else:
            print("No cache entries found.")
        
        # Get cache statistics
        cursor.execute("SELECT * FROM cache_statistics ORDER BY timestamp DESC LIMIT 1")
        stats = cursor.fetchone()
        
        if stats:
            print("\nCache statistics:")
            columns = [desc[0] for desc in cursor.description]
            for i, col in enumerate(columns):
                print(f"  - {col}: {stats[i]}")
        
        conn.close()
    except sqlite3.Error as e:
        print(f"Error accessing cache database: {e}")


@pytest.fixture
def api():
    """Create a CachedScreenRunAPI instance for testing."""
    # Load .env file if it exists
    env_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded environment variables from {env_path}")
    
    # Get API credentials from environment variables
    api_id = os.environ.get("P123_API_ID")
    api_key = os.environ.get("P123_API_KEY")
    
    if not api_id or not api_key:
        pytest.skip("API credentials not available")
    
    # Ensure the cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create cache configuration
    cache_config = CacheConfig(
        enabled=True,
        db_path=str(CACHE_DB_PATH),
        enable_statistics=True
    )
    
    # Create API client
    api = CachedScreenRunAPI(
        api_id=api_id,
        api_key=api_key,
        cache_config=cache_config
    )
    
    print(f"Testing with cache database: {CACHE_DB_PATH}")
    print(f"Cache enabled: {cache_config.enabled}")
    print(f"Refresh time: {cache_config.refresh_time} {cache_config.timezone}")
    
    return api


def test_basic_caching(api):
    """Test basic caching functionality."""
    print_section("Basic Caching Test")
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
    
    # Check if results are identical
    if isinstance(result1, pd.DataFrame) and isinstance(result2, pd.DataFrame):
        if result1.equals(result2):
            print("\n✅ Results are identical - caching is working correctly!")
        else:
            print("\n❌ Results differ - caching might not be working correctly!")
    
    return result1, result2


def test_bypass_cache(api):
    """Test bypassing the cache."""
    print_section("Bypass Cache Test")
    print("Running a simple screen with cache...")
    
    # First call - should make an API request
    result1 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE > 200",
        as_dataframe=True
    )
    
    print_result_summary(result1)
    
    print("\nRunning the same screen with bypass_cache=True...")
    
    # Second call with bypass_cache - should make a new API request
    result2 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE > 200",
        as_dataframe=True,
        bypass_cache=True
    )
    
    print_result_summary(result2)
    
    # Check API costs
    cost1 = result1.attrs.get("cost", 0)
    cost2 = result2.attrs.get("cost", 0)
    
    if cost2 > 0:
        print("\n✅ Second call made a new API request (bypass_cache works)")
    else:
        print("\n❌ Second call did not make a new API request (bypass_cache failed)")
    
    return result1, result2


def test_cache_invalidation(api):
    """Test cache invalidation."""
    print_section("Cache Invalidation Test")
    print("Running a simple screen to populate cache...")
    
    # First call - should make an API request
    result1 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE < 50",
        as_dataframe=True
    )
    
    print_result_summary(result1)
    
    print("\nInvalidating cache...")
    
    # Invalidate cache
    invalidated = api.cache_manager.invalidate_all()
    print(f"Invalidated {invalidated} cache entries")
    
    print("\nRunning the same screen again (should make a new API request)...")
    
    # Second call after invalidation - should make a new API request
    result2 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE < 50",
        as_dataframe=True
    )
    
    print_result_summary(result2)
    
    # Check API costs
    cost1 = result1.attrs.get("cost", 0)
    cost2 = result2.attrs.get("cost", 0)
    
    if cost2 > 0:
        print("\n✅ Second call made a new API request (invalidation works)")
    else:
        print("\n❌ Second call did not make a new API request (invalidation failed)")
    
    return result1, result2


def test_different_parameters(api):
    """Test caching with different parameters."""
    print_section("Different Parameters Test")
    
    # Run with different formulas
    print("Running screen with formula 'PRICE > 300'...")
    api.run_simple_screen(
        universe="SP500",
        formula="PRICE > 300",
        as_dataframe=True
    )
    
    print("\nRunning screen with formula 'PRICE < 30'...")
    api.run_simple_screen(
        universe="SP500",
        formula="PRICE < 30",
        as_dataframe=True
    )
    
    # Run with different universes
    try:
        print("\nRunning screen with universe 'RUSSELL1000'...")
        api.run_simple_screen(
            universe="RUSSELL1000",
            formula="PRICE > 100",
            as_dataframe=True
        )
    except Exception as e:
        print(f"Error with RUSSELL1000 universe: {e}")
        # Try with a different universe
        try:
            print("\nFalling back to universe 'RUSSELL2000'...")
            api.run_simple_screen(
                universe="RUSSELL2000",
                formula="PRICE > 100",
                as_dataframe=True
            )
        except Exception as e:
            print(f"Error with RUSSELL2000 universe: {e}")
    
    # Get cache statistics
    stats = api.cache_manager.get_stats()
    print("\nCache statistics after different parameter tests:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return stats


def run_all_tests():
    """Run all cache tests."""
    print_section("P123 API Caching Test")
    
    print("Using credentials from .env file or environment variables...")
    
    # Create API client
    api_instance = api()
    
    # Run tests
    print_section("P123 API Caching Test")
    
    test_basic_caching(api_instance)
    test_bypass_cache(api_instance)
    test_cache_invalidation(api_instance)
    test_different_parameters(api_instance)
    
    # View cache database
    print_section("Cache Database Contents")
    view_cache_database(CACHE_DB_PATH)
    
    print_section("Test Complete")
    print("Tests completed - check results above for any errors")


if __name__ == "__main__":
    run_all_tests()
