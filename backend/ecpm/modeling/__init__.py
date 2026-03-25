"""Econometric modeling pipeline: VECM forecasting, crisis index, regime-switching."""

from ecpm.modeling.backtest import run_all_backtests, run_episode
from ecpm.modeling.crisis_index import (
    DEFAULT_WEIGHTS,
    MECHANISM_INDICATORS,
    compute,
    compute_sub_indices,
    learn_weights,
)
from ecpm.modeling.crisis_target import build_crisis_target
from ecpm.modeling.regime_switching import fit_regime_model
from ecpm.modeling.schemas import (
    BacktestResult,
    BacktestsResponse,
    CrisisIndex,
    ForecastPoint,
    ForecastsResponse,
    IndicatorForecast,
    RegimeResult,
    TrainingStatus,
    TrainingStep,
)
from ecpm.modeling.vecm_model import fit_vecm, get_indicator_forecasts

__all__ = [
    # Schemas
    "BacktestResult",
    "BacktestsResponse",
    "CrisisIndex",
    "ForecastPoint",
    "ForecastsResponse",
    "IndicatorForecast",
    "RegimeResult",
    "TrainingStatus",
    "TrainingStep",
    # VECM
    "fit_vecm",
    "get_indicator_forecasts",
    # Regime switching
    "fit_regime_model",
    # Crisis index
    "compute",
    "compute_sub_indices",
    "learn_weights",
    "MECHANISM_INDICATORS",
    "DEFAULT_WEIGHTS",
    # Crisis target
    "build_crisis_target",
    # Backtest
    "run_episode",
    "run_all_backtests",
]
