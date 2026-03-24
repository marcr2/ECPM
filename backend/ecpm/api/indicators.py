"""Indicator data API endpoints for computed Marxist economic indicators.

Provides:
- GET /api/indicators/ -- Overview with summaries for all 8 indicators
- GET /api/indicators/methodology -- Documentation for all methodologies
- GET /api/indicators/methodology/{methodology_slug} -- Docs for one methodology
- GET /api/indicators/{slug} -- Time-series data for one indicator
- GET /api/indicators/{slug}/compare -- Same indicator across all methodologies

IMPORTANT: methodology routes are defined BEFORE the dynamic {slug} routes
to prevent "methodology" from being captured as a slug parameter.

All endpoints use Redis caching with appropriate TTLs.
"""

from __future__ import annotations

import json
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.cache import build_cache_key, cache_get, cache_set
from ecpm.cache_manager import (
    get_cached_indicator,
    get_cached_overview,
    set_cached_indicator,
    set_cached_overview,
)
from ecpm.database import get_db
from ecpm.indicators.computation import compute_all_summaries, compute_indicator
from ecpm.indicators.definitions import INDICATOR_DEFS, IndicatorSlug
from ecpm.indicators.registry import MethodologyRegistry
from ecpm.schemas.indicators import (
    IndicatorDataPoint,
    IndicatorMethodologyDoc,
    IndicatorOverviewResponse,
    IndicatorResponse,
    IndicatorSummary,
    MethodologyDocResponse,
    NIPAMappingDoc,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/indicators", tags=["indicators"])

# Cache TTLs
_DATA_CACHE_TTL = 3600  # 1 hour for indicator data
_DOCS_CACHE_TTL = 86400  # 24 hours for methodology docs


def _get_redis():
    """Return the Redis client from app state, or None if unavailable."""
    from ecpm.main import _redis_pool

    return _redis_pool


def _mapper_to_doc_response(mapper) -> MethodologyDocResponse:
    """Convert a mapper's get_documentation() output to a MethodologyDocResponse."""
    indicator_docs = mapper.get_documentation()

    indicators = []
    for doc in indicator_docs:
        mappings = [
            NIPAMappingDoc(
                marx_category=m.marx_category,
                nipa_table=m.nipa_table,
                nipa_line=m.nipa_line,
                nipa_description=m.nipa_description,
                operation=m.operation,
                notes=m.notes,
            )
            for m in doc.mappings
        ]
        indicators.append(
            IndicatorMethodologyDoc(
                indicator_slug=doc.slug,
                indicator_name=doc.name,
                formula_latex=doc.formula_latex,
                interpretation=doc.interpretation,
                mappings=mappings,
                citations=doc.citations,
            )
        )

    return MethodologyDocResponse(
        methodology_slug=mapper.slug,
        methodology_name=mapper.name,
        indicators=indicators,
    )


# ---------------------------------------------------------------------------
# Overview endpoint (root)
# ---------------------------------------------------------------------------


@router.get("/", response_model=IndicatorOverviewResponse)
async def indicator_overview(
    methodology: str = Query("shaikh-tonak", description="Methodology slug"),
    db: AsyncSession = Depends(get_db),
) -> IndicatorOverviewResponse:
    """Return overview with summaries for all 8 indicators under a methodology.

    Each summary includes slug, name, units, latest value, trend, and sparkline
    data for the overview dashboard cards.
    """
    # Validate methodology exists
    try:
        MethodologyRegistry.get(methodology)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Unknown methodology: {methodology}"
        )

    # Try disk cache first (fast)
    cached_data = get_cached_overview(methodology)
    if cached_data is not None:
        logger.debug("indicators.disk_cache_hit", methodology=methodology)
        return IndicatorOverviewResponse(
            methodology=cached_data["methodology"],
            indicators=[IndicatorSummary(**s) for s in cached_data["indicators"]],
        )

    # Fallback: compute on-demand and cache to disk
    logger.info("indicators.computing_overview", methodology=methodology)
    try:
        summaries = await compute_all_summaries(methodology, db, redis=None)
    except Exception:
        logger.error(
            "indicators.overview_failed",
            methodology=methodology,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to compute indicator summaries"
        )

    response_data = {
        "methodology": methodology,
        "indicators": summaries,
    }
    set_cached_overview(methodology, response_data)

    response = IndicatorOverviewResponse(
        methodology=methodology,
        indicators=[IndicatorSummary(**s) for s in summaries],
    )

    return response


# ---------------------------------------------------------------------------
# Methodology documentation endpoints (BEFORE {slug} to avoid capture)
# ---------------------------------------------------------------------------


@router.get("/methodology", response_model=list[MethodologyDocResponse])
async def list_methodology_docs() -> list[MethodologyDocResponse]:
    """Return documentation for all registered methodologies.

    Each methodology includes its indicator definitions with LaTeX formulas,
    NIPA table/line mappings, and theoretical citations.
    """
    redis = _get_redis()
    cache_key = build_cache_key("/api/indicators/methodology/all", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("methodology.cache_hit", key=cache_key)
        return [
            MethodologyDocResponse.model_validate(item)
            for item in json.loads(cached)
        ]

    mappers = MethodologyRegistry.list_all()
    results = [_mapper_to_doc_response(mapper) for mapper in mappers]

    # Cache the response
    cached_json = json.dumps([r.model_dump(mode="json") for r in results])
    await cache_set(cache_key, cached_json, ttl=_DOCS_CACHE_TTL, redis=redis)

    return results


@router.get(
    "/methodology/{methodology_slug}", response_model=MethodologyDocResponse
)
async def get_methodology_doc(
    methodology_slug: str,
) -> MethodologyDocResponse:
    """Return documentation for a single methodology.

    Includes all indicator definitions with LaTeX formulas, NIPA table/line
    mappings, interpretation notes, and theoretical citations.
    """
    redis = _get_redis()
    cache_key = build_cache_key(
        f"/api/indicators/methodology/{methodology_slug}", {}
    )

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("methodology.cache_hit", key=cache_key)
        return MethodologyDocResponse.model_validate_json(cached)

    try:
        mapper = MethodologyRegistry.get(methodology_slug)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown methodology: {methodology_slug}",
        )

    result = _mapper_to_doc_response(mapper)

    # Cache the response
    await cache_set(
        cache_key, result.model_dump_json(), ttl=_DOCS_CACHE_TTL, redis=redis
    )

    return result


# ---------------------------------------------------------------------------
# Indicator detail and compare endpoints (dynamic {slug} AFTER static routes)
# ---------------------------------------------------------------------------


@router.get("/{slug}", response_model=IndicatorResponse)
async def indicator_detail(
    slug: str,
    methodology: str = Query("shaikh-tonak", description="Methodology slug"),
    start: Optional[str] = Query(None, description="Start date (ISO format)"),
    end: Optional[str] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
) -> IndicatorResponse:
    """Return full time-series data for one indicator under a methodology.

    Supports optional date range filtering via start/end query parameters.
    """
    # Validate indicator slug
    valid_slugs = {s.value for s in IndicatorSlug}
    if slug not in valid_slugs:
        raise HTTPException(
            status_code=404, detail=f"Unknown indicator: {slug}"
        )

    # Validate methodology
    try:
        MethodologyRegistry.get(methodology)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Unknown methodology: {methodology}"
        )

    # Try disk cache first (only if no date filters)
    if start is None and end is None:
        cached_data = get_cached_indicator(methodology, slug)
        if cached_data is not None:
            logger.debug("indicators.disk_cache_hit", methodology=methodology, slug=slug)
            return IndicatorResponse(**cached_data)

    # Fallback: compute on-demand
    logger.info("indicators.computing_detail", methodology=methodology, slug=slug)
    try:
        series = await compute_indicator(slug, methodology, db, redis=None)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception:
        logger.error(
            "indicators.detail_failed",
            slug=slug,
            methodology=methodology,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute indicator '{slug}'",
        )

    # Convert pd.Series to list of IndicatorDataPoint
    import datetime as dt
    import math

    data_points = []
    for date, value in series.items():
        # Skip NaN/None values to avoid Pydantic validation errors
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        d = date.to_pydatetime() if hasattr(date, "to_pydatetime") else date
        data_points.append(IndicatorDataPoint(date=d, value=float(value)))

    # Apply date range filtering
    if start:
        try:
            start_dt = dt.datetime.fromisoformat(start)
            data_points = [p for p in data_points if p.date >= start_dt]
        except ValueError:
            pass  # Ignore invalid date format

    if end:
        try:
            end_dt = dt.datetime.fromisoformat(end)
            data_points = [p for p in data_points if p.date <= end_dt]
        except ValueError:
            pass  # Ignore invalid date format

    # Build response
    indicator_def = INDICATOR_DEFS.get(IndicatorSlug(slug), {})

    # Get latest non-NaN value and date
    latest_value = None
    latest_date = None
    if len(data_points) > 0:
        latest_value = data_points[-1].value
        latest_date = data_points[-1].date

    response = IndicatorResponse(
        slug=slug,
        name=indicator_def.get("name", slug),
        units=indicator_def.get("units", ""),
        methodology=methodology,
        frequency="A",  # Annual frequency for NIPA-derived indicators
        data=data_points,
        latest_value=latest_value,
        latest_date=latest_date,
    )

    # Cache to disk if no date filters
    if start is None and end is None:
        indicator_data = response.model_dump(mode="json")
        set_cached_indicator(methodology, slug, indicator_data)

    return response


@router.get("/{slug}/compare")
async def indicator_compare(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> list[IndicatorResponse]:
    """Return the same indicator computed under all registered methodologies.

    Allows visual comparison of how different NIPA-to-Marx mappings affect
    the indicator trajectory.
    """
    # Validate indicator slug
    valid_slugs = {s.value for s in IndicatorSlug}
    if slug not in valid_slugs:
        raise HTTPException(
            status_code=404, detail=f"Unknown indicator: {slug}"
        )

    redis = _get_redis()
    cache_key = build_cache_key(f"/api/indicators/{slug}/compare", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("indicators.cache_hit", key=cache_key)
        return [
            IndicatorResponse.model_validate(item)
            for item in json.loads(cached)
        ]

    mappers = MethodologyRegistry.list_all()
    results: list[IndicatorResponse] = []

    indicator_def = INDICATOR_DEFS.get(IndicatorSlug(slug), {})
    import math

    for mapper in mappers:
        try:
            series = await compute_indicator(
                slug, mapper.slug, db, redis=redis
            )

            data_points = []
            for date, value in series.items():
                # Skip NaN/None values to avoid Pydantic validation errors
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    continue
                d = (
                    date.to_pydatetime()
                    if hasattr(date, "to_pydatetime")
                    else date
                )
                data_points.append(
                    IndicatorDataPoint(date=d, value=float(value))
                )

            # Get latest non-NaN value and date from filtered data_points
            latest_value = None
            latest_date = None
            if len(data_points) > 0:
                latest_value = data_points[-1].value
                latest_date = data_points[-1].date

            results.append(
                IndicatorResponse(
                    slug=slug,
                    name=indicator_def.get("name", slug),
                    units=indicator_def.get("units", ""),
                    methodology=mapper.slug,
                    frequency="A",
                    data=data_points,
                    latest_value=latest_value,
                    latest_date=latest_date,
                )
            )
        except Exception:
            logger.warning(
                "indicators.compare_failed",
                slug=slug,
                methodology=mapper.slug,
                exc_info=True,
            )

    # Cache the response
    cached_json = json.dumps([r.model_dump(mode="json") for r in results])
    await cache_set(
        cache_key, cached_json, ttl=_DATA_CACHE_TTL, redis=redis
    )

    return results
