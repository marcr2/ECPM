"""VAR model fitting with automatic lag selection and forecast generation.

Provides unrestricted Vector Autoregression fitting using AIC-optimal lag
selection, with forecast generation including 68% and 95% confidence
interval bands.

Exports:
    fit_var             -- fit VAR model with automatic lag selection
    forecast            -- generate point forecasts with CI bands (numpy arrays)
    get_indicator_forecasts -- per-indicator forecast dict with lists
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import structlog
from statsmodels.tsa.api import VAR

from ecpm.modeling.stationarity import ensure_stationarity

logger = structlog.get_logger(__name__)


def fit_var(
    data: pd.DataFrame,
    max_lags: int = 12,
    ensure_stationary: bool = True,
) -> dict:
    """Fit a VAR model with automatic AIC-optimal lag selection.

    Optionally preprocesses data through ``ensure_stationarity`` to
    difference non-stationary series before fitting.

    Parameters
    ----------
    data : pd.DataFrame
        Input time series data. Columns are endogenous variables.
    max_lags : int
        Maximum lag order to consider during selection (default 12).
    ensure_stationary : bool
        If True, run stationarity tests and difference if needed.

    Returns
    -------
    dict
        Keys: results (VARResults), lag_order (int), aic (float),
        bic (float), hqic (float), lag_criteria (dict),
        diff_orders (dict), original_data (DataFrame),
        stationary_data (DataFrame).
    """
    diff_orders: dict[str, int] = {col: 0 for col in data.columns}

    if ensure_stationary:
        stationary_data, diff_orders = ensure_stationarity(data)
    else:
        stationary_data = data.copy()

    model = VAR(stationary_data)

    # Select optimal lag order -- cap max_lags to available observations
    max_possible = max(1, len(stationary_data) // 3 - 1)
    effective_max_lags = min(max_lags, max_possible)

    lag_order_results = model.select_order(maxlags=effective_max_lags)

    # Use AIC-optimal lag; fall back to BIC if AIC returns 0
    selected_lag = lag_order_results.aic
    if selected_lag == 0:
        selected_lag = lag_order_results.bic
    if selected_lag == 0:
        selected_lag = 1  # absolute minimum

    logger.info(
        "var_lag_selection",
        selected_lag=selected_lag,
        aic_lag=lag_order_results.aic,
        bic_lag=lag_order_results.bic,
        max_lags=effective_max_lags,
    )

    results = model.fit(selected_lag)

    return {
        "results": results,
        "lag_order": selected_lag,
        "aic": float(results.aic),
        "bic": float(results.bic),
        "hqic": float(results.hqic),
        "lag_criteria": {
            "aic": lag_order_results.aic,
            "bic": lag_order_results.bic,
            "hqic": lag_order_results.hqic,
            "fpe": lag_order_results.fpe,
        },
        "diff_orders": diff_orders,
        "original_data": data,
        "stationary_data": stationary_data,
    }


def forecast(
    var_result: dict,
    steps: int = 8,
) -> dict:
    """Generate point forecasts with 68% and 95% confidence intervals.

    Parameters
    ----------
    var_result : dict
        Output from ``fit_var``.
    steps : int
        Number of steps ahead to forecast (default 8 quarters).

    Returns
    -------
    dict
        Keys: point_forecasts (ndarray), lower_68, upper_68,
        lower_95, upper_95 -- all shape (steps, n_variables).
        Also columns (list of column names).
    """
    results = var_result["results"]
    stationary_data = var_result["stationary_data"]
    lag_order = var_result["lag_order"]

    # Last lag_order observations as forecast seed
    y_input = stationary_data.values[-lag_order:]

    # 68% CI (alpha=0.32)
    point_68, lower_68, upper_68 = results.forecast_interval(
        y_input, steps=steps, alpha=0.32
    )

    # 95% CI (alpha=0.05)
    point_95, lower_95, upper_95 = results.forecast_interval(
        y_input, steps=steps, alpha=0.05
    )

    # Point forecasts from the 68% call (identical to 95% call)
    point_forecasts = point_68

    # Optionally invert differencing
    diff_orders = var_result.get("diff_orders", {})
    if any(d > 0 for d in diff_orders.values()):
        original_data = var_result["original_data"]
        last_level = original_data.iloc[-1].values  # shape (n_vars,)

        point_forecasts = _undifference(point_forecasts, last_level)
        lower_68 = _undifference(lower_68, last_level)
        upper_68 = _undifference(upper_68, last_level)
        lower_95 = _undifference(lower_95, last_level)
        upper_95 = _undifference(upper_95, last_level)

    return {
        "point_forecasts": point_forecasts,
        "lower_68": lower_68,
        "upper_68": upper_68,
        "lower_95": lower_95,
        "upper_95": upper_95,
        "columns": list(stationary_data.columns),
    }


def _undifference(forecast_diffs: np.ndarray, last_level: np.ndarray) -> np.ndarray:
    """Convert differenced forecasts back to levels via cumulative sum.

    Parameters
    ----------
    forecast_diffs : ndarray
        Shape (steps, n_vars) of differenced forecast values.
    last_level : ndarray
        Shape (n_vars,) of the last observed level values.

    Returns
    -------
    ndarray
        Shape (steps, n_vars) of level forecasts.
    """
    cumulative = np.cumsum(forecast_diffs, axis=0)
    return cumulative + last_level


def get_indicator_forecasts(
    var_result: dict,
    steps: int = 8,
) -> dict[str, dict]:
    """Generate per-indicator forecasts with CI bands as Python lists.

    Parameters
    ----------
    var_result : dict
        Output from ``fit_var``.
    steps : int
        Number of steps ahead to forecast.

    Returns
    -------
    dict[str, dict]
        Maps each indicator name to a dict with keys: point, lower_68,
        upper_68, lower_95, upper_95 -- each a list of floats.
    """
    fc = forecast(var_result, steps=steps)
    columns = fc["columns"]

    result = {}
    for i, col in enumerate(columns):
        result[col] = {
            "point": fc["point_forecasts"][:, i].tolist(),
            "lower_68": fc["lower_68"][:, i].tolist(),
            "upper_68": fc["upper_68"][:, i].tolist(),
            "lower_95": fc["lower_95"][:, i].tolist(),
            "upper_95": fc["upper_95"][:, i].tolist(),
        }

    return result
