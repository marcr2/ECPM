"""Kliman TSSI methodology mapper for NIPA-to-Marx translation.

Implements the Kliman (2012) Temporal Single-System Interpretation (TSSI)
methodology for computing Marxist economic indicators from US national
accounts data. Key distinguishing feature: uses historical-cost net stock
of private fixed assets for constant capital (C), which produces a different
long-run profit rate trajectory from Shaikh/Tonak's current-cost approach.

Reference: Kliman, A. (2012). The Failure of Capitalist Production:
Underlying Causes of the Great Recession. Pluto Press.
"""

from __future__ import annotations

import pandas as pd

from ecpm.indicators.base import IndicatorDoc, MethodologyMapper, NIPAMapping

# FRED series IDs used by this methodology
SERIES_NATIONAL_INCOME = "A053RC1Q027SBEA"
SERIES_COMPENSATION = "A576RC1"
SERIES_NET_FIXED_ASSETS_HISTORICAL = "K1NTOTL1HI000"

# Internal data dict keys
_KEY_NI = "national_income"
_KEY_COMP = "compensation"
_KEY_ASSETS = "net_fixed_assets_historical"

_CITATION = (
    "Kliman, A. (2012). The Failure of Capitalist Production: "
    "Underlying Causes of the Great Recession. Pluto Press."
)


class KlimanMapper(MethodologyMapper):
    """Kliman TSSI (2012) methodology for Marxist indicator computation.

    Computes surplus value identically to Shaikh/Tonak (National Income
    minus Compensation), but uses historical-cost net stock of private
    fixed assets for constant capital. This temporal interpretation means
    the denominator reflects what capitalists actually paid for the capital
    stock, not its current replacement cost.

    The key empirical consequence: under Kliman's TSSI, the rate of profit
    does NOT recover during the neoliberal period (post-1982), because
    historical-cost capital stock grows faster than current-cost stock
    when inflation decelerates. This produces a secular declining trend
    that Shaikh/Tonak's current-cost measure does not show.

    Series key convention:
        - national_income: FRED A053RC1Q027SBEA (National Income)
        - compensation: FRED A576RC1 (Compensation of Employees)
        - net_fixed_assets_historical: FRED K1NTOTL1HI000 (Historical-Cost Net Stock)
    """

    @property
    def name(self) -> str:
        return "Kliman TSSI"

    @property
    def slug(self) -> str:
        return "kliman"

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
        """C = Historical-Cost Net Stock of Private Fixed Assets.

        This is the TSSI distinguishing choice: capital is valued at
        historical (original purchase) prices, not replacement cost.
        """
        return data[_KEY_ASSETS]

    def compute_rate_of_profit(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of profit: r = S / (C + V).

        Uses historical-cost C, producing different values from Shaikh/Tonak.

        Args:
            data: Dict with keys 'national_income', 'compensation',
                  'net_fixed_assets_historical'.

        Returns:
            pd.Series of rate of profit values indexed by date.
        """
        s = self._surplus_value(data)
        c = self._constant_capital(data)
        v = self._variable_capital(data)
        return s / (c + v)

    def compute_occ(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute organic composition of capital: OCC = C / V.

        Uses historical-cost C.

        Args:
            data: Dict with keys 'compensation', 'net_fixed_assets_historical'.

        Returns:
            pd.Series of OCC values indexed by date.
        """
        c = self._constant_capital(data)
        v = self._variable_capital(data)
        return c / v

    def compute_rate_of_surplus_value(self, data: dict[str, pd.Series]) -> pd.Series:
        """Compute rate of surplus value: s/v = S / V.

        Same as Shaikh/Tonak -- surplus value and variable capital
        definitions do not differ between methodologies.

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

        Same as Shaikh/Tonak -- surplus value definition does not differ.

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
            SERIES_NET_FIXED_ASSETS_HISTORICAL,
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
            nipa_table="FAAt102",
            nipa_line=2,
            nipa_description="Historical-cost net stock of private fixed assets",
            operation="direct",
            notes=(
                "FRED series K1NTOTL1HI000. Kliman's TSSI uses historical-cost "
                "(original purchase price) valuation. When inflation decelerates, "
                "historical-cost capital grows faster than current-cost, producing "
                "a persistently lower rate of profit that does not 'recover' in "
                "the neoliberal period as current-cost measures suggest."
            ),
        )

        return [
            IndicatorDoc(
                name="Rate of Profit",
                slug="rate_of_profit",
                formula_latex=r"r = \frac{S}{C_{hist} + V}",
                interpretation=(
                    "The general rate of profit under TSSI. Uses historical-cost "
                    "capital stock in the denominator, reflecting the actual "
                    "capital advanced by the capitalist class. This measure shows "
                    "a secular decline without neoliberal recovery, unlike "
                    "current-cost measures."
                ),
                mappings=[ni_mapping, comp_mapping, assets_mapping],
                citations=[_CITATION],
            ),
            IndicatorDoc(
                name="Organic Composition of Capital",
                slug="occ",
                formula_latex=r"OCC = \frac{C_{hist}}{V}",
                interpretation=(
                    "The ratio of constant to variable capital, measured at "
                    "historical cost. The rising OCC under historical-cost "
                    "valuation is more pronounced than under current-cost "
                    "because accumulated capital is not revalued downward "
                    "during disinflationary periods."
                ),
                mappings=[assets_mapping, comp_mapping],
                citations=[_CITATION],
            ),
            IndicatorDoc(
                name="Rate of Surplus Value",
                slug="rate_of_surplus_value",
                formula_latex=r"\frac{s}{v} = \frac{S}{V}",
                interpretation=(
                    "The rate of exploitation. Identical to Shaikh/Tonak's "
                    "computation since surplus value and variable capital "
                    "definitions do not differ between methodologies."
                ),
                mappings=[ni_mapping, comp_mapping],
                citations=[_CITATION],
            ),
            IndicatorDoc(
                name="Mass of Profit",
                slug="mass_of_profit",
                formula_latex=r"M = S = NI - V",
                interpretation=(
                    "The absolute volume of surplus value. Identical to "
                    "Shaikh/Tonak's computation. The mass can rise even as "
                    "the rate of profit falls, illustrating Marx's law of "
                    "the tendential fall of the rate of profit alongside "
                    "counteracting tendencies."
                ),
                mappings=[ni_mapping, comp_mapping],
                citations=[_CITATION],
            ),
        ]
