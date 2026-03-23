"""Markov regime-switching model for economic regime detection.

Fits a Markov-switching autoregression to detect distinct economic
regimes (Normal, Stagnation, Crisis) with automatic fallback from
3 regimes to 2 when convergence fails.

Exports:
    fit_regime_model -- fit regime-switching model with fallback
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import structlog
from statsmodels.tsa.regime_switching.markov_autoregression import (
    MarkovAutoregression,
)

logger = structlog.get_logger(__name__)

# Regime label mapping by mean (highest mean = Normal, lowest = Crisis)
_LABELS_3 = {0: "Crisis", 1: "Stagnation", 2: "Normal"}
_LABELS_2 = {0: "Crisis", 1: "Normal"}


def fit_regime_model(
    series: pd.Series,
    max_regimes: int = 3,
    order: int = 2,
) -> dict:
    """Fit a Markov regime-switching autoregression model.

    Attempts to fit with ``max_regimes`` regimes. If convergence fails,
    automatically retries with fewer regimes down to 2.

    Parameters
    ----------
    series : pd.Series
        Univariate time series to model.
    max_regimes : int
        Maximum number of regimes to attempt (default 3).
    order : int
        Autoregressive order for the Markov model (default 2).

    Returns
    -------
    dict
        Keys: n_regimes, current_regime, regime_label,
        regime_probabilities, transition_matrix, smoothed_probabilities,
        regime_labels, regime_durations.
    """
    clean = series.dropna()

    # Try from max_regimes down to 2
    for k_regimes in range(max_regimes, 1, -1):
        result = _try_fit(clean, k_regimes=k_regimes, order=order)
        if result is not None:
            return result

    # Should not reach here, but handle gracefully
    logger.error("regime_model_all_attempts_failed")
    return _fallback_result(clean)


def _try_fit(
    series: pd.Series,
    k_regimes: int,
    order: int,
) -> dict | None:
    """Attempt a single regime model fit. Returns None on failure."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = MarkovAutoregression(
                series,
                k_regimes=k_regimes,
                order=order,
                switching_variance=True,
                switching_ar=False,
                trend="c",
            )
            results = model.fit(disp=False)

        smoothed_probs = results.smoothed_marginal_probabilities

        # Map regime indices to labels by mean of series in each regime
        regime_means = {}
        for regime_idx in range(k_regimes):
            prob_col = smoothed_probs.iloc[:, regime_idx]
            # Weighted mean of series by regime probability
            regime_means[regime_idx] = float(
                np.average(series.values[: len(prob_col)], weights=prob_col.values)
            )

        # Sort by mean: highest = Normal, lowest = Crisis
        sorted_regimes = sorted(regime_means.items(), key=lambda x: x[1])
        if k_regimes == 3:
            regime_labels = {
                sorted_regimes[0][0]: "Crisis",
                sorted_regimes[1][0]: "Stagnation",
                sorted_regimes[2][0]: "Normal",
            }
        elif k_regimes == 2:
            regime_labels = {
                sorted_regimes[0][0]: "Crisis",
                sorted_regimes[1][0]: "Normal",
            }
        else:
            regime_labels = {
                i: f"Regime_{i}" for i in range(k_regimes)
            }

        # Current regime (last observation)
        last_probs = smoothed_probs.iloc[-1]
        current_regime = int(last_probs.values.argmax())
        regime_label = regime_labels.get(current_regime, f"Regime_{current_regime}")

        # Regime probabilities at current time
        regime_probabilities = {
            regime_labels.get(i, f"Regime_{i}"): float(last_probs.iloc[i])
            for i in range(k_regimes)
        }

        # Transition matrix as list of lists
        # statsmodels stores P[j|i] in column i, so columns sum to 1.
        # We transpose so each ROW represents "from state i" and rows sum to 1.
        raw_tm = np.squeeze(results.regime_transition)  # remove trailing dim
        transition_matrix = raw_tm.T.tolist()  # now rows = from-state

        # Smoothed probabilities as list of dicts (for JSON serialization)
        smoothed_list = []
        for idx in range(len(smoothed_probs)):
            entry: dict = {}
            if hasattr(smoothed_probs.index[idx], "isoformat"):
                entry["date"] = smoothed_probs.index[idx].isoformat()
            else:
                entry["date"] = str(smoothed_probs.index[idx])
            for regime_idx in range(k_regimes):
                label = regime_labels.get(regime_idx, f"Regime_{regime_idx}")
                entry[label] = float(smoothed_probs.iloc[idx, regime_idx])
            smoothed_list.append(entry)

        # Regime durations: average consecutive run lengths
        regime_durations = _compute_regime_durations(
            smoothed_probs, regime_labels, k_regimes
        )

        logger.info(
            "regime_model_fitted",
            k_regimes=k_regimes,
            current_regime=regime_label,
        )

        return {
            "n_regimes": k_regimes,
            "current_regime": current_regime,
            "regime_label": regime_label,
            "regime_probabilities": regime_probabilities,
            "transition_matrix": transition_matrix,
            "smoothed_probabilities": smoothed_list,
            "regime_labels": regime_labels,
            "regime_durations": regime_durations,
        }

    except Exception as exc:
        logger.warning(
            "regime_model_fit_failed",
            k_regimes=k_regimes,
            error=str(exc),
        )
        return None


def _compute_regime_durations(
    smoothed_probs: pd.DataFrame,
    regime_labels: dict[int, str],
    k_regimes: int,
) -> dict[str, float]:
    """Compute average regime duration from smoothed probabilities.

    For each regime, count consecutive quarters where it has the highest
    probability, then average the run lengths.
    """
    # Dominant regime at each time point
    dominant = smoothed_probs.values.argmax(axis=1)

    durations: dict[str, float] = {}
    for regime_idx in range(k_regimes):
        label = regime_labels.get(regime_idx, f"Regime_{regime_idx}")
        runs = []
        current_run = 0
        for d in dominant:
            if d == regime_idx:
                current_run += 1
            else:
                if current_run > 0:
                    runs.append(current_run)
                current_run = 0
        if current_run > 0:
            runs.append(current_run)

        durations[label] = float(np.mean(runs)) if runs else 0.0

    return durations


def _fallback_result(series: pd.Series) -> dict:
    """Produce a minimal single-regime fallback result."""
    n = len(series)
    return {
        "n_regimes": 2,
        "current_regime": 0,
        "regime_label": "Normal",
        "regime_probabilities": {"Normal": 1.0, "Crisis": 0.0},
        "transition_matrix": [[1.0, 0.0], [0.0, 1.0]],
        "smoothed_probabilities": [
            {"date": str(i), "Normal": 1.0, "Crisis": 0.0} for i in range(n)
        ],
        "regime_labels": {0: "Normal", 1: "Crisis"},
        "regime_durations": {"Normal": float(n), "Crisis": 0.0},
    }
