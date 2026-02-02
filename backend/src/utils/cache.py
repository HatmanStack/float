"""Simple TTL cache for Lambda warm invocation reuse.

This module provides a lightweight in-memory cache that:
- Persists within a Lambda container for warm invocations
- Automatically expires entries after a configurable TTL
- Resets on cold starts (acceptable - cache is an optimization only)

Use cases:
- Caching S3 list_objects results (music files don't change frequently)
- Caching configuration lookups
- Any repeated read-only operation within a request lifecycle
"""

import time
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Simple TTL cache that persists within Lambda container.

    This cache is designed for Lambda's execution model where:
    - Cold starts create a fresh cache (acceptable)
    - Warm invocations reuse the cache (performance benefit)
    - No cross-invocation consistency is required

    Thread Safety:
        This implementation is NOT thread-safe. For Lambda, this is fine
        because each invocation runs in a single thread. If used elsewhere,
        consider adding locks.

    Example:
        >>> cache = TTLCache[list[str]](ttl_seconds=300)
        >>> cache.set("music_files", ["track1.mp3", "track2.mp3"])
        >>> cache.get("music_files")
        ['track1.mp3', 'track2.mp3']
        >>> # After 5 minutes...
        >>> cache.get("music_files")
        None
    """

    def __init__(self, ttl_seconds: float = 300.0):
        """Initialize cache with TTL.

        Args:
            ttl_seconds: Time-to-live for cache entries. Default: 5 minutes.
        """
        self._cache: dict[str, tuple[T, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[T]:
        """Get value from cache if not expired.

        Args:
            key: Cache key to look up.

        Returns:
            Cached value if present and not expired, None otherwise.
        """
        if key in self._cache:
            value, expires_at = self._cache[key]
            if time.time() < expires_at:
                return value
            # Entry expired, remove it
            del self._cache[key]
        return None

    def set(self, key: str, value: T) -> None:
        """Set value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        self._cache[key] = (value, time.time() + self._ttl)

    def delete(self, key: str) -> bool:
        """Remove entry from cache.

        Args:
            key: Cache key to remove.

        Returns:
            True if entry was removed, False if not found.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Remove all entries from cache."""
        self._cache.clear()

    def size(self) -> int:
        """Return number of entries in cache (including expired)."""
        return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove all expired entries and return count removed."""
        now = time.time()
        expired_keys = [
            key for key, (_, expires_at) in self._cache.items() if now >= expires_at
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# =============================================================================
# Module-level cache instances
# =============================================================================
# These persist within Lambda container for warm invocations.
# Each cache has its own TTL appropriate for the data type.

# Cache for S3 music file listings (changes infrequently)
music_list_cache: TTLCache[list[str]] = TTLCache(ttl_seconds=300.0)  # 5 minutes

# Cache for job data lookups (short TTL to avoid stale status)
job_cache: TTLCache[dict] = TTLCache(ttl_seconds=10.0)  # 10 seconds
