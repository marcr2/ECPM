"""Dual ADF/KPSS stationarity testing and automatic differencing.

Provides a conservative stationarity assessment: both ADF and KPSS must
agree for a series to be classified as stationary. When tests disagree,
differencing is recommended (conservative approach).

Exports:
    check_stationarity  -- dual ADF + KPSS test on a single series
    ensure_stationarity -- test and difference a full DataFrame if needed
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import structlog
from statsmodels.tsa.stattools import adfuller, kpss

logger = structlog.get_logger(__name__)


def check_stationarity(series: pd.Series, alpha: float = 0.05) -> dict:
    """Run dual ADF + KPSS stationarity test on a single series.

    ADF null hypothesis: unit root present (non-stationary).
    KPSS null hypothesis: series is stationary.

    Both must agree for ``is_stationary=True``. When they disagree,
    the conservative default is ``recommendation="difference"``.

    Parameters
    ----------
    series : pd.Series
        Time series to test. NaNs are dropped before testing.
    alpha : float
        Significance level for both tests (default 0.05).

    Returns
    -------
    dict
        Keys: adf_pvalue, kpss_pvalue, adf_stationary, kpss_stationary,
        is_stationary, recommendation.
    """
    clean = series.dropna()
    if len(clean) < 20:
        logger.warning("series_too_short", length=len(clean))
        return {
            "adf_pvalue": 1.0,
            "kpss_pvalue": 0.0,
            "adf_stationary": False,
            "kpss_stationary": False,
            "is_stationary": False,
            "recommendation": "difference",
        }

    # ADF test: reject null (unit root) => stationary
    adf_result = adfuller(clean, regression="c", autolag="AIC")
    adf_pvalue = float(adf_result[1])
    adf_stationary = adf_pvalue < alpha

    # KPSS test: fail to reject null => stationary
    # Suppress FutureWarning and InterpolationWarning from kpss
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kpss_result = kpss(clean, regression="c", nlags="auto")
    kpss_pvalue = float(kpss_result[1])
    kpss_stationary = kpss_pvalue > alpha

    # Both must agree for conservative stationarity assessment
    is_stationary = adf_stationary and kpss_stationary

    recommendation = "stationary" if is_stationary else "difference"

    logger.debug(
        "stationarity_check",
        series_name=getattr(series, "name", None),
        adf_pvalue=round(adf_pvalue, 4),
        kpss_pvalue=round(kpss_pvalue, 4),
        adf_stationary=adf_stationary,
        kpss_stationary=kpss_stationary,
        is_stationary=is_stationary,
        recommendation=recommendation,
    )

    return {
        "adf_pvalue": adf_pvalue,
        "kpss_pvalue": kpss_pvalue,
        "adf_stationary": adf_stationary,
        "kpss_stationary": kpss_stationary,
        "is_stationary": is_stationary,
        "recommendation": recommendation,
    }


def ensure_stationarity(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Test each column for stationarity and difference if needed.

    If ANY column is non-stationary, ALL columns are differenced
    (VAR requires equal-length series). Returns the transformed
    DataFrame and a dict mapping column names to differencing orders.

    Parameters
    ----------
    data : pd.DataFrame
        Input time series data with columns as variables.

    Returns
    -------
    tuple[pd.DataFrame, dict[str, int]]
        (transformed_data, diff_orders) where diff_orders maps each column
        name to the number of times it was differenced (0 or 1).
    """
    diff_orders: dict[str, int] = {}
    needs_differencing = False

    for col in data.columns:
        result = check_stationarity(data[col])
        if not result["is_stationary"]:
            needs_differencing = True
            diff_orders[col] = 1
        else:
            diff_orders[col] = 0

    if needs_differencing:
        # Difference ALL columns to maintain equal length
        logger.info(
            "differencing_all_columns",
            non_stationary=[c for c, d in diff_orders.items() if d > 0],
        )
        # Set all diff_orders to 1 since we difference all together
        diff_orders = {col: 1 for col in data.columns}
        transformed = data.diff().dropna()
    else:
        logger.info("all_columns_stationary")
        transformed = data.copy()

    return transformed, diff_orders
