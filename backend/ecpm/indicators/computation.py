"""Indicator computation orchestrator.

Provides async entry points for computing individual and summary indicators.
Fetches raw series data from the database, builds a data dict, calls the
appropriate mapper method, and returns computed pd.Series results.

Results are cached in Redis with key pattern `indicators:{slug}:{methodology}`
and TTL of 3600s (1 hour).
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.cache import build_cache_key, cache_get, cache_set
from ecpm.indicators.definitions import IndicatorSlug
from ecpm.indicators.registry import MethodologyRegistry
from ecpm.models.observation import Observation

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# FRED series ID -> descriptive key mapping
# Used by the orchestrator to build the data dict that mappers expect.
# ---------------------------------------------------------------------------

# Core series (used by methodology-dependent indicators)
_FRED_TO_KEY: dict[str, str] = {
    "A053RC1Q027SBEA": "national_income",
    "A576RC1": "compensation",
    "K1NTOTL1SI000": "net_fixed_assets_current",
    "K1NTOTL1HI000": "net_fixed_assets_historical",
}

# Per-indicator financial FRED-to-key mappings.
# Each financial indicator has its own mapping because the same FRED series
# can map to different descriptive keys depending on context (e.g.,
# BOGZ1FL073164003Q -> "credit_total" for credit-GDP gap, but
# "financial_assets" for financial-real ratio).
_FINANCIAL_INDICATOR_MAPPINGS: dict[str, dict[str, str]] = {
    IndicatorSlug.productivity_wage_gap: {
        "OPHNFB": "output_per_hour",
        "PRS85006092": "real_compensation_per_hour",
    },
    IndicatorSlug.credit_gdp_gap: {
        "BOGZ1FL073164003Q": "credit_total",
        "GDP": "nominal_gdp",
    },
    IndicatorSlug.financial_real_ratio: {
        "BOGZ1FL073164003Q": "financial_assets",
        "K1NTOTL1SI000": "real_assets",
    },
    IndicatorSlug.debt_service_ratio: {
        "BOGZ1FA096130001Q": "debt_service",
        "A445RC1Q027SBEA": "corporate_income",
    },
}

# Financial indicator slugs and their required FRED series
_FINANCIAL_SERIES: dict[str, list[str]] = {
    IndicatorSlug.productivity_wage_gap: ["OPHNFB", "PRS85006092"],
    IndicatorSlug.credit_gdp_gap: ["BOGZ1FL073164003Q", "GDP"],
    IndicatorSlug.financial_real_ratio: ["BOGZ1FL073164003Q", "K1NTOTL1SI000"],
    IndicatorSlug.debt_service_ratio: ["BOGZ1FA096130001Q", "A445RC1Q027SBEA"],
}

# ---------------------------------------------------------------------------
# Dispatch map: IndicatorSlug -> method name on MethodologyMapper
# ---------------------------------------------------------------------------

INDICATOR_DISPATCH: dict[str, str] = {
    IndicatorSlug.rate_of_profit: "compute_rate_of_profit",
    IndicatorSlug.occ: "compute_occ",
    IndicatorSlug.rate_of_surplus_value: "compute_rate_of_surplus_value",
    IndicatorSlug.mass_of_profit: "compute_mass_of_profit",
    IndicatorSlug.productivity_wage_gap: "compute_productivity_wage_gap",
    IndicatorSlug.credit_gdp_gap: "compute_credit_gdp_gap",
    IndicatorSlug.financial_real_ratio: "compute_financial_real_ratio",
    IndicatorSlug.debt_service_ratio: "compute_debt_service_ratio",
}

# Cache TTL: 1 hour (data changes at most daily)
_CACHE_TTL = 3600


def _is_financial_indicator(slug: str) -> bool:
    """Check if the indicator is a financial (methodology-independent) indicator."""
    return slug in _FINANCIAL_SERIES


def _get_required_series_ids(slug: str, mapper: Any) -> list[str]:
    """Get all FRED series IDs needed for computing the given indicator.

    For core (methodology-dependent) indicators, uses the mapper's
    get_required_series(). For financial indicators, uses the known
    FRED series IDs.

    Args:
        slug: The indicator slug.
        mapper: The methodology mapper instance.

    Returns:
        List of FRED series IDs to query from the database.
    """
    if _is_financial_indicator(slug):
        return _FINANCIAL_SERIES[slug]
    return mapper.get_required_series()


async def _fetch_series_from_db(
    series_ids: list[str],
    db: AsyncSession,
    key_mapping: dict[str, str] | None = None,
) -> dict[str, pd.Series]:
    """Query observations from the database and build a data dict.

    For each series_id, queries all observations ordered by date, then
    converts to a pd.Series. Maps FRED series IDs to the descriptive
    keys that mappers expect.

    Args:
        series_ids: List of FRED series IDs to fetch.
        db: Async database session.
        key_mapping: Optional dict mapping FRED IDs to descriptive keys.
            If None, uses the combined core + financial mapping (note:
            overlapping keys will be resolved in favor of financial).

    Returns:
        Dict mapping descriptive keys to pd.Series indexed by date.
    """
    if key_mapping is None:
        key_mapping = {**_FRED_TO_KEY, **_FINANCIAL_FRED_TO_KEY}
    data: dict[str, pd.Series] = {}

    for series_id in series_ids:
        stmt = (
            select(Observation.observation_date, Observation.value)
            .where(Observation.series_id == series_id)
            .order_by(Observation.observation_date)
        )
        result = await db.execute(stmt)
        rows = result.all()

        if rows:
            dates = [row[0] for row in rows]
            values = [row[1] for row in rows]
            series = pd.Series(values, index=pd.DatetimeIndex(dates), dtype=float)
        else:
            series = pd.Series(dtype=float)
            logger.warning(
                "computation.empty_series",
                series_id=series_id,
                msg="No observations found in database",
            )

        # Map to descriptive key if known, otherwise use series_id
        key = key_mapping.get(series_id, series_id)
        data[key] = series

    return data


def _series_to_json(series: pd.Series) -> str:
    """Serialize a pd.Series to JSON for Redis caching."""
    return json.dumps(
        {
            "dates": [d.isoformat() for d in series.index],
            "values": series.tolist(),
        }
    )


def _json_to_series(json_str: str) -> pd.Series:
    """Deserialize a pd.Series from cached JSON."""
    payload = json.loads(json_str)
    return pd.Series(
        payload["values"],
        index=pd.DatetimeIndex(payload["dates"]),
        dtype=float,
    )


async def compute_indicator(
    slug: str, methodology_slug: str, db: AsyncSession, redis: Any = None
) -> pd.Series:
    """Compute a single indicator time-series.

    1. Check Redis cache for precomputed result.
    2. Get mapper from registry.
    3. Determine required FRED series IDs.
    4. Fetch observations from database.
    5. Call the appropriate compute method via dispatch map.
    6. Cache the result in Redis.
    7. Return the computed pd.Series.

    Args:
        slug: Indicator slug (e.g., 'rate_of_profit').
        methodology_slug: Methodology to use (e.g., 'shaikh-tonak').
        db: Async database session for querying observations.
        redis: Optional Redis client for caching.

    Returns:
        pd.Series of computed values indexed by date.

    Raises:
        KeyError: If methodology or indicator slug is unknown.
    """
    # Check cache
    cache_key = build_cache_key(
        f"indicators/{slug}/{methodology_slug}"
    )
    cached = await cache_get(cache_key, redis=redis)
    if cached:
        logger.debug("computation.cache_hit", slug=slug, methodology=methodology_slug)
        return _json_to_series(cached)

    # Get mapper and dispatch method
    mapper = MethodologyRegistry.get(methodology_slug)
    method_name = INDICATOR_DISPATCH.get(slug)
    if method_name is None:
        raise KeyError(f"Unknown indicator slug: {slug}")

    method = getattr(mapper, method_name)

    # Fetch required series from database with the correct key mapping.
    # Core indicators use _FRED_TO_KEY; financial indicators use their own
    # per-indicator mapping from _FINANCIAL_INDICATOR_MAPPINGS.
    # This avoids key collisions where the same FRED series ID maps to
    # different descriptive keys in different contexts (e.g., K1NTOTL1SI000
    # maps to "net_fixed_assets_current" for core, "real_assets" for financial).
    series_ids = _get_required_series_ids(slug, mapper)
    if _is_financial_indicator(slug):
        mapping = _FINANCIAL_INDICATOR_MAPPINGS[slug]
    else:
        mapping = _FRED_TO_KEY
    data = await _fetch_series_from_db(series_ids, db, key_mapping=mapping)

    # Compute indicator
    logger.info(
        "computation.computing",
        slug=slug,
        methodology=methodology_slug,
        series_count=len(data),
    )
    result = method(data)

    # Cache result
    await cache_set(cache_key, _series_to_json(result), ttl=_CACHE_TTL, redis=redis)

    return result


async def compute_all_summaries(
    methodology_slug: str, db: AsyncSession, redis: Any = None
) -> list[dict]:
    """Compute summary statistics for all indicators.

    For each IndicatorSlug, computes the indicator and extracts:
    - latest_value: most recent computed value
    - latest_date: date of the most recent value
    - trend: "rising", "falling", or "flat" (compares last 2 values)
    - sparkline: last 20 values for overview card visualization

    Args:
        methodology_slug: Methodology to use (e.g., 'shaikh-tonak').
        db: Async database session for querying observations.
        redis: Optional Redis client for caching.

    Returns:
        List of summary dicts with slug, latest_value, latest_date, trend, sparkline.
    """
    from ecpm.indicators.definitions import INDICATOR_DEFS

    summaries: list[dict] = []

    for slug in IndicatorSlug:
        try:
            series = await compute_indicator(
                slug.value, methodology_slug, db, redis=redis
            )

            if len(series) == 0:
                summaries.append(
                    {
                        "slug": slug.value,
                        "name": INDICATOR_DEFS[slug]["name"],
                        "units": INDICATOR_DEFS[slug]["units"],
                        "latest_value": None,
                        "latest_date": None,
                        "trend": None,
                        "sparkline": [],
                    }
                )
                continue

            latest_value = float(series.iloc[-1])
            latest_date = series.index[-1].isoformat()

            # Determine trend from last 2 values
            if len(series) >= 2:
                diff = series.iloc[-1] - series.iloc[-2]
                if abs(diff) < 1e-6:
                    trend = "flat"
                elif diff > 0:
                    trend = "rising"
                else:
                    trend = "falling"
            else:
                trend = "flat"

            # Sparkline: last 20 values
            sparkline = series.tail(20).tolist()

            summaries.append(
                {
                    "slug": slug.value,
                    "name": INDICATOR_DEFS[slug]["name"],
                    "units": INDICATOR_DEFS[slug]["units"],
                    "latest_value": latest_value,
                    "latest_date": latest_date,
                    "trend": trend,
                    "sparkline": sparkline,
                }
            )

        except Exception:
            logger.warning(
                "computation.summary_failed",
                slug=slug.value,
                methodology=methodology_slug,
                exc_info=True,
            )
            summaries.append(
                {
                    "slug": slug.value,
                    "name": INDICATOR_DEFS.get(slug, {}).get("name", slug.value),
                    "units": INDICATOR_DEFS.get(slug, {}).get("units", ""),
                    "latest_value": None,
                    "latest_date": None,
                    "trend": None,
                    "sparkline": [],
                }
            )

    return summaries
