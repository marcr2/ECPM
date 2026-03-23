"""Forecasting API endpoints with SSE streaming for training progress.

Provides:
- GET /api/forecasting/forecasts -- Cached VAR forecast results
- GET /api/forecasting/regime -- Cached regime detection results
- GET /api/forecasting/crisis-index -- Cached composite crisis index
- GET /api/forecasting/backtests -- Cached backtest results
- POST /api/forecasting/train -- Trigger model training pipeline
- GET /api/forecasting/training/stream -- SSE stream of training progress

All GET endpoints read from Redis cache via versioned keys with "latest" pointers.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from ecpm.modeling.schemas import (
    BacktestsResponse,
    CrisisIndex,
    ForecastsResponse,
    RegimeResult,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])

# Redis key prefixes (must match training_tasks.py)
KEY_PREFIX_FORECASTS = "ecpm:forecasts"
KEY_PREFIX_REGIME = "ecpm:regime"
KEY_PREFIX_CRISIS = "ecpm:crisis"
KEY_PREFIX_BACKTESTS = "ecpm:backtests"

# Pubsub channel for training progress
PROGRESS_CHANNEL = "ecpm:training:progress"


def _get_redis():
    """Return the Redis client from app state, or None if unavailable."""
    from ecpm.main import _redis_pool

    return _redis_pool


async def _get_cached_result(prefix: str, redis) -> dict | None:
    """Retrieve cached result via the 'latest' pointer.

    Returns the parsed JSON dict, or None if not found.
    """
    if redis is None:
        return None

    try:
        # Get the versioned key from the latest pointer
        latest_key = await redis.get(f"{prefix}:latest")
        if latest_key is None:
            logger.debug("cache.no_latest_pointer", prefix=prefix)
            return None

        # Get the actual data from the versioned key
        data = await redis.get(latest_key)
        if data is None:
            logger.debug("cache.versioned_key_missing", key=latest_key)
            return None

        return json.loads(data)

    except Exception:
        logger.warning("cache.get_failed", prefix=prefix, exc_info=True)
        return None


@router.get("/forecasts", response_model=ForecastsResponse)
async def get_forecasts(
    indicator: Optional[str] = Query(None, description="Filter by indicator slug"),
    horizon: int = Query(8, ge=1, le=24, description="Forecast horizon in quarters"),
) -> ForecastsResponse:
    """Return cached VAR forecast results.

    Reads from Redis key 'ecpm:forecasts:latest' -> versioned key -> JSON data.
    Returns 404 if no cached results exist.
    """
    redis = _get_redis()
    cached = await _get_cached_result(KEY_PREFIX_FORECASTS, redis)

    if cached is None:
        logger.info("forecasts.cache_miss")
        raise HTTPException(
            status_code=404,
            detail="No cached forecasts available. Run POST /api/forecasting/train first.",
        )

    logger.debug("forecasts.cache_hit")

    # Filter by indicator if specified
    if indicator is not None and "forecasts" in cached:
        if indicator not in cached["forecasts"]:
            raise HTTPException(
                status_code=404,
                detail=f"No forecast available for indicator: {indicator}",
            )
        cached["forecasts"] = {indicator: cached["forecasts"][indicator]}

    # Truncate forecasts to requested horizon
    if "forecasts" in cached:
        for ind_key, ind_data in cached["forecasts"].items():
            if "forecasts" in ind_data and len(ind_data["forecasts"]) > horizon:
                ind_data["forecasts"] = ind_data["forecasts"][:horizon]
                ind_data["horizon_quarters"] = horizon

    return ForecastsResponse.model_validate(cached)


@router.get("/regime", response_model=RegimeResult)
async def get_regime() -> RegimeResult:
    """Return cached regime detection results.

    Reads from Redis key 'ecpm:regime:latest' -> versioned key -> JSON data.
    Returns 404 if no cached results exist.
    """
    redis = _get_redis()
    cached = await _get_cached_result(KEY_PREFIX_REGIME, redis)

    if cached is None:
        logger.info("regime.cache_miss")
        raise HTTPException(
            status_code=404,
            detail="No cached regime results available. Run POST /api/forecasting/train first.",
        )

    logger.debug("regime.cache_hit")
    return RegimeResult.model_validate(cached)


@router.get("/crisis-index", response_model=CrisisIndex)
async def get_crisis_index() -> CrisisIndex:
    """Return cached composite crisis index.

    Reads from Redis key 'ecpm:crisis:latest' -> versioned key -> JSON data.
    Returns 404 if no cached results exist.
    """
    redis = _get_redis()
    cached = await _get_cached_result(KEY_PREFIX_CRISIS, redis)

    if cached is None:
        logger.info("crisis.cache_miss")
        raise HTTPException(
            status_code=404,
            detail="No cached crisis index available. Run POST /api/forecasting/train first.",
        )

    logger.debug("crisis.cache_hit")
    return CrisisIndex.model_validate(cached)


@router.get("/backtests", response_model=BacktestsResponse)
async def get_backtests() -> BacktestsResponse:
    """Return cached backtest results.

    Reads from Redis key 'ecpm:backtests:latest' -> versioned key -> JSON data.
    Returns 404 if no cached results exist.
    """
    redis = _get_redis()
    cached = await _get_cached_result(KEY_PREFIX_BACKTESTS, redis)

    if cached is None:
        logger.info("backtests.cache_miss")
        raise HTTPException(
            status_code=404,
            detail="No cached backtest results available. Run POST /api/forecasting/train first.",
        )

    logger.debug("backtests.cache_hit")
    return BacktestsResponse.model_validate(cached)


@router.post("/train", status_code=202)
async def trigger_training() -> dict:
    """Trigger model training pipeline.

    Calls run_training_pipeline.delay() to start async Celery task.
    Returns 202 Accepted with task_id for tracking.
    """
    try:
        from ecpm.tasks.training_tasks import run_training_pipeline

        result = run_training_pipeline.delay()
        task_id = result.id

        logger.info("training.triggered", task_id=task_id)

        return {"task_id": task_id, "status": "accepted"}

    except ImportError:
        logger.error("training.import_failed")
        raise HTTPException(
            status_code=503,
            detail="Training tasks not available. Is Celery running?",
        )
    except Exception as exc:
        logger.error("training.trigger_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger training: {str(exc)}",
        )


@router.get("/training/stream")
async def training_progress_stream():
    """SSE endpoint for training progress events.

    Subscribes to Redis pubsub channel 'ecpm:training:progress'.
    Yields SSE events with JSON data from pubsub messages.

    Headers:
        Cache-Control: no-cache
        Connection: keep-alive
        Content-Type: text/event-stream
    """
    redis = _get_redis()

    if redis is None:
        raise HTTPException(
            status_code=503,
            detail="Redis not available for progress streaming",
        )

    async def event_generator():
        """Generate SSE events from Redis pubsub."""
        pubsub = redis.pubsub()

        try:
            await pubsub.subscribe(PROGRESS_CHANNEL)
            logger.debug("training_stream.subscribed", channel=PROGRESS_CHANNEL)

            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "channel": PROGRESS_CHANNEL}),
            }

            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=30.0,
                    )

                    if message is not None and message["type"] == "message":
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")

                        yield {
                            "event": "progress",
                            "data": data,
                        }

                        # Check if training is complete
                        try:
                            parsed = json.loads(data)
                            if parsed.get("step") == "pipeline" and parsed.get("status") in ("complete", "error"):
                                logger.debug("training_stream.pipeline_finished")
                                yield {
                                    "event": "done",
                                    "data": json.dumps({"status": parsed.get("status")}),
                                }
                                break
                        except json.JSONDecodeError:
                            pass

                except asyncio.TimeoutError:
                    # Send keepalive ping every 30s
                    yield {
                        "event": "ping",
                        "data": json.dumps({"status": "waiting"}),
                    }

        except asyncio.CancelledError:
            logger.debug("training_stream.cancelled")
            raise
        finally:
            await pubsub.unsubscribe(PROGRESS_CHANNEL)
            await pubsub.close()

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
