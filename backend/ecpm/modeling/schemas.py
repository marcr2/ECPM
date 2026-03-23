"""Pydantic v2 response models for the econometric modeling pipeline.

Defines the API contract for forecasts, regime detection, crisis index,
backtesting, and training status endpoints. All models follow the existing
pattern established in ecpm/schemas/series.py.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class TrainingStep(BaseModel):
    """A single step in the model training pipeline."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    status: str  # "pending" | "running" | "complete" | "error"
    duration_ms: Optional[int] = None
    detail: Optional[str] = None


class TrainingStatus(BaseModel):
    """Overall training pipeline status with per-step progress."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str
    status: str  # "idle" | "running" | "complete" | "error"
    current_step: str
    steps: list[TrainingStep]
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ForecastPoint(BaseModel):
    """A single forecast data point with confidence intervals."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    point: float
    lower_68: float
    upper_68: float
    lower_95: float
    upper_95: float


class IndicatorForecast(BaseModel):
    """Forecast results for a single indicator.

    model_info includes: lag_order, aic, differencing_order.
    """

    model_config = ConfigDict(from_attributes=True)

    indicator: str
    horizon_quarters: int
    forecasts: list[ForecastPoint]
    model_info: dict


class RegimeResult(BaseModel):
    """Regime-switching model detection results.

    smoothed_probabilities entries: {date, regime_0, regime_1, ...}
    """

    model_config = ConfigDict(from_attributes=True)

    current_regime: int
    regime_label: str
    regime_probabilities: dict[str, float]
    transition_matrix: list[list[float]]
    smoothed_probabilities: list[dict]
    regime_durations: Optional[dict[str, float]] = None


class CrisisIndex(BaseModel):
    """Composite crisis index with mechanism decomposition.

    history entries: {date, composite, trpf, realization, financial}
    """

    model_config = ConfigDict(from_attributes=True)

    current_value: float
    trpf_component: float
    realization_component: float
    financial_component: float
    history: list[dict]


class BacktestResult(BaseModel):
    """Backtest results for a single historical crisis episode.

    crisis_index_series entries: {date, value}
    """

    model_config = ConfigDict(from_attributes=True)

    episode_name: str
    start_date: str
    end_date: str
    crisis_index_series: list[dict]
    warning_12m: bool
    warning_24m: bool
    peak_value: float
    peak_date: str


class ForecastsResponse(BaseModel):
    """Response wrapper for all indicator forecasts."""

    model_config = ConfigDict(from_attributes=True)

    forecasts: dict[str, IndicatorForecast]
    generated_at: str


class BacktestsResponse(BaseModel):
    """Response wrapper for all backtest results."""

    model_config = ConfigDict(from_attributes=True)

    backtests: list[BacktestResult]
    generated_at: str
