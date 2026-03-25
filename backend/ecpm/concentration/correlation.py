"""Correlation engine for concentration-indicator mapping.

Computes rolling correlations, lead-lag analysis, and confidence scores
for mapping corporate concentration to Marxist crisis indicators.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def compute_rolling_correlation(
    concentration_series: pd.Series,
    indicator_series: pd.Series,
    window_months: int = 24,
    method: str = "pearson",
) -> pd.Series:
    """Compute rolling correlation between concentration and indicator time series.

    Uses a rolling window approach to track how correlation evolves over time.

    Args:
        concentration_series: Time series of concentration values (CR4/HHI).
        indicator_series: Time series of indicator values.
        window_months: Rolling window size in periods (default 24).
        method: Correlation method - "pearson" (linear) or "spearman" (rank-based).

    Returns:
        pd.Series of correlation coefficients (-1 to +1) indexed by date.
    """
    if concentration_series.empty or indicator_series.empty:
        return pd.Series(dtype=float)

    # Align the series on their index
    df = pd.DataFrame({
        "concentration": concentration_series,
        "indicator": indicator_series,
    })

    # Drop rows with NaN in either column
    df = df.dropna()

    if len(df) < window_months // 2:
        return pd.Series(dtype=float)

    # Minimum observations for partial windows
    min_periods = max(window_months // 2, 2)

    # Compute rolling correlation
    rolling_corr = df["concentration"].rolling(
        window=window_months,
        min_periods=min_periods,
    ).corr(df["indicator"])

    if method == "spearman":
        # For Spearman, convert to ranks first
        ranks = df.rank()
        rolling_corr = ranks["concentration"].rolling(
            window=window_months,
            min_periods=min_periods,
        ).corr(ranks["indicator"])

    return rolling_corr


def compute_lead_lag_correlation(
    concentration: pd.Series,
    indicator: pd.Series,
    max_lag_months: int = 24,
) -> dict[str, Any]:
    """Compute correlation at various lead/lag offsets.

    Tests whether concentration leads or lags indicator changes.
    Positive lag means concentration leads (early warning signal).

    Args:
        concentration: Time series of concentration values.
        indicator: Time series of indicator values.
        max_lag_months: Maximum lag to test in months.

    Returns:
        Dict with:
        - lag_months: List of lag values tested
        - correlations: Corresponding correlation at each lag
        - peak_lag: Lag with highest absolute correlation
        - peak_corr: Correlation at peak lag
    """
    if concentration.empty or indicator.empty:
        return {
            "lag_months": [],
            "correlations": [],
            "peak_lag": 0,
            "peak_corr": 0.0,
        }

    # Test lags: [0, 3, 6, 12, 18, 24] months
    lags = [0, 3, 6, 12, 18, max_lag_months]
    lags = [l for l in lags if l <= max_lag_months]

    correlations = []

    for lag in lags:
        if lag == 0:
            shifted_conc = concentration
        else:
            shifted_conc = concentration.shift(lag)

        # Align and compute correlation
        df = pd.DataFrame({
            "concentration": shifted_conc,
            "indicator": indicator,
        }).dropna()

        if len(df) >= 10:
            corr = df["concentration"].corr(df["indicator"])
        else:
            corr = 0.0

        correlations.append(float(corr) if not np.isnan(corr) else 0.0)

    # Find peak correlation
    if correlations:
        abs_corrs = [abs(c) for c in correlations]
        peak_idx = abs_corrs.index(max(abs_corrs))
        peak_lag = lags[peak_idx]
        peak_corr = correlations[peak_idx]
    else:
        peak_lag = 0
        peak_corr = 0.0

    return {
        "lag_months": lags,
        "correlations": correlations,
        "peak_lag": peak_lag,
        "peak_corr": peak_corr,
    }


def _indicator_values_by_calendar_year(ind_series: pd.Series) -> dict[int, float]:
    """Map calendar year -> last observed annual indicator value for that year."""
    out: dict[int, float] = {}
    for ts, val in ind_series.items():
        if pd.isna(val):
            continue
        y = int(pd.Timestamp(ts).year)
        out[y] = float(val)
    return out


def _merge_concentration_with_indicator(
    conc_df: pd.DataFrame,
    conc_col: str,
    ind_series: pd.Series,
) -> pd.DataFrame:
    """Inner-join concentration rows to indicator values by calendar year."""
    if conc_df.empty or ind_series.empty:
        return pd.DataFrame(columns=["year", "concentration", "indicator"])

    by_year = _indicator_values_by_calendar_year(ind_series)
    m = conc_df[["year", conc_col]].dropna().copy()
    m["year"] = m["year"].astype(int)
    m["indicator"] = m["year"].map(by_year)
    m = m.dropna(subset=["indicator"])
    m = m.rename(columns={conc_col: "concentration"})
    return m.sort_values("year").reset_index(drop=True)


def _annual_observation_lag_correlation(
    merged: pd.DataFrame,
    max_lag_obs: int = 3,
    min_obs: int = 4,
) -> tuple[float, int, int]:
    """Lead/lag correlation on aligned annual panels (lags = observation shifts).

    For lag k >= 0: correlate concentration[:-k] with indicator[k:] so positive k
    tests whether concentration leads the indicator by k survey waves.

    Returns:
        (peak_corr, peak_lag_observations, n_pairs_at_peak)
    """
    if len(merged) < min_obs:
        return 0.0, 0, len(merged)

    conc = merged["concentration"].astype(float)
    ind = merged["indicator"].astype(float)

    best_r = 0.0
    best_lag = 0
    best_n = 0

    for lag in range(0, max_lag_obs + 1):
        if lag == 0:
            c_seg, i_seg = conc, ind
        else:
            c_seg, i_seg = conc.iloc[:-lag], ind.iloc[lag:]
        n = len(c_seg)
        if n < min_obs:
            continue
        r = float(c_seg.corr(i_seg))
        if np.isnan(r):
            continue
        if abs(r) > abs(best_r):
            best_r = r
            best_lag = lag
            best_n = n

    return best_r, best_lag, best_n


def _concentration_panel_confidence(correlation: float, n_observations: int) -> float:
    """Confidence for short annual panels (e.g. Census every 5 years).

    Scales with |r| and sample size without requiring n >= 10 like monthly logic.
    """
    if n_observations < 4 or np.isnan(correlation):
        return 0.0
    return float(
        min(100.0, abs(correlation) * 100.0 * min(1.0, n_observations / 5.0))
    )


def compute_confidence_score(
    correlation: float,
    n_observations: int,
    r_squared: float,
) -> float:
    """Compute confidence score for a correlation estimate.

    Combines correlation strength, sample size, and goodness of fit
    into a single 0-100 confidence score.

    Formula: confidence = min(100, abs(corr) * 100 * sqrt(n/24) * r_squared)

    Args:
        correlation: Correlation coefficient (-1 to +1).
        n_observations: Number of observations used.
        r_squared: R-squared value (0 to 1).

    Returns:
        Confidence score (0-100).
        - > 70: High confidence (strong, reliable signal)
        - 30-70: Medium confidence
        - < 30: Low confidence (weak, noisy signal)
    """
    if n_observations < 2:
        return 0.0

    # Ensure r_squared is valid
    r_squared = max(0.0, min(1.0, r_squared))

    # Confidence formula
    confidence = abs(correlation) * 100 * math.sqrt(n_observations / 24) * r_squared

    # Clamp to 0-100 range
    return min(100.0, max(0.0, confidence))


def map_concentration_to_indicators(
    concentration_data: pd.DataFrame,
    indicator_data: dict[str, pd.Series],
    naics_code: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> list[dict[str, Any]]:
    """Map concentration metrics to all Marxist indicators for an industry.

    Computes correlation with all 8 indicators from Phase 2.

    Args:
        concentration_data: DataFrame with year and cr4/hhi columns.
        indicator_data: Dict mapping indicator slug to time series.
        naics_code: NAICS industry code.
        start_year: Optional start year for filtering.
        end_year: Optional end year for filtering.

    Returns:
        List of dicts, one per indicator, sorted by confidence descending:
        - indicator_slug: Indicator identifier
        - correlation: Correlation coefficient
        - confidence: Confidence score (0-100)
        - lag_months: Optimal lag in months
        - relationship: "positive", "negative", or "none"
    """
    # Indicator slugs from Phase 2
    indicator_slugs = [
        "rate-of-profit",
        "occ",
        "rate-of-surplus-value",
        "mass-of-profit",
        "productivity-wage-gap",
        "credit-gdp-gap",
        "financial-real-ratio",
        "debt-service-ratio",
    ]

    results = []

    # Build concentration time series
    if concentration_data.empty:
        return results

    conc_df = concentration_data.copy()

    # Filter by year range if specified
    if start_year is not None:
        conc_df = conc_df[conc_df["year"] >= start_year]
    if end_year is not None:
        conc_df = conc_df[conc_df["year"] <= end_year]

    if conc_df.empty:
        return results

    # Use CR4 as default concentration metric
    conc_col = "cr4" if "cr4" in conc_df.columns else "hhi"

    for slug in indicator_slugs:
        ind_series = indicator_data.get(slug, pd.Series(dtype=float))

        if ind_series.empty:
            # No data for this indicator
            results.append({
                "indicator_slug": slug,
                "correlation": 0.0,
                "confidence": 0.0,
                "lag_months": 0,
                "relationship": "none",
            })
            continue

        merged = _merge_concentration_with_indicator(conc_df, conc_col, ind_series)
        correlation, lag_obs, n_obs = _annual_observation_lag_correlation(merged)
        # API field is lag_months; lags are in observation steps (~economic census waves)
        lag_months = int(lag_obs * 12)

        confidence = _concentration_panel_confidence(correlation, n_obs)

        # Determine relationship
        if abs(correlation) < 0.1:
            relationship = "none"
        elif correlation > 0:
            relationship = "positive"
        else:
            relationship = "negative"

        results.append({
            "indicator_slug": slug,
            "correlation": correlation,
            "confidence": confidence,
            "lag_months": lag_months,
            "relationship": relationship,
        })

    # Sort by confidence descending
    results.sort(key=lambda x: x["confidence"], reverse=True)

    return results


def find_strongest_correlations(
    concentration_data: pd.DataFrame,
    indicator_data: dict[str, pd.Series],
    min_confidence: float = 50,
    top_n: int = 20,
) -> pd.DataFrame:
    """Find strongest concentration-indicator correlations across all industries.

    Scans all industries and indicators to find the most reliable
    early warning signals.

    Args:
        concentration_data: DataFrame with naics_code, year, cr4, hhi columns.
        indicator_data: Dict mapping indicator slug to time series.
        min_confidence: Minimum confidence threshold.
        top_n: Number of top correlations to return.

    Returns:
        DataFrame with columns:
        - naics_code: Industry NAICS code
        - industry_name: Industry name
        - indicator_slug: Indicator identifier
        - correlation: Correlation coefficient
        - confidence: Confidence score
        - lag_months: Optimal lag
    """
    if concentration_data.empty:
        return pd.DataFrame(columns=[
            "naics_code",
            "industry_name",
            "indicator_slug",
            "correlation",
            "confidence",
            "lag_months",
        ])

    results = []

    # Get unique industries
    industries = concentration_data["naics_code"].unique()

    for naics in industries:
        industry_df = concentration_data[concentration_data["naics_code"] == naics]

        # Get industry name
        industry_name = ""
        if "naics_name" in industry_df.columns:
            names = industry_df["naics_name"].dropna()
            if len(names) > 0:
                industry_name = str(names.iloc[0])

        # Map to indicators
        correlations = map_concentration_to_indicators(
            concentration_data=industry_df,
            indicator_data=indicator_data,
            naics_code=naics,
        )

        for corr in correlations:
            if corr["confidence"] >= min_confidence:
                results.append({
                    "naics_code": naics,
                    "industry_name": industry_name,
                    "indicator_slug": corr["indicator_slug"],
                    "correlation": corr["correlation"],
                    "confidence": corr["confidence"],
                    "lag_months": corr["lag_months"],
                })

    # Sort by confidence and take top N
    results.sort(key=lambda x: x["confidence"], reverse=True)
    results = results[:top_n]

    return pd.DataFrame(results)
