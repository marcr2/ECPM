"""Celery tasks for model training pipeline.

Contains the training pipeline orchestrator and individual step tasks
that run the modeling pipeline: stationarity, VAR, SVAR, regime detection,
backtesting, and result caching.

Each step publishes progress to Redis pubsub channel "ecpm:training:progress".
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import structlog

from ecpm.tasks.celery_app import celery_app

logger = structlog.get_logger()

# Redis pubsub channel for training progress
PROGRESS_CHANNEL = "ecpm:training:progress"

# Redis key prefixes for versioned storage
KEY_PREFIX_FORECASTS = "ecpm:forecasts"
KEY_PREFIX_REGIME = "ecpm:regime"
KEY_PREFIX_CRISIS = "ecpm:crisis"
KEY_PREFIX_BACKTESTS = "ecpm:backtests"

# Cache TTL for versioned data (1 hour)
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
    """Publish training progress to Redis pubsub channel."""
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

    try:
        redis_client.publish(PROGRESS_CHANNEL, json.dumps(message))
    except Exception:
        logger.warning("progress_publish_failed", step=step, status=status)


@celery_app.task(
    name="ecpm.tasks.training_tasks.run_training_pipeline",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def run_training_pipeline(self: Any) -> dict[str, Any]:
    """Orchestrate the full model training pipeline.

    Executes 7 steps sequentially:
    1. Load indicator data from database
    2. Stationarity preprocessing
    3. VAR model fitting and forecasting
    4. SVAR model fitting
    5. Regime-switching detection
    6. Historical backtesting
    7. Cache results to Redis

    Returns:
        Dict with pipeline result summary.
    """
    logger.info("training_pipeline_start", task_id=self.request.id)
    pipeline_start = time.time()

    redis_client = _get_sync_redis()
    _publish_progress(redis_client, "pipeline", "running", detail="Starting training pipeline")

    try:
        # Step 1: Fetch indicator data from database
        _publish_progress(redis_client, "data_load", "running", detail="Loading indicator data")
        step_start = time.time()
        indicators_data = _load_indicators_data()
        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client,
            "data_load",
            "complete",
            duration_ms=duration_ms,
            detail=f"Loaded {len(indicators_data)} observations",
        )

        # Step 2: Stationarity
        stationarity_result = run_stationarity_step(indicators_data)

        # Step 3: VAR
        var_result = run_var_step(stationarity_result)

        # Step 4: SVAR
        svar_result = run_svar_step(stationarity_result)

        # Step 5: Regime detection
        regime_result = run_regime_step(indicators_data)

        # Step 6: Backtesting
        backtest_result = run_backtest_step(indicators_data)

        # Step 7: Cache results
        cache_results_step(var_result, svar_result, regime_result, backtest_result, indicators_data)

        pipeline_duration_ms = int((time.time() - pipeline_start) * 1000)
        _publish_progress(
            redis_client,
            "pipeline",
            "complete",
            duration_ms=pipeline_duration_ms,
            detail="Training pipeline complete",
        )

        logger.info(
            "training_pipeline_complete",
            task_id=self.request.id,
            duration_ms=pipeline_duration_ms,
        )

        return {
            "status": "complete",
            "task_id": self.request.id,
            "duration_ms": pipeline_duration_ms,
            "steps_completed": 7,
        }

    except Exception as exc:
        _publish_progress(
            redis_client,
            "pipeline",
            "error",
            error=str(exc),
            detail="Pipeline failed",
        )
        logger.error(
            "training_pipeline_error",
            task_id=self.request.id,
            error=str(exc),
        )
        raise


def _load_indicators_data() -> dict[str, Any]:
    """Load indicator data from database for training.

    Returns dict with 'dataframe' key containing pandas DataFrame
    and 'columns' key with column names.
    """
    import asyncio

    import pandas as pd

    from ecpm.database import async_session
    from ecpm.indicators.computation import compute_indicator
    from ecpm.indicators.definitions import IndicatorSlug

    async def _fetch_all_indicators():
        """Fetch all indicators and combine into DataFrame."""
        indicator_series = {}

        async with async_session() as session:
            for slug in IndicatorSlug:
                try:
                    series = await compute_indicator(
                        slug.value, "shaikh-tonak", session, redis=None
                    )
                    if series is not None and len(series) > 0:
                        indicator_series[slug.value] = series
                except Exception as e:
                    logger.warning(
                        "indicator_load_failed",
                        slug=slug.value,
                        error=str(e),
                    )

        if not indicator_series:
            raise ValueError("No indicator data available")

        # Combine into DataFrame
        df = pd.DataFrame(indicator_series)
        # Forward-fill and drop remaining NaN
        df = df.ffill().dropna()

        return df

    # Run async code in sync context
    # Use get_event_loop() instead of asyncio.run() to avoid conflicts
    # with existing event loops in Celery worker context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    df = loop.run_until_complete(_fetch_all_indicators())

    return {
        "dataframe": df,
        "columns": list(df.columns),
        "n_observations": len(df),
    }


@celery_app.task(
    name="ecpm.tasks.training_tasks.run_stationarity_step",
    bind=True,
)
def run_stationarity_step(self: Any, indicators_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Preprocess indicators DataFrame via ensure_stationarity.

    Parameters
    ----------
    indicators_data : dict
        Dict with 'dataframe' key containing pd.DataFrame.

    Returns
    -------
    dict
        Keys: stationary_data (as dict for serialization), diff_orders.
    """
    import pandas as pd

    from ecpm.modeling import ensure_stationarity

    redis_client = _get_sync_redis()
    _publish_progress(redis_client, "stationarity", "running", detail="Testing stationarity")
    step_start = time.time()

    try:
        # Handle both direct call and Celery task call patterns
        if indicators_data is None:
            indicators_data = _load_indicators_data()

        if isinstance(indicators_data, dict) and "dataframe" in indicators_data:
            df = indicators_data["dataframe"]
            if isinstance(df, dict):
                df = pd.DataFrame(df)
        else:
            raise ValueError("Invalid indicators_data format")

        stationary_df, diff_orders = ensure_stationarity(df)

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client,
            "stationarity",
            "complete",
            duration_ms=duration_ms,
            detail=f"Differenced {sum(1 for d in diff_orders.values() if d > 0)} columns",
        )

        logger.info(
            "stationarity_step_complete",
            diff_orders=diff_orders,
            duration_ms=duration_ms,
        )

        return {
            "stationary_data": stationary_df.to_dict(),
            "stationary_index": [str(idx) for idx in stationary_df.index],
            "original_data": df.to_dict(),
            "original_index": [str(idx) for idx in df.index],
            "diff_orders": diff_orders,
            "columns": list(df.columns),
        }

    except Exception as exc:
        _publish_progress(
            redis_client,
            "stationarity",
            "error",
            error=str(exc),
        )
        logger.error("stationarity_step_error", error=str(exc))
        raise


@celery_app.task(
    name="ecpm.tasks.training_tasks.run_var_step",
    bind=True,
)
def run_var_step(self: Any, stationarity_result: dict[str, Any]) -> dict[str, Any]:
    """Fit VAR model and generate forecasts.

    Parameters
    ----------
    stationarity_result : dict
        Output from run_stationarity_step.

    Returns
    -------
    dict
        Keys: forecasts (per-indicator), lag_order, aic, model_info.
    """
    import pandas as pd

    from ecpm.modeling import fit_var, get_indicator_forecasts

    redis_client = _get_sync_redis()
    _publish_progress(redis_client, "var", "running", detail="Fitting VAR model")
    step_start = time.time()

    try:
        # Reconstruct DataFrame from serialized data
        df = pd.DataFrame(stationarity_result["original_data"])
        df.index = pd.DatetimeIndex(stationarity_result["original_index"])

        var_result = fit_var(df, max_lags=12, ensure_stationary=True)
        forecasts = get_indicator_forecasts(var_result, steps=8)

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client,
            "var",
            "complete",
            duration_ms=duration_ms,
            detail=f"Lag order: {var_result['lag_order']}, AIC: {var_result['aic']:.2f}",
        )

        logger.info(
            "var_step_complete",
            lag_order=var_result["lag_order"],
            aic=var_result["aic"],
            duration_ms=duration_ms,
        )

        return {
            "forecasts": forecasts,
            "lag_order": var_result["lag_order"],
            "aic": var_result["aic"],
            "bic": var_result["bic"],
            "diff_orders": var_result["diff_orders"],
            "model_info": {
                "lag_order": var_result["lag_order"],
                "aic": var_result["aic"],
                "bic": var_result["bic"],
                "differenced": any(d > 0 for d in var_result["diff_orders"].values()),
            },
        }

    except Exception as exc:
        _publish_progress(redis_client, "var", "error", error=str(exc))
        logger.error("var_step_error", error=str(exc))
        raise


@celery_app.task(
    name="ecpm.tasks.training_tasks.run_svar_step",
    bind=True,
)
def run_svar_step(self: Any, stationarity_result: dict[str, Any]) -> dict[str, Any]:
    """Fit SVAR model with Marxist A-matrix.

    Parameters
    ----------
    stationarity_result : dict
        Output from run_stationarity_step.

    Returns
    -------
    dict
        Keys: a_matrix (estimated), fit_success.
    """
    import pandas as pd

    from ecpm.modeling import fit_svar

    redis_client = _get_sync_redis()
    _publish_progress(redis_client, "svar", "running", detail="Fitting SVAR with Marxist causal ordering")
    step_start = time.time()

    try:
        df = pd.DataFrame(stationarity_result["original_data"])
        df.index = pd.DatetimeIndex(stationarity_result["original_index"])

        svar_result = fit_svar(df, max_lags=12)

        duration_ms = int((time.time() - step_start) * 1000)

        if svar_result is not None:
            _publish_progress(
                redis_client,
                "svar",
                "complete",
                duration_ms=duration_ms,
                detail="SVAR estimation converged",
            )
            a_matrix = svar_result["a_matrix_estimated"].tolist()
            fit_success = True
        else:
            _publish_progress(
                redis_client,
                "svar",
                "complete",
                duration_ms=duration_ms,
                detail="SVAR did not converge (using VAR only)",
            )
            a_matrix = None
            fit_success = False

        logger.info(
            "svar_step_complete",
            fit_success=fit_success,
            duration_ms=duration_ms,
        )

        return {
            "a_matrix": a_matrix,
            "fit_success": fit_success,
        }

    except Exception as exc:
        _publish_progress(redis_client, "svar", "error", error=str(exc))
        logger.error("svar_step_error", error=str(exc))
        raise


@celery_app.task(
    name="ecpm.tasks.training_tasks.run_regime_step",
    bind=True,
)
def run_regime_step(self: Any, indicators_data: dict[str, Any]) -> dict[str, Any]:
    """Detect regime states via fit_regime_model on composite crisis index.

    Parameters
    ----------
    indicators_data : dict
        Dict with 'dataframe' key containing pd.DataFrame.

    Returns
    -------
    dict
        RegimeResult-compatible dict.
    """
    import pandas as pd

    from ecpm.modeling import compute as compute_crisis_index
    from ecpm.modeling import fit_regime_model

    redis_client = _get_sync_redis()
    _publish_progress(redis_client, "regime", "running", detail="Detecting economic regimes")
    step_start = time.time()

    try:
        if isinstance(indicators_data, dict) and "dataframe" in indicators_data:
            df = indicators_data["dataframe"]
            if isinstance(df, dict):
                df = pd.DataFrame(df)
        else:
            raise ValueError("Invalid indicators_data format")

        # Compute crisis index
        crisis_result = compute_crisis_index(df)

        # Extract composite series for regime detection
        history = crisis_result["history"]
        dates = pd.DatetimeIndex([entry["date"] for entry in history])
        composite_series = pd.Series(
            [entry["composite"] for entry in history],
            index=dates,
            name="composite_crisis_index",
        )

        # Fit regime model
        regime_result = fit_regime_model(composite_series, max_regimes=3, order=2)

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client,
            "regime",
            "complete",
            duration_ms=duration_ms,
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


@celery_app.task(
    name="ecpm.tasks.training_tasks.run_backtest_step",
    bind=True,
)
def run_backtest_step(self: Any, indicators_data: dict[str, Any]) -> dict[str, Any]:
    """Run historical backtesting via run_all_backtests.

    Parameters
    ----------
    indicators_data : dict
        Dict with 'dataframe' key containing pd.DataFrame.

    Returns
    -------
    dict
        Keys: backtests (list of BacktestResult dicts).
    """
    import pandas as pd

    from ecpm.modeling import run_all_backtests

    redis_client = _get_sync_redis()
    _publish_progress(redis_client, "backtest", "running", detail="Running historical backtests")
    step_start = time.time()

    try:
        if isinstance(indicators_data, dict) and "dataframe" in indicators_data:
            df = indicators_data["dataframe"]
            if isinstance(df, dict):
                df = pd.DataFrame(df)
        else:
            raise ValueError("Invalid indicators_data format")

        backtests = run_all_backtests(df)

        # Count warning successes
        warning_12m_count = sum(1 for bt in backtests if bt["warning_12m"])
        warning_24m_count = sum(1 for bt in backtests if bt["warning_24m"])

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client,
            "backtest",
            "complete",
            duration_ms=duration_ms,
            detail=f"{len(backtests)} episodes, {warning_12m_count}/6 12m warnings, {warning_24m_count}/6 24m warnings",
        )

        logger.info(
            "backtest_step_complete",
            n_episodes=len(backtests),
            warning_12m_count=warning_12m_count,
            warning_24m_count=warning_24m_count,
            duration_ms=duration_ms,
        )

        return {"backtests": backtests}

    except Exception as exc:
        _publish_progress(redis_client, "backtest", "error", error=str(exc))
        logger.error("backtest_step_error", error=str(exc))
        raise


@celery_app.task(
    name="ecpm.tasks.training_tasks.cache_results_step",
    bind=True,
)
def cache_results_step(
    self: Any,
    var_result: dict[str, Any],
    svar_result: dict[str, Any],
    regime_result: dict[str, Any],
    backtest_result: dict[str, Any],
    indicators_data: dict[str, Any],
) -> dict[str, Any]:
    """Store versioned results in Redis with atomic pointer swap.

    Uses versioned keys (e.g., ecpm:forecasts:v{timestamp}) and atomic
    pointer swap for consistent reads.

    Parameters
    ----------
    var_result : dict
        VAR/forecast results.
    svar_result : dict
        SVAR results.
    regime_result : dict
        Regime detection results.
    backtest_result : dict
        Backtest results.
    indicators_data : dict
        Original indicator data.

    Returns
    -------
    dict
        Keys: version, cached_keys.
    """
    import pandas as pd

    from ecpm.modeling import compute as compute_crisis_index

    redis_client = _get_sync_redis()
    _publish_progress(redis_client, "cache", "running", detail="Caching results to Redis")
    step_start = time.time()

    try:
        # Generate version timestamp with milliseconds to prevent collisions
        version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:17]  # Include milliseconds
        generated_at = datetime.now(timezone.utc).isoformat()

        # Build forecast response
        forecasts_response = {
            "forecasts": {},
            "generated_at": generated_at,
        }
        for indicator, fc in var_result["forecasts"].items():
            forecasts_response["forecasts"][indicator] = {
                "indicator": indicator,
                "horizon_quarters": 8,
                "forecasts": _build_forecast_points(fc),
                "model_info": var_result["model_info"],
            }

        # Build crisis index from original data
        if isinstance(indicators_data, dict) and "dataframe" in indicators_data:
            df = indicators_data["dataframe"]
            if isinstance(df, dict):
                df = pd.DataFrame(df)
        else:
            df = pd.DataFrame()

        if len(df) > 0:
            crisis_result = compute_crisis_index(df)
        else:
            crisis_result = {
                "current_value": 0.0,
                "trpf_component": 0.0,
                "realization_component": 0.0,
                "financial_component": 0.0,
                "history": [],
            }

        # Build backtests response
        backtests_response = {
            "backtests": backtest_result["backtests"],
            "generated_at": generated_at,
        }

        # Store with versioned keys
        versioned_keys = {
            f"{KEY_PREFIX_FORECASTS}:v{version}": forecasts_response,
            f"{KEY_PREFIX_REGIME}:v{version}": regime_result,
            f"{KEY_PREFIX_CRISIS}:v{version}": crisis_result,
            f"{KEY_PREFIX_BACKTESTS}:v{version}": backtests_response,
        }

        # Write versioned data with TTL
        for key, data in versioned_keys.items():
            redis_client.setex(key, CACHE_TTL, json.dumps(data))

        # Atomic pointer swap using Redis pipeline (no TTL on pointers)
        pipe = redis_client.pipeline()
        pipe.set(f"{KEY_PREFIX_FORECASTS}:latest", f"{KEY_PREFIX_FORECASTS}:v{version}")
        pipe.set(f"{KEY_PREFIX_REGIME}:latest", f"{KEY_PREFIX_REGIME}:v{version}")
        pipe.set(f"{KEY_PREFIX_CRISIS}:latest", f"{KEY_PREFIX_CRISIS}:v{version}")
        pipe.set(f"{KEY_PREFIX_BACKTESTS}:latest", f"{KEY_PREFIX_BACKTESTS}:v{version}")
        pipe.execute()

        duration_ms = int((time.time() - step_start) * 1000)
        _publish_progress(
            redis_client,
            "cache",
            "complete",
            duration_ms=duration_ms,
            detail=f"Cached {len(versioned_keys)} result sets with version {version}",
        )

        logger.info(
            "cache_step_complete",
            version=version,
            n_keys=len(versioned_keys),
            duration_ms=duration_ms,
        )

        return {
            "version": version,
            "cached_keys": list(versioned_keys.keys()),
        }

    except Exception as exc:
        _publish_progress(redis_client, "cache", "error", error=str(exc))
        logger.error("cache_step_error", error=str(exc))
        raise


def _build_forecast_points(forecast_data: dict[str, list]) -> list[dict]:
    """Convert forecast arrays to ForecastPoint-compatible list of dicts.

    Generates quarterly dates starting from next quarter.
    """
    from datetime import date
    from dateutil.relativedelta import relativedelta

    # Start from next quarter
    today = date.today()
    # Align to quarter start
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
