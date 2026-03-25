"""Celery tasks for BEA Input-Output table ingestion.

Fetches Use tables from BEA, computes technical coefficients,
and stores cells + metadata in the io_cells / io_metadata tables.
"""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np
import structlog

from ecpm.tasks.celery_app import celery_app

logger = structlog.get_logger()

# Historical BEA benchmark years (summary-level I-O). The API also exposes
# additional years (e.g. annual I-O updates); when ``years`` is omitted we merge
# these with ``BEAIOClient.discover_available_years()``.
DEFAULT_IO_YEARS = [1997, 2002, 2007, 2012, 2017, 2022]


def _years_to_ingest(client: Any, years: list[int] | None) -> list[int]:
    """Resolve the year list: explicit request, or union of defaults + BEA API."""
    if years is not None:
        return years
    discovered: list[int] = []
    try:
        discovered = client.discover_available_years()
    except Exception as exc:
        logger.warning("io_ingestion_year_discovery_failed", error=str(exc))
    merged = sorted(set(DEFAULT_IO_YEARS) | set(discovered))
    logger.info(
        "io_ingestion_years_resolved",
        count=len(merged),
        min_year=min(merged) if merged else None,
        max_year=max(merged) if merged else None,
    )
    return merged


@celery_app.task(
    name="ecpm.tasks.structural_tasks.fetch_io_tables",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def fetch_io_tables(self: Any, years: list[int] | None = None) -> dict[str, Any]:
    """Fetch BEA I-O Use tables, compute coefficients, and store in DB.

    Args:
        years: List of years to fetch. If omitted, ingests the union of
            :data:`DEFAULT_IO_YEARS` and all years reported by the BEA
            InputOutput API for the summary Use table.

    Returns:
        Dict with ingestion summary.
    """
    logger.info("fetch_io_tables_start", task_id=self.request.id)

    try:
        result = asyncio.run(_run_io_ingestion(years))
        logger.info(
            "fetch_io_tables_complete",
            task_id=self.request.id,
            years_processed=result.get("years_processed", 0),
            cells_stored=result.get("cells_stored", 0),
        )
        return result
    except Exception as exc:
        logger.error(
            "fetch_io_tables_error",
            task_id=self.request.id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


async def _run_io_ingestion(years: list[int] | None) -> dict[str, Any]:
    """Run the I-O ingestion pipeline with a dedicated engine."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from ecpm.config import get_settings
    from ecpm.models.io_table import IOCell, IOMetadata
    from ecpm.structural.bea_io_client import BEAIOClient
    from ecpm.structural.leontief import compute_technical_coefficients

    settings = get_settings()

    if not settings.bea_api_key:
        return {"error": "BEA_API_KEY not configured", "years_processed": 0, "cells_stored": 0}

    client = BEAIOClient(api_key=settings.bea_api_key)
    years = _years_to_ingest(client, years)

    local_engine = create_async_engine(
        settings.database_url, pool_size=5, max_overflow=10, echo=False
    )
    local_session = async_sessionmaker(
        local_engine, class_=AsyncSession, expire_on_commit=False
    )

    years_processed = 0
    total_cells = 0
    errors: dict[int, str] = {}

    try:
        for year in years:
            try:
                logger.info("io_ingestion_year_start", year=year)

                # Fetch Use table (synchronous BEA call)
                use_df = client.fetch_use_table(year)
                if use_df.empty:
                    logger.warning("io_ingestion_empty_table", year=year)
                    errors[year] = "Empty Use table returned"
                    continue

                matrix = use_df.values.astype(float)
                row_codes = list(use_df.index.astype(str))
                col_codes = list(use_df.columns.astype(str))

                # Compute technical coefficients
                total_output = matrix.sum(axis=0)
                A = compute_technical_coefficients(matrix, total_output)

                n_rows, n_cols = A.shape
                year_cells = 0

                # Sector descriptions (shared by both table types)
                row_descriptions = {code: code for code in row_codes}
                col_descriptions = {code: code for code in col_codes}
                try:
                    descs = client.get_sector_descriptions(year)
                    row_descriptions.update(descs)
                    col_descriptions.update(descs)
                except Exception:
                    pass

                async with local_session() as session:
                    from sqlalchemy import delete

                    # --- Store both table types: "coefficients" and "use" ---
                    for ttype, mat in [("coefficients", A), ("use", matrix)]:
                        existing_meta = await session.execute(
                            select(IOMetadata).where(
                                IOMetadata.year == year,
                                IOMetadata.table_type == ttype,
                            )
                        )
                        meta = existing_meta.scalar_one_or_none()
                        if meta:
                            meta.num_industries = min(n_rows, n_cols)
                        else:
                            meta = IOMetadata(
                                year=year,
                                table_type=ttype,
                                table_id=client._DEFAULT_USE_TABLE_ID,
                                num_industries=min(n_rows, n_cols),
                                source="BEA InputOutput",
                            )
                            session.add(meta)
                        await session.flush()

                        await session.execute(
                            delete(IOCell).where(
                                IOCell.year == year,
                                IOCell.table_type == ttype,
                            )
                        )

                        batch_size = 5000
                        cells_batch: list[dict] = []
                        year_cells_for_type = 0

                        for i, r_code in enumerate(row_codes):
                            for j, c_code in enumerate(col_codes):
                                val = float(mat[i, j])
                                if abs(val) < 1e-12:
                                    continue
                                cells_batch.append({
                                    "year": year,
                                    "row_code": r_code,
                                    "col_code": c_code,
                                    "value": val,
                                    "row_description": row_descriptions.get(r_code),
                                    "col_description": col_descriptions.get(c_code),
                                    "table_type": ttype,
                                })
                                if len(cells_batch) >= batch_size:
                                    session.add_all([IOCell(**c) for c in cells_batch])
                                    year_cells_for_type += len(cells_batch)
                                    cells_batch = []
                                    await session.flush()

                        if cells_batch:
                            session.add_all([IOCell(**c) for c in cells_batch])
                            year_cells_for_type += len(cells_batch)

                        year_cells += year_cells_for_type

                    await session.commit()

                total_cells += year_cells
                years_processed += 1
                logger.info(
                    "io_ingestion_year_complete",
                    year=year,
                    cells=year_cells,
                    industries=min(n_rows, n_cols),
                )

            except Exception as e:
                logger.error("io_ingestion_year_error", year=year, error=str(e))
                errors[year] = str(e)
    finally:
        await local_engine.dispose()

    return {
        "years_processed": years_processed,
        "cells_stored": total_cells,
        "errors": {str(k): v for k, v in errors.items()},
    }
