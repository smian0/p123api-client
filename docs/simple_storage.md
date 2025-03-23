# SimpleStorage Cache Documentation

## Overview

The SimpleStorage class provides a lightweight SQLite-based caching solution for the P123 API client. It offers a simpler alternative to the full-featured cache manager while retaining the most important functionality.

## Features

- Thread-safe SQLite database operations
- Automatic serialization/deserialization of data
- Support for pandas DataFrames
- Configurable cache expiration
- Endpoint-based cache invalidation
- Low memory overhead
- Minimal dependencies

## Basic Usage

```python
from datetime import datetime, timedelta
from p123api_client.cache.simple_storage import SimpleStorage

# Initialize the cache with a path to the SQLite database
cache = SimpleStorage("~/.p123api/cache.db")

# Store some data
key = "market_data_20230615"
data = {"indexes": {"SP500": 4500.12}, "date": "2023-06-15"}
endpoint = "market_data"
expires_at = datetime.now() + timedelta(days=1)

cache.store(key, data, endpoint, expires_at)

# Retrieve data
retrieved_data, metadata = cache.retrieve(key)
print(f"Retrieved data: {retrieved_data}")
print(f"Metadata: {metadata}")

# Clear cache for a specific endpoint
cache.clear_endpoint("market_data")

# Clean up expired entries
cache.remove_expired(datetime.now())

# Close the connections when done
cache.close()
```

## Storing pandas DataFrames

SimpleStorage supports pandas DataFrames with automatic serialization:

```python
import pandas as pd
from datetime import datetime, timedelta
from p123api_client.cache.simple_storage import SimpleStorage

# Create a DataFrame with some data
df = pd.DataFrame({
    'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
    'Price': [150.25, 250.75, 2500.50],
    'Volume': [1000000, 750000, 250000]
})

# Initialize the cache
cache = SimpleStorage("~/.p123api/cache.db")

# Store the DataFrame
key = "market_prices_20230615"
endpoint = "market_prices"
expires_at = datetime.now() + timedelta(days=1)
cache.store(key, df, endpoint, expires_at)

# Retrieve the DataFrame
retrieved_df, metadata = cache.retrieve(key)
print(f"DataFrame data: {retrieved_df.head()}")
```

## Integration with API Clients

You can use SimpleStorage with the P123 API clients by configuring the cache:

```python
from p123api_client import MarketClient
from p123api_client.cache.simple_storage import SimpleStorage

# Initialize the cache
cache = SimpleStorage("~/.p123api/cache.db")

# Initialize client with custom cache
client = MarketClient(
    cache_enabled=True,
    cache_storage=cache
)

# Use the client normally - data will be cached
data = client.get_market_data()
```

## API Reference

### Constructor

```python
SimpleStorage(db_path: str)
```

- `db_path`: Path to the SQLite database file (will be created if it doesn't exist)

### Methods

#### `store`

```python
store(key: str, data: Any, endpoint: str, expires_at: datetime) -> bool
```

- `key`: Unique identifier for the cached item
- `data`: Data to cache (can be any JSON-serializable object or DataFrame)
- `endpoint`: API endpoint or category this data belongs to
- `expires_at`: When this cache entry should expire
- Returns: `True` if storing was successful, `False` otherwise

#### `retrieve`

```python
retrieve(key: str) -> Tuple[Optional[Any], Optional[Dict]]
```

- `key`: Key of the cached item to retrieve
- Returns: Tuple of `(data, metadata)` if found, `(None, None)` if not found or expired
- Metadata includes endpoint, creation time, expiration time, and access statistics

#### `delete`

```python
delete(key: str) -> bool
```

- `key`: Key of the cached item to delete
- Returns: `True` if deletion was successful, `False` otherwise

#### `clear`

```python
clear() -> bool
```

- Removes all cached items
- Returns: `True` if successful, `False` otherwise

#### `remove_expired`

```python
remove_expired(before: datetime) -> int
```

- `before`: Remove entries expiring before this time
- Returns: Number of entries removed

#### `clear_endpoint`

```python
clear_endpoint(endpoint: str) -> int
```

- `endpoint`: API endpoint to clear cache entries for
- Returns: Number of entries removed

#### `close`

```python
close()
```

- Closes all database connections and releases resources
- Should be called when the cache is no longer needed

## Thread Safety

SimpleStorage is designed to be thread-safe through connection pooling and locking. Each thread gets its own SQLite connection, and access to the connection pool is synchronized with a reentrant lock.

## Error Handling

All methods include comprehensive error handling and logging. If an operation fails, it will generally return `None`, `False`, or `0` depending on the method, and the error will be logged.

## Database Structure

The SQLite database uses a single table `cache_entries` with the following columns:

- `key`: Primary key, unique identifier for the cache entry
- `data`: Serialized data blob
- `endpoint`: API endpoint this data belongs to
- `created_at`: When the entry was created
- `expires_at`: When the entry expires
- `access_count`: How many times this entry has been accessed
- `last_accessed`: When the entry was last accessed
- `size_bytes`: Size of the serialized data in bytes

Indexes are created for efficient lookup by endpoint and expiration time. 