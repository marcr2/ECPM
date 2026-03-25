"""Celery tasks for Census Bureau concentration data ingestion (fallback).

Fetches establishment and revenue data from Census CBP/Economic Census,
computes CR4, CR8, HHI metrics, and stores results in the
industry_concentration, firm_market_share, and concentration_trend tables.

This task acts as a *fallback* for historical Census years.  For the
current year, the weekly EDGAR task (edgar_tasks.py) provides real
firm-level revenue data.  Census rows are never allowed to overwrite
existing EDGAR-sourced rows.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from ecpm.tasks.celery_app import celery_app

logger = structlog.get_logger()

# Census Economic Census years: 1997, 2002, 2007, 2012, 2017, 2022
DEFAULT_CENSUS_YEARS = [2002, 2007, 2012, 2017, 2022]

DEFAULT_NAICS_CODES = [
    # Department I - Means of Production
    "211",  # Oil and gas extraction
    "212",  # Mining (except oil and gas)
    "221",  # Utilities
    "236",  # Construction of buildings
    "237",  # Heavy and civil engineering
    "325",  # Chemical manufacturing
    "326",  # Plastics and rubber
    "331",  # Primary metals
    "332",  # Fabricated metal products
    "333",  # Machinery manufacturing
    "334",  # Computer and electronic products
    "335",  # Electrical equipment
    "336",  # Transportation equipment
    "423",  # Merchant wholesalers (durable)
    "424",  # Merchant wholesalers (nondurable)
    "484",  # Truck transportation
    "517",  # Telecommunications
    # Department II - Means of Consumption
    "311",  # Food manufacturing
    "312",  # Beverage and tobacco
    "315",  # Apparel manufacturing
    "441",  # Motor vehicle dealers
    "445",  # Food and beverage stores
    "448",  # Clothing stores
    "452",  # General merchandise stores
    "454",  # Nonstore retailers
    "511",  # Publishing industries
    "512",  # Motion picture and sound
    "621",  # Ambulatory health care
    "622",  # Hospitals
    "722",  # Food services and drinking places
]


@celery_app.task(
    name="ecpm.tasks.concentration_tasks.fetch_concentration_data",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def fetch_concentration_data(
    self: Any,
    naics_codes: list[str] | None = None,
    years: list[int] | None = None,
) -> dict[str, Any]:
    """Fetch Census concentration data for target industries.

    Args:
        naics_codes: NAICS codes to fetch. Defaults to DEFAULT_NAICS_CODES.
        years: Census years to fetch. Defaults to DEFAULT_CENSUS_YEARS.

    Returns:
        Dict with ingestion summary.
    """
    logger.info("fetch_concentration_start", task_id=self.request.id)

    try:
        result = asyncio.run(
            _run_concentration_ingestion(
                naics_codes or DEFAULT_NAICS_CODES,
                years or DEFAULT_CENSUS_YEARS,
            )
        )
        logger.info(
            "fetch_concentration_complete",
            task_id=self.request.id,
            industries_processed=result.get("industries_processed", 0),
        )
        return result
    except Exception as exc:
        logger.error(
            "fetch_concentration_error",
            task_id=self.request.id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


async def _run_concentration_ingestion(
    naics_codes: list[str],
    years: list[int],
) -> dict[str, Any]:
    """Run the concentration ingestion pipeline."""
    import pandas as pd
    from sqlalchemy import delete, select
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from ecpm.concentration.metrics import (
        classify_concentration_level,
        compute_cr4,
        compute_cr8,
        compute_hhi,
        compute_trend,
    )
    from ecpm.config import get_settings
    from ecpm.ingestion.census_client import CensusClient
    from ecpm.models.concentration import (
        ConcentrationTrend,
        FirmMarketShare,
        IndustryConcentration,
    )

    settings = get_settings()

    if not settings.census_api_key:
        return {
            "error": "CENSUS_API_KEY not configured",
            "industries_processed": 0,
            "rows_stored": 0,
        }

    client = CensusClient(api_key=settings.census_api_key)

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
            industry_data_points: list[dict] = []

            for year in years:
                try:
                    # Never overwrite EDGAR-sourced rows with Census data
                    async with local_session() as session:
                        existing = await session.execute(
                            select(IndustryConcentration).where(
                                IndustryConcentration.year == year,
                                IndustryConcentration.naics_code == naics,
                            )
                        )
                        existing_row = existing.scalar_one_or_none()
                        if existing_row and existing_row.data_source == "edgar":
                            logger.info(
                                "census_skip_edgar_exists",
                                naics=naics,
                                year=year,
                            )
                            industry_data_points.append({
                                "year": year,
                                "naics_code": naics,
                                "naics_name": existing_row.naics_name,
                                "cr4": existing_row.cr4,
                                "cr8": existing_row.cr8,
                                "hhi": existing_row.hhi,
                                "num_firms": existing_row.num_firms,
                                "total_revenue": existing_row.total_revenue,
                            })
                            continue

                    logger.info(
                        "concentration_fetch_industry",
                        naics=naics,
                        year=year,
                    )

                    info = client.fetch_concentration_data(year, naics)
                    if not info:
                        continue

                    # Fetch market share approximation data
                    firms_df = client.fetch_market_share_data(year, naics)

                    naics_name = info.get("naics_name", naics)
                    num_establishments = info.get("num_establishments", 0)
                    total_revenue = info.get("annual_payroll", 0.0)

                    # Determine data source and compute metrics
                    if not firms_df.empty and "RCPTOT" in firms_df.columns:
                        receipts = pd.to_numeric(
                            firms_df["RCPTOT"], errors="coerce"
                        ).dropna()
                        if len(receipts) > 0:
                            total_revenue = float(receipts.sum())
                            shares = (receipts / receipts.sum() * 100)
                            cr4 = float(compute_cr4(shares))
                            cr8 = float(compute_cr8(shares))
                            hhi = float(compute_hhi(shares))
                            data_source = "census"
                        else:
                            cr4, cr8, hhi = _estimate_from_establishments(
                                num_establishments
                            )
                            data_source = "estimated"
                    else:
                        cr4, cr8, hhi = _estimate_from_establishments(
                            num_establishments
                        )
                        data_source = "estimated"

                    industry_data_points.append({
                        "year": year,
                        "naics_code": naics,
                        "naics_name": naics_name,
                        "cr4": cr4,
                        "cr8": cr8,
                        "hhi": hhi,
                        "num_firms": num_establishments,
                        "total_revenue": total_revenue,
                    })

                    async with local_session() as session:
                        existing = await session.execute(
                            select(IndustryConcentration).where(
                                IndustryConcentration.year == year,
                                IndustryConcentration.naics_code == naics,
                            )
                        )
                        row = existing.scalar_one_or_none()
                        if row:
                            row.naics_name = naics_name
                            row.cr4 = cr4
                            row.cr8 = cr8
                            row.hhi = hhi
                            row.num_firms = num_establishments
                            row.total_revenue = total_revenue
                            row.data_source = data_source
                        else:
                            session.add(IndustryConcentration(
                                year=year,
                                naics_code=naics,
                                naics_name=naics_name,
                                cr4=cr4,
                                cr8=cr8,
                                hhi=hhi,
                                num_firms=num_establishments,
                                total_revenue=total_revenue,
                                data_source=data_source,
                            ))

                        await session.commit()
                        rows_stored += 1

                except Exception as e:
                    logger.warning(
                        "concentration_fetch_error",
                        naics=naics,
                        year=year,
                        error=str(e),
                    )
                    errors[f"{naics}/{year}"] = str(e)

            # Compute and store trend if we have multiple years
            if len(industry_data_points) >= 2:
                try:
                    cr4_series = pd.Series(
                        [d["cr4"] for d in industry_data_points]
                    )
                    years_series = pd.Series(
                        [d["year"] for d in industry_data_points]
                    )
                    trend_result = compute_trend(cr4_series, years_series)

                    start_year = min(d["year"] for d in industry_data_points)
                    end_year = max(d["year"] for d in industry_data_points)

                    async with local_session() as session:
                        existing_trend = await session.execute(
                            select(ConcentrationTrend).where(
                                ConcentrationTrend.naics_code == naics,
                                ConcentrationTrend.start_year == start_year,
                            )
                        )
                        trend_row = existing_trend.scalar_one_or_none()
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
                        await session.commit()
                except Exception as e:
                    logger.warning(
                        "concentration_trend_error",
                        naics=naics,
                        error=str(e),
                    )

            if industry_data_points:
                industries_processed += 1
                logger.info(
                    "concentration_industry_complete",
                    naics=naics,
                    data_points=len(industry_data_points),
                )

    finally:
        await local_engine.dispose()

    return {
        "industries_processed": industries_processed,
        "rows_stored": rows_stored,
        "errors": errors,
    }


def _estimate_from_establishments(num_establishments: int) -> tuple[float, float, float]:
    """Estimate CR4/CR8/HHI from establishment count when firm data unavailable.

    Uses a rough inverse relationship: fewer establishments -> higher concentration.
    These are approximations; real Census microdata would be needed for precision.
    """
    if num_establishments <= 0:
        return 0.0, 0.0, 0.0

    if num_establishments <= 4:
        cr4 = 90.0
        cr8 = 95.0
        hhi = 5000.0
    elif num_establishments <= 20:
        cr4 = 70.0
        cr8 = 85.0
        hhi = 2500.0
    elif num_establishments <= 100:
        cr4 = 40.0
        cr8 = 60.0
        hhi = 1200.0
    elif num_establishments <= 500:
        cr4 = 20.0
        cr8 = 35.0
        hhi = 600.0
    else:
        cr4 = max(5.0, 2000.0 / num_establishments)
        cr8 = min(cr4 * 1.8, 100.0)
        hhi = max(100.0, 10000.0 / (num_establishments ** 0.5))

    return cr4, cr8, hhi
