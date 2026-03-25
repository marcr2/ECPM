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

from ecpm.indicators.base import (
    IndicatorDoc,
    NIPAMapping,
    _one_sided_hp_filter,
)


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
    credit = data["credit_total"] / 1000.0  # Convert millions to billions
    gdp = data["nominal_gdp"]  # Already in billions

    ratio = (credit / gdp) * 100  # percentage

    # Drop NaN values before HP filter (filter can't handle NaN)
    ratio_clean = ratio.dropna()
    if len(ratio_clean) == 0:
        return ratio  # Return all NaN if no valid data

    # One-sided HP filter (recursive approximation, BIS lambda=400,000)
    trend = _one_sided_hp_filter(ratio_clean.values, lamb=400_000)
    gap_clean = ratio_clean - pd.Series(trend, index=ratio_clean.index)

    # Re-align with original index (fills NaN where data was missing)
    gap = gap_clean.reindex(ratio.index)
    return gap


def compute_financial_real_ratio(data: dict[str, pd.Series]) -> pd.Series:
    """Compute financial-to-real asset ratio.

    Uses FRED series:
        - TFAABSNNCB (nonfinancial corporate total financial assets)
          -> key: "financial_assets"
        - K1PTOTL1ES000 (current-cost net stock of private fixed assets)
          -> key: "real_assets"

    Frequency alignment: real_assets (annual) is reindexed onto the
    financial_assets (quarterly) index using forward-fill (LOCF).

    Args:
        data: Must contain 'financial_assets' and 'real_assets'.

    Returns:
        pd.Series of ratio values.
    """
    financial = data["financial_assets"]
    real = data["real_assets"]

    combined_idx = financial.index.union(real.index).sort_values()
    real_aligned = real.reindex(combined_idx).ffill()
    real_aligned = real_aligned.reindex(financial.index)

    return financial / real_aligned


def compute_debt_service_ratio(data: dict[str, pd.Series]) -> pd.Series:
    """Compute corporate debt service ratio.

    Uses FRED series:
        - BOGZ1FU106130001Q (interest payments, nonfinancial corporate)
          -> key: "debt_service"
        - A445RC1Q027SBEA (corporate profits before tax) -> key: "corporate_income"

    Ratio = interest / corporate_income * 100 (as percent).

    Args:
        data: Must contain 'debt_service' and 'corporate_income'.

    Returns:
        pd.Series of ratio values in percent.
    """
    debt_service = data["debt_service"] / 1000.0  # Convert millions to billions
    corporate_income = data["corporate_income"]  # Already in billions
    return (debt_service / corporate_income) * 100


_METHOD_INDEPENDENT_INTRO = (
    "Identical under Shaikh/Tonak and Kliman TSSI: Marxist methodology applies "
    "only to the core NIPA-based C, V, and S indicators. "
)

_BIS_CREDIT_GAP_CITATION = (
    "Drehmann, M. & Tsatsaronis, K. (2014). The Credit-to-GDP Gap and "
    "Countercyclical Capital Buffers. BIS Quarterly Review, March 2014."
)

def methodology_independent_indicator_docs(
    *, marxist_citation: str | None = None
) -> list[IndicatorDoc]:
    """Documentation for financial fragility indicators (shared by all mappers).

    ``marxist_citation`` is appended to each entry so methodology-specific docs
    remain citable alongside BIS/Z.1 references.
    """

    def _cite(*extra: str) -> list[str]:
        base = list(extra)
        if marxist_citation:
            base.append(marxist_citation)
        return base

    return [
        IndicatorDoc(
            name="Productivity-Wage Gap",
            slug="productivity_wage_gap",
            formula_latex=(
                r"\text{Gap} = \frac{\text{Output/Hour Index}}"
                r"{\text{Real Comp/Hour Index}} \times 100"
            ),
            interpretation=(
                _METHOD_INDEPENDENT_INTRO
                + "Nonfarm business output per hour vs. real compensation per hour, "
                "each normalized to 100 at the first observation; 20-period "
                "rolling mean for smoothing."
            ),
            mappings=[
                NIPAMapping(
                    marx_category="labor_productivity_index",
                    nipa_table="FRED",
                    nipa_line=1,
                    nipa_description="Output per hour, nonfarm business",
                    operation="direct",
                    notes="FRED OPHNFB",
                ),
                NIPAMapping(
                    marx_category="real_compensation_index",
                    nipa_table="FRED",
                    nipa_line=2,
                    nipa_description="Real compensation per hour, nonfarm business",
                    operation="direct",
                    notes="FRED PRS85006092",
                ),
            ],
            citations=_cite(),
        ),
        IndicatorDoc(
            name="Credit-to-GDP Gap",
            slug="credit_gdp_gap",
            formula_latex=(
                r"\text{Gap}_t = \frac{\text{Credit}_t}{\text{GDP}_t} \times 100"
                r" - \text{HP}^{(\text{one-sided})}_{\lambda=400{,}000}"
                r"\!\left(\frac{\text{Credit}_t}{\text{GDP}_t}\right)"
            ),
            interpretation=(
                _METHOD_INDEPENDENT_INTRO
                + "Nonfinancial corporate credit vs. nominal GDP; one-sided "
                "Hodrick-Prescott filter (BIS, lambda=400,000 for quarterly data). "
                "Positive gap: credit growth above long-run trend."
            ),
            mappings=[
                NIPAMapping(
                    marx_category="private_credit",
                    nipa_table="Z.1",
                    nipa_line=1,
                    nipa_description="Nonfinancial corporate debt securities and loans",
                    operation="direct",
                    notes="FRED BOGZ1FL073164003Q (millions; converted to billions)",
                ),
                NIPAMapping(
                    marx_category="nominal_output",
                    nipa_table="NIPA",
                    nipa_line=2,
                    nipa_description="Gross domestic product",
                    operation="direct",
                    notes="FRED GDP (billions)",
                ),
            ],
            citations=_cite(_BIS_CREDIT_GAP_CITATION),
        ),
        IndicatorDoc(
            name="Financial-to-Real Asset Ratio",
            slug="financial_real_ratio",
            formula_latex=r"\frac{\text{Financial Assets}}{\text{Real (Tangible) Assets}}",
            interpretation=(
                _METHOD_INDEPENDENT_INTRO
                + "Nonfinancial corporate total financial assets (Z.1 B.103) "
                "relative to current-cost net stock of private fixed assets "
                "(FRED K1PTOTL1ES000), with annual real assets LOCF-aligned to "
                "the quarterly financial series."
            ),
            mappings=[
                NIPAMapping(
                    marx_category="financial_assets",
                    nipa_table="Z.1",
                    nipa_line=1,
                    nipa_description="Total financial assets, nonfinancial corporate",
                    operation="direct",
                    notes="FRED TFAABSNNCB",
                ),
                NIPAMapping(
                    marx_category="tangible_assets_proxy",
                    nipa_table="FAAt101",
                    nipa_line=2,
                    nipa_description="Current-cost net stock of private fixed assets",
                    operation="direct",
                    notes="FRED K1PTOTL1ES000 (millions; ratio uses consistent units)",
                ),
            ],
            citations=_cite(
                "Board of Governors of the Federal Reserve System (2024). "
                "Financial Accounts of the United States (Z.1)."
            ),
        ),
        IndicatorDoc(
            name="Corporate Debt Service Ratio",
            slug="debt_service_ratio",
            formula_latex=(
                r"\text{DSR} = \frac{\text{Interest Payments}}"
                r"{\text{Corporate Income}} \times 100"
            ),
            interpretation=(
                _METHOD_INDEPENDENT_INTRO
                + "Interest and miscellaneous payments (Z.1) as a share of "
                "corporate profits before tax (NIPA); indicates leverage "
                "pressure and sensitivity to rate shocks."
            ),
            mappings=[
                NIPAMapping(
                    marx_category="debt_service",
                    nipa_table="Z.1",
                    nipa_line=1,
                    nipa_description="Interest and miscellaneous payments, NFCB",
                    operation="direct",
                    notes="FRED BOGZ1FU106130001Q (millions; converted to billions)",
                ),
                NIPAMapping(
                    marx_category="corporate_income",
                    nipa_table="NIPA",
                    nipa_line=2,
                    nipa_description="Corporate profits before tax",
                    operation="direct",
                    notes="FRED A445RC1Q027SBEA (billions)",
                ),
            ],
            citations=_cite(),
        ),
    ]
