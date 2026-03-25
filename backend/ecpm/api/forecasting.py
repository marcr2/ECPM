"""Forecasting API endpoints with SSE streaming for training progress.

Provides:
- GET /api/forecasting/forecasts -- Cached VECM forecast results
- GET /api/forecasting/regime -- Cached regime detection results
- GET /api/forecasting/crisis-index -- Cached composite crisis index
- GET /api/forecasting/backtests -- Cached backtest results
- POST /api/forecasting/train -- Trigger model training pipeline (auth required)
- GET /api/forecasting/training/stream -- SSE stream of training progress
- GET /api/forecasting/training/log -- Latest persisted training log

All GET endpoints read from Redis cache via versioned keys with "latest" pointers.
The training pipeline fits a Vector Error Correction Model (VECM) with
Johansen-selected cointegration rank and recursive residual bootstrap CIs.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ecpm.config import get_settings
from ecpm.middleware.rate_limit import RATE_READ, RATE_TRAINING, RATE_WRITE, limiter

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

# Redis key for persisted training log (must match training_tasks.py)
TRAINING_LOG_KEY = "ecpm:training:log"

# Training lock key and TTL (1 hour)
TRAINING_LOCK_KEY = "ecpm:training:lock"
TRAINING_LOCK_TTL = 3600


async def require_training_auth(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> str:
    """Authenticate training requests via JWT or static training token.

    Accepts either:
      - Standard JWT Bearer token (same as require_auth)
      - Static training token: ``Bearer <TRAINING_TOKEN>`` from settings
    """
    settings = get_settings()

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    # Check static training token first
    if settings.training_token and token == settings.training_token:
        logger.info("training.auth_via_token")
        return "training-token"

    # Fall back to JWT
    from ecpm.auth.jwt import decode_access_token
    from jose import JWTError

    try:
        token_data = decode_access_token(token)
        return token_data.username
    except (JWTError, Exception):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Response models
class TrainingStartResponse(BaseModel):
    """Response for POST /train endpoint."""

    task_id: str
    status: str = "accepted"


class TaskStatusResponse(BaseModel):
    """Response for GET /train/{task_id} endpoint."""

    task_id: str
    status: str
    result: Optional[dict] = None


class TrainingLogEntry(BaseModel):
    """Single training log entry."""

    name: str
    status: str
    timestamp: str
    duration_ms: Optional[int] = None
    detail: Optional[str] = None
    error: Optional[str] = None


class TrainingLogResponse(BaseModel):
    """Response for GET /training/log endpoint."""

    entries: list[TrainingLogEntry]
    count: int


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
            # Versioned key expired after reading latest pointer
            logger.warning("cache.expired_version", prefix=prefix, version=latest_key)
            return None

        return json.loads(data)

    except json.JSONDecodeError as e:
        logger.error("cache.corrupt_data", prefix=prefix, error=str(e))
        return None
    except Exception:
        logger.warning("cache.get_failed", prefix=prefix, exc_info=True)
        return None


async def _check_training_in_progress(redis) -> bool:
    """Check if training pipeline is already running."""
    if redis is None:
        return False
    lock_value = await redis.get(TRAINING_LOCK_KEY)
    return lock_value is not None


async def _set_training_lock(redis, task_id: str) -> None:
    """Set training lock with TTL to prevent concurrent runs."""
    if redis is not None:
        await redis.setex(TRAINING_LOCK_KEY, TRAINING_LOCK_TTL, task_id)


@router.get("/forecasts", response_model=ForecastsResponse)
@limiter.limit(RATE_READ)
async def get_forecasts(
    request: Request,
    indicator: Optional[str] = Query(None, description="Filter by indicator slug"),
    horizon: int = Query(40, ge=1, le=40, description="Forecast horizon in quarters"),
) -> ForecastsResponse:
    """Return cached VECM forecast results.

    Reads from Redis key 'ecpm:forecasts:latest' -> versioned key -> JSON data.
    Returns 404 if no cached results exist.
    """
    # Validate indicator slug if provided
    if indicator is not None:
        from ecpm.indicators.definitions import IndicatorSlug

        valid_slugs = [s.value for s in IndicatorSlug]
        if indicator not in valid_slugs:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid indicator: {indicator}. Must be one of: {', '.join(valid_slugs)}",
            )

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
@limiter.limit(RATE_READ)
async def get_regime(request: Request) -> RegimeResult:
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
@limiter.limit(RATE_READ)
async def get_crisis_index(request: Request) -> CrisisIndex:
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
@limiter.limit(RATE_READ)
async def get_backtests(request: Request) -> BacktestsResponse:
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


@router.post("/train", status_code=202, response_model=TrainingStartResponse)
@limiter.limit(RATE_TRAINING)
async def trigger_training(
    request: Request,
    _identity: str = Depends(require_training_auth),
) -> TrainingStartResponse:
    """Trigger model training pipeline.

    Requires authentication via JWT Bearer token or static training token.
    Calls run_training_pipeline.delay() to start async Celery task.
    Returns 202 Accepted with task_id for tracking.

    Returns 409 if training is already in progress.
    """
    redis = _get_redis()

    # Check if training is already in progress
    if await _check_training_in_progress(redis):
        logger.warning("training.already_in_progress")
        raise HTTPException(
            status_code=409,
            detail="Training pipeline already in progress. Wait for completion or check /training/stream",
        )

    try:
        from ecpm.tasks.training_tasks import run_training_pipeline

        result = run_training_pipeline.delay()
        task_id = result.id

        # Set lock to prevent concurrent training runs
        await _set_training_lock(redis, task_id)

        logger.info("training.triggered", task_id=task_id)

        return TrainingStartResponse(task_id=task_id, status="accepted")

    except ImportError:
        logger.error("training.import_failed")
        raise HTTPException(
            status_code=503,
            detail="Training tasks not available. Is Celery running?",
        )
    except Exception:
        logger.error("training.trigger_failed", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger training pipeline",
        )


@router.get("/train/{task_id}", response_model=TaskStatusResponse)
@limiter.limit(RATE_READ)
async def get_training_status(
    request: Request,
    task_id: str,
    _identity: str = Depends(require_training_auth),
) -> TaskStatusResponse:
    """Check status of a training pipeline task.

    Returns the task status and result if complete.
    """
    try:
        from ecpm.tasks.celery_app import celery_app

        result = celery_app.AsyncResult(task_id)

        return TaskStatusResponse(
            task_id=task_id,
            status=result.state,
            result=result.result if result.ready() else None,
        )

    except ImportError:
        logger.error("training.celery_unavailable")
        raise HTTPException(
            status_code=503,
            detail="Celery not available",
        )
    except Exception:
        logger.error("training.status_check_failed", task_id=task_id, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Unable to check task status",
        )


@router.get("/training/log", response_model=TrainingLogResponse)
@limiter.limit(RATE_READ)
async def get_training_log(request: Request) -> TrainingLogResponse:
    """Return the persisted log from the most recent training run.

    Reads all entries from the Redis list at TRAINING_LOG_KEY.
    No authentication required (read-only, public dashboard data).
    """
    redis = _get_redis()

    if redis is None:
        raise HTTPException(status_code=503, detail="Redis not available")

    try:
        raw_entries = await redis.lrange(TRAINING_LOG_KEY, 0, -1)
    except Exception:
        logger.warning("training_log.read_failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Failed to read training log")

    entries: list[dict] = []
    for raw in raw_entries:
        try:
            entry = json.loads(raw)
            entries.append(entry)
        except json.JSONDecodeError:
            continue

    return TrainingLogResponse(entries=entries, count=len(entries))


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
                            if parsed.get("name") == "pipeline" and parsed.get("status") in ("complete", "error"):
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
