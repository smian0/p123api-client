# Epic-7-caching: Implement P123 API Result Caching System
# Story-Combined: Implement Complete SQLite-based API Caching System

## Story

**As a** quantitative researcher
**I want** a comprehensive API response caching system with SQLite persistence
**so that** I can maximize my API quota usage, work with consistent data, and maintain cache benefits across sessions

## Status

Draft

## Context

Part of Epic-7-caching which implements a caching system for P123 API responses. This consolidated story combines the core caching infrastructure, time-based invalidation, and SQLite-based persistent storage into a single comprehensive implementation.

The Portfolio123 API has strict rate limits, and data is only updated once daily (by 3 AM Eastern Standard Time). This makes caching an effective strategy for optimizing API quota usage. This implementation will create a complete caching solution with SQLite persistence that ensures cached responses survive application restarts while maintaining proper data freshness through time-based invalidation tied to P123's data update cycle.

## Estimation

**Story Points**: 8

**Implementation Time Estimates**:
- **Human Development**: 8 days
- **AI-Assisted Development**: 0.13 days (~80 minutes)

## Tasks

1. - [ ] Write Comprehensive Cache Tests
   1. - [ ] Write tests for cache key generation
   2. - [ ] Write tests for in-memory cache operations
   3. - [ ] Write tests for time-based invalidation
   4. - [ ] Write tests for SQLite database schema
   5. - [ ] Write tests for database operations (CRUD)
   6. - [ ] Write tests for cache persistence across sessions
   7. - [ ] Write tests for concurrent access scenarios
   8. - [ ] Write integration tests for full caching system

2. - [ ] Design Cache Architecture
   1. - [ ] Define cache key generation algorithm
   2. - [ ] Design storage interface supporting multiple backends
   3. - [ ] Plan integration with existing client
   4. - [ ] Design SQLite database schema
   5. - [ ] Design invalidation mechanism

3. - [ ] Implement Core Cache Components
   1. - [ ] Create parameter normalization utilities
   2. - [ ] Implement deterministic serialization
   3. - [ ] Create cache key generation function
   4. - [ ] Implement cache entry data structures
   5. - [ ] Add cache statistics tracking

4. - [ ] Implement Timezone and Invalidation System
   1. - [ ] Add timezone configuration support
   2. - [ ] Implement reference time calculation (3 AM EST)
   3. - [ ] Create next invalidation time calculator
   4. - [ ] Implement cache entry expiration calculator
   5. - [ ] Build automatic invalidation trigger

5. - [ ] Implement Serialization System
   1. - [ ] Create cache entry serializer/deserializer
   2. - [ ] Implement response data serialization for BLOB storage
   3. - [ ] Add versioning for serialized format
   4. - [ ] Implement data integrity validation

6. - [ ] Implement SQLite Storage Backend
   1. - [ ] Create SQLite connection manager
   2. - [ ] Implement database initialization and schema creation
   3. - [ ] Create CRUD operations for cache entries
   4. - [ ] Add transaction support for atomicity
   5. - [ ] Implement write-ahead logging for better concurrency
   6. - [ ] Add connection pooling for multi-threaded access
   7. - [ ] Implement prepared statements for common operations

7. - [ ] Implement Cache Manager
   1. - [ ] Create CacheManager class
   2. - [ ] Implement initialization from SQLite database
   3. - [ ] Add cache lookup/store/delete operations
   4. - [ ] Integrate time-based invalidation
   5. - [ ] Add cache bypass option for force refresh
   6. - [ ] Implement periodic database maintenance
   7. - [ ] Add database corruption recovery mechanisms

8. - [ ] Integrate with API Client
   1. - [ ] Add cache layer to base API client
   2. - [ ] Implement cache lookup before API calls
   3. - [ ] Add cache update after successful API calls
   4. - [ ] Add configurable caching behavior
   5. - [ ] Implement endpoint-specific cache settings

9. - [ ] Add Monitoring and Management
   1. - [ ] Implement cache statistics collection
   2. - [ ] Create cache performance metrics
   3. - [ ] Add manual cache control functions
   4. - [ ] Implement cache event logging
   5. - [ ] Add cache visualization utilities

10. - [ ] Add Documentation
    1. - [ ] Document caching architecture
    2. - [ ] Document SQLite cache configuration
    3. - [ ] Create usage examples
    4. - [ ] Add database management guidelines
    5. - [ ] Create troubleshooting guide

## Data Models / Schema

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic, Tuple
import sqlite3
import threading
import json
import pickle
import hashlib
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
import logging
from pathlib import Path
import pytz

T = TypeVar('T')

@dataclass
class CacheEntry:
    """Represents a cached API response."""
    
    key: str  # Unique identifier for this cache entry
    data: Any  # The cached API response
    endpoint: str  # The API endpoint this entry is for
    created_at: datetime  # When this entry was created
    expires_at: datetime  # When this entry expires
    access_count: int = 0  # Number of times this entry has been accessed
    last_accessed: Optional[datetime] = None  # When this entry was last accessed
    size_bytes: int = 0  # Size of the data in bytes
    
@dataclass
class CacheStatistics:
    """Tracks cache performance statistics."""
    
    hits: int = 0  # Number of cache hits
    misses: int = 0  # Number of cache misses
    hit_ratio: float = 0.0  # Ratio of hits to total requests
    saved_quota: int = 0  # Estimated saved API quota
    total_entries: int = 0  # Total number of cache entries
    total_size_bytes: int = 0  # Total size of cached data
    created_at: datetime = datetime.now()  # When these statistics were created
    oldest_entry: Optional[datetime] = None  # Creation time of oldest entry
    newest_entry: Optional[datetime] = None  # Creation time of newest entry
    
@dataclass
class CacheConfig:
    """Configuration for the caching system."""
    
    enabled: bool = True  # Whether caching is enabled
    refresh_time: str = "03:00"  # When to invalidate cache (3 AM EST by default)
    timezone: str = "US/Eastern"  # Timezone for refresh_time
    db_path: str = "~/.p123cache/cache.db"  # Path to SQLite database
    in_memory_cache_size: int = 100  # Number of entries to keep in memory
    enable_statistics: bool = True  # Whether to collect cache statistics
    log_level: str = "INFO"  # Logging level for cache events
    maintenance_interval: int = 3600  # Seconds between maintenance runs
    max_entries: Optional[int] = None  # Maximum number of entries to keep
```

## Implementation Details

### SQLite Database Schema

```sql
-- Cache entries table
CREATE TABLE cache_entries (
    key TEXT PRIMARY KEY,
    data BLOB NOT NULL,
    endpoint TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TIMESTAMP,
    size_bytes INTEGER NOT NULL,
    UNIQUE(key)
);

-- Create indexes for efficient lookups
CREATE INDEX idx_endpoint ON cache_entries(endpoint);
CREATE INDEX idx_expires_at ON cache_entries(expires_at);
CREATE INDEX idx_last_accessed ON cache_entries(last_accessed);

-- Cache metadata table
CREATE TABLE cache_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Cache statistics table
CREATE TABLE cache_statistics (
    timestamp TIMESTAMP PRIMARY KEY,
    hits INTEGER NOT NULL,
    misses INTEGER NOT NULL,
    total_entries INTEGER NOT NULL,
    total_size_bytes INTEGER NOT NULL
);

-- Initialization with default metadata
INSERT INTO cache_metadata (key, value) VALUES
    ('schema_version', '1.0'),
    ('created_at', CURRENT_TIMESTAMP),
    ('last_maintenance', CURRENT_TIMESTAMP);
```

### Core Architecture Components

1. **Storage Backend Interface**:
   ```python
   class StorageBackend(ABC):
       """Abstract base class for cache storage backends."""
       
       @abstractmethod
       def store(self, key: str, data: bytes, metadata: dict) -> bool:
           """Store data in the backend."""
           pass
           
       @abstractmethod
       def retrieve(self, key: str) -> Tuple[Optional[bytes], Optional[dict]]:
           """Retrieve data and metadata from the backend."""
           pass
           
       @abstractmethod
       def delete(self, key: str) -> bool:
           """Delete data from the backend."""
           pass
           
       @abstractmethod
       def clear(self) -> bool:
           """Clear all data from the backend."""
           pass
           
       @abstractmethod
       def contains(self, key: str) -> bool:
           """Check if key exists in the backend."""
           pass
           
       @abstractmethod
       def list_keys(self) -> List[str]:
           """List all keys in the backend."""
           pass
           
       @abstractmethod
       def get_stats(self) -> dict:
           """Get statistics about the storage backend."""
           pass
   ```

2. **SQLite Connection Manager**:
   ```python
   class SQLiteConnectionManager:
       """Manages SQLite database connections."""
       
       def __init__(self, db_path: str, isolation_level: str = None):
           """Initialize connection manager with database path."""
           self.db_path = Path(db_path).expanduser().resolve()
           self.isolation_level = isolation_level
           self._connection_pool = {}
           self._lock = threading.RLock()
           
           # Ensure directory exists
           self.db_path.parent.mkdir(parents=True, exist_ok=True)
       
       @contextmanager
       def get_connection(self) -> sqlite3.Connection:
           """Get a connection for the current thread."""
           thread_id = threading.get_ident()
           
           with self._lock:
               if thread_id not in self._connection_pool:
                   conn = sqlite3.connect(
                       str(self.db_path),
                       isolation_level=self.isolation_level,
                       detect_types=sqlite3.PARSE_DECLTYPES
                   )
                   conn.row_factory = sqlite3.Row
                   
                   # Enable foreign keys
                   conn.execute("PRAGMA foreign_keys = ON")
                   
                   # Use WAL journal mode for better concurrency
                   conn.execute("PRAGMA journal_mode = WAL")
                   
                   # Set busy timeout to avoid lock errors
                   conn.execute("PRAGMA busy_timeout = 5000")
                   
                   self._connection_pool[thread_id] = conn
               
               try:
                   yield self._connection_pool[thread_id]
               except sqlite3.Error as e:
                   logging.error(f"SQLite error: {e}")
                   raise
       
       def close_all(self):
           """Close all connections in the pool."""
           with self._lock:
               for conn in self._connection_pool.values():
                   conn.close()
               self._connection_pool.clear()
   ```

3. **SQLite Storage Backend**:
   ```python
   class SQLiteStorageBackend(StorageBackend):
       """SQLite implementation of cache storage backend."""
       
       def __init__(self, db_path: str):
           """Initialize SQLite storage with database path."""
           self.connection_manager = SQLiteConnectionManager(db_path)
           self._init_db()
       
       def _init_db(self):
           """Initialize database schema if needed."""
           with self.connection_manager.get_connection() as conn:
               # Create tables and indexes
               conn.executescript("""
                   -- Cache entries table
                   CREATE TABLE IF NOT EXISTS cache_entries (
                       key TEXT PRIMARY KEY,
                       data BLOB NOT NULL,
                       endpoint TEXT NOT NULL,
                       created_at TIMESTAMP NOT NULL,
                       expires_at TIMESTAMP NOT NULL,
                       access_count INTEGER NOT NULL DEFAULT 0,
                       last_accessed TIMESTAMP,
                       size_bytes INTEGER NOT NULL,
                       UNIQUE(key)
                   );
                   
                   -- Create indexes for efficient lookups
                   CREATE INDEX IF NOT EXISTS idx_endpoint ON cache_entries(endpoint);
                   CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at);
                   CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed);
                   
                   -- Cache metadata table
                   CREATE TABLE IF NOT EXISTS cache_metadata (
                       key TEXT PRIMARY KEY,
                       value TEXT NOT NULL
                   );
                   
                   -- Cache statistics table
                   CREATE TABLE IF NOT EXISTS cache_statistics (
                       timestamp TIMESTAMP PRIMARY KEY,
                       hits INTEGER NOT NULL,
                       misses INTEGER NOT NULL,
                       total_entries INTEGER NOT NULL,
                       total_size_bytes INTEGER NOT NULL
                   );
               """)
               
               # Initialize metadata if empty
               cursor = conn.execute("SELECT COUNT(*) FROM cache_metadata")
               if cursor.fetchone()[0] == 0:
                   conn.executescript("""
                       INSERT INTO cache_metadata (key, value) VALUES
                           ('schema_version', '1.0'),
                           ('created_at', CURRENT_TIMESTAMP),
                           ('last_maintenance', CURRENT_TIMESTAMP);
                   """)
       
       def store(self, key: str, data: bytes, metadata: dict) -> bool:
           """Store data in the SQLite database."""
           try:
               with self.connection_manager.get_connection() as conn:
                   cursor = conn.cursor()
                   cursor.execute("""
                       INSERT OR REPLACE INTO cache_entries
                           (key, data, endpoint, created_at, expires_at, size_bytes)
                       VALUES (?, ?, ?, ?, ?, ?)
                   """, (
                       key,
                       data,
                       metadata.get('endpoint', ''),
                       metadata.get('created_at', datetime.now()),
                       metadata.get('expires_at', datetime.now()),
                       len(data)
                   ))
                   conn.commit()
                   return True
           except Exception as e:
               logging.error(f"Error storing cache entry: {e}")
               return False
       
       def retrieve(self, key: str) -> Tuple[Optional[bytes], Optional[dict]]:
           """Retrieve data from the SQLite database."""
           try:
               with self.connection_manager.get_connection() as conn:
                   cursor = conn.cursor()
                   cursor.execute("""
                       SELECT data, endpoint, created_at, expires_at, access_count, last_accessed, size_bytes
                       FROM cache_entries
                       WHERE key = ?
                   """, (key,))
                   
                   row = cursor.fetchone()
                   if row is None:
                       return None, None
                   
                   # Update access count and last_accessed
                   now = datetime.now()
                   cursor.execute("""
                       UPDATE cache_entries
                       SET access_count = access_count + 1, last_accessed = ?
                       WHERE key = ?
                   """, (now, key))
                   conn.commit()
                   
                   # Extract metadata
                   metadata = {
                       'endpoint': row['endpoint'],
                       'created_at': row['created_at'],
                       'expires_at': row['expires_at'],
                       'access_count': row['access_count'] + 1,  # Include the current access
                       'last_accessed': now,
                       'size_bytes': row['size_bytes']
                   }
                   
                   return row['data'], metadata
           except Exception as e:
               logging.error(f"Error retrieving cache entry: {e}")
               return None, None
       
       # Other methods implementation...
   ```

4. **Cache Manager**:
   ```python
   class CacheManager:
       """Manages caching operations."""
       
       def __init__(self, config: CacheConfig = None):
           """Initialize cache manager with configuration."""
           self.config = config or CacheConfig()
           self.stats = CacheStatistics()
           
           # Initialize storage backend
           self.storage = SQLiteStorageBackend(self.config.db_path)
           
           # Initialize in-memory LRU cache for faster access
           self.memory_cache = {}  # Simple dict for now, could use lru_cache
           
           # Initialize invalidation timer
           self.last_invalidation_check = datetime.now()
           
           # Start maintenance thread if enabled
           if self.config.enabled and self.config.maintenance_interval > 0:
               self._start_maintenance_thread()
       
       def _start_maintenance_thread(self):
           """Start a background thread for periodic maintenance."""
           def maintenance_worker():
               while self.config.enabled:
                   try:
                       # Sleep first to avoid immediate maintenance
                       time.sleep(self.config.maintenance_interval)
                       
                       # Run maintenance tasks
                       self._run_maintenance()
                   except Exception as e:
                       logging.error(f"Error in maintenance thread: {e}")
           
           thread = threading.Thread(target=maintenance_worker, daemon=True)
           thread.start()
       
       def _run_maintenance(self):
           """Run maintenance tasks."""
           self._check_invalidation()
           self._update_statistics()
           
           # Record maintenance time
           with self.storage.connection_manager.get_connection() as conn:
               conn.execute("""
                   UPDATE cache_metadata
                   SET value = ?
                   WHERE key = 'last_maintenance'
               """, (datetime.now().isoformat(),))
               conn.commit()
       
       def _check_invalidation(self):
           """Check for and remove expired cache entries."""
           now = datetime.now()
           
           # Only check periodically
           if (now - self.last_invalidation_check).total_seconds() < 60:
               return
               
           self.last_invalidation_check = now
           
           with self.storage.connection_manager.get_connection() as conn:
               # Delete expired entries
               cursor = conn.execute("""
                   DELETE FROM cache_entries
                   WHERE expires_at < ?
               """, (now,))
               deleted_count = cursor.rowcount
               conn.commit()
               
               if deleted_count > 0:
                   logging.info(f"Cache invalidation: removed {deleted_count} expired entries")
                   
                   # Clear memory cache as well
                   self.memory_cache.clear()
       
       def get(self, key: str, bypass_cache: bool = False) -> Optional[Any]:
           """Get a value from the cache."""
           if not self.config.enabled or bypass_cache:
               self.stats.misses += 1
               return None
               
           # Check memory cache first
           if key in self.memory_cache:
               entry = self.memory_cache[key]
               
               # Check if expired
               if entry.expires_at < datetime.now():
                   del self.memory_cache[key]
                   self.stats.misses += 1
                   return None
                   
               # Update access stats
               entry.access_count += 1
               entry.last_accessed = datetime.now()
               
               self.stats.hits += 1
               return entry.data
           
           # Check persistent storage
           data, metadata = self.storage.retrieve(key)
           if data is None:
               self.stats.misses += 1
               return None
               
           # Check if expired
           if metadata['expires_at'] < datetime.now():
               self.storage.delete(key)
               self.stats.misses += 1
               return None
           
           # Deserialize data
           try:
               value = pickle.loads(data)
           except Exception as e:
               logging.error(f"Error deserializing cache data: {e}")
               self.storage.delete(key)
               self.stats.misses += 1
               return None
           
           # Update memory cache
           if len(self.memory_cache) < self.config.in_memory_cache_size:
               entry = CacheEntry(
                   key=key,
                   data=value,
                   endpoint=metadata['endpoint'],
                   created_at=metadata['created_at'],
                   expires_at=metadata['expires_at'],
                   access_count=metadata['access_count'],
                   last_accessed=metadata['last_accessed'],
                   size_bytes=metadata['size_bytes']
               )
               self.memory_cache[key] = entry
           
           self.stats.hits += 1
           return value
       
       def put(self, key: str, value: Any, endpoint: str, force_ttl: Optional[int] = None) -> bool:
           """Put a value in the cache."""
           if not self.config.enabled:
               return False
               
           # Calculate expiration time
           now = datetime.now()
           if force_ttl is not None:
               expires_at = now + timedelta(seconds=force_ttl)
           else:
               # Use P123 refresh schedule for all normal operations
               expires_at = self.calculate_next_refresh_time(now)
           
           # Serialize data
           try:
               data = pickle.dumps(value)
           except Exception as e:
               logging.error(f"Error serializing cache data: {e}")
               return False
           
           # Create entry
           entry = CacheEntry(
               key=key,
               data=value,
               endpoint=endpoint,
               created_at=now,
               expires_at=expires_at,
               access_count=0,
               last_accessed=None,
               size_bytes=len(data)
           )
           
           # Update memory cache
           if len(self.memory_cache) < self.config.in_memory_cache_size:
               self.memory_cache[key] = entry
           elif key in self.memory_cache:
               self.memory_cache[key] = entry
           
           # Store in persistent storage
           metadata = {
               'endpoint': endpoint,
               'created_at': now,
               'expires_at': expires_at,
               'size_bytes': len(data)
           }
           return self.storage.store(key, data, metadata)
       
       def calculate_next_refresh_time(self, now: datetime = None) -> datetime:
           """Calculate the next P123 data refresh time (3 AM EST)."""
           now = now or datetime.now()
           
           # Get configured timezone
           p123_tz = pytz.timezone(self.config.timezone)
           
           # Parse refresh time
           hour, minute = map(int, self.config.refresh_time.split(':'))
           
           # Convert current time to configured timezone
           now_tz = now.astimezone(p123_tz)
           
           # Create refresh time today in configured timezone
           refresh_time_today = datetime.combine(
               now_tz.date(), 
               time(hour=hour, minute=minute, second=0)
           )
           refresh_time_today = p123_tz.localize(refresh_time_today)
           
           # If it's already past refresh time today, use tomorrow
           if now_tz > refresh_time_today:
               next_day = now_tz.date() + timedelta(days=1)
               refresh_time = datetime.combine(
                   next_day,
                   time(hour=hour, minute=minute, second=0)
               )
               refresh_time = p123_tz.localize(refresh_time)
           else:
               refresh_time = refresh_time_today
               
           # Convert back to UTC for storage
           return refresh_time.astimezone(pytz.UTC)
       
       def force_refresh_after_update(self):
           """
           Call this after P123 updates to immediately invalidate the cache.
           Useful if P123 updates earlier than the configured refresh time.
           """
           with self.storage.connection_manager.get_connection() as conn:
               conn.execute("DELETE FROM cache_entries")
               conn.commit()
           
           # Clear memory cache
           self.memory_cache.clear()
           
           logging.info("Cache forcibly invalidated due to P123 data update")
       
       # Other methods...
   ```

5. **Cache Key Generation**:
   ```python
   def generate_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
       """Generate a cache key from endpoint and parameters."""
       # Normalize parameters
       normalized_params = _normalize_params(params)
       
       # Serialize to JSON with sorted keys for consistency
       param_str = json.dumps(normalized_params, sort_keys=True)
       
       # Combine endpoint and parameters
       combined = f"{endpoint}:{param_str}"
       
       # Hash the combined string for shorter keys
       return hashlib.sha256(combined.encode()).hexdigest()
       
   def _normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
       """Normalize parameters for consistent cache keys."""
       result = {}
       
       # Handle None values
       for key, value in params.items():
           if value is None:
               continue
               
           # Convert nested dictionaries
           if isinstance(value, dict):
               result[key] = _normalize_params(value)
           # Convert lists/tuples
           elif isinstance(value, (list, tuple)):
               result[key] = _normalize_list(value)
           # Convert datetimes to ISO format
           elif isinstance(value, datetime):
               result[key] = value.isoformat()
           # Handle basic types
           elif isinstance(value, (str, int, float, bool)):
               result[key] = value
           # Use string representation for other types
           else:
               result[key] = str(value)
               
       return result
       
   def _normalize_list(values: List[Any]) -> List[Any]:
       """Normalize a list of values."""
       result = []
       
       for value in values:
           # Handle nested dictionaries
           if isinstance(value, dict):
               result.append(_normalize_params(value))
           # Handle nested lists
           elif isinstance(value, (list, tuple)):
               result.append(_normalize_list(value))
           # Convert datetimes to ISO format
           elif isinstance(value, datetime):
               result.append(value.isoformat())
           # Handle basic types
           elif isinstance(value, (str, int, float, bool)):
               result.append(value)
           # Use string representation for other types
           else:
               result.append(str(value))
               
       return result
   ```

6. **API Client Integration**:
   ```python
   class CachedApiClient(BaseApiClient):
       """API client with caching capabilities."""
       
       def __init__(self, *args, cache_config: CacheConfig = None, **kwargs):
           """Initialize client with cache configuration."""
           super().__init__(*args, **kwargs)
           self.cache_manager = CacheManager(cache_config)
       
       def _request(self, method: str, endpoint: str, params: dict = None, 
                   data: dict = None, headers: dict = None, 
                   bypass_cache: bool = False, force_ttl: Optional[int] = None, **kwargs) -> dict:
           """Make a request with caching support."""
           # Only cache GET requests
           if method.upper() != "GET" or bypass_cache or not self.cache_manager.config.enabled:
               return super()._request(method, endpoint, params, data, headers, **kwargs)
           
           # Generate cache key
           combined_params = {**(params or {}), **(data or {})}
           cache_key = generate_cache_key(endpoint, combined_params)
           
           # Try to get from cache
           cached_response = self.cache_manager.get(cache_key, bypass_cache)
           if cached_response is not None:
               logging.debug(f"Cache hit for {endpoint}")
               return cached_response
           
           # Make actual API request
           response = super()._request(method, endpoint, params, data, headers, **kwargs)
           
           # Store in cache
           self.cache_manager.put(cache_key, response, endpoint, force_ttl)
           
           return response
       
       def invalidate_cache(self, endpoint: str = None):
           """Invalidate cache for specific endpoint or all."""
           if endpoint:
               self.cache_manager.invalidate_endpoint(endpoint)
           else:
               self.cache_manager.invalidate_all()
       
       def force_refresh(self):
           """Force immediate refresh of all cached data."""
           self.cache_manager.force_refresh_after_update()
       
       def get_cache_stats(self) -> CacheStatistics:
           """Get cache statistics."""
           return self.cache_manager.get_stats()
   ```

### Performance Considerations

1. **Optimizing SQLite Performance**:
   - Use Write-Ahead Logging (WAL) journal mode for better concurrency
   - Create proper indexes for frequent query patterns
   - Use prepared statements to reduce parsing overhead
   - Keep transactions short to avoid locking issues
   - Implement connection pooling for multi-threaded access
   - Set appropriate busy timeout to handle contention

2. **Memory-Database Hybrid Approach**:
   - Keep frequently accessed entries in memory with an LRU cache
   - Use persistent storage for complete cache
   - Periodically synchronize for durability
   - Optimize memory usage by controlling cache size

3. **Serialization Strategy**:
   - Use pickle for Python object serialization
   - Store serialized data as BLOB type in SQLite
   - Consider compression for large responses
   - Implement versioning for forward compatibility
   - Validate data integrity on retrieval

4. **Refresh-Time-Based Invalidation**:
   - All cache entries expire based on P123's refresh schedule
   - Use timezone-aware datetime calculations for accuracy
   - Implement efficient bulk invalidation at refresh time
   - Provide manual invalidation method for exceptional cases
   - Use background thread for maintenance operations

## Dev Notes

- The cache implementation transparently integrates with the existing API client
- SQLite is chosen for its reliability, zero configuration, and SQL capabilities
- The combined approach balances performance (memory cache) with durability (SQLite)
- Consider security implications of pickle serialization; only cache data from trusted sources
- The caching strategy is specifically optimized for P123's once-daily data update pattern
- Invalidation is tied directly to P123's refresh schedule (3 AM EST by default)
- All cache entries for all endpoints expire simultaneously when P123 updates its data
- Add appropriate error handling for database corruption or locking issues
- Consider implementing a vacuum operation to reclaim space after database growth
- Thread safety is maintained through connection pooling and transaction isolation
- Use the pytz library for robust timezone handling
- The force_refresh_after_update method provides manual control when needed 

### Required Dependencies

```
pytz>=2023.3      # Timezone handling
pytest>=7.3.1     # Testing framework
pytest-mock>=3.10 # Test mocking
```

## Change Log

| Date | Change | Description |
|------|--------|-------------|
| 2023-03-21 | Creation | Initial draft of combined story |
| 2023-03-22 | SQLite Integration | Updated with SQLite-based implementation details |
| 2023-03-22 | Simplify Invalidation | Removed TTL-based expiration in favor of refresh-time-only approach | 