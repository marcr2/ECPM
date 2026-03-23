"""Tests for Redis caching -- INFR-04.

Covers cache set/get, TTL expiration, and key format conventions.
Tests are in RED state until Plan 01-04 implements caching.
"""

from __future__ import annotations

import pytest

# Import guard
try:
    from ecpm.cache import cache_get, cache_set

    _HAS_CACHE = True
except ImportError:
    _HAS_CACHE = False

pytestmark = pytest.mark.skipif(
    not _HAS_CACHE, reason="ecpm.cache not yet implemented"
)


class TestCacheSetGet:
    """cache_set stores value, cache_get retrieves it."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self, mock_redis) -> None:
        await cache_set("test-key", "test-value", redis=mock_redis)
        result = await cache_get("test-key", redis=mock_redis)
        assert result == "test-value", (
            f"cache_get should return stored value, got {result}"
        )

    @pytest.mark.asyncio
    async def test_cache_get_missing_key(self, mock_redis) -> None:
        result = await cache_get("nonexistent-key", redis=mock_redis)
        assert result is None, "cache_get for missing key should return None"

    @pytest.mark.asyncio
    async def test_cache_set_overwrites(self, mock_redis) -> None:
        await cache_set("key", "value1", redis=mock_redis)
        await cache_set("key", "value2", redis=mock_redis)
        result = await cache_get("key", redis=mock_redis)
        assert result == "value2", "cache_set should overwrite existing value"


class TestCacheTTL:
    """Cached value expires after TTL."""

    @pytest.mark.asyncio
    async def test_cache_ttl(self, mock_redis) -> None:
        await cache_set("ttl-key", "ttl-value", ttl=300, redis=mock_redis)

        # Verify the TTL was passed to Redis set command
        mock_redis.set.assert_called()

        # Check that 'ex' parameter was passed (TTL in seconds)
        call_args = mock_redis.set.call_args
        if call_args.kwargs:
            assert call_args.kwargs.get("ex") == 300, (
                "TTL should be passed as 'ex' parameter to Redis SET"
            )
        else:
            # May be passed as positional arg
            assert 300 in call_args.args, (
                "TTL of 300 should be passed to Redis SET"
            )


class TestCacheKeyFormat:
    """Cache keys follow ecpm:api:{endpoint}:{hash} pattern."""

    @pytest.mark.asyncio
    async def test_cache_key_format(self, mock_redis) -> None:
        # Use a realistic endpoint-based cache call
        try:
            from ecpm.cache import build_cache_key
        except ImportError:
            pytest.skip("build_cache_key not yet available")

        key = build_cache_key("/api/data/series", {"limit": 10, "offset": 0})

        assert key.startswith("ecpm:api:"), (
            f"Cache key should start with 'ecpm:api:', got '{key}'"
        )
        # Key should contain a hash component for parameter deduplication
        parts = key.split(":")
        assert len(parts) >= 3, (
            f"Cache key should have at least 3 colon-separated parts, got {len(parts)}"
        )
