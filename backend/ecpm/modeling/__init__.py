"""Econometric modeling pipeline: VAR/SVAR forecasting, regime-switching, crisis index."""

from ecpm.modeling.backtest import run_all_backtests, run_episode
from ecpm.modeling.crisis_index import (
    DEFAULT_WEIGHTS,
    MECHANISM_INDICATORS,
    compute,
)
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
from ecpm.modeling.stationarity import check_stationarity, ensure_stationarity
from ecpm.modeling.svar_model import build_a_matrix, fit_svar
from ecpm.modeling.var_model import fit_var, forecast, get_indicator_forecasts

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
    # Stationarity
    "check_stationarity",
    "ensure_stationarity",
    # VAR
    "fit_var",
    "forecast",
    "get_indicator_forecasts",
    # SVAR
    "build_a_matrix",
    "fit_svar",
    # Regime switching
    "fit_regime_model",
    # Crisis index
    "compute",
    "MECHANISM_INDICATORS",
    "DEFAULT_WEIGHTS",
    # Backtest
    "run_episode",
    "run_all_backtests",
]
