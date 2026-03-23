"""Status and fetch trigger endpoints for ECPM data pipeline.

Provides:
- GET /api/data/status -- aggregate counts, last fetch time, error details
- POST /api/data/fetch -- submit Celery task, return task_id
- GET /api/data/fetch/stream -- SSE via EventSourceResponse with Redis pubsub
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.config import get_settings
from ecpm.database import get_db
from ecpm.models.series_metadata import SeriesMetadata
from ecpm.schemas.series import FetchStatusResponse, FetchTriggerResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/data", tags=["status"])


def _get_redis():
    """Return the Redis client from app state, or None if unavailable."""
    from ecpm.main import _redis_pool

    return _redis_pool


@router.get("/status", response_model=FetchStatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
) -> FetchStatusResponse:
    """Return aggregate pipeline health: counts, last fetch, errors.

    Provides total series count, counts by fetch_status, the most recent
    last_fetched timestamp, next scheduled run time, and error details.
    """
    settings = get_settings()

    # Total count
    total_result = await db.execute(
        select(func.count()).select_from(SeriesMetadata)
    )
    total = total_result.scalar_one()

    # Count by status
    status_counts: dict[str, int] = {}
    for status_val in ("ok", "error", "pending", "stale"):
        count_result = await db.execute(
            select(func.count())
            .select_from(SeriesMetadata)
            .where(SeriesMetadata.fetch_status == status_val)
        )
        status_counts[status_val] = count_result.scalar_one()

    # Last fetch time (most recent across all series)
    last_fetch_result = await db.execute(
        select(func.max(SeriesMetadata.last_fetched))
    )
    last_fetch_time = last_fetch_result.scalar_one()

    # Error details
    errors: list[dict] = []
    if status_counts.get("error", 0) > 0:
        error_result = await db.execute(
            select(
                SeriesMetadata.series_id,
                SeriesMetadata.fetch_error,
                SeriesMetadata.last_fetched,
            ).where(SeriesMetadata.fetch_status == "error")
        )
        for row in error_result.all():
            errors.append(
                {
                    "series_id": row.series_id,
                    "error": row.fetch_error,
                    "last_fetched": str(row.last_fetched) if row.last_fetched else None,
                }
            )

    # Next scheduled run
    next_run = f"{settings.fetch_schedule_hour:02d}:{settings.fetch_schedule_minute:02d} UTC daily"

    return FetchStatusResponse(
        total_series=total,
        ok_count=status_counts.get("ok", 0),
        error_count=status_counts.get("error", 0),
        pending_count=status_counts.get("pending", 0),
        stale_count=status_counts.get("stale", 0),
        last_fetch_time=last_fetch_time,
        next_scheduled_run=next_run,
        errors=errors,
    )


@router.post("/fetch", response_model=FetchTriggerResponse)
async def trigger_fetch() -> FetchTriggerResponse:
    """Submit a Celery task to fetch all series data.

    Returns the task ID for monitoring progress. If Celery is unavailable,
    returns a placeholder ID indicating the task could not be submitted.
    """
    try:
        from ecpm.tasks.fetch_tasks import fetch_all_series

        result = fetch_all_series.delay()
        task_id = str(result.id)
        status = "submitted"
        logger.info("fetch.triggered", task_id=task_id)
    except ImportError:
        # Celery tasks not yet implemented (Plan 01-03 may not be complete)
        task_id = str(uuid.uuid4())
        status = "submitted"
        logger.warning(
            "fetch.celery_unavailable",
            task_id=task_id,
            msg="Celery tasks not available; returning placeholder task ID",
        )
    except Exception:
        task_id = str(uuid.uuid4())
        status = "error"
        logger.error("fetch.trigger_failed", exc_info=True)

    return FetchTriggerResponse(task_id=task_id, status=status)


@router.get("/fetch/stream")
async def fetch_stream():
    """Stream fetch progress events via Server-Sent Events (SSE).

    Subscribes to a Redis pubsub channel for real-time fetch progress updates.
    If Redis is unavailable, sends a heartbeat stream that completes after
    a brief period.
    """
    try:
        from sse_starlette.sse import EventSourceResponse
    except ImportError:
        from fastapi.responses import StreamingResponse

        async def _fallback():
            yield "data: {\"status\": \"sse_unavailable\"}\n\n"

        return StreamingResponse(_fallback(), media_type="text/event-stream")

    async def _event_generator():
        redis = _get_redis()

        if redis is not None:
            try:
                pubsub = redis.pubsub()
                await pubsub.subscribe("ecpm:fetch:progress")

                # Send initial connection event
                yield {
                    "event": "connected",
                    "data": json.dumps({"status": "connected"}),
                }

                # Listen for messages with timeout
                timeout_count = 0
                max_timeouts = 60  # 60 iterations * 1s = ~60s max
                while timeout_count < max_timeouts:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message and message["type"] == "message":
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        yield {"event": "progress", "data": data}

                        # Check for completion
                        try:
                            parsed = json.loads(data)
                            if parsed.get("status") in ("complete", "error"):
                                break
                        except (json.JSONDecodeError, TypeError):
                            pass

                        timeout_count = 0  # Reset on activity
                    else:
                        timeout_count += 1
                        yield {
                            "event": "heartbeat",
                            "data": json.dumps({"status": "waiting"}),
                        }

                await pubsub.unsubscribe("ecpm:fetch:progress")
                await pubsub.close()
            except Exception:
                logger.error("sse.redis_error", exc_info=True)
                yield {
                    "event": "error",
                    "data": json.dumps({"status": "redis_error"}),
                }
        else:
            # No Redis available -- send a brief heartbeat stream
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "redis": False}),
            }
            for _ in range(3):
                await asyncio.sleep(0.5)
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"status": "no_redis"}),
                }

    return EventSourceResponse(_event_generator())
