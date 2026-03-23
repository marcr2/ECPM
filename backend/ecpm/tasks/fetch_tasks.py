"""Celery tasks for data fetching.

Contains the fetch_all_series task that runs the full ingestion pipeline
synchronously within a Celery worker.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from ecpm.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(
    name="ecpm.tasks.fetch_tasks.fetch_all_series",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def fetch_all_series(self: Any) -> dict[str, Any]:
    """Fetch all configured FRED and BEA series.

    This task runs the full ingestion pipeline. It creates its own
    database session and API clients, then runs the async pipeline
    in a new event loop.

    Returns:
        Dict with ingestion result summary.
    """
    logger.info("fetch_all_series_start", task_id=self.request.id)

    try:
        result = asyncio.run(_run_pipeline())
        logger.info(
            "fetch_all_series_complete",
            task_id=self.request.id,
            processed=result.get("series_processed", 0),
            failed=result.get("series_failed", 0),
        )
        return result
    except Exception as exc:
        logger.error(
            "fetch_all_series_error",
            task_id=self.request.id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


async def _run_pipeline() -> dict[str, Any]:
    """Run the ingestion pipeline with a fresh session and clients.

    Creates all necessary resources (session, clients, config) and
    tears them down on completion.
    """
    from ecpm.config import get_settings
    from ecpm.database import async_session
    from ecpm.ingestion.bea_client import BEAClient
    from ecpm.ingestion.fred_client import FredClient
    from ecpm.ingestion.pipeline import IngestionPipeline
    from ecpm.ingestion.series_config import load_series_config

    settings = get_settings()
    config = load_series_config()

    fred_client = FredClient(api_key=settings.fred_api_key)
    bea_client = BEAClient(api_key=settings.bea_api_key)

    async with async_session() as session:
        pipeline = IngestionPipeline(
            session=session,
            fred_client=fred_client,
            bea_client=bea_client,
            config=config,
        )
        result = await pipeline.ingest_all()
        await session.commit()

    return result.to_dict()
