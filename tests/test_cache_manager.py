"""Integration tests for cache manager."""

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
import pytz

from p123api_client.cache.config import CacheConfig
from p123api_client.cache.keys import generate_cache_key
from p123api_client.cache.manager import CacheManager


class TestCacheManager:
    """Integration tests for cache manager with real SQLite database."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        yield cache_dir
        # Clean up not needed as pytest will remove the tmp_path

    @pytest.fixture
    def cache_config(self, temp_cache_dir):
        """Create a cache configuration for testing using a temporary SQLite database."""
        return CacheConfig(
            enabled=True,
            db_path=str(temp_cache_dir / "test_cache.db"),
            refresh_time="03:00",
            timezone="US/Eastern",
            enable_statistics=True,
        )

    @pytest.fixture
    def cache_manager(self, cache_config):
        """Create a cache manager with real SQLite storage for testing."""
        manager = None
        try:
            # Create the manager with the specified config
            manager = CacheManager(config=cache_config)
            yield manager
        finally:
            # Ensure the manager is closed even if tests fail
            if manager:
                manager.close()

    def test_init_with_default_config(self, temp_cache_dir):
        """Test initialization with default configuration."""
        # Use a custom path inside our temp directory to avoid interfering with actual cache
        custom_path = str(temp_cache_dir / f"test_init_{int(time.time())}.db")

        # Initialize with default config except for db_path
        config = CacheConfig(db_path=custom_path)
        manager = CacheManager(config=config)

        # Verify initialization succeeded
        assert manager.config is not None
        assert manager.config.db_path == custom_path
        assert manager.config.enabled is True
        assert Path(custom_path).exists()

        # Cleanup
        manager.close()

    def test_store_and_retrieve(self, cache_manager):
        """Test basic storage and retrieval."""
        # Test data
        endpoint = "test_endpoint"
        params = {"param1": "value1", "param2": 123}
        test_data = {"result": "test_value", "items": [1, 2, 3]}

        # Generate the cache key manually to verify
        key = generate_cache_key(endpoint, params)

        # Store data with a far future expiration
        future = datetime.now(timezone.utc) + timedelta(days=1)

        # Store data
        result = cache_manager.put(endpoint, params, test_data, force_ttl=86400)  # 1 day TTL
        assert result is True

        # Verify storage by directly checking the database
        storage = cache_manager.storage
        conn = storage._connection_pool[threading.get_ident()]

        # Check that entry exists
        cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
        count = cursor.fetchone()[0]
        assert count == 1, "Expected one entry in the database"

        # Debug: Get the actual data from the database
        cursor = conn.execute("SELECT key, data, endpoint FROM cache_entries")
        row = cursor.fetchone()
        stored_key = row[0]
        stored_data_blob = row[1]
        stored_endpoint = row[2]

        print(f"Generated key: {key}")
        print(f"Stored key: {stored_key}")
        print(f"Stored endpoint: {stored_endpoint}")

        # Verify the key matches what we expect
        assert stored_key == key, "Stored key should match generated key"

        # Try to manually decode the data
        import pickle

        try:
            decoded_data = pickle.loads(stored_data_blob)
            print(f"Successfully decoded with pickle: {decoded_data}")
        except Exception as e:
            print(f"Failed to decode with pickle: {e}")
            try:
                decoded_data = json.loads(stored_data_blob.decode())
                print(f"Successfully decoded with JSON: {decoded_data}")
            except Exception as e:
                print(f"Failed to decode with JSON: {e}")

        # Debug: Call the SQLiteStorage.retrieve method directly
        print("\nTesting direct retrieval with SQLiteStorage:")
        try:
            direct_result = storage.retrieve(key)
            print(f"Direct retrieve result: {direct_result}")
            if isinstance(direct_result, tuple) and len(direct_result) == 2:
                data_part, meta_part = direct_result
                print(f"Data part: {data_part}")
                print(f"Metadata part: {meta_part}")
            else:
                print(
                    f"Unexpected type or length: {type(direct_result)}, length: {len(direct_result) if hasattr(direct_result, '__len__') else 'N/A'}"
                )
        except Exception as e:
            print(f"Error with direct retrieval: {e}")

        # Retrieve data
        retrieved = cache_manager.get(endpoint, params)
        assert retrieved is not None, "Retrieved data should not be None"
        assert retrieved == test_data, "Retrieved data should match original"

    def test_hit_miss_counting(self, cache_manager):
        """Test hit/miss tracking."""
        # Directly set initial stats to zero to avoid dependency on other tests
        cache_manager.hits = 0
        cache_manager.misses = 0

        endpoint = "test_endpoint"
        params1 = {"test": "value1"}
        params2 = {"test": "value2"}
        data = {"sample": "data"}

        # Test initial stats
        stats = cache_manager.get_stats()
        assert stats["hits"] == 0, "Initial hits should be zero"
        assert stats["misses"] == 0, "Initial misses should be zero"

        # First get should be a miss
        retrieved = cache_manager.get(endpoint, params1)
        assert retrieved is None, "Should be cache miss"

        # Check stats after miss
        stats = cache_manager.get_stats()
        assert stats["hits"] == 0, "Hits should still be zero"
        assert stats["misses"] == 1, "Misses should be incremented to 1"

        # Put data and then get - should be a hit
        # Store with a far future expiration
        cache_manager.put(endpoint, params1, data, force_ttl=86400)  # 1 day TTL

        # Retrieve the data - should be a hit
        retrieved = cache_manager.get(endpoint, params1)
        assert retrieved == data, "Retrieved data should match stored data"

        # Check stats after hit
        stats = cache_manager.get_stats()
        assert stats["hits"] == 1, "Hits should be incremented to 1"
        assert stats["misses"] == 1, "Misses should still be 1"

        # Different params - should be another miss
        retrieved = cache_manager.get(endpoint, params2)
        assert retrieved is None, "Should be another cache miss"

        # Check final stats
        stats = cache_manager.get_stats()
        assert stats["hits"] == 1, "Hits should still be 1"
        assert stats["misses"] == 2, "Misses should be incremented to 2"

        # Test hit ratio calculation
        assert stats["hit_ratio"] == 1 / 3, "Hit ratio should be 1/3"

    def test_cache_expiration(self, cache_manager):
        """Test cache expiration with a real TTL."""
        endpoint = "test_endpoint"
        params = {"param": "value"}
        data = {"result": "test"}

        # Store with short TTL (1 second)
        cache_manager.put(endpoint, params, data, force_ttl=1)

        # Immediate retrieval should succeed
        result = cache_manager.get(endpoint, params)
        assert result == data

        # Wait for expiration
        time.sleep(1.1)  # Wait a bit more than 1 second to ensure expiration

        # After expiration, retrieval should fail
        expired_result = cache_manager.get(endpoint, params)
        assert expired_result is None

    def test_invalidate_all(self, cache_manager):
        """Test invalidating all cache."""
        # Store multiple entries with far future expiration
        cache_manager.put("endpoint1", {"p": 1}, "data1", force_ttl=86400)
        cache_manager.put("endpoint2", {"p": 2}, "data2", force_ttl=86400)

        # Verify entries exist
        assert cache_manager.get("endpoint1", {"p": 1}) == "data1"
        assert cache_manager.get("endpoint2", {"p": 2}) == "data2"

        # Invalidate all
        assert cache_manager.invalidate_all() is True

        # Verify entries are gone
        assert cache_manager.get("endpoint1", {"p": 1}) is None
        assert cache_manager.get("endpoint2", {"p": 2}) is None

        # Stats should reflect the misses after invalidation
        stats = cache_manager.get_stats()
        assert stats["misses"] == 2  # From the two get operations after invalidation

    def test_invalidate_endpoint(self, cache_manager):
        """Test invalidating specific endpoint."""
        # Store entries for different endpoints with far future expiration
        cache_manager.put("endpoint1", {"p": 1}, "data1", force_ttl=86400)
        cache_manager.put("endpoint1", {"p": 2}, "data2", force_ttl=86400)
        cache_manager.put("endpoint2", {"p": 1}, "data3", force_ttl=86400)

        # Verify all entries exist
        assert cache_manager.get("endpoint1", {"p": 1}) == "data1"
        assert cache_manager.get("endpoint1", {"p": 2}) == "data2"
        assert cache_manager.get("endpoint2", {"p": 1}) == "data3"

        # Invalidate only endpoint1
        cache_manager.invalidate_endpoint("endpoint1")

        # Verify endpoint1 entries are gone but endpoint2 remains
        assert cache_manager.get("endpoint1", {"p": 1}) is None
        assert cache_manager.get("endpoint1", {"p": 2}) is None
        assert cache_manager.get("endpoint2", {"p": 1}) == "data3"

    def test_data_types(self, cache_manager):
        """Test with various data types."""
        endpoint = "test_endpoint"
        ttl = 86400  # 1 day TTL for all tests

        # Test string
        cache_manager.put(endpoint, {"type": "string"}, "string_value", force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "string"}) == "string_value"

        # Test dict
        dict_data = {"key1": "value1", "key2": 123, "nested": {"a": 1, "b": 2}}
        cache_manager.put(endpoint, {"type": "dict"}, dict_data, force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "dict"}) == dict_data

        # Test list
        list_data = [1, 2, "three", {"four": 4}]
        cache_manager.put(endpoint, {"type": "list"}, list_data, force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "list"}) == list_data

        # Test numeric values
        cache_manager.put(endpoint, {"type": "int"}, 12345, force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "int"}) == 12345

        cache_manager.put(endpoint, {"type": "float"}, 123.45, force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "float"}) == 123.45

        # Test boolean values
        cache_manager.put(endpoint, {"type": "bool_true"}, True, force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "bool_true"}) is True

        cache_manager.put(endpoint, {"type": "bool_false"}, False, force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "bool_false"}) is False

        # Test None value
        cache_manager.put(endpoint, {"type": "none"}, None, force_ttl=ttl)
        assert cache_manager.get(endpoint, {"type": "none"}) is None

        # Test DataFrame conversion via dict
        df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"]})
        df_dict = df.to_dict()
        cache_manager.put(endpoint, {"type": "dataframe"}, df_dict, force_ttl=ttl)
        retrieved_dict = cache_manager.get(endpoint, {"type": "dataframe"})
        retrieved_df = pd.DataFrame.from_dict(retrieved_dict)
        # Reset index to handle the string conversion issue
        retrieved_df = retrieved_df.reset_index(drop=True)
        pd.testing.assert_frame_equal(retrieved_df, df)

    def test_persistence(self, cache_config):
        """Test data survives between manager instances using real SQLite."""
        # Create first manager and store data with 1 day TTL
        manager1 = CacheManager(config=cache_config)
        manager1.put("test", {"id": 123}, "persistent data", force_ttl=86400)
        manager1.close()

        # Create second manager and verify data exists
        manager2 = CacheManager(config=cache_config)
        assert manager2.get("test", {"id": 123}) == "persistent data"
        manager2.close()

    def test_bypass_cache(self, cache_manager):
        """Test bypassing the cache."""
        endpoint = "test_endpoint"
        params = {"param": "value"}
        data = {"result": "test"}

        # Store data with 1 day TTL
        cache_manager.put(endpoint, params, data, force_ttl=86400)

        # Normal retrieval should succeed
        result1 = cache_manager.get(endpoint, params)
        assert result1 == data

        # Bypass should ignore cache
        result2 = cache_manager.get(endpoint, params, bypass_cache=True)
        assert result2 is None

        # Stats should show one hit and one miss
        stats = cache_manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_refresh_calculation(self):
        """Test next refresh time calculation."""
        # Test refresh time calculation with custom timezone
        config = CacheConfig(refresh_time="03:00", timezone="US/Eastern")

        manager = CacheManager(config=config)

        try:
            # Calculate refresh time
            refresh_time = manager._calculate_next_refresh()

            # Convert refresh_time to Eastern for comparison
            eastern = pytz.timezone("US/Eastern")
            refresh_time_eastern = refresh_time.astimezone(eastern)

            # The refresh time should be at 3 AM Eastern
            assert refresh_time_eastern.hour == 3
            assert refresh_time_eastern.minute == 0

            # It should be either today (if current time < 3 AM) or tomorrow
            now_eastern = datetime.now().astimezone(eastern)
            if now_eastern.hour < 3:
                # Should be today
                assert refresh_time_eastern.day == now_eastern.day
            else:
                # Should be tomorrow
                tomorrow = now_eastern + timedelta(days=1)
                assert refresh_time_eastern.day == tomorrow.day
        finally:
            # Clean up
            manager.close()

    def test_storage_size_limits(self, cache_config, temp_cache_dir):
        """Test storage size limits with many entries."""
        # Configure with small max cache size
        small_config = CacheConfig(
            enabled=True,
            db_path=str(temp_cache_dir / "size_test.db"),
            max_cache_size_mb=1,  # Very small cache size (1MB)
            refresh_time="03:00",
            timezone="US/Eastern",
        )

        manager = CacheManager(config=small_config)

        try:
            # Add many entries to test size limits
            for i in range(10):
                manager.put(f"endpoint{i}", {"id": i}, f"data{i}", force_ttl=86400)

            # Check that we can still retrieve the latest entries
            assert manager.get("endpoint9", {"id": 9}) == "data9"
            assert manager.get("endpoint8", {"id": 8}) == "data8"

            # Earlier entries should still be in SQLite but may have been evicted from memory cache
            # Just verify we can access them through the manager
            assert manager.get("endpoint0", {"id": 0}) == "data0"

        finally:
            manager.close()
