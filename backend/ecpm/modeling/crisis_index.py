"""Composite Crisis Probability Index with mechanism decomposition.

Synthesizes TRPF (tendency of the rate of profit to fall), realization
crisis, and financial fragility sub-indices into a single 0-100
composite crisis probability index.

Exports:
    compute            -- compute crisis index from indicator DataFrame
    MECHANISM_INDICATORS -- mapping of mechanisms to indicator slugs
    DEFAULT_WEIGHTS    -- default 1/3 weights for each mechanism
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


# Mechanism-to-indicator mapping per Marxist crisis theory
MECHANISM_INDICATORS: dict[str, list[str]] = {
    "trpf": ["rate_of_profit", "occ", "rate_of_surplus_value", "mass_of_profit"],
    "realization": ["productivity_wage_gap"],
    "financial": ["credit_gdp_gap", "financial_real_ratio", "debt_service_ratio"],
}

# Default equal weights
DEFAULT_WEIGHTS: dict[str, float] = {
    "trpf": 1 / 3,
    "realization": 1 / 3,
    "financial": 1 / 3,
}

# Indicators where HIGHER values mean HIGHER crisis risk
# (no inversion needed)
_CRISIS_POSITIVE = {
    "occ",              # higher OCC = more capital-intensive = higher crisis risk
    "mass_of_profit",   # declining mass = crisis, but we track rising which can mask TRPF
    "productivity_wage_gap",
    "credit_gdp_gap",
    "financial_real_ratio",
    "debt_service_ratio",
}

# Indicators where LOWER values mean HIGHER crisis risk
# (must be inverted: percentile_rank -> 1 - percentile_rank)
_CRISIS_INVERTED = {
    "rate_of_profit",        # lower profit rate = higher crisis signal
    "rate_of_surplus_value", # lower exploitation rate = higher crisis signal
}


def compute(
    data: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> dict:
    """Compute the Composite Crisis Probability Index.

    Each indicator is normalized to [0, 1] via historical percentile rank.
    Inverted indicators (rate_of_profit, rate_of_surplus_value) are flipped
    so that lower values produce higher crisis signals. Sub-indices are
    averaged within mechanism groups, then combined with weights.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame with indicator columns (matching IndicatorSlug values).
    weights : dict or None
        Custom weights for mechanism groups. Keys: trpf, realization,
        financial. Values should sum to 1.0. Default: 1/3 each.

    Returns
    -------
    dict
        Keys: current_value (float, 0-100), trpf_component (float, 0-100),
        realization_component (float, 0-100), financial_component (float, 0-100),
        history (list of dicts with date/composite/trpf/realization/financial).
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()

    # Normalize each indicator to [0, 1] via global cross-sectional
    # percentile rank. By ranking ALL values across ALL columns together,
    # the normalization captures absolute level differences -- a column
    # whose values are uniformly lower will receive lower global ranks.
    stacked = data.stack()
    global_ranks = stacked.rank(pct=True)
    normalized = global_ranks.unstack()

    # Invert crisis-negative indicators (lower value = higher crisis)
    for col in data.columns:
        if col in _CRISIS_INVERTED:
            normalized[col] = 1.0 - normalized[col]

    # Compute sub-indices for each mechanism
    mechanism_series: dict[str, pd.Series] = {}
    available_mechanisms: dict[str, float] = {}

    for mechanism, indicators in MECHANISM_INDICATORS.items():
        available_cols = [c for c in indicators if c in normalized.columns]
        if available_cols:
            mechanism_series[mechanism] = normalized[available_cols].mean(axis=1)
            available_mechanisms[mechanism] = weights.get(mechanism, 0.0)
        else:
            logger.warning(
                "mechanism_missing_indicators",
                mechanism=mechanism,
                expected=indicators,
            )

    if not available_mechanisms:
        logger.error("no_mechanisms_available")
        return {
            "current_value": 0.0,
            "trpf_component": 0.0,
            "realization_component": 0.0,
            "financial_component": 0.0,
            "history": [],
        }

    # Renormalize weights to sum to 1.0 from available mechanisms
    total_weight = sum(available_mechanisms.values())
    if total_weight > 0:
        norm_weights = {k: v / total_weight for k, v in available_mechanisms.items()}
    else:
        norm_weights = {k: 1.0 / len(available_mechanisms) for k in available_mechanisms}

    # Compute weighted composite (0 to 1 scale, then multiply by 100)
    composite = pd.Series(0.0, index=data.index)
    for mechanism, series in mechanism_series.items():
        composite = composite + series * norm_weights.get(mechanism, 0.0)

    # Scale to 0-100
    composite_100 = composite * 100
    trpf_100 = mechanism_series.get("trpf", pd.Series(0.0, index=data.index)) * 100
    realization_100 = mechanism_series.get("realization", pd.Series(0.0, index=data.index)) * 100
    financial_100 = mechanism_series.get("financial", pd.Series(0.0, index=data.index)) * 100

    # Build history list
    history = []
    for idx in data.index:
        entry: dict = {}
        if hasattr(idx, "isoformat"):
            entry["date"] = idx.isoformat()
        else:
            entry["date"] = str(idx)
        entry["composite"] = float(composite_100.loc[idx])
        entry["trpf"] = float(trpf_100.loc[idx])
        entry["realization"] = float(realization_100.loc[idx])
        entry["financial"] = float(financial_100.loc[idx])
        history.append(entry)

    # Current values (last row)
    current_value = float(composite_100.iloc[-1])
    trpf_component = float(trpf_100.iloc[-1])
    realization_component = float(realization_100.iloc[-1])
    financial_component = float(financial_100.iloc[-1])

    logger.info(
        "crisis_index_computed",
        current_value=round(current_value, 2),
        trpf=round(trpf_component, 2),
        realization=round(realization_component, 2),
        financial=round(financial_component, 2),
    )

    return {
        "current_value": current_value,
        "trpf_component": trpf_component,
        "realization_component": realization_component,
        "financial_component": financial_component,
        "history": history,
    }
