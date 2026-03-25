"""Concentration analysis API endpoints.

Provides:
- GET /api/concentration/industries -- List industries with concentration metrics
- GET /api/concentration/industry/{naics_code}/history -- Concentration time series
- GET /api/concentration/industry/{naics_code}/firms/{year} -- Top firms by market share
- GET /api/concentration/correlations/{naics_code} -- Indicator correlations
- GET /api/concentration/top-correlations -- Top industry-indicator pairs (or full matrix)
- GET /api/concentration/overview -- Department-level overview
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

import pandas as pd
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.middleware.rate_limit import RATE_READ, limiter

from ecpm.cache import build_cache_key, cache_get, cache_set
from ecpm.concentration import (
    classify_concentration_level,
    compute_trend,
    aggregate_by_department,
)
from ecpm.database import get_db
from ecpm.models.concentration import (
    IndustryConcentration,
    FirmMarketShare,
    ConcentrationTrend,
)
from ecpm.schemas.concentration import (
    ConcentrationDataPoint,
    ConcentrationHistoryResponse,
    CorrelationInfo,
    CorrelationsResponse,
    DeptConcentration,
    FirmInfo,
    FirmsResponse,
    IndustriesResponse,
    IndustryListItem,
    OverviewResponse,
    TopCorrelationItem,
    TopCorrelationsResponse,
    TrendInfo,
)

logger = structlog.get_logger(__name__)


def _latest_trend_by_naics(trends: list[ConcentrationTrend]) -> dict[str, ConcentrationTrend]:
    """Resolve one trend row per NAICS (table has composite PK naics_code + start_year)."""
    by_naics: dict[str, ConcentrationTrend] = {}
    for t in trends:
        prev = by_naics.get(t.naics_code)
        if prev is None or t.end_year > prev.end_year:
            by_naics[t.naics_code] = t
    return by_naics


def _cr4_history_by_naics(rows: list[IndustryConcentration]) -> dict[str, list[tuple[int, float]]]:
    """All (year, cr4) points per NAICS, ascending by year."""
    hist: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for row in rows:
        hist[row.naics_code].append((row.year, row.cr4))
    for pts in hist.values():
        pts.sort(key=lambda p: p[0])
    return hist


def _trend_direction_and_slope(
    naics: str,
    trend_row: Optional[ConcentrationTrend],
    cr4_history: dict[str, list[tuple[int, float]]],
) -> tuple[str, Optional[float]]:
    """Prefer persisted trend; otherwise linear fit on CR4 history (same as ingestion)."""
    if trend_row is not None:
        return trend_row.trend_direction, trend_row.trend_slope
    pts = cr4_history.get(naics, [])
    if len(pts) < 2:
        return "stable", None
    years = pd.Series([p[0] for p in pts])
    cr4s = pd.Series([p[1] for p in pts])
    tr = compute_trend(cr4s, years)
    return tr["direction"], tr["slope"]

router = APIRouter(prefix="/api/concentration", tags=["concentration"])

# Cache TTLs
_INDUSTRIES_CACHE_TTL = 3600  # 1 hour
_HISTORY_CACHE_TTL = 86400  # 24 hours
_FIRMS_CACHE_TTL = 86400  # 24 hours
_CORRELATIONS_CACHE_TTL = 3600  # 1 hour
_OVERVIEW_CACHE_TTL = 3600  # 1 hour

# Indicator name mapping
INDICATOR_NAMES = {
    "rate-of-profit": "Rate of Profit",
    "occ": "Organic Composition of Capital",
    "rate-of-surplus-value": "Rate of Surplus Value",
    "mass-of-profit": "Mass of Profit",
    "productivity-wage-gap": "Productivity-Wage Gap",
    "credit-gdp-gap": "Credit-to-GDP Gap",
    "financial-real-ratio": "Financial-to-Real Asset Ratio",
    "debt-service-ratio": "Corporate Debt Service Ratio",
}


def _get_redis():
    """Return the Redis client from app state, or None if unavailable."""
    try:
        from ecpm.main import _redis_pool
        return _redis_pool
    except (ImportError, AttributeError):
        return None


async def _load_indicator_annual_series(
    db: AsyncSession,
) -> dict[str, pd.Series]:
    """Load all 8 crisis indicator time series as annual averages.

    Computes each indicator via the computation orchestrator, then
    resamples to annual frequency for correlation with concentration data.

    Returns:
        Dict mapping indicator slug (hyphenated) to pd.Series indexed by year.
    """
    from ecpm.indicators.computation import compute_indicator
    from ecpm.indicators.definitions import IndicatorSlug

    # Default methodology
    methodology = "shaikh-tonak"

    indicator_data: dict[str, pd.Series] = {}

    for slug_enum in IndicatorSlug:
        slug_value = slug_enum.value  # e.g., "rate_of_profit"
        # The INDICATOR_NAMES dict uses hyphenated slugs
        hyphenated = slug_value.replace("_", "-")

        try:
            series = await compute_indicator(slug_value, methodology, db, redis=None)
            if series.empty:
                indicator_data[hyphenated] = pd.Series(dtype=float)
                continue

            s = series.dropna()
            if not isinstance(s.index, pd.DatetimeIndex):
                s = s.copy()
                s.index = pd.to_datetime(s.index, errors="coerce")
                s = s[s.index.notna()]
            if s.empty:
                indicator_data[hyphenated] = pd.Series(dtype=float)
                continue
            s = s.sort_index()
            # Calendar-year mean (matches integer ``year`` on concentration rows;
            # resample("YE") labels can mis-align with census / fiscal years).
            annual = s.groupby(s.index.year, sort=True).mean()
            annual.index = pd.to_datetime(annual.index.astype(str), format="%Y")
            indicator_data[hyphenated] = annual
        except Exception:
            logger.warning(
                "concentration.indicator_load_failed",
                slug=slug_value,
                exc_info=True,
            )
            indicator_data[hyphenated] = pd.Series(dtype=float)

    return indicator_data


@router.get("/industries", response_model=IndustriesResponse)
@limiter.limit(RATE_READ)
async def get_industries(
    request: Request,
    department: Optional[str] = Query(
        None,
        description="Filter by department: 'I' or 'II'",
    ),
    db: AsyncSession = Depends(get_db),
) -> IndustriesResponse:
    """List industries with latest concentration metrics.

    Optionally filter by Marxist department classification.
    """
    redis = _get_redis()
    # v2: includes trend_slope + avoids stale cache missing that field
    cache_key = build_cache_key("concentration/industries/v2", {"dept": department})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("concentration.industries.cache_hit", key=cache_key)
        return IndustriesResponse.model_validate_json(cached)

    # Query latest concentration data for each industry
    # Get the most recent year's data
    stmt = select(IndustryConcentration).order_by(
        IndustryConcentration.naics_code,
        IndustryConcentration.year.desc(),
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    if not rows:
        # Return placeholder data if no data in DB
        response = IndustriesResponse(industries=[])
        return response

    # Group by industry and take most recent year
    latest_by_industry: dict[str, IndustryConcentration] = {}
    for row in rows:
        if row.naics_code not in latest_by_industry:
            latest_by_industry[row.naics_code] = row

    cr4_history = _cr4_history_by_naics(rows)

    trends_stmt = select(ConcentrationTrend)
    trends_result = await db.execute(trends_stmt)
    trends_by_naics = _latest_trend_by_naics(list(trends_result.scalars().all()))

    # Build response
    industries = []
    for naics, conc in latest_by_industry.items():
        level = classify_concentration_level(conc.cr4, conc.hhi)
        trend_direction, trend_slope = _trend_direction_and_slope(
            naics, trends_by_naics.get(naics), cr4_history
        )

        # Filter by department if specified
        if department:
            from ecpm.structural.departments import DEPT_I_CODES
            is_dept_i = naics in DEPT_I_CODES or any(
                naics.startswith(p) for p in DEPT_I_CODES
            )
            if department.upper() == "I" and not is_dept_i:
                continue
            if department.upper() == "II" and is_dept_i:
                continue

        industries.append(IndustryListItem(
            naics=naics,
            name=conc.naics_name or naics,
            cr4=conc.cr4,
            hhi=conc.hhi,
            level=level,
            trend_direction=trend_direction,
            trend_slope=trend_slope,
            data_source=getattr(conc, "data_source", None),
        ))

    response = IndustriesResponse(industries=industries)

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_INDUSTRIES_CACHE_TTL, redis=redis
    )

    return response


@router.get("/industry/{naics_code}/history", response_model=ConcentrationHistoryResponse)
@limiter.limit(RATE_READ)
async def get_industry_history(
    request: Request,
    naics_code: str,
    db: AsyncSession = Depends(get_db),
) -> ConcentrationHistoryResponse:
    """Get concentration history time series for an industry.

    Returns CR4, CR8, HHI values from 1997-2022 with trend analysis.
    """
    redis = _get_redis()
    cache_key = build_cache_key(f"concentration/history/{naics_code}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("concentration.history.cache_hit", key=cache_key)
        return ConcentrationHistoryResponse.model_validate_json(cached)

    # Query historical data
    stmt = select(IndustryConcentration).where(
        IndustryConcentration.naics_code == naics_code
    ).order_by(IndustryConcentration.year)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No concentration data for industry {naics_code}",
        )

    # Build data points
    data_points = [
        ConcentrationDataPoint(
            year=row.year,
            cr4=row.cr4,
            cr8=row.cr8,
            hhi=row.hhi,
        )
        for row in rows
    ]

    # Compute trend
    concentration_series = pd.Series([row.cr4 for row in rows])
    years_series = pd.Series([row.year for row in rows])
    trend_result = compute_trend(concentration_series, years_series)

    response = ConcentrationHistoryResponse(
        naics=naics_code,
        name=rows[0].naics_name or naics_code,
        data=data_points,
        trend=TrendInfo(
            slope=trend_result["slope"],
            direction=trend_result["direction"],
            r_squared=trend_result["r_squared"],
        ),
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_HISTORY_CACHE_TTL, redis=redis
    )

    return response


@router.get("/industry/{naics_code}/firms/{year}", response_model=FirmsResponse)
@limiter.limit(RATE_READ)
async def get_firms(
    request: Request,
    naics_code: str,
    year: int,
    db: AsyncSession = Depends(get_db),
) -> FirmsResponse:
    """Get top firms by market share for an industry and year."""
    redis = _get_redis()
    cache_key = build_cache_key(f"concentration/firms/{naics_code}/{year}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("concentration.firms.cache_hit", key=cache_key)
        return FirmsResponse.model_validate_json(cached)

    # Query firm data
    stmt = select(FirmMarketShare).where(
        FirmMarketShare.naics_code == naics_code,
        FirmMarketShare.year == year,
    ).order_by(FirmMarketShare.rank)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No firm data for {naics_code} in {year}",
        )

    firms = [
        FirmInfo(
            rank=row.rank,
            name=row.firm_name,
            parent=row.parent_company,
            market_share=row.market_share_pct,
            revenue=row.revenue,
        )
        for row in rows
    ]

    response = FirmsResponse(
        naics=naics_code,
        year=year,
        firms=firms,
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_FIRMS_CACHE_TTL, redis=redis
    )

    return response


@router.get("/correlations/{naics_code}", response_model=CorrelationsResponse)
@limiter.limit(RATE_READ)
async def get_correlations(
    request: Request,
    naics_code: str,
    min_confidence: float = Query(50, description="Minimum confidence threshold"),
    db: AsyncSession = Depends(get_db),
) -> CorrelationsResponse:
    """Get correlations between industry concentration and crisis indicators."""
    redis = _get_redis()
    cache_key = build_cache_key(
        f"concentration/correlations/{naics_code}",
        {"min_conf": min_confidence},
    )

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("concentration.correlations.cache_hit", key=cache_key)
        return CorrelationsResponse.model_validate_json(cached)

    # Get concentration history
    stmt = select(IndustryConcentration).where(
        IndustryConcentration.naics_code == naics_code
    ).order_by(IndustryConcentration.year)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No concentration data for industry {naics_code}",
        )

    industry_name = rows[0].naics_name or naics_code

    # Build concentration DataFrame
    conc_df = pd.DataFrame([
        {"year": row.year, "cr4": row.cr4, "hhi": row.hhi}
        for row in rows
    ])

    # Load real indicator time series and compute correlations
    indicator_data = await _load_indicator_annual_series(db)

    from ecpm.concentration import map_concentration_to_indicators

    raw_correlations = map_concentration_to_indicators(
        concentration_data=conc_df,
        indicator_data=indicator_data,
        naics_code=naics_code,
    )

    correlations = []
    for corr in raw_correlations:
        slug = corr["indicator_slug"]
        name = INDICATOR_NAMES.get(slug, slug)
        correlations.append(CorrelationInfo(
            indicator_slug=slug,
            indicator_name=name,
            correlation=corr["correlation"],
            confidence=corr["confidence"],
            lag_months=corr["lag_months"],
            relationship=corr["relationship"],
        ))

    correlations = [c for c in correlations if c.confidence >= min_confidence]

    response = CorrelationsResponse(
        naics=naics_code,
        name=industry_name,
        correlations=correlations,
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_CORRELATIONS_CACHE_TTL, redis=redis
    )

    return response


@router.get("/top-correlations", response_model=TopCorrelationsResponse)
@limiter.limit(RATE_READ)
async def get_top_correlations(
    request: Request,
    min_confidence: float = Query(
        25,
        description="Minimum confidence threshold (annual panels use a short-series score)",
    ),
    full_matrix: bool = Query(
        False,
        description=(
            "If true, return all industry×indicator pairs meeting min_confidence "
            "(for overview heatmaps). If false, return only the top 20 pairs by confidence."
        ),
    ),
    db: AsyncSession = Depends(get_db),
) -> TopCorrelationsResponse:
    """Get top industry-indicator correlations, or the full matrix for heatmaps."""
    redis = _get_redis()
    cache_key = build_cache_key(
        "concentration/top-correlations",
        {"min_conf": min_confidence, "full": full_matrix},
    )

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("concentration.top-correlations.cache_hit", key=cache_key)
        return TopCorrelationsResponse.model_validate_json(cached)

    # Load all concentration data
    stmt = select(IndustryConcentration).order_by(
        IndustryConcentration.naics_code,
        IndustryConcentration.year,
    )
    result = await db.execute(stmt)
    all_rows = result.scalars().all()

    if not all_rows:
        response = TopCorrelationsResponse(correlations=[])
        await cache_set(
            cache_key, response.model_dump_json(), ttl=_CORRELATIONS_CACHE_TTL, redis=redis
        )
        return response

    # Build DataFrame for all industries
    all_df = pd.DataFrame([
        {
            "naics_code": r.naics_code,
            "naics_name": r.naics_name or r.naics_code,
            "year": r.year,
            "cr4": r.cr4,
            "hhi": r.hhi,
        }
        for r in all_rows
    ])

    # Load indicator data
    indicator_data = await _load_indicator_annual_series(db)

    from ecpm.concentration import find_strongest_correlations

    top_df = find_strongest_correlations(
        concentration_data=all_df,
        indicator_data=indicator_data,
        min_confidence=min_confidence,
        top_n=None if full_matrix else 20,
    )

    top_items = []
    for _, row in top_df.iterrows():
        slug = row.get("indicator_slug", "")
        top_items.append(TopCorrelationItem(
            naics=row.get("naics_code", ""),
            industry=row.get("industry_name", ""),
            indicator_slug=slug,
            indicator_name=INDICATOR_NAMES.get(slug, slug),
            correlation=row.get("correlation", 0.0),
            confidence=row.get("confidence", 0.0),
        ))

    response = TopCorrelationsResponse(correlations=top_items)

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_CORRELATIONS_CACHE_TTL, redis=redis
    )

    return response


@router.get("/overview", response_model=OverviewResponse)
@limiter.limit(RATE_READ)
async def get_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> OverviewResponse:
    """Get concentration overview with department-level aggregations."""
    redis = _get_redis()
    cache_key = build_cache_key("concentration/overview/v2", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("concentration.overview.cache_hit", key=cache_key)
        return OverviewResponse.model_validate_json(cached)

    # Query all concentration data
    stmt = select(IndustryConcentration).order_by(
        IndustryConcentration.naics_code,
        IndustryConcentration.year.desc(),
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    if not rows:
        # Return placeholder
        response = OverviewResponse(
            dept_i=DeptConcentration(cr4=0.0, hhi=0.0, trend_direction="stable"),
            dept_ii=DeptConcentration(cr4=0.0, hhi=0.0, trend_direction="stable"),
            most_concentrated=[],
            fastest_increasing=[],
        )
        return response

    # Get latest by industry
    latest_by_industry: dict[str, IndustryConcentration] = {}
    for row in rows:
        if row.naics_code not in latest_by_industry:
            latest_by_industry[row.naics_code] = row

    cr4_history = _cr4_history_by_naics(rows)

    # Build DataFrame for aggregation
    df = pd.DataFrame([
        {
            "naics_code": naics,
            "cr4": conc.cr4,
            "hhi": conc.hhi,
            "total_revenue": conc.total_revenue or 0,
        }
        for naics, conc in latest_by_industry.items()
    ])

    # Aggregate by department
    dept_agg = aggregate_by_department(df)

    trends_stmt = select(ConcentrationTrend)
    trends_result = await db.execute(trends_stmt)
    trends_by_naics = _latest_trend_by_naics(list(trends_result.scalars().all()))

    # Compute department trend directions (simplified - would aggregate trends)
    dept_i_trend = "stable"
    dept_ii_trend = "stable"

    # Build industry lists with levels and trends
    industries_with_info: list[IndustryListItem] = []
    for naics, conc in latest_by_industry.items():
        level = classify_concentration_level(conc.cr4, conc.hhi)
        trend_direction, trend_slope = _trend_direction_and_slope(
            naics, trends_by_naics.get(naics), cr4_history
        )

        industries_with_info.append(IndustryListItem(
            naics=naics,
            name=conc.naics_name or naics,
            cr4=conc.cr4,
            hhi=conc.hhi,
            level=level,
            trend_direction=trend_direction,
            trend_slope=trend_slope,
            data_source=getattr(conc, "data_source", None),
        ))

    # Top 5 most concentrated by HHI
    most_concentrated = sorted(
        industries_with_info,
        key=lambda x: x.hhi,
        reverse=True,
    )[:5]

    # Top 5 fastest increasing
    fastest_increasing = [
        ind for ind in industries_with_info
        if ind.trend_direction == "increasing"
    ][:5]

    response = OverviewResponse(
        dept_i=DeptConcentration(
            cr4=dept_agg["Dept_I"]["cr4"],
            hhi=dept_agg["Dept_I"]["hhi"],
            trend_direction=dept_i_trend,
        ),
        dept_ii=DeptConcentration(
            cr4=dept_agg["Dept_II"]["cr4"],
            hhi=dept_agg["Dept_II"]["hhi"],
            trend_direction=dept_ii_trend,
        ),
        most_concentrated=most_concentrated,
        fastest_increasing=fastest_increasing,
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_OVERVIEW_CACHE_TTL, redis=redis
    )

    return response
