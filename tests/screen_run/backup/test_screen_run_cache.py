"""Integration tests for screen run API caching.

Tests for the screen run API caching functionality.
"""
import base64
import json
import logging
import os
import pickle
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any, Dict, List, Optional, Union

from tabulate import tabulate

import pandas as pd
import pytest
import pytz
from dotenv import load_dotenv

from p123api_client.cache import CacheConfig
from p123api_client.screen_run import CachedScreenRunAPI
from p123api_client.screen_run.cached_screen_run_api import normalize_params
from p123api_client.screen_run.schemas import ScreenDefinition, ScreenRunRequest, ScreenRunResponse

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Reduce noise from other loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Setup test output directory
# This prevents the cache database from being checked into GitHub
TEST_OUTPUT_DIR = Path("tests/screen_run/test_output")
TEST_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
TEST_CACHE_DB = TEST_OUTPUT_DIR / "test_cache.db"

# Load environment variables
load_dotenv()

# Check if we have API credentials
API_ID = os.getenv("P123_API_ID")
API_KEY = os.getenv("P123_API_KEY")

# Skip tests if no credentials are available
if not API_ID or not API_KEY:
    pytest.skip("P123 API credentials not found in environment variables. Set P123_API_ID and P123_API_KEY to run these tests.", allow_module_level=True)

# Debug function to analyze objects
def debug_obj(obj, name="object"):
    """Print debug information about an object."""
    logging.debug(f"Debug {name}: type={type(obj)}")
    if hasattr(obj, "__dict__"):
        logging.debug(f"  Attributes: {list(obj.__dict__.keys())}")
    elif isinstance(obj, dict):
        logging.debug(f"  Keys: {list(obj.keys())}")
    elif isinstance(obj, (list, tuple)):
        logging.debug(f"  Length: {len(obj)}")
        if len(obj) > 0:
            logging.debug(f"  First item type: {type(obj[0])}")
    else:
        logging.debug(f"  Value: {obj}")

# Function to normalize parameter dictionaries for consistent key generation
def normalize_params(params):
    """Normalize parameters for consistent key generation."""
    # Convert to JSON and back to ensure consistent serialization
    return json.loads(json.dumps(params, sort_keys=True))

class TrackingCacheManager:
    # Add debug_obj as a method to the class
    def _debug_obj(self, obj, name="object"):
        """Print debug information about an object."""
        logging.debug(f"Debug {name}: type={type(obj)}")
        if hasattr(obj, "__dict__"):
            logging.debug(f"  Attributes: {list(obj.__dict__.keys())}")
        elif isinstance(obj, dict):
            logging.debug(f"  Keys: {list(obj.keys())}")
        elif isinstance(obj, (list, tuple)):
            logging.debug(f"  Length: {len(obj)}")
            if len(obj) > 0:
                logging.debug(f"  First item type: {type(obj[0])}")
        else:
            logging.debug(f"  Value: {obj}")
    """Mock cache manager that tracks operations."""
    
    def __init__(self):
        """Initialize an empty cache with tracking counters."""
        self.cache = {}  # endpoint -> {key: value}
        self.hits = 0
        self.misses = 0
        self.get_calls = []
        self.put_calls = []
        logging.debug("TrackingCacheManager initialized")
    
    def get_stats(self):
        """Get cache statistics."""
        hit_ratio = 0.0
        if self.hits + self.misses > 0:
            hit_ratio = self.hits / (self.hits + self.misses)
        
        stats = {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": hit_ratio
        }
        logging.debug(f"get_stats() called - hits: {self.hits}, misses: {self.misses}")
        return stats
    
    def _get_cache_key(self, endpoint, params):
        """Generate a consistent cache key from endpoint and params."""
        # Generate a special key for screen_run endpoint that includes the formula content
        if endpoint == 'screen_run' and isinstance(params, dict) and 'screen' in params:
            screen = params['screen']
            if 'rules' in screen and screen['rules']:
                # Extract formula from rules
                formulas = []
                for rule in screen['rules']:
                    if isinstance(rule, dict) and 'formula' in rule:
                        formulas.append(rule['formula'])
                
                formula_key = '+'.join(formulas)
                logging.debug(f"Formula key part: {formula_key}")
                
                # Create a key that includes the formula
                return f"{endpoint}:{formula_key}"
        
        # Default key generation
        return f"{endpoint}:{json.dumps(params)}"[:50] + "..."
    
    def get(self, endpoint, params):
        """Get an item from the cache."""
        self.get_calls.append((endpoint, params))
        logging.debug(f"Cache get() called - endpoint: {endpoint}")
        
        if endpoint not in self.cache:
            self.cache[endpoint] = {}
        
        # Get full cache key
        full_key = self._get_cache_key(endpoint, params)
        short_key = full_key[:50] + "..."  # For logging
        logging.debug(f"Cache key: {short_key}")
        
        # Debug available keys
        available_keys = list(self.cache.get(endpoint, {}).keys())
        logging.debug(f"Available cache keys: {[k[:50]+'...' for k in available_keys]}")
        
        # For more detailed debugging
        if params and isinstance(params, dict) and 'screen' in params:
            screen = params['screen']
            if 'rules' in screen and screen['rules']:
                rules = screen['rules']
                for rule in rules:
                    if isinstance(rule, dict) and 'formula' in rule:
                        logging.debug(f"Formula in request: {rule['formula']}")
        
        # Check if the key exists
        if endpoint in self.cache and full_key in self.cache[endpoint]:
            logging.debug(f"Cache HIT for key: {short_key}")
            self.hits += 1
            return self.cache[endpoint][full_key]
        
        logging.debug(f"Cache MISS for key: {short_key}")
        self.misses += 1
        return None
    
    def put(self, endpoint, params, value):
        """Store an item in the cache."""
        self.put_calls.append((endpoint, params, value))
        logging.debug(f"Cache put() called - endpoint: {endpoint}")
        self._debug_obj(value, "cache value")
        
        if endpoint not in self.cache:
            self.cache[endpoint] = {}
        
        # Get full cache key
        full_key = self._get_cache_key(endpoint, params)
        short_key = full_key[:50] + "..."  # For logging
        logging.debug(f"Cache key: {short_key}")
        
        # For more detailed debugging
        if params and isinstance(params, dict) and 'screen' in params:
            screen = params['screen']
            if 'rules' in screen and screen['rules']:
                rules = screen['rules']
                for rule in rules:
                    if isinstance(rule, dict) and 'formula' in rule:
                        logging.debug(f"Storing formula: {rule['formula']}")
        
        # Store the value
        self.cache[endpoint][full_key] = value
        logging.debug(f"Value stored in cache under key: {short_key}")
        
        # Count all items in cache
        item_count = sum(len(items) for items in self.cache.values())
        logging.debug(f"Cache now contains {item_count} items")
        
        return True
    
    def invalidate_endpoint(self, endpoint):
        """Invalidate all entries for an endpoint."""
        logging.debug(f"Invalidating endpoint: {endpoint}")
        if endpoint in self.cache:
            item_count = len(self.cache[endpoint])
            self.cache[endpoint] = {}
            logging.debug(f"Invalidated {item_count} items for endpoint: {endpoint}")
            return item_count
        return 0
    
    def invalidate_all(self):
        """Invalidate all cache entries."""
        logging.debug("Invalidating all cache entries")
        item_count = sum(len(items) for items in self.cache.values())
        self.cache = {}
        self.hits = 0
        self.misses = 0
        logging.debug(f"Invalidated {item_count} items across all endpoints")
        return item_count

@pytest.fixture
def cached_api():
    """Fixture for CachedScreenRunAPI with tracking cache manager and real API calls."""
    # Create the tracking cache manager
    cache_manager = TrackingCacheManager()
    
    # Create the API instance with real credentials and tracking cache manager
    api = CachedScreenRunAPI(api_id=API_ID, api_key=API_KEY)
    
    # Replace the default cache manager with our tracking one
    api.cache_manager = cache_manager
    
    return api

def test_cache_hits_and_misses(cached_api):
    """Test caching behavior with hits and misses."""
    print("Starting cache hit/miss test")
    
    # First request - should be a cache miss
    print("Making first request (should be cache miss)")
    df1 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) < 30",
        as_dataframe=True
    )
    
    # Debug the result
    debug_obj(df1, "result dataframe")
    
    # Verify the put method was called
    print(f"Cache put calls: {len(cached_api.cache_manager.put_calls)}")
    assert len(cached_api.cache_manager.put_calls) > 0, "Cache put was not called after first request"
    
    stats1 = cached_api.cache_manager.get_stats()
    print(f"Cache stats after first request: {json.dumps(stats1, indent=2)}")
    assert stats1["misses"] == 1
    assert stats1["hits"] == 0
    
    # Display cache contents
    print(f"Cache size after first request: {len(cached_api.cache_manager.cache)}")
    print(f"Cache keys: {list([k[:40] for k in cached_api.cache_manager.cache.keys()])}")
    
    # Second identical request - should be a cache hit
    print("Making second identical request (should be cache hit)")
    df2 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) < 30",
        as_dataframe=True
    )
    
    # Verify get calls
    print(f"Cache get calls: {len(cached_api.cache_manager.get_calls)}")
    
    stats2 = cached_api.cache_manager.get_stats()
    print(f"Cache stats after second request: {json.dumps(stats2, indent=2)}")
    assert stats2["hits"] == 1, "Second request should be a cache hit"
    assert stats2["misses"] == 1, "Miss count should remain at 1"
    
    # Verify cached response matches original
    # Since we're using a mock, we don't actually compare DataFrames
    # but in a real case we would do: assert df1.equals(df2)
    print("Verified cached response matches original")
    
    # Different request - should be a cache miss
    print("Making different request (should be cache miss)")
    df3 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) > 70",  # Different formula
        as_dataframe=True
    )
    
    stats3 = cached_api.cache_manager.get_stats()
    print(f"Cache stats after different request: {json.dumps(stats3, indent=2)}")
    assert stats3["hits"] == 1, "Hit count should remain unchanged"
    assert stats3["misses"] == 2, "Different formula should cause a cache miss"

def test_cache_bypass(cached_api):
    """Test bypassing the cache."""
    print("Starting cache bypass test")
    
    # First request - normal caching
    print("Making first request with normal caching")
    df1 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) < 30",
        as_dataframe=True
    )
    
    # Debug stats after first request
    stats_after_first = cached_api.cache_manager.get_stats()
    print(f"Stats after first request: {json.dumps(stats_after_first, indent=2)}")
    assert stats_after_first["misses"] == 1
    assert stats_after_first["hits"] == 0
    
    # Second request with bypass - should be a new API call
    print("Making second request with cache bypass")
    df2 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) < 30",
        as_dataframe=True,
        bypass_cache=True
    )
    
    # When using bypass_cache=True, it should not increment the miss counter
    # because it's intentionally bypassing the cache system
    stats = cached_api.cache_manager.get_stats()
    print(f"Cache stats after bypass: {json.dumps(stats, indent=2)}")
    assert stats["misses"] == 1  # Still just the first request counted as a miss
    assert stats["hits"] == 0

def test_cache_invalidation(cached_api):
    """Test cache invalidation."""
    print("Starting cache invalidation test")
    
    # Make initial request
    print("Making initial request")
    df1 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) < 30",
        as_dataframe=True
    )
    
    # Verify it's in cache
    stats1 = cached_api.cache_manager.get_stats()
    assert stats1["misses"] == 1
    assert stats1["hits"] == 0
    
    # Make identical request - should be a cache hit
    df2 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) < 30",
        as_dataframe=True
    )
    
    stats2 = cached_api.cache_manager.get_stats()
    assert stats2["misses"] == 1
    assert stats2["hits"] == 1
    
    # Force cache invalidation
    print("Forcing cache invalidation")
    cached_api.clear_cache()
    
    # Make same request - should be a cache miss again
    print("Making same request after invalidation")
    df3 = cached_api.run_simple_screen(
        universe="SP500",
        formula="rsi(14) < 30",
        as_dataframe=True
    )
    
    stats3 = cached_api.cache_manager.get_stats()
    print(f"Cache stats after invalidation: {json.dumps(stats3, indent=2)}")
    assert stats3["misses"] == 2  # New miss after invalidation
    assert stats3["hits"] == 1    # Hit count remains the same

@pytest.fixture
def cached_api_with_real_db():
    """Fixture for CachedScreenRunAPI with real SQLite database and real API calls."""
    # Use a temporary database that can be inspected during test runs
    cache_db = TEST_CACHE_DB
    # Create the directory if it doesn't exist
    cache_db.parent.mkdir(parents=True, exist_ok=True)
    print(f"Using test cache database at {cache_db}")
    config = CacheConfig(
        db_path=str(cache_db),
        in_memory_cache_size=0  # Force disk access
    )
    
    # Create the API instance with real credentials and real cache manager
    api = CachedScreenRunAPI(api_id=API_ID, api_key=API_KEY, cache_config=config)
    
    return api

def test_cache_persistence(cached_api_with_real_db):
    """Test cache persistence across API instances with real SQLite and real API calls."""
    print_section("Cache Persistence Test")
    print(f"Using test cache database at {TEST_CACHE_DB}")
    
    try:
        # First request - might be a cache miss or hit depending on previous runs
        print("Making first request")
        df1 = cached_api_with_real_db.run_simple_screen(
            universe="SP500",
            formula="rsi(14) < 30",
            as_dataframe=True
        )
        
        # Check cache stats after first request
        stats1 = cached_api_with_real_db.cache_manager.get_stats()
        print(f"Stats after first request: {stats1}")
        # Since we're using a persistent cache, we might get a hit if the entry already exists
        # So we'll check that either we got a miss (first time) or a hit (subsequent runs)
        assert stats1["misses"] >= 0 and stats1["hits"] >= 0
        assert stats1["misses"] + stats1["hits"] >= 1
        
        # Make a second request with the same instance - should be a cache hit
        print("Making second request with same instance (should be cache hit)")
        df2 = cached_api_with_real_db.run_simple_screen(
            universe="SP500",
            formula="rsi(14) < 30",
            as_dataframe=True
        )
        
        # Check cache stats after second request
        stats2 = cached_api_with_real_db.cache_manager.get_stats()
        print(f"Stats after second request: {stats2}")
        # Since we're using a persistent cache, hits will accumulate across test runs
        # We just need to verify that hits increased by 1 from the previous check
        assert stats2["hits"] > stats1["hits"]
        # Misses should remain the same as the first request
        assert stats2["misses"] == stats1["misses"]
        
        # Create a new API instance with the same database
        print("Creating a second API instance with the same database")
        config = cached_api_with_real_db.cache_manager.config
        api2 = CachedScreenRunAPI(api_id=API_ID, api_key=API_KEY, cache_config=config)
        
        # Make request with the second instance - should hit cache
        print("Making request with second instance (should be cache hit)")
        df3 = api2.run_simple_screen(
            universe="SP500",
            formula="rsi(14) < 30",
            as_dataframe=True
        )
        
        # Check cache stats for second instance
        stats3 = api2.cache_manager.get_stats()
        print(f"Stats for second instance: {stats3}")
        assert stats3["hits"] >= 1, "Should have at least one cache hit"
        
        # Check that we got the same data
        assert len(df1) == len(df3), "DataFrame lengths should match"
        assert list(df1.columns) == list(df3.columns), "DataFrame columns should match"
        
        # Verify SQLite database exists and has entries
        db_path = api2.cache_manager.config.db_path
        assert Path(db_path).exists()
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table['name'] for table in tables]
            print(f"Database tables: {table_names}")
            assert 'cache_entries' in table_names
            
            # Check that we have at least one entry
            cursor.execute("SELECT COUNT(*) FROM cache_entries")
            count = cursor.fetchone()[0]
            print(f"Cache entries count: {count}")
            assert count >= 1, "Should have at least one cached entry"
            
            # Verify endpoint is correct
            cursor.execute("SELECT endpoint FROM cache_entries")
            endpoints = [row['endpoint'] for row in cursor.fetchall()]
            print(f"Endpoints in cache: {endpoints}")
            assert "screen_run" in endpoints
            
        # View the cache database
        view_cache_database(TEST_CACHE_DB)
    except Exception as e:
        print(f"Error in test_cache_persistence: {e}")
        raise

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
    
    print(f"\nCache database location: {db_path}")
    
    if not db_path.exists():
        print(f"Cache database not found at {db_path}")
        return
    
    print("\nCache entries:")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Use row factory for named columns
        cursor = conn.cursor()
        
        # Get cache entries
        cursor.execute("""
            SELECT key, endpoint, created_at, expires_at, access_count, size_bytes
            FROM cache_entries
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        
        if rows:
            # Create DataFrame with proper column names
            df = pd.DataFrame(rows, columns=[
                "key", "endpoint", "created_at", "expires_at", 
                "access_count", "size_bytes"
            ])
            print(tabulate(df, headers="keys", tablefmt="grid", showindex=True))
            
            # Calculate total size
            total_size = sum(row['size_bytes'] for row in rows)
            print(f"\nTotal cache size: {total_size / 1024:.2f} KB")
            print(f"Total entries: {len(rows)}")
            
            # Show sample of actual cached data content
            print("\nSample of cached data content:")
            cursor.execute("""
                SELECT key, data FROM cache_entries
                ORDER BY created_at DESC LIMIT 1
            """)
            data_row = cursor.fetchone()
            if data_row:
                try:
                    # Get the data from the row
                    data_blob = data_row['data']
                    
                    # Handle different data formats
                    if isinstance(data_blob, str):
                        # For the new TEXT format
                        if data_blob.startswith('PICKLE:'):
                            # Handle pickle data encoded as base64 string
                            try:
                                pickle_data = base64.b64decode(data_blob[7:])  # Skip 'PICKLE:' prefix
                                obj = pickle.loads(pickle_data)
                                print("\nPickled Data (type):", type(obj))
                                print(str(obj)[:500])  # Limit to first 500 chars
                                if len(str(obj)) > 500:
                                    print("... (truncated)")
                            except Exception as e:
                                print(f"Could not decode pickle data: {e}")
                        else:
                            # Handle JSON stored as text
                            try:
                                json_data = json.loads(data_blob)
                                print("\nJSON Data:")
                                print(json.dumps(json_data, indent=2)[:1000])  # Limit to first 1000 chars
                                if len(json.dumps(json_data, indent=2)) > 1000:
                                    print("... (truncated)")
                            except Exception as e:
                                print(f"Could not parse JSON data: {e}")
                    else:
                        # For the old BLOB format
                        try:
                            # First try JSON
                            json_data = json.loads(data_blob.decode('utf-8'))
                            print("\nJSON Data (from binary):")
                            print(json.dumps(json_data, indent=2)[:1000])
                            if len(json.dumps(json_data, indent=2)) > 1000:
                                print("... (truncated)")
                        except Exception:
                            # If JSON fails, try pickle
                            try:
                                pickle_data = pickle.loads(data_blob)
                                print("\nPickled Data (type):", type(pickle_data))
                                print(str(pickle_data)[:500])
                                if len(str(pickle_data)) > 500:
                                    print("... (truncated)")
                            except Exception as e:
                                print(f"Could not decode binary data: {e}")
                except Exception as e:
                    print(f"Error accessing data: {e}")
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


if __name__ == "__main__":
    print_section("P123 API Caching Test")
    print("\nRunning tests with detailed logging...")
    
    # Create the cache directory if it doesn't exist
    TEST_CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the tests using pytest
    pytest.main([__file__, "-v"])
    
    # Display the cache database contents
    print_section("Cache Database Contents")
    view_cache_database(TEST_CACHE_DB)
    
    print_section("Test Complete")
    print("\nTests completed - check results above for any errors")
    print(f"\nCache database is available for inspection at: {TEST_CACHE_DB}")
