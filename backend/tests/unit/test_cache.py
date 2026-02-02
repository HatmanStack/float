"""Unit tests for the TTL cache implementation."""

import time

import pytest

from src.utils.cache import TTLCache, music_list_cache, job_cache


@pytest.mark.unit
class TestTTLCache:
    """Test TTLCache class."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_get_returns_none_for_missing_key(self):
        """Get should return None for missing keys."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=60)

        result = cache.get("nonexistent")
        assert result is None

    def test_entry_expires_after_ttl(self):
        """Entries should expire after TTL."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=0.1)  # 100ms TTL
        cache.set("key1", "value1")

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.15)

        # Should be gone
        assert cache.get("key1") is None

    def test_overwrite_existing_key(self):
        """Setting a key that exists should overwrite it."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key1", "value2")

        assert cache.get("key1") == "value2"

    def test_delete_existing_key(self):
        """Delete should remove entry and return True."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")

        result = cache.delete("key1")

        assert result is True
        assert cache.get("key1") is None

    def test_delete_nonexistent_key(self):
        """Delete should return False for missing keys."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=60)

        result = cache.delete("nonexistent")
        assert result is False

    def test_clear_removes_all_entries(self):
        """Clear should remove all entries."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
        assert cache.size() == 0

    def test_size_returns_entry_count(self):
        """Size should return number of entries."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=60)

        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

    def test_cleanup_expired_removes_old_entries(self):
        """Cleanup should remove expired entries."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=0.1)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        time.sleep(0.15)

        # Add a fresh entry
        cache._ttl = 60  # Increase TTL for new entry
        cache.set("key3", "value3")

        # Now cleanup
        cache._ttl = 0.1  # Restore TTL for comparison
        removed = cache.cleanup_expired()

        assert removed == 2  # key1 and key2 removed
        assert cache.get("key3") == "value3"  # key3 still there

    def test_works_with_different_types(self):
        """Cache should work with various value types."""
        # List
        list_cache: TTLCache[list] = TTLCache(ttl_seconds=60)
        list_cache.set("files", ["a.mp3", "b.mp3"])
        assert list_cache.get("files") == ["a.mp3", "b.mp3"]

        # Dict
        dict_cache: TTLCache[dict] = TTLCache(ttl_seconds=60)
        dict_cache.set("config", {"timeout": 30})
        assert dict_cache.get("config") == {"timeout": 30}

        # Int
        int_cache: TTLCache[int] = TTLCache(ttl_seconds=60)
        int_cache.set("count", 42)
        assert int_cache.get("count") == 42

    def test_get_removes_expired_entry(self):
        """Getting an expired entry should remove it from cache."""
        cache: TTLCache[str] = TTLCache(ttl_seconds=0.1)
        cache.set("key1", "value1")

        time.sleep(0.15)

        # Get should return None and remove the entry
        assert cache.get("key1") is None
        # Entry should be removed from internal storage
        assert "key1" not in cache._cache


@pytest.mark.unit
class TestModuleLevelCaches:
    """Test module-level cache instances."""

    def test_music_list_cache_exists(self):
        """Music list cache should be defined."""
        assert music_list_cache is not None

    def test_job_cache_exists(self):
        """Job cache should be defined."""
        assert job_cache is not None

    def test_music_list_cache_has_appropriate_ttl(self):
        """Music list cache should have ~5 minute TTL."""
        # Music list doesn't change often
        assert music_list_cache._ttl == 300.0  # 5 minutes

    def test_job_cache_has_short_ttl(self):
        """Job cache should have short TTL to avoid stale status."""
        # Job status changes frequently
        assert job_cache._ttl == 10.0  # 10 seconds

    def test_caches_are_independent(self):
        """Module caches should not share state."""
        # Clear both
        music_list_cache.clear()
        job_cache.clear()

        # Set in one
        music_list_cache.set("test", ["a", "b"])

        # Should not appear in other
        assert job_cache.get("test") is None
        assert music_list_cache.get("test") == ["a", "b"]

        # Cleanup
        music_list_cache.clear()
