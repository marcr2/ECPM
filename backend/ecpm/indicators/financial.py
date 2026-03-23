"""Standalone financial fragility indicator functions.

These functions are methodology-independent -- they compute the same values
regardless of which Marxist methodology (Shaikh/Tonak, Kliman) is active.
The MethodologyMapper ABC delegates its default financial method implementations
to these functions.

All functions accept a dict[str, pd.Series] keyed by descriptive series names
and return a pd.Series of computed indicator values.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ecpm.indicators.base import _one_sided_hp_filter


def compute_productivity_wage_gap(
    data: dict[str, pd.Series], window: int = 20
) -> pd.Series:
    """Compute productivity-wage gap as ratio of indices over rolling window.

    Uses FRED series:
        - OPHNFB (output per hour, nonfarm business) -> key: "output_per_hour"
        - PRS85006092 (real compensation per hour) -> key: "real_compensation_per_hour"

    Both are normalized to base 100 at the first observation.
    Returns output_index / compensation_index * 100.
    Values > 100 indicate the gap is widening (productivity growing faster
    than compensation).

    Args:
        data: Must contain 'output_per_hour' and 'real_compensation_per_hour'.
        window: Rolling window size for smoothing (default 20 periods).
                Set to 1 or 0 for no smoothing.

    Returns:
        pd.Series of gap index values (base=100 at start).
    """
    output = data["output_per_hour"]
    compensation = data["real_compensation_per_hour"]

    # Normalize to index base=100
    output_idx = (output / output.iloc[0]) * 100
    comp_idx = (compensation / compensation.iloc[0]) * 100

    gap = output_idx / comp_idx * 100
    if window > 1 and len(gap) >= window:
        gap = gap.rolling(window=window, min_periods=1).mean()
    return gap


def compute_credit_gdp_gap(data: dict[str, pd.Series]) -> pd.Series:
    """Compute credit-to-GDP gap using one-sided HP filter (BIS methodology).

    Uses FRED series:
        - BOGZ1FL073164003Q (nonfinancial corporate debt) -> key: "credit_total"
        - GDP (nominal GDP) -> key: "nominal_gdp"

    Credit-to-GDP ratio = credit / GDP (as percentage).
    Apply one-sided HP filter with lambda=400,000 (BIS standard for quarterly data).
    Gap = actual ratio - trend (in percentage points).

    Args:
        data: Must contain 'credit_total' and 'nominal_gdp'.

    Returns:
        pd.Series of gap values in percentage points.
    """
    credit = data["credit_total"]
    gdp = data["nominal_gdp"]

    ratio = (credit / gdp) * 100  # percentage

    # One-sided HP filter (recursive approximation, BIS lambda=400,000)
    trend = _one_sided_hp_filter(ratio.values, lamb=400_000)
    gap = ratio - pd.Series(trend, index=ratio.index)
    return gap


def compute_financial_real_ratio(data: dict[str, pd.Series]) -> pd.Series:
    """Compute financial-to-real asset ratio.

    Uses FRED series:
        - BOGZ1FL073164003Q (financial corporate debt proxy) -> key: "financial_assets"
        - K1NTOTL1SI000 (tangible/real assets) -> key: "real_assets"

    Simple ratio: financial / real.

    Args:
        data: Must contain 'financial_assets' and 'real_assets'.

    Returns:
        pd.Series of ratio values.
    """
    return data["financial_assets"] / data["real_assets"]


def compute_debt_service_ratio(data: dict[str, pd.Series]) -> pd.Series:
    """Compute corporate debt service ratio.

    Uses FRED series:
        - BOGZ1FA096130001Q (interest payments, nonfinancial corporate)
          -> key: "debt_service"
        - A445RC1Q027SBEA (net operating surplus) -> key: "corporate_income"

    Ratio = interest / operating_surplus * 100 (as percent).

    Args:
        data: Must contain 'debt_service' and 'corporate_income'.

    Returns:
        pd.Series of ratio values in percent.
    """
    return (data["debt_service"] / data["corporate_income"]) * 100
