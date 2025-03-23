#!/usr/bin/env python3
"""
Example demonstrating the SimpleStorage cache for P123 API.

This example shows how to:
1. Initialize a SimpleStorage cache
2. Store and retrieve different types of data
3. Handle cache expiration
4. Work with pandas DataFrames
5. Integrate with API clients
"""

import os
import time
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Import SimpleStorage
from p123api_client.cache.simple_storage import SimpleStorage
from p123api_client import MarketClient


def main():
    """Run the SimpleStorage cache example."""
    # Load environment variables
    load_dotenv()
    
    # Create a temporary cache file in the current directory
    cache_path = "simple_cache_example.db"
    print(f"Creating cache at: {cache_path}")
    
    # Initialize the cache
    cache = SimpleStorage(cache_path)
    
    try:
        # Example 1: Basic storage and retrieval
        basic_cache_example(cache)
        
        # Example 2: Working with DataFrames
        dataframe_cache_example(cache)
        
        # Example 3: Cache expiration
        expiration_example(cache)
        
        # Example 4: Endpoint-based operations
        endpoint_operations_example(cache)
        
        # Example 5: API client integration (if credentials available)
        if os.environ.get("P123_API_KEY") and os.environ.get("P123_API_SECRET"):
            api_integration_example(cache)
        else:
            print("\n[API Integration Example] Skipped - API credentials not found in .env file")
    
    finally:
        # Close the cache connections
        cache.close()
        
        # Clean up the example database file
        try:
            os.remove(cache_path)
            print(f"\nCleaned up cache file: {cache_path}")
        except OSError:
            pass


def basic_cache_example(cache):
    """Demonstrate basic cache operations."""
    print("\n=== Basic Cache Operations ===")
    
    # Store some example data
    key = "company_info_AAPL"
    data = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "sector": "Technology",
        "price": 175.23,
        "pe_ratio": 28.5,
        "market_cap": 2850000000000
    }
    endpoint = "company_info"
    expires_at = datetime.now() + timedelta(hours=24)
    
    success = cache.store(key, data, endpoint, expires_at)
    print(f"Stored data with key '{key}': {success}")
    
    # Retrieve the data
    retrieved_data, metadata = cache.retrieve(key)
    print(f"Retrieved data: {retrieved_data}")
    print(f"Metadata:")
    for k, v in metadata.items():
        print(f"  {k}: {v}")
    
    # Delete the data
    deleted = cache.delete(key)
    print(f"Deleted entry: {deleted}")
    
    # Verify it's gone
    retrieved_after_delete, _ = cache.retrieve(key)
    print(f"Retrieved after delete: {retrieved_after_delete}")


def dataframe_cache_example(cache):
    """Demonstrate caching pandas DataFrames."""
    print("\n=== DataFrame Caching ===")
    
    # Create a sample DataFrame (stock data)
    df = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
        'Price': [175.23, 328.45, 2659.12, 135.23, 302.67],
        'Change': [1.2, -0.5, 0.8, -1.5, 2.3],
        'Volume': [28500000, 15600000, 1200000, 32500000, 18700000],
        'Market_Cap_B': [2850, 2456, 1789, 1380, 765]
    })
    
    print(f"Original DataFrame:\n{df.head()}")
    
    # Store the DataFrame
    key = "market_data_top5"
    endpoint = "market_data"
    expires_at = datetime.now() + timedelta(hours=4)
    
    success = cache.store(key, df, endpoint, expires_at)
    print(f"Stored DataFrame: {success}")
    
    # Retrieve the DataFrame
    retrieved_df, metadata = cache.retrieve(key)
    print(f"Retrieved DataFrame:\n{retrieved_df.head()}")
    
    # Verify data types were preserved
    print(f"Data types preserved: {retrieved_df.dtypes}")
    
    # Perform calculations on the retrieved DataFrame
    print(f"Average price: {retrieved_df['Price'].mean():.2f}")
    print(f"Total market cap: {retrieved_df['Market_Cap_B'].sum():.2f} billion")


def expiration_example(cache):
    """Demonstrate cache expiration."""
    print("\n=== Cache Expiration ===")
    
    # Store data with short expiration (2 seconds)
    key = "short_lived_data"
    data = {"timestamp": datetime.now().isoformat(), "value": 42}
    endpoint = "test_expiration"
    expires_at = datetime.now() + timedelta(seconds=2)
    
    cache.store(key, data, endpoint, expires_at)
    print(f"Stored data with 2-second expiration")
    
    # Retrieve immediately
    immediate_data, _ = cache.retrieve(key)
    print(f"Immediate retrieval: {immediate_data is not None}")
    
    # Wait for expiration
    print("Waiting for expiration (3 seconds)...")
    time.sleep(3)
    
    # Try to retrieve after expiration
    expired_data, _ = cache.retrieve(key)
    print(f"Retrieval after expiration: {expired_data is not None}")
    
    # Demonstrate removing expired entries
    # Store a mix of expired and valid entries
    cache.store("expired_1", {"data": 1}, "cleanup", datetime.now() - timedelta(hours=1))
    cache.store("expired_2", {"data": 2}, "cleanup", datetime.now() - timedelta(minutes=30))
    cache.store("valid_1", {"data": 3}, "cleanup", datetime.now() + timedelta(hours=1))
    
    # Remove expired entries
    removed = cache.remove_expired(datetime.now())
    print(f"Removed {removed} expired entries")
    
    # Verify valid entries remain
    valid_data, _ = cache.retrieve("valid_1")
    print(f"Valid entry still exists: {valid_data is not None}")


def endpoint_operations_example(cache):
    """Demonstrate endpoint-based operations."""
    print("\n=== Endpoint Operations ===")
    
    # Store multiple entries for different endpoints
    cache.store("key1", {"data": 1}, "endpoint1", datetime.now() + timedelta(hours=1))
    cache.store("key2", {"data": 2}, "endpoint1", datetime.now() + timedelta(hours=1))
    cache.store("key3", {"data": 3}, "endpoint2", datetime.now() + timedelta(hours=1))
    cache.store("key4", {"data": 4}, "endpoint2", datetime.now() + timedelta(hours=1))
    cache.store("key5", {"data": 5}, "endpoint3", datetime.now() + timedelta(hours=1))
    
    print("Stored 5 entries across 3 endpoints")
    
    # Clear one endpoint
    removed = cache.clear_endpoint("endpoint1")
    print(f"Cleared endpoint1 - removed {removed} entries")
    
    # Verify what remains
    for key in ["key1", "key2", "key3", "key4", "key5"]:
        data, _ = cache.retrieve(key)
        exists = data is not None
        print(f"Key '{key}' exists: {exists}")
    
    # Clear all entries
    success = cache.clear()
    print(f"Cleared all entries: {success}")


def api_integration_example(cache):
    """Demonstrate integration with an API client."""
    print("\n=== API Client Integration ===")
    
    try:
        # Create API client with the cache
        client = MarketClient(
            api_id=os.environ.get("P123_API_ID"),
            api_key=os.environ.get("P123_API_KEY"),
            cache_enabled=True,
            cache_storage=cache
        )
        
        print("Created MarketClient with SimpleStorage cache")
        
        # First call will fetch from API and cache
        print("Fetching market data (first call)...")
        start_time = time.time()
        data1 = client.get_market_data()
        elapsed1 = time.time() - start_time
        print(f"First call completed in {elapsed1:.2f} seconds")
        
        # Second call should be from cache
        print("Fetching market data again (should use cache)...")
        start_time = time.time()
        data2 = client.get_market_data()
        elapsed2 = time.time() - start_time
        print(f"Second call completed in {elapsed2:.2f} seconds")
        
        # Compare performance
        if elapsed1 > 0 and elapsed2 > 0:
            speedup = elapsed1 / elapsed2
            print(f"Cache speedup: {speedup:.1f}x faster")
            
        # Verify data equality
        print(f"Data from both calls is identical: {data1 == data2}")
        
    except Exception as e:
        print(f"Error in API integration example: {e}")


if __name__ == "__main__":
    main() 