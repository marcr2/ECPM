"""Concentration metrics computation functions.

Provides CR4, CR8, HHI calculation along with trend analysis
and concentration level classification per DoJ/FTC thresholds.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from ecpm.structural.departments import DEPT_I_CODES


def compute_cr4(market_shares: pd.Series) -> float:
    """Compute CR4 (Concentration Ratio for top 4 firms).

    The CR4 is the sum of market shares of the four largest firms
    in an industry.

    Args:
        market_shares: Series of market shares (as percentages 0-100).

    Returns:
        CR4 value (0-100). Returns sum of available firms if fewer than 4.
    """
    if market_shares.empty:
        return 0.0

    # Sort descending and take top 4
    top_4 = market_shares.nlargest(min(4, len(market_shares)))
    return float(top_4.sum())


def compute_cr8(market_shares: pd.Series) -> float:
    """Compute CR8 (Concentration Ratio for top 8 firms).

    The CR8 is the sum of market shares of the eight largest firms
    in an industry.

    Args:
        market_shares: Series of market shares (as percentages 0-100).

    Returns:
        CR8 value (0-100). Returns sum of available firms if fewer than 8.
    """
    if market_shares.empty:
        return 0.0

    # Sort descending and take top 8
    top_8 = market_shares.nlargest(min(8, len(market_shares)))
    return float(top_8.sum())


def compute_hhi(market_shares: pd.Series) -> float:
    """Compute Herfindahl-Hirschman Index (HHI).

    The HHI is the sum of squared market shares of all firms in an industry.
    A monopoly has HHI = 10,000. Perfect competition approaches 0.

    DoJ/FTC merger guidelines thresholds:
    - < 1,500: Competitive/unconcentrated market
    - 1,500 - 2,500: Moderately concentrated
    - > 2,500: Highly concentrated
    - > 7,000: Near-monopoly

    Args:
        market_shares: Series of market shares (as percentages 0-100).

    Returns:
        HHI value (0-10,000).
    """
    if market_shares.empty:
        return 0.0

    # HHI = sum of squared market shares
    # Input is percentages (0-100), so HHI range is 0-10,000
    return float((market_shares ** 2).sum())


def compute_trend(
    concentration_series: pd.Series,
    years: pd.Series,
) -> dict[str, Any]:
    """Compute trend in concentration over time using linear regression.

    Fits a linear regression to the concentration time series and
    determines trend direction based on slope.

    Args:
        concentration_series: Time series of concentration values (CR4 or HHI).
        years: Corresponding years for each observation.

    Returns:
        Dict with:
        - slope: Annual change in concentration
        - direction: "increasing", "decreasing", or "stable"
        - r_squared: Coefficient of determination
    """
    if len(concentration_series) < 2:
        return {
            "slope": 0.0,
            "direction": "stable",
            "r_squared": 0.0,
        }

    # Align and drop NaN
    valid_mask = ~(concentration_series.isna() | years.isna())
    y = concentration_series[valid_mask].values
    x = years[valid_mask].values

    if len(x) < 2:
        return {
            "slope": 0.0,
            "direction": "stable",
            "r_squared": 0.0,
        }

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Determine direction based on slope magnitude
    # > 0.5 CR4 points per year is "increasing"
    # < -0.5 CR4 points per year is "decreasing"
    if slope > 0.5:
        direction = "increasing"
    elif slope < -0.5:
        direction = "decreasing"
    else:
        direction = "stable"

    return {
        "slope": float(slope),
        "direction": direction,
        "r_squared": float(r_value ** 2),
    }


def classify_concentration_level(cr4: float, hhi: float) -> str:
    """Classify market concentration level per DoJ/FTC guidelines.

    Uses a combination of CR4 and HHI thresholds to determine
    the market structure classification.

    Args:
        cr4: CR4 ratio (0-100).
        hhi: Herfindahl-Hirschman Index (0-10,000).

    Returns:
        Classification string:
        - "monopoly": HHI > 7,000 or CR4 > 90
        - "highly_concentrated": HHI > 2,500 or CR4 > 70
        - "moderately_concentrated": HHI > 1,500 or CR4 > 50
        - "competitive": Otherwise
    """
    # Check for near-monopoly first
    if hhi > 7000 or cr4 > 90:
        return "monopoly"

    # Highly concentrated
    if hhi > 2500 or cr4 > 70:
        return "highly_concentrated"

    # Moderately concentrated
    if hhi > 1500 or cr4 > 50:
        return "moderately_concentrated"

    # Competitive market
    return "competitive"


def aggregate_by_department(
    concentration_df: pd.DataFrame,
    dept_classification: dict[str, str] | None = None,
) -> dict[str, dict[str, float]]:
    """Aggregate concentration metrics by Marxist department classification.

    Computes weighted average CR4 and HHI for Department I (means of production)
    and Department II (means of consumption), weighted by total revenue.

    Args:
        concentration_df: DataFrame with columns:
            - naics_code: NAICS industry code
            - cr4: CR4 concentration ratio
            - hhi: Herfindahl-Hirschman Index
            - total_revenue: Industry total revenue (for weighting)
        dept_classification: Optional dict mapping NAICS codes to "Dept_I" or "Dept_II".
            If not provided, uses default DEPT_I_CODES from structural.departments.

    Returns:
        Dict with Dept_I and Dept_II subdicts containing weighted avg cr4 and hhi.
    """
    if concentration_df.empty:
        return {
            "Dept_I": {"cr4": 0.0, "hhi": 0.0},
            "Dept_II": {"cr4": 0.0, "hhi": 0.0},
        }

    # Build classification if not provided
    if dept_classification is None:
        dept_classification = {}
        for naics in concentration_df["naics_code"].unique():
            # Check if NAICS code or prefix is in DEPT_I_CODES
            if naics in DEPT_I_CODES or any(
                naics.startswith(prefix) for prefix in DEPT_I_CODES
            ):
                dept_classification[naics] = "Dept_I"
            else:
                dept_classification[naics] = "Dept_II"

    # Add department column
    df = concentration_df.copy()
    df["department"] = df["naics_code"].map(
        lambda x: dept_classification.get(x, "Dept_II")
    )

    # Ensure we have required columns
    if "total_revenue" not in df.columns:
        # Use equal weights if no revenue data
        df["total_revenue"] = 1.0

    # Fill NaN revenues with 0
    df["total_revenue"] = df["total_revenue"].fillna(0)

    result = {}

    for dept in ["Dept_I", "Dept_II"]:
        dept_df = df[df["department"] == dept]

        if dept_df.empty or dept_df["total_revenue"].sum() == 0:
            result[dept] = {"cr4": 0.0, "hhi": 0.0}
            continue

        total_rev = dept_df["total_revenue"].sum()

        # Weighted average
        weighted_cr4 = (dept_df["cr4"] * dept_df["total_revenue"]).sum() / total_rev
        weighted_hhi = (dept_df["hhi"] * dept_df["total_revenue"]).sum() / total_rev

        result[dept] = {
            "cr4": float(weighted_cr4),
            "hhi": float(weighted_hhi),
        }

    return result
