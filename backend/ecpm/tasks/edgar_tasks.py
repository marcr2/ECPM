"""Celery task for weekly SEC EDGAR concentration data refresh.

Loads the curated firm registry, pulls annual revenue for every
listed CIK from the EDGAR XBRL CompanyFacts API, aggregates by
parent company, and computes CR4/CR8/HHI for each NAICS sector.

Scheduled weekly via Celery Beat (Sunday 2:00 AM US/Eastern).
"""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

import structlog

from ecpm.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(
    name="ecpm.tasks.edgar_tasks.refresh_edgar_concentration",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def refresh_edgar_concentration(
    self: Any,
    fiscal_year: int | None = None,
) -> dict[str, Any]:
    """Refresh concentration data from SEC EDGAR for all curated industries.

    Args:
        fiscal_year: Specific fiscal year to fetch.  Defaults to the
            current calendar year (EDGAR returns most recent 10-K).

    Returns:
        Summary dict with industries_processed, rows_stored, errors.
    """
    logger.info("edgar_refresh_start", task_id=self.request.id)

    try:
        result = asyncio.run(_run_edgar_ingestion(fiscal_year))
        logger.info(
            "edgar_refresh_complete",
            task_id=self.request.id,
            industries_processed=result.get("industries_processed", 0),
        )
        return result
    except Exception as exc:
        logger.error(
            "edgar_refresh_error",
            task_id=self.request.id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


async def _run_edgar_ingestion(
    fiscal_year: int | None = None,
) -> dict[str, Any]:
    """Core async pipeline: EDGAR -> concentration metrics -> database."""
    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from ecpm.config import get_settings
    from ecpm.ingestion.edgar_client import EdgarClient
    from ecpm.models.concentration import (
        ConcentrationTrend,
        FirmMarketShare,
        IndustryConcentration,
    )
    from ecpm.concentration.metrics import compute_trend

    settings = get_settings()

    if not settings.edgar_user_agent:
        return {
            "error": "EDGAR_USER_AGENT not configured",
            "industries_processed": 0,
            "rows_stored": 0,
        }

    client = EdgarClient(user_agent=settings.edgar_user_agent)
    naics_codes = client.get_registry_naics_codes()

    if fiscal_year is None:
        fiscal_year = dt.date.today().year

    local_engine = create_async_engine(
        settings.database_url, pool_size=5, max_overflow=10, echo=False
    )
    local_session = async_sessionmaker(
        local_engine, class_=AsyncSession, expire_on_commit=False
    )

    industries_processed = 0
    rows_stored = 0
    errors: dict[str, str] = {}

    try:
        for naics in naics_codes:
            try:
                logger.info("edgar_fetch_industry", naics=naics)
                industry_name = client.get_registry_industry_name(naics)

                result = client.compute_industry_concentration(
                    naics, fiscal_year=fiscal_year
                )
                if result is None:
                    logger.warning(
                        "edgar_no_data",
                        naics=naics,
                        fiscal_year=fiscal_year,
                    )
                    errors[naics] = "No revenue data from EDGAR"
                    continue

                cr4 = result["cr4"]
                cr8 = result["cr8"]
                hhi = result["hhi"]
                num_firms = result["num_firms"]
                total_revenue = result["total_revenue"]
                firms = result["firms"]

                async with local_session() as session:
                    # Upsert industry_concentration row
                    existing = await session.execute(
                        select(IndustryConcentration).where(
                            IndustryConcentration.year == fiscal_year,
                            IndustryConcentration.naics_code == naics,
                        )
                    )
                    row = existing.scalar_one_or_none()
                    if row:
                        row.naics_name = industry_name
                        row.cr4 = cr4
                        row.cr8 = cr8
                        row.hhi = hhi
                        row.num_firms = num_firms
                        row.total_revenue = total_revenue
                        row.data_source = "edgar"
                        row.last_updated = dt.datetime.now(dt.timezone.utc)
                    else:
                        session.add(IndustryConcentration(
                            year=fiscal_year,
                            naics_code=naics,
                            naics_name=industry_name,
                            cr4=cr4,
                            cr8=cr8,
                            hhi=hhi,
                            num_firms=num_firms,
                            total_revenue=total_revenue,
                            data_source="edgar",
                        ))

                    # Replace firm_market_share rows for this industry/year
                    await session.execute(
                        delete(FirmMarketShare).where(
                            FirmMarketShare.year == fiscal_year,
                            FirmMarketShare.naics_code == naics,
                        )
                    )

                    for firm in firms:
                        session.add(FirmMarketShare(
                            year=fiscal_year,
                            naics_code=naics,
                            firm_name=firm["firm_name"],
                            parent_company=firm["parent_company"],
                            cik=None,  # Parent-level, not individual CIK
                            revenue=firm["revenue"],
                            market_share_pct=firm["market_share_pct"],
                            rank=firm["rank"],
                        ))

                    await session.commit()
                    rows_stored += 1 + len(firms)

                industries_processed += 1
                logger.info(
                    "edgar_industry_complete",
                    naics=naics,
                    cr4=round(cr4, 1),
                    hhi=round(hhi, 0),
                    firms=len(firms),
                )

            except Exception as e:
                logger.warning(
                    "edgar_industry_error",
                    naics=naics,
                    error=str(e),
                    exc_info=True,
                )
                errors[naics] = str(e)

        # Update trends for all processed industries
        await _update_edgar_trends(local_session, naics_codes)

    finally:
        await local_engine.dispose()

    return {
        "industries_processed": industries_processed,
        "rows_stored": rows_stored,
        "errors": errors,
    }


async def _update_edgar_trends(
    session_factory: Any,
    naics_codes: list[str],
) -> None:
    """Recompute concentration trends for EDGAR-sourced industries."""
    import pandas as pd
    from sqlalchemy import select

    from ecpm.concentration.metrics import compute_trend
    from ecpm.models.concentration import (
        ConcentrationTrend,
        IndustryConcentration,
    )

    async with session_factory() as session:
        for naics in naics_codes:
            try:
                stmt = select(IndustryConcentration).where(
                    IndustryConcentration.naics_code == naics
                ).order_by(IndustryConcentration.year)
                result = await session.execute(stmt)
                rows = result.scalars().all()

                if len(rows) < 2:
                    continue

                cr4_series = pd.Series([r.cr4 for r in rows])
                years_series = pd.Series([r.year for r in rows])
                trend_result = compute_trend(cr4_series, years_series)

                start_year = rows[0].year
                end_year = rows[-1].year

                existing = await session.execute(
                    select(ConcentrationTrend).where(
                        ConcentrationTrend.naics_code == naics,
                        ConcentrationTrend.start_year == start_year,
                    )
                )
                trend_row = existing.scalar_one_or_none()
                if trend_row:
                    trend_row.end_year = end_year
                    trend_row.trend_slope = trend_result["slope"]
                    trend_row.trend_direction = trend_result["direction"]
                    trend_row.r_squared = trend_result["r_squared"]
                else:
                    session.add(ConcentrationTrend(
                        naics_code=naics,
                        start_year=start_year,
                        end_year=end_year,
                        trend_slope=trend_result["slope"],
                        trend_direction=trend_result["direction"],
                        r_squared=trend_result["r_squared"],
                    ))

            except Exception:
                logger.warning(
                    "edgar_trend_error",
                    naics=naics,
                    exc_info=True,
                )

        await session.commit()
