#!/usr/bin/env python
"""
Manual test script for P123 API caching functionality.

This script demonstrates how to use and test the caching system
implemented for the P123 API client.

Usage:
    python test_cache_manually.py [--api-id API_ID] [--api-key API_KEY]

The API credentials can also be provided via environment variables:
    P123_API_ID and P123_API_KEY
"""

import argparse
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tabulate import tabulate

from p123api_client.cache import CacheConfig, CacheManager
from p123api_client.screen_run import CachedScreenRunAPI


def setup_logging():
    """Configure logging for the test script."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Reduce noise from other loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def parse_args():
    """Parse command line arguments."""
    # Get the project root directory
    project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    default_db_path = project_root / ".cache" / "p123cache.db"
    
    parser = argparse.ArgumentParser(description="Test P123 API caching functionality")
    parser.add_argument("--api-id", help="P123 API ID")
    parser.add_argument("--api-key", help="P123 API Key")
    parser.add_argument("--db-path", default=str(default_db_path),
                        help="Path to cache database")
    return parser.parse_args()


def get_credentials(args):
    """Get API credentials from args, environment variables, or .env file."""
    # Load .env file if it exists
    env_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded environment variables from {env_path}")
    
    api_id = args.api_id or os.environ.get("P123_API_ID")
    api_key = args.api_key or os.environ.get("P123_API_KEY")
    
    if not api_id or not api_key:
        raise ValueError(
            "API credentials are required. Provide them via command line arguments, "
            "set P123_API_ID and P123_API_KEY environment variables, "
            "or add them to a .env file in the project root."
        )
    
    return api_id, api_key


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def print_result_summary(result, is_dataframe=True):
    """Print a summary of the screen run result."""
    if is_dataframe:
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
    
    if is_dataframe and not result.empty:
        print("\nSample data:")
        print(tabulate(result.head(5), headers="keys", tablefmt="grid"))


def view_cache_database(db_path):
    """View the contents of the cache database."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        print(f"Cache database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Get cache entries
        cursor = conn.execute("""
            SELECT key, endpoint, created_at, expires_at, access_count, size_bytes
            FROM cache_entries
            ORDER BY created_at DESC
        """)
        entries = [dict(row) for row in cursor.fetchall()]
        
        if entries:
            print("\nCache entries:")
            entries_df = pd.DataFrame(entries)
            print(tabulate(entries_df, headers="keys", tablefmt="grid"))
            
            # Calculate total size
            total_size = sum(entry["size_bytes"] for entry in entries)
            print(f"\nTotal cache size: {total_size / 1024:.2f} KB")
            print(f"Total entries: {len(entries)}")
        else:
            print("\nNo cache entries found.")
        
        # Get cache statistics if available
        try:
            cursor = conn.execute("""
                SELECT * FROM cache_statistics
                ORDER BY timestamp DESC LIMIT 1
            """)
            stats = cursor.fetchone()
            if stats:
                print("\nCache statistics:")
                stats_dict = dict(stats)
                for key, value in stats_dict.items():
                    print(f"  - {key}: {value}")
        except sqlite3.OperationalError:
            # Statistics table might not exist
            pass
            
    except Exception as e:
        print(f"Error accessing cache database: {e}")
    finally:
        conn.close()


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
        print("\n✅ Second call had an API cost - bypass_cache is working correctly!")
    else:
        print("\n❌ Second call had no API cost - bypass_cache might not be working correctly!")
    
    return result1, result2


def test_cache_invalidation(api):
    """Test cache invalidation."""
    print_section("Cache Invalidation Test")
    print("Running a simple screen with cache...")
    
    # First call - should make an API request
    result1 = api.run_simple_screen(
        universe="SP500",
        formula="PRICE < 50",
        as_dataframe=True
    )
    
    print_result_summary(result1)
    
    print("\nForcing cache invalidation...")
    api.cache_manager.force_refresh_after_update()
    
    print("\nRunning the same screen after invalidation...")
    
    # Call after invalidation - should make a new API request
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
        print("\n✅ Second call had an API cost - cache invalidation is working correctly!")
    else:
        print("\n❌ Second call had no API cost - cache invalidation might not be working correctly!")
    
    return result1, result2


def test_different_parameters(api):
    """Test caching with different parameters."""
    print_section("Different Parameters Test")
    results = []
    
    try:
        # Run screens with different parameters
        print("Running screen with formula 'PRICE > 300'...")
        result1 = api.run_simple_screen(
            universe="SP500",
            formula="PRICE > 300",
            as_dataframe=True
        )
        print_result_summary(result1)
        results.append(result1)
        
        print("\nRunning screen with formula 'PRICE < 30'...")
        result2 = api.run_simple_screen(
            universe="SP500",
            formula="PRICE < 30",
            as_dataframe=True
        )
        print_result_summary(result2)
        results.append(result2)
        
        # Try with a different universe - use SP400 instead of RUSSELL3000
        print("\nRunning screen with different universe 'SP400'...")
        try:
            result3 = api.run_simple_screen(
                universe="SP400",
                formula="PRICE > 100",
                as_dataframe=True
            )
            print_result_summary(result3)
            results.append(result3)
        except Exception as e:
            print(f"Error with SP400 universe: {e}")
            print("Trying with 'SP600' universe instead...")
            try:
                result3 = api.run_simple_screen(
                    universe="SP600",
                    formula="PRICE > 100",
                    as_dataframe=True
                )
                print_result_summary(result3)
                results.append(result3)
            except Exception as e:
                print(f"Error with SP600 universe: {e}")
                print("Skipping different universe test.")
        
        # Get cache statistics
        stats = api.cache_manager.get_stats()
        print("\nCache statistics after different parameter tests:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
    
    except Exception as e:
        print(f"Error in parameter tests: {e}")
    
    return results


def main():
    """Main function to run the tests."""
    setup_logging()
    args = parse_args()
    
    print_section("P123 API Caching Test")
    print("Using credentials from .env file or environment variables...")
    
    try:
        api_id, api_key = get_credentials(args)
        
        # Create cache configuration
        # Ensure the cache directory exists
        cache_dir = Path(args.db_path).parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_config = CacheConfig(
            enabled=True,
            db_path=args.db_path,
            enable_statistics=True
        )
        
        # Create cached API client
        api = CachedScreenRunAPI(
            api_id=api_id,
            api_key=api_key,
            cache_config=cache_config
        )
        
        print_section("P123 API Caching Test")
        print(f"Testing with cache database: {cache_config.db_path_expanded}")
        print(f"Cache enabled: {cache_config.enabled}")
        print(f"Refresh time: {cache_config.refresh_time} {cache_config.timezone}")
        
        # Run tests - continue even if some tests fail
        try:
            test_basic_caching(api)
        except Exception as e:
            print(f"\n❌ Basic caching test failed: {e}")
        
        try:
            test_bypass_cache(api)
        except Exception as e:
            print(f"\n❌ Bypass cache test failed: {e}")
        
        try:
            test_cache_invalidation(api)
        except Exception as e:
            print(f"\n❌ Cache invalidation test failed: {e}")
        
        try:
            test_different_parameters(api)
        except Exception as e:
            print(f"\n❌ Different parameters test failed: {e}")
        
        # View cache database
        print_section("Cache Database Contents")
        view_cache_database(cache_config.db_path_expanded)
        
        print_section("Test Complete")
        print("Tests completed - check results above for any errors")
        
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
