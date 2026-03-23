"""Tests for indicator computation -- FEAT-02 through FEAT-09.

These tests define the expected behavior of concrete methodology mappers.
They are skipped until Plan 02-02 implements the Shaikh/Tonak and Kliman
mappers. Each test uses known input values to verify formula correctness.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Shared mock NIPA data fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_nipa_data() -> dict[str, pd.Series]:
    """Return a dict of pd.Series with known values for formula verification.

    Core series (annual frequency):
        national_income: [1000, 1100, 1200]
        compensation: [600, 650, 700]
        corporate_profits: [200, 220, 240]
        net_fixed_assets_current: [3000, 3200, 3400]
        net_fixed_assets_historical: [2500, 2700, 2900]
        output_per_hour: [100, 105, 110]
        real_compensation_per_hour: [100, 101, 102]

    Financial series (quarterly, 40 periods for HP filter testing):
        credit_total: linear growth + sine wave
        nominal_gdp: linear growth
    """
    annual_idx = pd.date_range("2020", periods=3, freq="YE")

    data = {
        "national_income": pd.Series(
            [1000.0, 1100.0, 1200.0], index=annual_idx, name="national_income"
        ),
        "compensation": pd.Series(
            [600.0, 650.0, 700.0], index=annual_idx, name="compensation"
        ),
        "corporate_profits": pd.Series(
            [200.0, 220.0, 240.0], index=annual_idx, name="corporate_profits"
        ),
        "net_fixed_assets_current": pd.Series(
            [3000.0, 3200.0, 3400.0],
            index=annual_idx,
            name="net_fixed_assets_current",
        ),
        "net_fixed_assets_historical": pd.Series(
            [2500.0, 2700.0, 2900.0],
            index=annual_idx,
            name="net_fixed_assets_historical",
        ),
        "output_per_hour": pd.Series(
            [100.0, 105.0, 110.0], index=annual_idx, name="output_per_hour"
        ),
        "real_compensation_per_hour": pd.Series(
            [100.0, 101.0, 102.0],
            index=annual_idx,
            name="real_compensation_per_hour",
        ),
    }

    # Quarterly series for HP filter testing (40 quarters = 10 years)
    quarterly_idx = pd.date_range("2010-01-01", periods=40, freq="QE")
    t = np.arange(40, dtype=float)

    # Credit: linear growth with cyclical component
    data["credit_total"] = pd.Series(
        5000.0 + 100.0 * t + 200.0 * np.sin(2 * np.pi * t / 20),
        index=quarterly_idx,
        name="credit_total",
    )

    # GDP: steady linear growth
    data["nominal_gdp"] = pd.Series(
        20000.0 + 200.0 * t,
        index=quarterly_idx,
        name="nominal_gdp",
    )

    return data


# ---------------------------------------------------------------------------
# Core indicator computation tests (awaiting Plan 02-02)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestRateOfProfit:
    """Rate of profit = S / (C + V) with known values."""

    def test_rate_of_profit_known_values(self, mock_nipa_data: dict[str, pd.Series]) -> None:
        """S=400, C=3000, V=600 -> r = 400 / (3000+600) = 0.1111...

        Using national_income - compensation = surplus value (simplified).
        Year 2020: S = 1000 - 600 = 400, C = 3000, V = 600
        r = 400 / (3000 + 600) = 0.1111
        """
        # Import will work once Plan 02-02 provides a concrete mapper
        from ecpm.indicators.registry import MethodologyRegistry

        mapper = MethodologyRegistry.default()
        result = mapper.compute_rate_of_profit(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        # First year: S = 1000 - 600 = 400; C + V = 3000 + 600 = 3600
        assert result.iloc[0] == pytest.approx(400 / 3600, rel=1e-3)


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestOCC:
    """OCC = C / V with known values."""

    def test_occ_known_values(self, mock_nipa_data: dict[str, pd.Series]) -> None:
        """C=3000, V=600 -> OCC = 3000/600 = 5.0."""
        from ecpm.indicators.registry import MethodologyRegistry

        mapper = MethodologyRegistry.default()
        result = mapper.compute_occ(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(3000 / 600, rel=1e-3)


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestRateOfSurplusValue:
    """Rate of surplus value = S / V."""

    def test_rate_of_surplus_value_known_values(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """S = 1000-600 = 400, V = 600 -> s/v = 400/600 = 0.6667."""
        from ecpm.indicators.registry import MethodologyRegistry

        mapper = MethodologyRegistry.default()
        result = mapper.compute_rate_of_surplus_value(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(400 / 600, rel=1e-3)


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestMassOfProfit:
    """Mass of profit = absolute surplus value."""

    def test_mass_of_profit_returns_absolute_surplus(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Year 2020: S = 1000 - 600 = 400."""
        from ecpm.indicators.registry import MethodologyRegistry

        mapper = MethodologyRegistry.default()
        result = mapper.compute_mass_of_profit(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(400.0, rel=1e-3)


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestProductivityWageGap:
    """Productivity-wage gap = ratio of productivity index to compensation index."""

    def test_productivity_wage_gap_over_window(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Output grows 10% (100->110), compensation 2% (100->102).

        Gap should increase: output index / comp index > 100.
        """
        from ecpm.indicators.registry import MethodologyRegistry

        mapper = MethodologyRegistry.default()
        result = mapper.compute_productivity_wage_gap(mock_nipa_data, window=1)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        # First period: both at base=100, gap=100
        assert result.iloc[0] == pytest.approx(100.0, rel=1e-2)
        # Last period: output 110%, comp 102% -> gap > 100
        assert result.iloc[-1] > 100.0


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestCreditGDPGap:
    """Credit-to-GDP gap via HP filter trend extraction."""

    def test_credit_gdp_gap_with_hp_filter(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """With 40 quarterly observations, HP filter should extract a trend.

        Gap = actual ratio - HP trend. Should not be all zeros.
        """
        from ecpm.indicators.registry import MethodologyRegistry

        mapper = MethodologyRegistry.default()
        result = mapper.compute_credit_gdp_gap(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 40
        # Gap should have non-trivial variation (not all zeros)
        assert result.std() > 0.01


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestFinancialRealRatio:
    """Financial-to-real asset ratio."""

    def test_financial_real_ratio_computes_correctly(self) -> None:
        """financial_assets=5000, real_assets=2000 -> ratio=2.5."""
        from ecpm.indicators.registry import MethodologyRegistry

        idx = pd.date_range("2020", periods=3, freq="YE")
        data = {
            "financial_assets": pd.Series([5000.0, 5500.0, 6000.0], index=idx),
            "real_assets": pd.Series([2000.0, 2100.0, 2200.0], index=idx),
        }

        mapper = MethodologyRegistry.default()
        result = mapper.compute_financial_real_ratio(data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(5000 / 2000, rel=1e-3)


@pytest.mark.skip(reason="Awaiting Plan 02-02 implementation")
class TestFrequencyAlignment:
    """LOCF frequency alignment for mixed-frequency inputs."""

    def test_locf_alignment_for_mixed_frequency(self) -> None:
        """Verify that LOCF strategy is used for mixed-frequency alignment.

        Annual capital stock aligned with quarterly income data should
        produce meaningful ratios without NaN.
        """
        from ecpm.indicators.definitions import FREQUENCY_STRATEGY

        assert FREQUENCY_STRATEGY == "LOCF"

        # When mappers exist, they should handle mixed-frequency via LOCF
        # This test will be expanded in Plan 02-02
