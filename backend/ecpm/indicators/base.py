"""MethodologyMapper ABC for NIPA-to-Marx translation methodologies.

Defines the abstract interface that every methodology (Shaikh/Tonak, Kliman,
etc.) must implement, along with dataclasses for documenting NIPA mappings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class NIPAMapping:
    """Documents one NIPA-to-Marx mapping.

    Each mapping connects a Marxian economic category (e.g., surplus_value)
    to a specific NIPA table line item, with the operation describing how
    the line item contributes to the category.
    """

    marx_category: str  # e.g., "surplus_value", "variable_capital"
    nipa_table: str  # e.g., "T11200"
    nipa_line: int  # e.g., 1
    nipa_description: str  # e.g., "National income"
    operation: str  # e.g., "subtract", "add", "direct"
    notes: str = ""


@dataclass
class IndicatorDoc:
    """Self-documentation for one indicator under a methodology.

    Each methodology mapper produces documentation for all its indicators,
    including the formula (as KaTeX-compatible LaTeX), interpretation notes,
    and the specific NIPA mappings used.
    """

    name: str
    slug: str
    formula_latex: str  # KaTeX-compatible LaTeX string
    interpretation: str
    mappings: list[NIPAMapping] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)


class MethodologyMapper(ABC):
    """Abstract base for NIPA-to-Marx translation methodologies.

    Each methodology (Shaikh/Tonak, Kliman TSSI, etc.) subclasses this ABC
    and implements all abstract methods. The registry discovers implementations
    at startup and makes them available to API endpoints.

    All compute methods accept a dict of aligned pd.Series keyed by series
    name (e.g., "national_income", "compensation") and return a pd.Series
    of computed indicator values indexed by date.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable methodology name."""
        ...

    @property
    @abstractmethod
    def slug(self) -> str:
        """URL-safe identifier (e.g., 'shaikh-tonak', 'kliman')."""
        ...

    @abstractmethod
    def compute_rate_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of profit: r = S / (C + V)."""
        ...

    @abstractmethod
    def compute_occ(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute organic composition of capital: OCC = C / V."""
        ...

    @abstractmethod
    def compute_rate_of_surplus_value(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of surplus value: s/v = S / V."""
        ...

    @abstractmethod
    def compute_mass_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute mass of profit (absolute surplus value)."""
        ...

    def compute_productivity_wage_gap(
        self, data: dict[str, pd.Series], window: int = 20
    ) -> pd.Series:
        """Compute productivity-wage gap as ratio of indices over rolling window.

        Default implementation delegates to financial.py standalone function.
        This does not vary by Marxist methodology, so a default implementation
        is provided.

        Args:
            data: Must contain 'output_per_hour' and 'real_compensation_per_hour'.
            window: Rolling window size for smoothing (default 20 periods).

        Returns:
            pd.Series of gap index values (base=100 at start).
        """
        from ecpm.indicators.financial import compute_productivity_wage_gap

        return compute_productivity_wage_gap(data, window=window)

    def compute_credit_gdp_gap(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute credit-to-GDP gap using one-sided HP filter.

        Default implementation delegates to financial.py standalone function.
        Uses BIS methodology: lambda=400,000 for quarterly data.

        Args:
            data: Must contain 'credit_total' and 'nominal_gdp'.

        Returns:
            pd.Series of gap values in percentage points.
        """
        from ecpm.indicators.financial import compute_credit_gdp_gap

        return compute_credit_gdp_gap(data)

    def compute_financial_real_ratio(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute financial-to-real asset ratio.

        Default implementation delegates to financial.py standalone function.

        Args:
            data: Must contain 'financial_assets' and 'real_assets'.

        Returns:
            pd.Series of ratio values.
        """
        from ecpm.indicators.financial import compute_financial_real_ratio

        return compute_financial_real_ratio(data)

    def compute_debt_service_ratio(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute corporate debt service ratio.

        Default implementation delegates to financial.py standalone function.

        Args:
            data: Must contain 'debt_service' and 'corporate_income'.

        Returns:
            pd.Series of ratio values in percent.
        """
        from ecpm.indicators.financial import compute_debt_service_ratio

        return compute_debt_service_ratio(data)

    @abstractmethod
    def get_required_series(self) -> list[str]:
        """Return list of series_ids needed from the database."""
        ...

    @abstractmethod
    def get_documentation(self) -> list[IndicatorDoc]:
        """Return self-documentation for all indicators."""
        ...


def _one_sided_hp_filter(series, lamb: float = 400_000):
    """One-sided (backward-looking) HP filter for credit-to-GDP gap.

    The BIS uses lambda=400,000 for quarterly data.
    This is a recursive implementation that only uses past data.

    Args:
        series: numpy array of values.
        lamb: Smoothing parameter (default 400,000 for quarterly data).

    Returns:
        numpy array of trend values.
    """
    import numpy as np

    n = len(series)
    trend = np.zeros(n)
    if n == 0:
        return trend

    trend[0] = series[0]
    if n > 1:
        trend[1] = series[1]

    for t in range(2, n):
        trend[t] = (series[t] + lamb * (2 * trend[t - 1] - trend[t - 2])) / (1 + lamb)

    return trend
