"""Consolidated tests for cache functionality in the P123 API client."""

import os
import pickle
import tempfile
from datetime import datetime, timedelta

import pandas as pd
import pytest

from p123api_client.cache.simple_storage import SimpleStorage
from p123api_client.cache.storage import SQLiteStorage


class TestSimpleStorage:
    """Tests for the SimpleStorage implementation."""

    @pytest.fixture
    def storage(self):
        """Create a storage instance with a temporary database."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_cache.db")
            storage = SimpleStorage(db_path)
            yield storage
            storage.close()

    def test_store_and_retrieve(self, storage):
        """Test basic storage and retrieval operations."""
        # Test data
        key = "test-key"
        endpoint = "test-endpoint"
        data = {"name": "test", "value": 123}
        expires_at = datetime.now() + timedelta(hours=1)

        # Store the data
        result = storage.store(key, data, endpoint, expires_at)
        assert result is True

        # Retrieve the data
        retrieved_data, metadata = storage.retrieve(key)

        # Verify the data
        assert retrieved_data == data
        assert metadata["endpoint"] == endpoint
        assert metadata["access_count"] == 1
        assert isinstance(metadata["created_at"], datetime)
        assert isinstance(metadata["expires_at"], datetime)

    def test_expiration(self, storage):
        """Test that entries expire correctly."""
        key = "expiring-key"
        endpoint = "test-endpoint"
        data = {"status": "temporary"}

        # Set to expire in 1 second
        expires_at = datetime.now() + timedelta(seconds=1)

        # Store the data
        storage.store(key, data, endpoint, expires_at)

        # Immediate retrieval should work
        retrieved, _ = storage.retrieve(key)
        assert retrieved == data

        # Wait for expiration
        import time

        time.sleep(2)

        # Check that it's automatically removed on retrieval
        data_after_expiry, metadata_after_expiry = storage.retrieve(key)
        assert data_after_expiry is None
        assert metadata_after_expiry is None

    def test_delete_and_clear(self, storage):
        """Test deleting entries and clearing the cache."""
        # Store multiple entries
        storage.store("key1", {"data": 1}, "endpoint", datetime.now() + timedelta(hours=1))
        storage.store("key2", {"data": 2}, "endpoint", datetime.now() + timedelta(hours=1))

        # Verify they exist
        data1, _ = storage.retrieve("key1")
        data2, _ = storage.retrieve("key2")
        assert data1 == {"data": 1}
        assert data2 == {"data": 2}

        # Delete one entry
        result = storage.delete("key1")
        assert result is True

        # Verify it's gone, but the other remains
        data1_after, _ = storage.retrieve("key1")
        data2_after, _ = storage.retrieve("key2")
        assert data1_after is None
        assert data2_after == {"data": 2}

        # Clear all entries
        result = storage.clear()
        assert result is True

        # Verify all entries are gone
        data2_after_clear, _ = storage.retrieve("key2")
        assert data2_after_clear is None

    def test_endpoint_operations(self, storage):
        """Test endpoint-based operations."""
        # Store entries for different endpoints
        storage.store("key1", {"data": 1}, "endpoint1", datetime.now() + timedelta(hours=1))
        storage.store("key2", {"data": 2}, "endpoint1", datetime.now() + timedelta(hours=1))
        storage.store("key3", {"data": 3}, "endpoint2", datetime.now() + timedelta(hours=1))

        # Clear endpoint1
        removed = storage.clear_endpoint("endpoint1")
        assert removed == 2

        # Verify endpoint1 entries are gone, endpoint2 remains
        data1, _ = storage.retrieve("key1")
        data2, _ = storage.retrieve("key2")
        data3, _ = storage.retrieve("key3")
        assert data1 is None
        assert data2 is None
        assert data3 == {"data": 3}

    def test_dataframe(self, storage):
        """Test storing and retrieving pandas DataFrame."""
        key = "dataframe"
        endpoint = "dataframe-test"

        # Create a test DataFrame
        df = pd.DataFrame({"A": [1, 2, 3], "B": ["a", "b", "c"], "C": [1.1, 2.2, 3.3]})

        # Store DataFrame
        expires_at = datetime.now() + timedelta(hours=1)
        storage.store(key, df, endpoint, expires_at)

        # Retrieve DataFrame
        retrieved, metadata = storage.retrieve(key)

        # Verify it's a DataFrame
        assert isinstance(retrieved, pd.DataFrame)

        # Verify all columns are present
        assert set(retrieved.columns) == set(df.columns)

        # Verify data values match
        for col in df.columns:
            assert retrieved[col].tolist() == df[col].tolist()


# Core tests we want to keep for the SQLiteStorage class
# to ensure it works with the main cache manager
class TestSQLiteStorage:
    """Essential integration tests for SQLiteStorage."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create a SQLiteStorage instance for testing."""
        db_path = tmp_path / "test_storage.db"
        storage = SQLiteStorage(str(db_path))

        # Debug print the path
        print(f"\nUsing SQLiteStorage with path: {db_path}")

        yield storage
        storage.close()

    def test_basic_operations(self, storage):
        """Test basic operations like store, retrieve, and delete."""
        # Test data
        key = "test-key"
        data = {"name": "test", "value": 123}
        endpoint = "test-endpoint"
        expires_at = datetime.now() + timedelta(hours=1)

        # Test storing data
        result = storage.store(key, data, endpoint, expires_at)
        assert result is True

        # Manually verify data in the database using SQL
        with storage.get_connection() as conn:
            cursor = conn.execute(
                "SELECT key, data, endpoint FROM cache_entries WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            assert row is not None, "Row should exist in database"

        # Test retrieval
        retrieved, metadata = storage.retrieve(key)
        assert retrieved is not None
        assert metadata is not None
        assert retrieved == data
        assert metadata["endpoint"] == endpoint

        # Test deletion
        storage.delete(key)
        retrieved, metadata = storage.retrieve(key)
        assert retrieved is None
        assert metadata is None

    def test_expired_entries(self, storage):
        """Test expired entries are removed correctly."""
        # Create timestamps for testing
        now = datetime.now()
        expired_time = now - timedelta(hours=1)

        # Store an expired entry using direct SQL
        key = "expired-key"
        data = {"status": "expired"}
        endpoint = "test-endpoint"
        serialized = pickle.dumps(data)

        with storage.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cache_entries 
                (key, data, endpoint, created_at, expires_at, size_bytes, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    key,
                    serialized,
                    endpoint,
                    now,
                    expired_time,  # This is the key - setting an expired timestamp
                    len(serialized),
                    0,
                    None,
                ),
            )
            conn.commit()

            # Verify entry exists
            cursor = conn.execute("SELECT key FROM cache_entries WHERE key = ?", (key,))
            row = cursor.fetchone()
            assert row is not None

        # Remove expired entries
        removed = storage.remove_expired(now)
        assert removed >= 1

        # Verify entry no longer exists
        with storage.get_connection() as conn:
            cursor = conn.execute("SELECT key FROM cache_entries WHERE key = ?", (key,))
            row = cursor.fetchone()
            assert row is None
