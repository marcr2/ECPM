"""Data CRUD endpoints for series metadata and observations.

Provides:
- GET /api/data/series -- List all series with optional filters and Redis caching.
- GET /api/data/series/{series_id} -- Get series detail with observations,
  optional frequency alignment (LOCF), and Redis caching.
"""

from __future__ import annotations

import json
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.cache import build_cache_key, cache_get, cache_set
from ecpm.config import get_settings
from ecpm.database import get_db
from ecpm.models.observation import Observation
from ecpm.models.series_metadata import SeriesMetadata
from ecpm.schemas.series import (
    ObservationResponse,
    SeriesDataResponse,
    SeriesListResponse,
    SeriesMetadataResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])


def _get_redis():
    """Return the Redis client from app state, or None if unavailable."""
    from ecpm.main import _redis_pool

    return _redis_pool


@router.get("/series", response_model=SeriesListResponse)
async def list_series(
    source: Optional[str] = Query(None, description="Filter by source (FRED, BEA)"),
    frequency: Optional[str] = Query(None, description="Filter by frequency (D,M,Q,A)"),
    fetch_status: Optional[str] = Query(
        None, description="Filter by fetch status (pending, ok, error, stale)"
    ),
    search: Optional[str] = Query(None, description="Search series by name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SeriesListResponse:
    """List all series with optional filtering and pagination.

    Results are cached in Redis for 60 seconds.
    """
    redis = _get_redis()
    cache_params = {
        "source": source,
        "frequency": frequency,
        "fetch_status": fetch_status,
        "search": search,
        "limit": limit,
        "offset": offset,
    }
    cache_key = build_cache_key("/api/data/series", cache_params)

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("cache.hit", key=cache_key)
        return SeriesListResponse.model_validate_json(cached)

    # Build query
    stmt = select(SeriesMetadata)

    if source:
        stmt = stmt.where(SeriesMetadata.source == source.upper())
    if frequency:
        stmt = stmt.where(SeriesMetadata.frequency == frequency.upper())
    if fetch_status:
        stmt = stmt.where(SeriesMetadata.fetch_status == fetch_status)
    if search:
        stmt = stmt.where(SeriesMetadata.name.ilike(f"%{search}%"))

    # Count total matching
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Apply pagination
    stmt = stmt.order_by(SeriesMetadata.series_id).offset(offset).limit(limit)
    result = await db.execute(stmt)
    series_rows = result.scalars().all()

    response = SeriesListResponse(
        series=[SeriesMetadataResponse.model_validate(row) for row in series_rows],
        total=total,
    )

    # Cache the response
    settings = get_settings()
    _ = settings  # settings available for future TTL config
    await cache_set(cache_key, response.model_dump_json(), ttl=60, redis=redis)

    return response


@router.get("/series/{series_id}", response_model=SeriesDataResponse)
async def get_series(
    series_id: str,
    frequency: Optional[str] = Query(
        None, description="Align observations to frequency (M, Q, A) using LOCF"
    ),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SeriesDataResponse:
    """Get a single series with its observations.

    Supports optional frequency alignment using last-observation-carried-forward (LOCF).
    Results are cached in Redis for 300 seconds.
    """
    redis = _get_redis()
    cache_params = {
        "series_id": series_id,
        "frequency": frequency,
        "limit": limit,
        "offset": offset,
    }
    cache_key = build_cache_key(f"/api/data/series/{series_id}", cache_params)

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("cache.hit", key=cache_key)
        return SeriesDataResponse.model_validate_json(cached)

    # Fetch series metadata
    stmt = select(SeriesMetadata).where(SeriesMetadata.series_id == series_id)
    result = await db.execute(stmt)
    series = result.scalar_one_or_none()

    if series is None:
        raise HTTPException(status_code=404, detail=f"Series '{series_id}' not found")

    # Fetch observations
    obs_stmt = (
        select(Observation)
        .where(Observation.series_id == series_id)
        .order_by(Observation.observation_date)
    )

    obs_result = await db.execute(obs_stmt)
    observations = list(obs_result.scalars().all())

    # Apply LOCF frequency alignment if requested
    if frequency and observations:
        observations = _align_frequency(observations, frequency.upper())

    # Apply pagination after alignment
    total_observations = len(observations)
    observations = observations[offset : offset + limit]

    response = SeriesDataResponse(
        metadata=SeriesMetadataResponse.model_validate(series),
        observations=[ObservationResponse.model_validate(obs) for obs in observations],
        total_observations=total_observations,
    )

    # Cache for 300 seconds
    await cache_set(cache_key, response.model_dump_json(), ttl=300, redis=redis)

    return response


def _align_frequency(
    observations: list[Observation], target_frequency: str
) -> list[Observation]:
    """Align observations to a target frequency using LOCF.

    LOCF = Last Observation Carried Forward: for each target period,
    use the most recent available observation at or before that period end.

    Args:
        observations: Sorted list of Observation ORM objects.
        target_frequency: Target frequency code ("M", "Q", "A").

    Returns:
        List of observations aligned to the target frequency.
    """
    if not observations:
        return observations

    import datetime as dt

    # Map frequency to period boundaries
    freq_map = {
        "M": "month",
        "Q": "quarter",
        "A": "year",
    }

    period_type = freq_map.get(target_frequency)
    if period_type is None:
        return observations  # Unknown frequency, return unaligned

    # Group observations by period and keep last value in each period (LOCF)
    aligned: list[Observation] = []
    seen_periods: set[str] = set()

    for obs in reversed(observations):
        obs_date = obs.observation_date
        # Handle timezone-aware datetimes
        if hasattr(obs_date, "date"):
            naive_date = obs_date
        else:
            naive_date = obs_date

        if period_type == "month":
            period_key = f"{naive_date.year}-{naive_date.month:02d}"
        elif period_type == "quarter":
            quarter = (naive_date.month - 1) // 3 + 1
            period_key = f"{naive_date.year}-Q{quarter}"
        elif period_type == "year":
            period_key = f"{naive_date.year}"
        else:
            period_key = str(naive_date)

        if period_key not in seen_periods:
            seen_periods.add(period_key)
            aligned.append(obs)

    # Reverse back to chronological order
    aligned.reverse()
    return aligned
