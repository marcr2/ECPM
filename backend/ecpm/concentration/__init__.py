"""Concentration analysis module for corporate market structure.

Provides:
- Concentration metric computation (CR4, CR8, HHI)
- Trend analysis over time
- Correlation with Marxist crisis indicators
- Department I/II aggregation
"""

from ecpm.concentration.metrics import (
    compute_cr4,
    compute_cr8,
    compute_hhi,
    compute_trend,
    classify_concentration_level,
    aggregate_by_department,
)
from ecpm.concentration.correlation import (
    compute_rolling_correlation,
    compute_lead_lag_correlation,
    compute_confidence_score,
    map_concentration_to_indicators,
    find_strongest_correlations,
)

__all__ = [
    # Metrics
    "compute_cr4",
    "compute_cr8",
    "compute_hhi",
    "compute_trend",
    "classify_concentration_level",
    "aggregate_by_department",
    # Correlation
    "compute_rolling_correlation",
    "compute_lead_lag_correlation",
    "compute_confidence_score",
    "map_concentration_to_indicators",
    "find_strongest_correlations",
]
