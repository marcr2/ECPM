"""Background tasks for pre-computing and caching indicator data.

Provides daily scheduled task to compute all indicators for all methodologies
and store results in disk cache for fast API responses.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.cache_manager import (
    invalidate_cache,
    set_cached_indicator,
    set_cached_overview,
)
from ecpm.database import async_session
from ecpm.indicators.computation import compute_all_summaries, compute_indicator
from ecpm.indicators.definitions import INDICATOR_DEFS, IndicatorSlug
from ecpm.indicators.registry import MethodologyRegistry

logger = structlog.get_logger(__name__)


async def precompute_all_indicators() -> dict[str, int]:
    """Pre-compute all indicators for all methodologies and cache to disk.

    This should be run daily (via cron or scheduler) to refresh the cache.

    Returns:
        Dict with counts of cached items per methodology.
    """
    start_time = datetime.now()
    logger.info("cache.precompute.started")

    results = {}

    db = async_session()
    try:
        for mapper in MethodologyRegistry.list_all():
            methodology = mapper.slug
            logger.info("cache.precompute.methodology", methodology=methodology)

            try:
                # Compute and cache overview
                overview = await compute_all_summaries(methodology, db, redis=None)
                overview_data = {
                    "methodology": methodology,
                    "indicators": overview,
                }
                set_cached_overview(methodology, overview_data)

                # Compute and cache individual indicators
                cached_count = 1  # overview
                for slug in IndicatorSlug:
                    try:
                        series = await compute_indicator(
                            slug.value, methodology, db, redis=None
                        )

                        # Convert series to data points
                        import math
                        data_points = []
                        for date, value in series.items():
                            if value is None or (isinstance(value, float) and math.isnan(value)):
                                continue
                            d = date.to_pydatetime() if hasattr(date, "to_pydatetime") else date
                            data_points.append({
                                "date": d.isoformat(),
                                "value": float(value),
                            })

                        # Get latest non-NaN value
                        non_nan_series = series.dropna()
                        latest_value = None
                        latest_date = None
                        if len(non_nan_series) > 0:
                            latest_value = float(non_nan_series.iloc[-1])
                            latest_date = non_nan_series.index[-1].isoformat()

                        indicator_data = {
                            "slug": slug.value,
                            "name": INDICATOR_DEFS[slug]["name"],
                            "units": INDICATOR_DEFS[slug]["units"],
                            "methodology": methodology,
                            "frequency": "A",
                            "data": data_points,
                            "latest_value": latest_value,
                            "latest_date": latest_date,
                        }

                        set_cached_indicator(methodology, slug.value, indicator_data)
                        cached_count += 1

                    except Exception as e:
                        logger.warning(
                            "cache.precompute.indicator_failed",
                            methodology=methodology,
                            slug=slug.value,
                            error=str(e),
                            exc_info=True,
                        )

                results[methodology] = cached_count
                logger.info(
                    "cache.precompute.methodology_complete",
                    methodology=methodology,
                    cached_items=cached_count,
                )

            except Exception as e:
                logger.error(
                    "cache.precompute.methodology_failed",
                    methodology=methodology,
                    error=str(e),
                    exc_info=True,
                )
                results[methodology] = 0

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            "cache.precompute.completed",
            results=results,
            elapsed_seconds=elapsed,
        )

        return results
    finally:
        await db.close()


def run_precompute_sync() -> dict[str, int]:
    """Synchronous wrapper for precompute_all_indicators.

    Use this for cron jobs or manual triggering.
    """
    return asyncio.run(precompute_all_indicators())


# Register Celery task for scheduled execution
try:
    from ecpm.tasks.celery_app import celery_app

    @celery_app.task(name="ecpm.tasks.cache_tasks.celery_precompute_all_indicators")
    def celery_precompute_all_indicators():
        """Celery task for scheduled daily cache refresh."""
        return run_precompute_sync()

except ImportError:
    # Celery not available (e.g., running tests without Celery)
    pass


if __name__ == "__main__":
    # Allow direct execution for testing: python -m ecpm.tasks.cache_tasks
    print("Starting indicator pre-computation...")
    results = run_precompute_sync()
    print(f"Completed! Results: {results}")
