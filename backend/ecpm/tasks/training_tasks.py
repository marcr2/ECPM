"""Celery tasks for model training pipeline.

Contains the training pipeline orchestrator and individual step tasks
that run the modeling pipeline: VECM forecasting, learned crisis weights,
regime detection, backtesting, and result caching.

Each step publishes progress to Redis pubsub channel "ecpm:training:progress".
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np
import structlog

from ecpm.tasks.celery_app import celery_app

logger = structlog.get_logger()


class _NumpyEncoder(json.JSONEncoder):
    """Handle NumPy scalars/arrays that stdlib json cannot serialize."""

    def default(self, o: Any) -> Any:
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, np.bool_):
            return bool(o)
        return super().default(o)

PROGRESS_CHANNEL = "ecpm:training:progress"
TRAINING_LOG_KEY = "ecpm:training:log"
TRAINING_LOG_TTL = 86400 * 7

KEY_PREFIX_FORECASTS = "ecpm:forecasts"
KEY_PREFIX_REGIME = "ecpm:regime"
KEY_PREFIX_CRISIS = "ecpm:crisis"
KEY_PREFIX_BACKTESTS = "ecpm:backtests"

CACHE_TTL = 3600


def _get_sync_redis():
    """Get a synchronous Redis client for Celery task context."""
    import redis

    from ecpm.config import get_settings

    settings = get_settings()
    return redis.StrictRedis.from_url(settings.redis_url, decode_responses=True)


def _publish_progress(
    redis_client: Any,
    step: str,
    status: str,
    duration_ms: int | None = None,
    detail: str | None = None,
    error: str | None = None,
) -> None:
    """Publish training progress to Redis pubsub and persist to log list."""
    message = {
        "name": step,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if duration_ms is not None:
        message["duration_ms"] = duration_ms
    if detail is not None:
        message["detail"] = detail
    if error is not None:
        message["error"] = error

    serialized = json.dumps(message, cls=_NumpyEncoder)

    try:
        redis_client.publish(PROGRESS_CHANNEL, serialized)
    except Exception:
        logger.warning("progress_publish_failed", step=step, status=status)

    try:
        redis_client.rpush(TRAINING_LOG_KEY, serialized)
        redis_client.expire(TRAINING_LOG_KEY, TRAINING_LOG_TTL)
    except Exception:
        logger.warning("progress_persist_failed", step=step, status=status)


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

@celery_app.task(
    name="ecpm.tasks.training_tasks.run_training_pipeline",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def run_training_pipeline(self: Any) -> dict[str, Any]:
    """Orchestrate the full model training pipeline.

    Steps:
    1. Load indicator data + USREC from database
    2. Fit VECM and generate forecasts
    3. Learn crisis weights via logistic regression
    4. Regime-switching detection
    5. Historical backtesting
    6. Cache results to Redis
    """
    logger.info("training_pipeline_start", task_id=self.request.id)
    pipeline_start = time.time()

    redis_client = _get_sync_redis()
    redis_client.delete(TRAINING_LOG_KEY)

    _publish_progress(redis_client, "pipeline", "running", detail="Starting training pipeline")

    try:
        # Step 1: Load data
        _publish_progress(redis_client, "data_load", "running", detail="Loading indicator data + USREC")
        step_start = time.time()
        indicators_data = _load_indicators_data()
        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client,
            "data_load",
            "complete",
            duration_ms=duration_ms,
            detail=f"Loaded {indicators_data['n_observations']} observations across {len(indicators_data['columns'])} indicators",
        )

        # Step 2: VECM
        vecm_result = _run_vecm_step(indicators_data, redis_client)

        # Step 3: Learn crisis weights
        crisis_result = _run_crisis_weights_step(indicators_data, redis_client)

        # Step 4: Regime detection
        regime_result = _run_regime_step(crisis_result, redis_client)

        # Step 5: Backtesting
        backtest_result = _run_backtest_step(indicators_data, crisis_result, redis_client)

        # Step 6: Cache
        _cache_results_step(
            vecm_result, crisis_result, regime_result,
            backtest_result, redis_client,
        )

        pipeline_duration_ms = int((time.time() - pipeline_start) * 1000)
        _publish_progress(
            redis_client, "pipeline", "complete",
            duration_ms=pipeline_duration_ms, detail="Training pipeline complete",
        )

        logger.info("training_pipeline_complete", task_id=self.request.id, duration_ms=pipeline_duration_ms)

        return {
            "status": "complete",
            "task_id": self.request.id,
            "duration_ms": pipeline_duration_ms,
            "steps_completed": 6,
        }

    except Exception as exc:
        _publish_progress(redis_client, "pipeline", "error", error=str(exc), detail="Pipeline failed")
        logger.error("training_pipeline_error", task_id=self.request.id, error=str(exc))
        raise


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_indicators_data() -> dict[str, Any]:
    """Load indicator data and USREC from database.

    Returns dict with 'dataframe' (indicators), 'usrec' (pd.Series),
    'columns', 'n_observations'.
    """
    import asyncio

    import pandas as pd

    from ecpm.indicators.computation import compute_indicator
    from ecpm.indicators.definitions import IndicatorSlug

    async def _fetch():
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import (
            AsyncSession,
            async_sessionmaker,
            create_async_engine,
        )

        from ecpm.config import get_settings
        from ecpm.models.observation import Observation

        settings = get_settings()
        local_engine = create_async_engine(
            settings.database_url, pool_size=3, max_overflow=2, echo=False
        )
        local_session = async_sessionmaker(
            local_engine, class_=AsyncSession, expire_on_commit=False
        )

        indicator_series = {}
        usrec_series = pd.Series(dtype=float)

        try:
            # Load indicators
            for slug in IndicatorSlug:
                async with local_session() as session:
                    try:
                        series = await compute_indicator(
                            slug.value, "shaikh-tonak", session, redis=None
                        )
                        if series is not None and len(series) > 0:
                            indicator_series[slug.value] = series
                    except Exception as e:
                        await session.rollback()
                        logger.warning("indicator_load_failed", slug=slug.value, error=str(e))

            # Load USREC
            async with local_session() as session:
                try:
                    stmt = (
                        select(Observation.observation_date, Observation.value)
                        .where(Observation.series_id == "USREC")
                        .order_by(Observation.observation_date)
                    )
                    result = await session.execute(stmt)
                    rows = result.all()
                    if rows:
                        dates = pd.DatetimeIndex([r[0] for r in rows])
                        values = [float(r[1]) if r[1] is not None else 0.0 for r in rows]
                        usrec_series = pd.Series(values, index=dates, name="USREC")
                        logger.info("usrec_loaded", count=len(usrec_series))
                    else:
                        logger.warning("usrec_empty")
                except Exception as e:
                    await session.rollback()
                    logger.warning("usrec_load_failed", error=str(e))
        finally:
            await local_engine.dispose()

        if not indicator_series:
            raise ValueError("No indicator data available")

        df = pd.DataFrame(indicator_series)
        df = df.ffill().dropna()

        return df, usrec_series

    df, usrec = asyncio.run(_fetch())

    return {
        "dataframe": df,
        "usrec": usrec,
        "columns": list(df.columns),
        "n_observations": len(df),
    }


# ---------------------------------------------------------------------------
# Step 2: VECM
# ---------------------------------------------------------------------------

def _run_vecm_step(indicators_data: dict[str, Any], redis_client: Any) -> dict[str, Any]:
    """Fit VECM model and generate forecasts."""
    import pandas as pd

    from ecpm.modeling.vecm_model import fit_vecm, get_indicator_forecasts

    _publish_progress(redis_client, "vecm", "running", detail="Fitting VECM (cointegration-aware)")
    step_start = time.time()

    try:
        df = indicators_data["dataframe"]
        if isinstance(df, dict):
            df = pd.DataFrame(df)

        vecm_result = fit_vecm(df, max_lags=12)
        forecasts = get_indicator_forecasts(vecm_result, steps=40)

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client, "vecm", "complete", duration_ms=duration_ms,
            detail=f"Cointegration rank: {vecm_result['coint_rank']}, lags: {vecm_result['k_ar_diff']}",
        )

        logger.info(
            "vecm_step_complete",
            coint_rank=vecm_result["coint_rank"],
            k_ar_diff=vecm_result["k_ar_diff"],
            duration_ms=duration_ms,
        )

        return {
            "forecasts": forecasts,
            "model_info": {
                "model_type": "vecm",
                "cointegration_rank": vecm_result["coint_rank"],
                "k_ar_diff": vecm_result["k_ar_diff"],
                "det_order": vecm_result["det_order"],
            },
        }

    except Exception as exc:
        _publish_progress(redis_client, "vecm", "error", error=str(exc))
        logger.error("vecm_step_error", error=str(exc))
        raise


# ---------------------------------------------------------------------------
# Step 3: Crisis weights (logistic regression)
# ---------------------------------------------------------------------------

def _run_crisis_weights_step(
    indicators_data: dict[str, Any], redis_client: Any
) -> dict[str, Any]:
    """Learn crisis mechanism weights and compute crisis index."""
    import pandas as pd

    from ecpm.modeling.crisis_index import compute
    from ecpm.modeling.crisis_target import build_crisis_target

    _publish_progress(
        redis_client, "crisis_weights", "running",
        detail="Learning crisis weights via logistic regression",
    )
    step_start = time.time()

    try:
        df = indicators_data["dataframe"]
        if isinstance(df, dict):
            df = pd.DataFrame(df)

        usrec = indicators_data.get("usrec", pd.Series(dtype=float))

        crisis_target = None
        if len(usrec) > 24:
            crisis_target = build_crisis_target(usrec, target_index=df.index)

        crisis_result = compute(df, crisis_target=crisis_target)

        duration_ms = int((time.time() - step_start) * 1000)

        weights_info = crisis_result.get("learned_weights")
        if weights_info:
            w = weights_info["weights"]
            detail = (
                f"Learned weights: TRPF={w.get('trpf', 0):.2f}, "
                f"Real={w.get('realization', 0):.2f}, "
                f"Fin={w.get('financial', 0):.2f} "
                f"(CV AUC={weights_info.get('cv_auc', 0):.2f})"
            )
        else:
            detail = "Using default equal weights (USREC data unavailable)"

        _publish_progress(
            redis_client, "crisis_weights", "complete",
            duration_ms=duration_ms, detail=detail,
        )

        logger.info("crisis_weights_step_complete", duration_ms=duration_ms)

        return crisis_result

    except Exception as exc:
        _publish_progress(redis_client, "crisis_weights", "error", error=str(exc))
        logger.error("crisis_weights_step_error", error=str(exc))
        raise


# ---------------------------------------------------------------------------
# Step 4: Regime detection
# ---------------------------------------------------------------------------

def _run_regime_step(
    crisis_result: dict[str, Any], redis_client: Any
) -> dict[str, Any]:
    """Detect regime states from crisis index."""
    import pandas as pd

    from ecpm.modeling.regime_switching import fit_regime_model

    _publish_progress(redis_client, "regime", "running", detail="Detecting economic regimes")
    step_start = time.time()

    try:
        history = crisis_result["history"]
        dates = pd.DatetimeIndex([entry["date"] for entry in history])
        composite_series = pd.Series(
            [entry["composite"] for entry in history],
            index=dates,
            name="composite_crisis_index",
        )

        regime_result = fit_regime_model(composite_series, max_regimes=3, order=2)

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client, "regime", "complete", duration_ms=duration_ms,
            detail=f"Current regime: {regime_result['regime_label']} ({regime_result['n_regimes']} regimes)",
        )

        logger.info(
            "regime_step_complete",
            current_regime=regime_result["regime_label"],
            n_regimes=regime_result["n_regimes"],
            duration_ms=duration_ms,
        )

        return regime_result

    except Exception as exc:
        _publish_progress(redis_client, "regime", "error", error=str(exc))
        logger.error("regime_step_error", error=str(exc))
        raise


# ---------------------------------------------------------------------------
# Step 5: Backtesting
# ---------------------------------------------------------------------------

def _run_backtest_step(
    indicators_data: dict[str, Any],
    crisis_result: dict[str, Any],
    redis_client: Any,
) -> dict[str, Any]:
    """Run historical backtesting."""
    import pandas as pd

    from ecpm.modeling.backtest import run_all_backtests

    _publish_progress(redis_client, "backtest", "running", detail="Running historical backtests")
    step_start = time.time()

    try:
        df = indicators_data["dataframe"]
        if isinstance(df, dict):
            df = pd.DataFrame(df)

        backtests = run_all_backtests(df)

        testable = [bt for bt in backtests if not bt.get("insufficient_data")]
        warning_12m_count = sum(1 for bt in testable if bt.get("warning_12m"))
        warning_24m_count = sum(1 for bt in testable if bt.get("warning_24m"))

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client, "backtest", "complete", duration_ms=duration_ms,
            detail=f"{len(testable)} testable episodes, {warning_12m_count} 12m warnings, {warning_24m_count} 24m warnings",
        )

        logger.info(
            "backtest_step_complete",
            n_episodes=len(backtests),
            n_testable=len(testable),
            warning_12m_count=warning_12m_count,
            warning_24m_count=warning_24m_count,
            duration_ms=duration_ms,
        )

        return {"backtests": backtests}

    except Exception as exc:
        _publish_progress(redis_client, "backtest", "error", error=str(exc))
        logger.error("backtest_step_error", error=str(exc))
        raise


# ---------------------------------------------------------------------------
# Step 6: Cache results
# ---------------------------------------------------------------------------

def _cache_results_step(
    vecm_result: dict[str, Any],
    crisis_result: dict[str, Any],
    regime_result: dict[str, Any],
    backtest_result: dict[str, Any],
    redis_client: Any,
) -> dict[str, Any]:
    """Store versioned results in Redis with atomic pointer swap."""
    _publish_progress(redis_client, "cache", "running", detail="Caching results to Redis")
    step_start = time.time()

    try:
        version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:17]
        generated_at = datetime.now(timezone.utc).isoformat()

        # Forecasts
        forecasts_response = {"forecasts": {}, "generated_at": generated_at}
        for indicator, fc in vecm_result["forecasts"].items():
            forecasts_response["forecasts"][indicator] = {
                "indicator": indicator,
                "horizon_quarters": 40,
                "forecasts": _build_forecast_points(fc),
                "model_info": vecm_result["model_info"],
            }

        # Backtests
        backtests_response = {
            "backtests": backtest_result["backtests"],
            "generated_at": generated_at,
        }

        versioned_keys = {
            f"{KEY_PREFIX_FORECASTS}:v{version}": forecasts_response,
            f"{KEY_PREFIX_REGIME}:v{version}": regime_result,
            f"{KEY_PREFIX_CRISIS}:v{version}": crisis_result,
            f"{KEY_PREFIX_BACKTESTS}:v{version}": backtests_response,
        }

        for key, data in versioned_keys.items():
            redis_client.setex(key, CACHE_TTL, json.dumps(data, cls=_NumpyEncoder))

        pipe = redis_client.pipeline()
        pipe.set(f"{KEY_PREFIX_FORECASTS}:latest", f"{KEY_PREFIX_FORECASTS}:v{version}")
        pipe.set(f"{KEY_PREFIX_REGIME}:latest", f"{KEY_PREFIX_REGIME}:v{version}")
        pipe.set(f"{KEY_PREFIX_CRISIS}:latest", f"{KEY_PREFIX_CRISIS}:v{version}")
        pipe.set(f"{KEY_PREFIX_BACKTESTS}:latest", f"{KEY_PREFIX_BACKTESTS}:v{version}")
        pipe.execute()

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client, "cache", "complete", duration_ms=duration_ms,
            detail=f"Cached {len(versioned_keys)} result sets with version {version}",
        )

        logger.info("cache_step_complete", version=version, n_keys=len(versioned_keys), duration_ms=duration_ms)

        return {"version": version, "cached_keys": list(versioned_keys.keys())}

    except Exception as exc:
        _publish_progress(redis_client, "cache", "error", error=str(exc))
        logger.error("cache_step_error", error=str(exc))
        raise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_forecast_points(forecast_data: dict[str, list]) -> list[dict]:
    """Convert forecast arrays to ForecastPoint-compatible list of dicts."""
    from datetime import date

    from dateutil.relativedelta import relativedelta

    today = date.today()
    quarter_month = ((today.month - 1) // 3 + 1) * 3 + 1
    if quarter_month > 12:
        quarter_month = 1
        next_q_year = today.year + 1
    else:
        next_q_year = today.year if quarter_month > today.month else today.year
    start_date = date(next_q_year, quarter_month, 1)

    points = []
    n_steps = len(forecast_data.get("point", []))

    for i in range(n_steps):
        forecast_date = start_date + relativedelta(months=3 * i)
        points.append({
            "date": forecast_date.isoformat(),
            "point": forecast_data["point"][i],
            "lower_68": forecast_data["lower_68"][i],
            "upper_68": forecast_data["upper_68"][i],
            "lower_95": forecast_data["lower_95"][i],
            "upper_95": forecast_data["upper_95"][i],
        })

    return points


# ---------------------------------------------------------------------------
# Celery task stubs for names referenced by celery_app
# ---------------------------------------------------------------------------

@celery_app.task(name="ecpm.tasks.training_tasks.run_stationarity_step", bind=True)
def run_stationarity_step(self: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Deprecated: stationarity is handled inside VECM."""
    return {"deprecated": True}


@celery_app.task(name="ecpm.tasks.training_tasks.run_var_step", bind=True)
def run_var_step(self: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Deprecated: replaced by VECM."""
    return {"deprecated": True}


@celery_app.task(name="ecpm.tasks.training_tasks.run_svar_step", bind=True)
def run_svar_step(self: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Deprecated: SVAR removed in favour of VECM."""
    return {"deprecated": True}


@celery_app.task(name="ecpm.tasks.training_tasks.run_regime_step", bind=True)
def run_regime_step(self: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Stub -- regime detection is now called inline from pipeline."""
    return {"deprecated": True}


@celery_app.task(name="ecpm.tasks.training_tasks.run_backtest_step", bind=True)
def run_backtest_step(self: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Stub -- backtesting is now called inline from pipeline."""
    return {"deprecated": True}


@celery_app.task(name="ecpm.tasks.training_tasks.cache_results_step", bind=True)
def cache_results_step(self: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Stub -- caching is now called inline from pipeline."""
    return {"deprecated": True}
