"""Shaikh/Tonak methodology mapper for NIPA-to-Marx translation.

Implements the Shaikh & Tonak (1994) methodology for computing Marxist
economic indicators from US national accounts data. Key distinguishing
feature: uses current-cost net stock of private fixed assets for constant
capital (C).

Reference: Shaikh, A. & Tonak, E.A. (1994). Measuring the Wealth of Nations:
The Political Economy of National Accounts. Cambridge University Press.
"""

from __future__ import annotations

import pandas as pd

from ecpm.indicators.base import IndicatorDoc, MethodologyMapper, NIPAMapping

# FRED series IDs used by this methodology
SERIES_NATIONAL_INCOME = "A053RC1Q027SBEA"
SERIES_COMPENSATION = "A576RC1"
SERIES_NET_FIXED_ASSETS_CURRENT = "K1NTOTL1SI000"

# Internal data dict keys (mappers receive data keyed by these descriptive names
# after the computation orchestrator maps FRED IDs -> descriptive keys)
_KEY_NI = "national_income"
_KEY_COMP = "compensation"
_KEY_ASSETS = "net_fixed_assets_current"

_CITATION = (
    "Shaikh, A. & Tonak, E.A. (1994). Measuring the Wealth of Nations: "
    "The Political Economy of National Accounts. Cambridge University Press."
)


class ShaikhTonakMapper(MethodologyMapper):
    """Shaikh/Tonak (1994) methodology for Marxist indicator computation.

    Computes surplus value as National Income minus Employee Compensation.
    Uses current-cost net stock of private fixed assets for constant capital,
    which is the standard contemporary replacement-cost valuation.

    Series key convention:
        - national_income: FRED A053RC1Q027SBEA (National Income)
        - compensation: FRED A576RC1 (Compensation of Employees)
        - net_fixed_assets_current: FRED K1NTOTL1SI000 (Current-Cost Net Stock)
    """

    @property
    def name(self) -> str:
        return "Shaikh/Tonak"

    @property
    def slug(self) -> str:
        return "shaikh-tonak"

    # ------------------------------------------------------------------
    # Core Marxist indicator computations
    # ------------------------------------------------------------------

    def _surplus_value(self, data: dict[str, pd.Series]) -> pd.Series:
        """S = National Income - Compensation of Employees."""
        return data[_KEY_NI] - data[_KEY_COMP]

    def _variable_capital(self, data: dict[str, pd.Series]) -> pd.Series:
        """V = Compensation of Employees."""
        return data[_KEY_COMP]

    def _constant_capital(self, data: dict[str, pd.Series]) -> pd.Series:
        """C = Current-Cost Net Stock of Private Fixed Assets."""
        return data[_KEY_ASSETS]

    def compute_rate_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of profit: r = S / (C + V).

        Args:
            data: Dict with keys 'national_income', 'compensation',
                  'net_fixed_assets_current'.

        Returns:
            pd.Series of rate of profit values indexed by date.
        """
        s = self._surplus_value(data)
        c = self._constant_capital(data)
        v = self._variable_capital(data)
        return s / (c + v)

    def compute_occ(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute organic composition of capital: OCC = C / V.

        Args:
            data: Dict with keys 'compensation', 'net_fixed_assets_current'.

        Returns:
            pd.Series of OCC values indexed by date.
        """
        c = self._constant_capital(data)
        v = self._variable_capital(data)
        return c / v

    def compute_rate_of_surplus_value(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of surplus value: s/v = S / V.

        Args:
            data: Dict with keys 'national_income', 'compensation'.

        Returns:
            pd.Series of rate of surplus value indexed by date.
        """
        s = self._surplus_value(data)
        v = self._variable_capital(data)
        return s / v

    def compute_mass_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute mass of profit (absolute surplus value).

        Args:
            data: Dict with keys 'national_income', 'compensation'.

        Returns:
            pd.Series of absolute surplus value in billions USD.
        """
        return self._surplus_value(data)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_required_series(self) -> list[str]:
        """Return FRED series IDs needed for core indicator computation."""
        return [
            SERIES_NATIONAL_INCOME,
            SERIES_COMPENSATION,
            SERIES_NET_FIXED_ASSETS_CURRENT,
        ]

    def get_documentation(self) -> list[IndicatorDoc]:
        """Return self-documentation for all 4 core indicators."""
        ni_mapping = NIPAMapping(
            marx_category="national_income",
            nipa_table="T11200",
            nipa_line=1,
            nipa_description="National income",
            operation="direct",
            notes="FRED series A053RC1Q027SBEA",
        )
        comp_mapping = NIPAMapping(
            marx_category="variable_capital",
            nipa_table="T11200",
            nipa_line=2,
            nipa_description="Compensation of employees",
            operation="direct",
            notes="FRED series A576RC1",
        )
        assets_mapping = NIPAMapping(
            marx_category="constant_capital",
            nipa_table="FAAt101",
            nipa_line=2,
            nipa_description="Current-cost net stock of private fixed assets",
            operation="direct",
            notes=(
                "FRED series K1NTOTL1SI000. Shaikh/Tonak use current-cost "
                "(replacement-cost) valuation, reflecting the actual cost of "
                "reproducing the capital stock at current prices."
            ),
        )

        return [
            IndicatorDoc(
                name="Rate of Profit",
                slug="rate_of_profit",
                formula_latex=r"r = \frac{S}{C + V}",
                interpretation=(
                    "The general rate of profit measures the return on total "
                    "capital advanced. S = National Income - Compensation, "
                    "C = current-cost net fixed assets, V = compensation. "
                    "Shaikh/Tonak's current-cost valuation shows the profit "
                    "rate relative to replacement-cost capital."
                ),
                mappings=[ni_mapping, comp_mapping, assets_mapping],
                citations=[_CITATION],
            ),
            IndicatorDoc(
                name="Organic Composition of Capital",
                slug="occ",
                formula_latex=r"OCC = \frac{C}{V}",
                interpretation=(
                    "The ratio of constant capital to variable capital. "
                    "A rising OCC indicates capital-intensive accumulation, "
                    "which Marx argued would tend to depress the rate of profit. "
                    "Current-cost C reflects the actual replacement cost of "
                    "the capital stock."
                ),
                mappings=[assets_mapping, comp_mapping],
                citations=[_CITATION],
            ),
            IndicatorDoc(
                name="Rate of Surplus Value",
                slug="rate_of_surplus_value",
                formula_latex=r"\frac{s}{v} = \frac{S}{V}",
                interpretation=(
                    "The rate of exploitation: ratio of surplus value to "
                    "variable capital. Measures the share of new value "
                    "appropriated as profit vs. paid as wages."
                ),
                mappings=[ni_mapping, comp_mapping],
                citations=[_CITATION],
            ),
            IndicatorDoc(
                name="Mass of Profit",
                slug="mass_of_profit",
                formula_latex=r"M = S = NI - V",
                interpretation=(
                    "The absolute volume of surplus value in billions of "
                    "current USD. While the rate of profit may fall, the "
                    "mass of profit can still rise if total capital expands "
                    "faster than the rate declines."
                ),
                mappings=[ni_mapping, comp_mapping],
                citations=[_CITATION],
            ),
        ]
