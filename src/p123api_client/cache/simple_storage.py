"""Simple SQLite storage backend for caching.

This is a streamlined version of the SQLite storage that focuses on simplicity and performance.
It uses SQLite as the sole storage mechanism without any in-memory caching layer.
"""

import io
import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class SimpleStorage:
    """A simplified SQLite-based storage backend for caching."""

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

        # Ensure parent directory exists
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
                    data TEXT NOT NULL,  -- Using TEXT instead of BLOB for better inspection
                    endpoint TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    size_bytes INTEGER NOT NULL
                );
                
                -- Create indexes for efficient lookups
                CREATE INDEX IF NOT EXISTS idx_endpoint 
                    ON cache_entries(endpoint);
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                    ON cache_entries(expires_at);
                CREATE INDEX IF NOT EXISTS idx_last_accessed
                    ON cache_entries(last_accessed);
                
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
                # Important: Set row_factory to use dictionary access
                conn.row_factory = sqlite3.Row

                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Use WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode = WAL")

                # Set busy timeout
                conn.execute("PRAGMA busy_timeout = 5000")

                self._connection_pool[thread_id] = conn

            try:
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
            # Handle pandas DataFrame
            if isinstance(data, pd.DataFrame):
                # Store DataFrame with metadata flag
                serialized = json.dumps({"__pd_dataframe__": True, "data": data.to_json()})
            else:
                # Regular JSON serialization
                serialized = json.dumps(data)

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
                        datetime.now().isoformat(),
                        expires_at.isoformat(),
                        len(serialized),
                    ),
                )

                conn.commit()
                # Ensure changes are visible to other connections
                conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
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
                # First check if the key exists and if it's expired (optimization)
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

                # Check expiration
                try:
                    expires_at = datetime.fromisoformat(expiry_row["expires_at"])
                    now = datetime.now()

                    # Ensure consistent timezone handling
                    # If expires_at has timezone info but now doesn't
                    if expires_at.tzinfo is not None and now.tzinfo is None:
                        now = now.replace(tzinfo=expires_at.tzinfo)
                    # If now has timezone info but expires_at doesn't
                    elif now.tzinfo is not None and expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=now.tzinfo)

                    if expires_at < now:
                        # Expired entry - delete it
                        self.delete(key)
                        return None, None
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing expiration date: {e}")
                    return None, None

                # Now get the full data since we know it's valid
                cursor = conn.execute(
                    """
                    SELECT data, endpoint, created_at, expires_at,
                           access_count, last_accessed, size_bytes
                    FROM cache_entries WHERE key = ?
                """,
                    (key,),
                )

                # Fetch the row
                row = cursor.fetchone()
                if not row:
                    return None, None

                # Extract data
                try:
                    data_str = row["data"]
                    endpoint = row["endpoint"]
                    created_at_str = row["created_at"]
                    expires_at_str = row["expires_at"]
                    access_count = row["access_count"] or 0
                    last_accessed_str = row["last_accessed"]
                except (KeyError, IndexError) as e:
                    logger.error(f"Error accessing row data: {e}, row keys: {list(row.keys())}")
                    return None, None

                # Update access statistics
                now = datetime.now()
                access_count += 1
                conn.execute(
                    """
                    UPDATE cache_entries 
                    SET access_count = ?, last_accessed = ?
                    WHERE key = ?
                """,
                    (access_count, now.isoformat(), key),
                )
                conn.commit()

                # Deserialize data
                try:
                    # Parse JSON data
                    parsed = json.loads(data_str)

                    # Check if this is a DataFrame
                    if isinstance(parsed, dict) and parsed.get("__pd_dataframe__"):
                        # It's a DataFrame - use StringIO to avoid the warning
                        df_data = parsed["data"]
                        deserialized = pd.read_json(io.StringIO(df_data))
                    else:
                        # Regular JSON data
                        deserialized = parsed

                except Exception as e:
                    logger.error(f"Error deserializing data: {e}")
                    return None, None

                # Parse datetime strings
                try:
                    created_dt = datetime.fromisoformat(created_at_str) if created_at_str else None
                    expires_dt = datetime.fromisoformat(expires_at_str) if expires_at_str else None
                    last_accessed_dt = (
                        datetime.fromisoformat(last_accessed_str) if last_accessed_str else None
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing datetime: {e}")
                    created_dt = None
                    expires_dt = None
                    last_accessed_dt = None

                # Build metadata
                metadata = {
                    "endpoint": endpoint,
                    "created_at": created_dt,
                    "expires_at": expires_dt,
                    "access_count": access_count,
                    "last_accessed": last_accessed_dt,
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
                    (before.isoformat(),),
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error removing expired entries: {e}")
            return 0

    def clear_endpoint(self, endpoint: str) -> int:
        """Clear cache entries for a specific endpoint.

        Args:
            endpoint: API endpoint to clear

        Returns:
            Number of entries removed
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM cache_entries
                    WHERE endpoint = ?
                """,
                    (endpoint,),
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error clearing endpoint: {e}")
            return 0

    def _check_cache_size(self):
        """Check if the cache size exceeds the maximum and clean up if necessary."""
        try:
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
        """Close all database connections."""
        with self._lock:
            for conn in self._connection_pool.values():
                # Commit any pending transactions
                try:
                    conn.commit()
                except sqlite3.Error:
                    pass
                conn.close()
            self._connection_pool.clear()
