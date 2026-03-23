"""Structural VAR identification with Marxist causal ordering.

Constructs the lower-triangular A matrix encoding the theoretical
causal ordering from Marxist political economy:
  (1) OCC -> (2) rate of surplus value -> (3) rate of profit ->
  (4) mass of profit -> (5) productivity-wage gap ->
  (6) credit-GDP gap -> (7) financial-real ratio ->
  (8) debt service ratio

Exports:
    build_a_matrix -- construct the lower-triangular A matrix
    fit_svar       -- fit SVAR model given data (runs VAR internally)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import structlog
from statsmodels.tsa.vector_ar.svar_model import SVAR

from ecpm.modeling.var_model import fit_var

logger = structlog.get_logger(__name__)

# Marxist causal ordering of indicators
CAUSAL_ORDER = [
    "occ",
    "rate_of_surplus_value",
    "rate_of_profit",
    "mass_of_profit",
    "productivity_wage_gap",
    "credit_gdp_gap",
    "financial_real_ratio",
    "debt_service_ratio",
]


def build_a_matrix(n_vars: int = 8) -> np.ndarray:
    """Construct the lower-triangular A matrix for SVAR identification.

    The matrix has:
    - Diagonal = 1 (normalization)
    - Upper triangle = 0 (no contemporaneous effect from "later" variables)
    - Lower triangle = 'E' (free parameters to be estimated)

    Parameters
    ----------
    n_vars : int
        Number of endogenous variables (default 8).

    Returns
    -------
    np.ndarray
        Shape (n_vars, n_vars) with dtype=object for mixed types.
    """
    a_matrix = np.zeros((n_vars, n_vars), dtype=object)

    for i in range(n_vars):
        a_matrix[i, i] = 1  # diagonal
        for j in range(i):
            a_matrix[i, j] = "E"  # free parameters below diagonal

    logger.debug("svar_a_matrix_built", n_vars=n_vars)
    return a_matrix


def fit_svar(
    data: pd.DataFrame,
    a_matrix: np.ndarray | None = None,
    max_lags: int = 12,
) -> dict | None:
    """Fit a Structural VAR model with the Marxist causal A matrix.

    Runs an unrestricted VAR first, then identifies the structural
    model using the A matrix. If SVAR fitting fails (common with
    real data), logs a warning and returns None.

    Parameters
    ----------
    data : pd.DataFrame
        Input time series data. Columns should correspond to indicators.
    a_matrix : np.ndarray or None
        The A matrix for SVAR identification. If None, builds the default
        lower-triangular matrix with n_vars = number of columns.
    max_lags : int
        Maximum lag order for VAR fitting.

    Returns
    -------
    dict or None
        On success: dict with keys 'a_matrix_estimated', 'irf', 'var_result'.
        On failure: None.
    """
    n_vars = len(data.columns)

    if a_matrix is None:
        a_matrix = build_a_matrix(n_vars)

    # Fit the reduced-form VAR first
    var_result = fit_var(data, max_lags=max_lags, ensure_stationary=True)
    var_results = var_result["results"]
    stationary_data = var_result["stationary_data"]

    try:
        # Create and fit SVAR model
        svar_model = SVAR(
            stationary_data,
            svar_type="A",
            A=a_matrix,
        )
        svar_results = svar_model.fit(maxlags=var_results.k_ar)

        # Extract estimated A matrix
        a_estimated = svar_results.A

        logger.info(
            "svar_fitted",
            lag_order=var_results.k_ar,
            n_vars=n_vars,
        )

        return {
            "a_matrix_estimated": a_estimated,
            "svar_results": svar_results,
            "var_result": var_result,
            "irf": None,  # IRF can be computed on demand
        }

    except Exception as exc:
        logger.warning(
            "svar_fitting_failed",
            error=str(exc),
            n_vars=n_vars,
            lag_order=var_results.k_ar,
        )
        return None
