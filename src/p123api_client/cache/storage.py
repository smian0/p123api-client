"""SQLite storage backend for caching."""

import base64
import json
import logging
import pickle
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Register adapters and converters for datetime objects
def adapt_datetime(dt):
    """Convert datetime to SQLite timestamp string."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def convert_datetime(value):
    """Convert SQLite timestamp to datetime."""
    if value is None:
        return None
    try:
        return datetime.strptime(value.decode(), "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        logger.error(f"Failed to convert timestamp: {e}")
        return None


# Register adapters and converters
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)


class SQLiteStorage:
    """SQLite-based storage backend for caching."""

    def __init__(self, db_path: str, max_cache_size_mb: int = 100):
        """Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
            max_cache_size_mb: Maximum cache size in megabytes
        """
        self.db_path = Path(db_path).expanduser().resolve()
        self._connection_pool = {}
        self._lock = threading.RLock()
        self.max_cache_size_mb = max_cache_size_mb

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            conn.executescript("""
                -- Cache entries table
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,  -- Using TEXT for better inspection
                    endpoint TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    size_bytes INTEGER NOT NULL
                );
                
                -- Create indexes for efficient lookups
                CREATE INDEX IF NOT EXISTS idx_endpoint 
                    ON cache_entries(endpoint);
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                    ON cache_entries(expires_at);
                CREATE INDEX IF NOT EXISTS idx_last_accessed
                    ON cache_entries(last_accessed);
                
                -- Statistics table
                CREATE TABLE IF NOT EXISTS cache_statistics (
                    timestamp TIMESTAMP PRIMARY KEY,
                    hits INTEGER NOT NULL,
                    misses INTEGER NOT NULL,
                    total_entries INTEGER NOT NULL,
                    total_size_bytes INTEGER NOT NULL
                );
                
                -- Create index on timestamp for faster stats lookups
                CREATE INDEX IF NOT EXISTS idx_stats_timestamp
                    ON cache_statistics(timestamp DESC);
                
                -- Add pragma optimizations
                PRAGMA synchronous = NORMAL;  -- Faster writes with reasonable safety
                PRAGMA journal_mode = WAL;    -- Better concurrency
                PRAGMA cache_size = -2000;    -- Use 2MB of memory for cache
            """)

    @contextmanager
    def get_connection(self) -> sqlite3.Connection:
        """Get a SQLite connection for the current thread.

        Returns:
            A thread-local SQLite connection
        """
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id not in self._connection_pool:
                # Create new connection
                conn = sqlite3.connect(
                    str(self.db_path), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
                )
                # Ensure we can access rows by column name
                conn.row_factory = sqlite3.Row

                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Use WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode = WAL")

                # Set busy timeout
                conn.execute("PRAGMA busy_timeout = 5000")

                self._connection_pool[thread_id] = conn

            try:
                # Double-check row_factory is correctly set
                self._connection_pool[thread_id].row_factory = sqlite3.Row
                yield self._connection_pool[thread_id]
            except sqlite3.Error as e:
                logger.error(f"SQLite error: {e}")
                raise

    def store(self, key: str, data: Any, endpoint: str, expires_at: datetime) -> bool:
        """Store data in the cache.

        Args:
            key: Cache key
            data: Data to store
            endpoint: API endpoint this data is for
            expires_at: When this cache entry expires

        Returns:
            True if storage successful, False otherwise
        """
        # Check if we need to clean up the cache first
        self._check_cache_size()
        try:
            # Serialize data as JSON text for better readability and inspection
            try:
                # Store as plain text string, not binary
                serialized = json.dumps(data, default=str)
            except TypeError as e:
                # If JSON serialization fails (e.g., for complex objects), fall back to pickle
                # but encode it to a base64 string so it can be stored as text
                logger.warning(f"JSON serialization failed, falling back to pickle: {e}")
                pickle_data = pickle.dumps(data)
                serialized = f"PICKLE:{base64.b64encode(pickle_data).decode('ascii')}"

            with self.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache_entries
                        (key, data, endpoint, created_at, expires_at, size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        key,
                        serialized,
                        endpoint,
                        datetime.now(timezone.utc).replace(
                            microsecond=0
                        ),  # Store as native datetime
                        expires_at.astimezone(timezone.utc).replace(
                            microsecond=0
                        ),  # Store as native datetime
                        len(serialized),
                    ),
                )
                conn.commit()
                # Ensure changes are visible to other connections
                conn.execute("PRAGMA wal_checkpoint(FULL);")
                return True

        except Exception as e:
            logger.error(f"Error storing cache entry: {e}")
            return False

    def retrieve(self, key: str) -> tuple[Any | None, dict | None]:
        """Retrieve data from the cache.

        Args:
            key: Cache key

        Returns:
            Tuple of (data, metadata) if found, (None, None) if not found
        """
        try:
            with self.get_connection() as conn:
                # Make sure row_factory is set
                conn.row_factory = sqlite3.Row

                # First check if the key exists and if it's expired
                cursor = conn.execute(
                    """
                    SELECT expires_at FROM cache_entries 
                    WHERE key = ? LIMIT 1
                """,
                    (key,),
                )

                expiry_row = cursor.fetchone()
                if expiry_row is None:
                    return None, None

                # Check if expired
                now = datetime.now(timezone.utc).replace(microsecond=0)
                expires_at = expiry_row[0]

                # Ensure both datetimes have timezone info
                if expires_at and expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if expires_at and expires_at <= now:
                    # Delete expired entry
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    conn.commit()
                    return None, None

                # Get the full data now that we know it's valid
                cursor = conn.execute(
                    """
                    SELECT data, endpoint, created_at, expires_at,
                           access_count, last_accessed
                    FROM cache_entries WHERE key = ?
                """,
                    (key,),
                )

                row = cursor.fetchone()
                if row is None:
                    return None, None

                # Update access statistics
                conn.execute(
                    """
                    UPDATE cache_entries 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE key = ?
                """,
                    (now, key),
                )
                conn.commit()

                # Access row data by column name
                try:
                    data_blob = row["data"]
                    endpoint = row["endpoint"]
                    created_at = row["created_at"]
                    expires_at = row["expires_at"]
                    access_count = row["access_count"]
                    last_accessed = row["last_accessed"]
                except Exception:
                    # Try index-based access as fallback
                    try:
                        data_blob = row[0]
                        endpoint = row[1]
                        created_at = row[2]
                        expires_at = row[3]
                        access_count = row[4]
                        last_accessed = row[5]
                    except Exception as e2:
                        logger.error(f"Error accessing row data: {e2}")
                        return None, None

                # Deserialize data
                try:
                    # First check if it's a pickle-encoded string (for new format)
                    if isinstance(data_blob, str) and data_blob.startswith("PICKLE:"):
                        try:
                            pickle_data = base64.b64decode(data_blob[7:])  # Skip 'PICKLE:' prefix
                            deserialized = pickle.loads(pickle_data)
                        except Exception as e:
                            logger.error(f"Error deserializing pickle data: {e}")
                            deserialized = data_blob
                    # Then try JSON (our preferred format)
                    elif isinstance(data_blob, str):
                        try:
                            deserialized = json.loads(data_blob)
                        except Exception as e:
                            logger.error(f"Error deserializing JSON data: {e}")
                            deserialized = data_blob
                    # For backward compatibility with old binary format
                    else:
                        try:
                            # First try to decode as JSON
                            try:
                                deserialized = json.loads(data_blob.decode("utf-8"))
                            except Exception:
                                # If JSON fails, try pickle
                                try:
                                    deserialized = pickle.loads(data_blob)
                                except Exception:
                                    # Last resort, use raw data
                                    deserialized = data_blob
                        except Exception as e:
                            logger.error(f"Error deserializing binary data: {e}")
                            deserialized = data_blob

                except Exception as e:
                    logger.error(f"Error deserializing cache data: {e}")
                    # If we can't deserialize, treat as cache miss
                    return None, None

                # Return data with metadata
                metadata = {
                    "endpoint": endpoint,
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "access_count": access_count,
                    "last_accessed": last_accessed,
                }

                return deserialized, metadata

        except Exception as e:
            logger.error(f"Error retrieving cache entry: {e}")
            return None, None

    def delete(self, key: str) -> bool:
        """Delete a cache entry.

        Args:
            key: Cache key to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting cache entry: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries.

        Returns:
            True if clear successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM cache_entries")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def remove_expired(self, before: datetime) -> int:
        """Remove expired cache entries.

        Args:
            before: Remove entries expiring before this time

        Returns:
            Number of entries removed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM cache_entries
                    WHERE expires_at < ?
                """,
                    (before,),
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error removing expired entries: {e}")
            return 0

    def update_statistics(self, hits: int, misses: int):
        """Update cache statistics.

        Args:
            hits: Number of cache hits
            misses: Number of cache misses
        """
        try:
            with self.get_connection() as conn:
                # Get current totals
                cursor = conn.execute("""
                    SELECT COUNT(*) as count, SUM(size_bytes) as size
                    FROM cache_entries
                """)
                row = cursor.fetchone()

                # Get latest statistics to update cumulative counts
                latest_cursor = conn.execute("""
                    SELECT hits, misses FROM cache_statistics
                    ORDER BY timestamp DESC LIMIT 1
                """)
                latest_row = latest_cursor.fetchone()

                if latest_row:
                    # Update cumulative counts
                    hits += latest_row[0]
                    misses += latest_row[1]

                # Store statistics - use INSERT OR REPLACE to handle potential duplicates
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache_statistics
                        (timestamp, hits, misses, total_entries, total_size_bytes)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        # Use current time with second precision to avoid duplicates
                        datetime.now(timezone.utc).replace(microsecond=0),
                        hits,
                        misses,
                        row["count"] or 0,
                        row["size"] or 0,
                    ),
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error updating statistics: {e}")

    def _check_cache_size(self):
        """Check if the cache size exceeds the maximum and clean up if necessary."""
        try:
            # Get the config from the connection
            with self.get_connection() as conn:
                # First check the current cache size
                cursor = conn.execute("""
                    SELECT SUM(size_bytes) FROM cache_entries
                """)
                row = cursor.fetchone()
                if row and row[0]:
                    current_size_bytes = row[0]
                    # Convert max_cache_size_mb to bytes for comparison
                    max_size_bytes = self.max_cache_size_mb * 1024 * 1024

                    # If we're over the limit, clean up
                    if current_size_bytes > max_size_bytes:
                        logger.info(
                            f"Cache size ({current_size_bytes / 1024 / 1024:.2f}MB) exceeds limit "
                            f"({max_size_bytes / 1024 / 1024:.2f}MB). Cleaning up..."
                        )

                        # Delete oldest entries first, based on last_accessed
                        # Calculate how much we need to remove
                        excess_bytes = current_size_bytes - (
                            max_size_bytes * 0.8
                        )  # Remove enough to get to 80% of max

                        # Get the oldest entries up to the excess amount
                        cursor = conn.execute("""
                            SELECT key, size_bytes FROM cache_entries
                            ORDER BY last_accessed ASC
                        """)

                        entries_to_delete = []
                        bytes_to_delete = 0

                        for row in cursor:
                            entries_to_delete.append(row[0])
                            bytes_to_delete += row[1]
                            if bytes_to_delete >= excess_bytes:
                                break

                        # Delete the entries
                        if entries_to_delete:
                            placeholders = ", ".join(["?" for _ in entries_to_delete])
                            conn.execute(
                                f"""
                                DELETE FROM cache_entries
                                WHERE key IN ({placeholders})
                            """,
                                entries_to_delete,
                            )
                            conn.commit()

                            logger.info(
                                f"Removed {len(entries_to_delete)} entries "
                                f"({bytes_to_delete / 1024 / 1024:.2f}MB) from cache"
                            )
        except Exception as e:
            logger.error(f"Error checking cache size: {e}")

    def close(self):
        """Close all database connections.

        Note: This only closes connections, it does not delete the database file
        so it can be inspected after tests.
        """
        with self._lock:
            for conn in self._connection_pool.values():
                # Commit any pending transactions
                try:
                    conn.commit()
                except sqlite3.Error:
                    pass
                conn.close()
            self._connection_pool.clear()

    def delete_by_endpoint(self, endpoint: str) -> bool:
        """Delete all cache entries for a specific endpoint.

        Args:
            endpoint: The endpoint to delete entries for

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM cache_entries WHERE endpoint = ?", (endpoint,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting cache entries for endpoint {endpoint}: {e}")
            return False
