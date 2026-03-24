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

__all__ = [
    # Metrics
    "compute_cr4",
    "compute_cr8",
    "compute_hhi",
    "compute_trend",
    "classify_concentration_level",
    "aggregate_by_department",
]
