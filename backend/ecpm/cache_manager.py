"""Disk-based cache manager for computed indicators.

Stores indicator computation results as JSON files on disk, with daily refresh.
This avoids recomputing expensive operations on every request.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Cache directory path (configurable via env var)
CACHE_DIR = Path("/app/cache/indicators")

# Cache file TTL in hours (default: 24 hours for daily refresh)
CACHE_TTL_HOURS = 24


def _get_cache_path(methodology: str, slug: str | None = None) -> Path:
    """Get the cache file path for a given methodology and optional indicator slug.

    Args:
        methodology: Methodology slug (e.g., 'shaikh-tonak')
        slug: Optional indicator slug. If None, returns overview cache path.

    Returns:
        Path to the cache file.
    """
    cache_dir = CACHE_DIR / methodology
    cache_dir.mkdir(parents=True, exist_ok=True)

    if slug is None:
        return cache_dir / "_overview.json"
    return cache_dir / f"{slug}.json"


def _is_cache_valid(cache_path: Path) -> bool:
    """Check if a cache file exists and is still valid (within TTL).

    Args:
        cache_path: Path to the cache file.

    Returns:
        True if cache exists and is valid, False otherwise.
    """
    if not cache_path.exists():
        return False

    try:
        with cache_path.open("r") as f:
            data = json.load(f)
            cached_at_str = data.get("cached_at")
            if not cached_at_str:
                return False

            cached_at = datetime.fromisoformat(cached_at_str)
            now = datetime.now(timezone.utc)
            age_hours = (now - cached_at).total_seconds() / 3600

            is_valid = age_hours < CACHE_TTL_HOURS
            if not is_valid:
                logger.debug(
                    "cache.expired",
                    path=str(cache_path),
                    age_hours=age_hours,
                    ttl_hours=CACHE_TTL_HOURS,
                )
            return is_valid
    except Exception as e:
        logger.warning("cache.validation_failed", path=str(cache_path), error=str(e))
        return False


def get_cached_indicator(methodology: str, slug: str) -> dict[str, Any] | None:
    """Retrieve a cached indicator from disk.

    Args:
        methodology: Methodology slug.
        slug: Indicator slug.

    Returns:
        Cached indicator data dict, or None if cache miss/invalid.
    """
    cache_path = _get_cache_path(methodology, slug)

    if not _is_cache_valid(cache_path):
        return None

    try:
        with cache_path.open("r") as f:
            data = json.load(f)
            logger.debug("cache.hit", methodology=methodology, slug=slug)
            return data.get("data")
    except Exception as e:
        logger.warning(
            "cache.read_failed",
            methodology=methodology,
            slug=slug,
            error=str(e),
        )
        return None


def set_cached_indicator(methodology: str, slug: str, data: dict[str, Any]) -> None:
    """Store computed indicator data to disk cache.

    Args:
        methodology: Methodology slug.
        slug: Indicator slug.
        data: Indicator data to cache (will be wrapped with metadata).
    """
    cache_path = _get_cache_path(methodology, slug)

    cache_entry = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "methodology": methodology,
        "slug": slug,
        "data": data,
    }

    try:
        with cache_path.open("w") as f:
            json.dump(cache_entry, f, indent=2)
        logger.debug("cache.write", methodology=methodology, slug=slug)
    except Exception as e:
        logger.error(
            "cache.write_failed",
            methodology=methodology,
            slug=slug,
            error=str(e),
        )


def get_cached_overview(methodology: str) -> dict[str, Any] | None:
    """Retrieve cached overview data from disk.

    Args:
        methodology: Methodology slug.

    Returns:
        Cached overview data dict, or None if cache miss/invalid.
    """
    cache_path = _get_cache_path(methodology, slug=None)

    if not _is_cache_valid(cache_path):
        return None

    try:
        with cache_path.open("r") as f:
            data = json.load(f)
            logger.debug("cache.hit", methodology=methodology, type="overview")
            return data.get("data")
    except Exception as e:
        logger.warning(
            "cache.read_failed",
            methodology=methodology,
            type="overview",
            error=str(e),
        )
        return None


def set_cached_overview(methodology: str, data: dict[str, Any]) -> None:
    """Store computed overview data to disk cache.

    Args:
        methodology: Methodology slug.
        data: Overview data to cache.
    """
    cache_path = _get_cache_path(methodology, slug=None)

    cache_entry = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "methodology": methodology,
        "type": "overview",
        "data": data,
    }

    try:
        with cache_path.open("w") as f:
            json.dump(cache_entry, f, indent=2)
        logger.debug("cache.write", methodology=methodology, type="overview")
    except Exception as e:
        logger.error(
            "cache.write_failed",
            methodology=methodology,
            type="overview",
            error=str(e),
        )


def invalidate_cache(methodology: str | None = None, slug: str | None = None) -> int:
    """Invalidate (delete) cached files.

    Args:
        methodology: Optional methodology to invalidate. If None, invalidates all.
        slug: Optional indicator slug. If None, invalidates all indicators for methodology.

    Returns:
        Number of cache files deleted.
    """
    count = 0

    if methodology is None:
        # Invalidate all
        for cache_file in CACHE_DIR.rglob("*.json"):
            cache_file.unlink()
            count += 1
    elif slug is None:
        # Invalidate all for methodology
        methodology_dir = CACHE_DIR / methodology
        if methodology_dir.exists():
            for cache_file in methodology_dir.glob("*.json"):
                cache_file.unlink()
                count += 1
    else:
        # Invalidate specific indicator
        cache_path = _get_cache_path(methodology, slug)
        if cache_path.exists():
            cache_path.unlink()
            count += 1

    logger.info(
        "cache.invalidated",
        methodology=methodology,
        slug=slug,
        files_deleted=count,
    )
    return count
