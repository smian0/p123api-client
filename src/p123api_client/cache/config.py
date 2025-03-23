"""Cache configuration.

This module provides configuration options for the P123 API client caching system.
The cache location can be configured via the P123_CACHE_PATH environment variable.
"""
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CacheConfig:
    """Configuration for the caching system.
    
    By default, all caching is enabled with sensible defaults:
    - Cache is stored in ~/.p123cache/cache.db (or P123_CACHE_PATH env var)
    - Maximum cache size is 100MB with automatic cleanup
    - Cache statistics are enabled
    - Data refresh time is set to 3 AM Eastern (when P123 updates)
    
    For most users, no configuration is needed - just use EnhancedScreenRunAPI
    which will use these defaults automatically.
    """

    # Path to SQLite database (can be overridden with P123_CACHE_PATH env var)
    db_path: str = os.environ.get("P123_CACHE_PATH", "~/.p123cache/cache.db")
    
    # Maximum size of the cache in megabytes
    max_cache_size_mb: int = 100
    
    # When P123 updates its data (3 AM Eastern by default)
    refresh_time: str = "03:00"
    timezone: str = "US/Eastern"
    
    # These should always be enabled for best experience
    enabled: bool = True
    auto_cleanup: bool = True
    enable_statistics: bool = True

    @property
    def db_path_expanded(self) -> Path:
        """Get the expanded database path."""
        return Path(self.db_path).expanduser().resolve()

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate refresh time format
        try:
            hour, minute = map(int, self.refresh_time.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError("refresh_time must be in HH:MM format")
