"""Cache manager implementation."""

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Any

import pytz

from .config import CacheConfig
from .keys import generate_cache_key
from .storage import SQLiteStorage

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching operations and coordinates components."""

    def __init__(self, config: CacheConfig | None = None):
        """Initialize cache manager.

        Args:
            config: Optional cache configuration
        """
        self.config = config or CacheConfig()
        self.storage = SQLiteStorage(
            str(self.config.db_path_expanded), max_cache_size_mb=self.config.max_cache_size_mb
        )
        self.logger = logger

        # Initialize timezone
        self._tz = pytz.timezone(self.config.timezone)

        # Parse refresh time
        hour, minute = map(int, self.config.refresh_time.split(":"))
        self._refresh_time = time(hour=hour, minute=minute)

    def get(self, endpoint: str, params: dict[str, Any], bypass_cache: bool = False) -> Any | None:
        """Get a value from the cache.

        Args:
            endpoint: API endpoint name
            params: API call parameters
            bypass_cache: Whether to bypass the cache

        Returns:
            Cached value if found and valid, None otherwise
        """
        if not self.config.enabled or bypass_cache:
            # Track miss in SQLite if statistics are enabled
            if self.config.enable_statistics:
                self.storage.update_statistics(0, 1)
            return None

        # Generate cache key
        key = generate_cache_key(endpoint, params)

        # Get from storage
        data, metadata = self.storage.retrieve(key)
        if data is None:
            # Track miss in SQLite if statistics are enabled
            if self.config.enable_statistics:
                self.storage.update_statistics(0, 1)
            return None

        # Check if expired - ensure both datetimes have timezone info
        now = datetime.now(timezone.utc)
        expires_at = metadata["expires_at"]

        # If expires_at doesn't have timezone info, assume UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            self.storage.delete(key)
            # Track miss in SQLite if statistics are enabled
            if self.config.enable_statistics:
                self.storage.update_statistics(0, 1)
            return None

        # Track hit in SQLite if statistics are enabled
        if self.config.enable_statistics:
            self.storage.update_statistics(1, 0)

        return data

    def put(
        self, endpoint: str, params: dict[str, Any], data: Any, force_ttl: int | None = None
    ) -> bool:
        """Put a value in the cache.

        Args:
            endpoint: API endpoint name
            params: API call parameters
            data: Data to cache
            force_ttl: Optional TTL override in seconds

        Returns:
            True if storage successful
        """
        if not self.config.enabled:
            return False

        # Debug logging for troubleshooting serialization issues
        self.logger.debug(f"Caching data of type: {type(data)}")
        try:
            # Generate cache key
            key = generate_cache_key(endpoint, params)

            # Calculate expiration
            expires_at = (
                (datetime.now().astimezone(pytz.UTC) + timedelta(seconds=force_ttl))
                if force_ttl
                else self._calculate_next_refresh()
            )

            # Store data
            return self.storage.store(key, data, endpoint, expires_at)
        except Exception as e:
            self.logger.error(f"Error storing cache entry: {str(e)}")
            return False

    def _calculate_next_refresh(self) -> datetime:
        """Calculate the next P123 data refresh time.

        Returns:
            Next refresh time in UTC
        """
        now = datetime.now(self._tz)

        # Create refresh time today
        refresh = now.replace(
            hour=self._refresh_time.hour, minute=self._refresh_time.minute, second=0, microsecond=0
        )

        # If already past refresh time today, use tomorrow
        if now > refresh:
            refresh = refresh + timedelta(days=1)

        # Convert to UTC for storage
        return refresh.astimezone(pytz.UTC)

    def invalidate_endpoint(self, endpoint: str) -> bool:
        """Invalidate cache for a specific endpoint.

        Args:
            endpoint: The endpoint to invalidate

        Returns:
            True if the operation was successful
        """
        # Use the storage's delete_by_endpoint method to remove only entries for this endpoint
        return self.storage.delete_by_endpoint(endpoint)

    def invalidate_all(self) -> bool:
        """Invalidate all cached data.

        Returns:
            True if the operation was successful
        """
        result = self.storage.clear()
        return result is not None

    def force_refresh_after_update(self):
        """Force immediate refresh of all cached data.

        Call this after P123 updates to immediately invalidate the cache.
        """
        self.invalidate_all()
        self.logger.info("Cache forcibly invalidated due to P123 data update")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics from SQLite database.

        Returns:
            Dictionary of cache statistics
        """
        try:
            with self.storage.get_connection() as conn:
                # Get the latest statistics
                cursor = conn.execute("""
                    SELECT hits, misses FROM cache_statistics 
                    ORDER BY timestamp DESC LIMIT 1
                """)
                row = cursor.fetchone()

                if row:
                    hits = row[0]
                    misses = row[1]
                    hit_ratio = hits / (hits + misses) if (hits + misses) > 0 else 0
                    return {"hits": hits, "misses": misses, "hit_ratio": hit_ratio}
                else:
                    return {"hits": 0, "misses": 0, "hit_ratio": 0}
        except Exception as e:
            self.logger.error(f"Error getting cache statistics: {e}")
            return {"hits": 0, "misses": 0, "hit_ratio": 0}

    def close(self):
        """Close cache manager and release resources."""
        self.storage.close()
