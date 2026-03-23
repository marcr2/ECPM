"""Indicator definitions: slugs, display names, units, categories.

Enumerates all computed Marxist economic indicators with metadata
used by API endpoints, schemas, and the frontend.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, TypedDict


class IndicatorSlug(StrEnum):
    """URL-safe identifiers for all computed indicators."""

    rate_of_profit = "rate_of_profit"
    occ = "occ"
    rate_of_surplus_value = "rate_of_surplus_value"
    mass_of_profit = "mass_of_profit"
    productivity_wage_gap = "productivity_wage_gap"
    credit_gdp_gap = "credit_gdp_gap"
    financial_real_ratio = "financial_real_ratio"
    debt_service_ratio = "debt_service_ratio"


class IndicatorDef(TypedDict):
    """Type definition for an indicator's metadata."""

    name: str
    units: str
    category: Literal["core", "financial"]
    description: str


INDICATOR_DEFS: dict[IndicatorSlug, IndicatorDef] = {
    IndicatorSlug.rate_of_profit: {
        "name": "Rate of Profit",
        "units": "ratio",
        "category": "core",
        "description": (
            "The general rate of profit: ratio of surplus value to total "
            "capital advanced (constant + variable). r = S / (C + V)"
        ),
    },
    IndicatorSlug.occ: {
        "name": "Organic Composition of Capital",
        "units": "ratio",
        "category": "core",
        "description": (
            "Ratio of constant capital (means of production) to variable "
            "capital (labor power). OCC = C / V"
        ),
    },
    IndicatorSlug.rate_of_surplus_value: {
        "name": "Rate of Surplus Value",
        "units": "ratio",
        "category": "core",
        "description": (
            "Rate of exploitation: ratio of surplus value to variable "
            "capital. s/v = S / V"
        ),
    },
    IndicatorSlug.mass_of_profit: {
        "name": "Mass of Profit",
        "units": "billions USD",
        "category": "core",
        "description": (
            "Absolute mass of surplus value in nominal terms. "
            "Tracks the total volume of surplus extracted."
        ),
    },
    IndicatorSlug.productivity_wage_gap: {
        "name": "Productivity-Wage Gap",
        "units": "index, base=100",
        "category": "financial",
        "description": (
            "Ratio of labor productivity index to real compensation index. "
            "A rising gap indicates labor producing more value than it "
            "receives in wages."
        ),
    },
    IndicatorSlug.credit_gdp_gap: {
        "name": "Credit-to-GDP Gap",
        "units": "percentage points",
        "category": "financial",
        "description": (
            "Deviation of the credit-to-GDP ratio from its long-run trend "
            "(BIS one-sided HP filter, lambda=400,000). Positive values "
            "signal excessive credit growth."
        ),
    },
    IndicatorSlug.financial_real_ratio: {
        "name": "Financial-to-Real Asset Ratio",
        "units": "ratio",
        "category": "financial",
        "description": (
            "Ratio of financial assets to real (tangible) assets. "
            "Rising values indicate financialization of the economy."
        ),
    },
    IndicatorSlug.debt_service_ratio: {
        "name": "Corporate Debt Service Ratio",
        "units": "percent",
        "category": "financial",
        "description": (
            "Corporate debt service payments as a share of corporate income. "
            "High values indicate financial fragility and vulnerability to "
            "interest rate shocks."
        ),
    },
}


# Frequency alignment strategy: LOCF-only.
# Consistent with Phase 1 decision (ecpm/api/data.py _align_frequency).
# All mixed-frequency inputs are aligned using Last Observation Carried Forward.
# No per-indicator strategy selection -- LOCF is the only supported method.
FREQUENCY_STRATEGY: str = "LOCF"
