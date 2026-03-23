"""Redis caching utilities for ECPM API endpoints.

Provides cache_get, cache_set, and build_cache_key for endpoint response caching.
Cache keys follow the pattern: ecpm:api:{endpoint}:{params_hash}
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


def build_cache_key(endpoint: str, params: dict[str, Any] | None = None) -> str:
    """Build a deterministic cache key from endpoint path and query parameters.

    Format: ecpm:api:{endpoint_slug}:{params_hash}

    Args:
        endpoint: The API endpoint path (e.g., "/api/data/series").
        params: Query parameters dict to include in the key.

    Returns:
        A Redis cache key string.
    """
    # Normalize endpoint: strip leading slash, replace / with :
    slug = endpoint.strip("/").replace("/", ":")

    if params:
        # Sort keys for deterministic hashing
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.sha256(sorted_params.encode()).hexdigest()[:12]
    else:
        params_hash = "default"

    return f"ecpm:api:{slug}:{params_hash}"


async def cache_get(key: str, redis: Any = None) -> Optional[str]:
    """Retrieve a cached value from Redis.

    Args:
        key: The cache key.
        redis: Redis client instance.

    Returns:
        Cached string value, or None if not found or Redis unavailable.
    """
    if redis is None:
        return None

    try:
        return await redis.get(key)
    except Exception:
        logger.warning("cache.get_failed", key=key, exc_info=True)
        return None


async def cache_set(
    key: str,
    value: str,
    ttl: int = 60,
    redis: Any = None,
) -> None:
    """Store a value in Redis cache with a TTL.

    Args:
        key: The cache key.
        value: The string value to cache.
        ttl: Time-to-live in seconds (default 60).
        redis: Redis client instance.
    """
    if redis is None:
        return

    try:
        await redis.set(key, value, ex=ttl)
    except Exception:
        logger.warning("cache.set_failed", key=key, exc_info=True)
