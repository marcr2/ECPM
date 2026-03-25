"""Tests for indicator computation -- FEAT-02 through FEAT-09.

These tests verify the concrete Shaikh/Tonak and Kliman methodology mappers.
Each test uses known input values to verify formula correctness.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ecpm.indicators.shaikh_tonak import ShaikhTonakMapper
from ecpm.indicators.kliman import KlimanMapper
from ecpm.indicators.registry import MethodologyRegistry

# ---------------------------------------------------------------------------
# Shared mock NIPA data fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_nipa_data() -> dict[str, pd.Series]:
    """Return a dict of pd.Series with known values for formula verification.

    Core series (annual frequency):
        national_income: BEA-style millions [1_000_000, ...] (Shaikh /1000 -> billions)
        compensation: [600, 650, 700] billions (FRED)
        corporate_profits: [200, 220, 240]
        net_fixed_assets_current: FRED millions [3_000_000, ...] (Shaikh /1000 -> billions)
        net_fixed_assets_historical: FRED millions [2_500_000, ...] (Kliman /1000 -> billions)
        output_per_hour: [100, 105, 110]
        real_compensation_per_hour: [100, 101, 102]

    Financial series (quarterly, 40 periods for HP filter testing):
        credit_total: linear growth + sine wave
        nominal_gdp: linear growth
    """
    annual_idx = pd.date_range("2020", periods=3, freq="YE")

    data = {
        "national_income": pd.Series(
            [1_000_000.0, 1_100_000.0, 1_200_000.0],
            index=annual_idx,
            name="national_income",
        ),
        "compensation": pd.Series(
            [600.0, 650.0, 700.0], index=annual_idx, name="compensation"
        ),
        "corporate_profits": pd.Series(
            [200.0, 220.0, 240.0], index=annual_idx, name="corporate_profits"
        ),
        "net_fixed_assets_current": pd.Series(
            [3_000_000.0, 3_200_000.0, 3_400_000.0],
            index=annual_idx,
            name="net_fixed_assets_current",
        ),
        "net_fixed_assets_historical": pd.Series(
            [2_500_000.0, 2_700_000.0, 2_900_000.0],
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

    # Financial series for ratio tests -- quarterly financial_assets (from
    # TFAABSNNCB) and annual real_assets (from K1PTOTL1ES000) to
    # exercise the LOCF frequency alignment in compute_financial_real_ratio.
    financial_quarterly_idx = pd.date_range("2020-03-31", periods=8, freq="QE")
    data["financial_assets"] = pd.Series(
        [30000.0, 31000.0, 32000.0, 33000.0,
         34000.0, 35000.0, 36000.0, 37000.0],
        index=financial_quarterly_idx,
        name="financial_assets",
    )
    data["real_assets"] = pd.Series(
        [60000.0, 62000.0], index=pd.date_range("2020", periods=2, freq="YE"),
        name="real_assets",
    )
    data["debt_service"] = pd.Series(
        [100_000.0, 120_000.0, 130_000.0],
        index=annual_idx,
        name="debt_service",
    )
    data["corporate_income"] = pd.Series(
        [500.0, 550.0, 600.0], index=annual_idx, name="corporate_income"
    )

    return data


@pytest.fixture
def mock_nipa_data_kliman(mock_nipa_data: dict[str, pd.Series]) -> dict[str, pd.Series]:
    """KlimanMapper uses FRED national income in billions (no /1000)."""
    data = dict(mock_nipa_data)
    idx = data["national_income"].index
    data["national_income"] = pd.Series(
        [1000.0, 1100.0, 1200.0], index=idx, name="national_income"
    )
    return data


@pytest.fixture(autouse=True)
def _register_mappers():
    """Register both real mappers and reset after each test."""
    MethodologyRegistry.reset()
    MethodologyRegistry.register(ShaikhTonakMapper())
    MethodologyRegistry.register(KlimanMapper())
    yield
    MethodologyRegistry.reset()


# ---------------------------------------------------------------------------
# Shaikh/Tonak core indicator computation tests
# ---------------------------------------------------------------------------


class TestShaikhTonakRateOfProfit:
    """Rate of profit = S / (C + V) with Shaikh/Tonak (current-cost C)."""

    def test_rate_of_profit_known_values(self, mock_nipa_data: dict[str, pd.Series]) -> None:
        """S=400, C=3000, V=600 -> r = 400 / (3000+600) = 0.1111...

        Using national_income - compensation = surplus value (simplified).
        Year 2020: S = 1000 - 600 = 400, C = 3000, V = 600
        r = 400 / (3000 + 600) = 0.1111
        """
        mapper = MethodologyRegistry.default()
        result = mapper.compute_rate_of_profit(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        # First year: S = 1000 - 600 = 400; C + V = 3000 + 600 = 3600
        assert result.iloc[0] == pytest.approx(400 / 3600, rel=1e-3)

    def test_rate_of_profit_all_years(self, mock_nipa_data: dict[str, pd.Series]) -> None:
        """All three years should produce correct rates."""
        mapper = MethodologyRegistry.default()
        result = mapper.compute_rate_of_profit(mock_nipa_data)

        # Year 2021: S = 1100 - 650 = 450, C = 3200, V = 650
        assert result.iloc[1] == pytest.approx(450 / (3200 + 650), rel=1e-3)
        # Year 2022: S = 1200 - 700 = 500, C = 3400, V = 700
        assert result.iloc[2] == pytest.approx(500 / (3400 + 700), rel=1e-3)


class TestShaikhTonakOCC:
    """OCC = C / V with Shaikh/Tonak (current-cost C)."""

    def test_occ_known_values(self, mock_nipa_data: dict[str, pd.Series]) -> None:
        """C=3000, V=600 -> OCC = 3000/600 = 5.0."""
        mapper = MethodologyRegistry.default()
        result = mapper.compute_occ(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(3000 / 600, rel=1e-3)


class TestShaikhTonakRateOfSurplusValue:
    """Rate of surplus value = S / V."""

    def test_rate_of_surplus_value_known_values(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """S = 1000-600 = 400, V = 600 -> s/v = 400/600 = 0.6667."""
        mapper = MethodologyRegistry.default()
        result = mapper.compute_rate_of_surplus_value(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(400 / 600, rel=1e-3)


class TestShaikhTonakMassOfProfit:
    """Mass of profit = absolute surplus value."""

    def test_mass_of_profit_returns_absolute_surplus(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Year 2020: S = 1000 - 600 = 400."""
        mapper = MethodologyRegistry.default()
        result = mapper.compute_mass_of_profit(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(400.0, rel=1e-3)


# ---------------------------------------------------------------------------
# Kliman TSSI core indicator computation tests
# ---------------------------------------------------------------------------


class TestKlimanRateOfProfit:
    """Rate of profit with Kliman (historical-cost C) should differ from Shaikh/Tonak."""

    def test_rate_of_profit_uses_historical_cost(
        self, mock_nipa_data_kliman: dict[str, pd.Series]
    ) -> None:
        """S=400, C_hist=2500, V=600 -> r = 400 / (2500+600) = 0.1290...

        Different from Shaikh/Tonak because historical-cost C is lower.
        """
        mapper = MethodologyRegistry.get("kliman")
        result = mapper.compute_rate_of_profit(mock_nipa_data_kliman)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        # Historical-cost C = 2500, not 3000
        assert result.iloc[0] == pytest.approx(400 / (2500 + 600), rel=1e-3)

    def test_kliman_rate_differs_from_shaikh_tonak(
        self,
        mock_nipa_data: dict[str, pd.Series],
        mock_nipa_data_kliman: dict[str, pd.Series],
    ) -> None:
        """Kliman and Shaikh/Tonak produce different rate of profit values."""
        st_mapper = MethodologyRegistry.get("shaikh-tonak")
        kl_mapper = MethodologyRegistry.get("kliman")

        st_result = st_mapper.compute_rate_of_profit(mock_nipa_data)
        kl_result = kl_mapper.compute_rate_of_profit(mock_nipa_data_kliman)

        # Kliman rate should be higher (lower C in denominator)
        assert kl_result.iloc[0] > st_result.iloc[0]


class TestKlimanOCC:
    """OCC with Kliman uses historical-cost C."""

    def test_occ_uses_historical_cost(
        self, mock_nipa_data_kliman: dict[str, pd.Series]
    ) -> None:
        """C_hist=2500, V=600 -> OCC = 2500/600 = 4.1667."""
        mapper = MethodologyRegistry.get("kliman")
        result = mapper.compute_occ(mock_nipa_data_kliman)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(2500 / 600, rel=1e-3)


# ---------------------------------------------------------------------------
# Mapper metadata tests
# ---------------------------------------------------------------------------


class TestShaikhTonakMetadata:
    """Shaikh/Tonak mapper properties and documentation."""

    def test_name_and_slug(self) -> None:
        mapper = ShaikhTonakMapper()
        assert mapper.name == "Shaikh/Tonak"
        assert mapper.slug == "shaikh-tonak"

    def test_get_required_series_returns_fred_ids(self) -> None:
        mapper = ShaikhTonakMapper()
        series = mapper.get_required_series()
        assert isinstance(series, list)
        assert len(series) >= 3  # At least NI, compensation, fixed assets
        assert "BEA:T11200:L1" in series  # National Income (NIPA T11200 L1)
        assert "A576RC1" in series  # Compensation
        assert "K1PTOTL1ES000" in series  # Current-cost net fixed assets

    def test_get_documentation_returns_indicator_docs(self) -> None:
        mapper = ShaikhTonakMapper()
        docs = mapper.get_documentation()
        assert isinstance(docs, list)
        assert len(docs) == 8  # 4 core + 4 methodology-independent financial
        slugs = {d.slug for d in docs}
        assert "rate_of_profit" in slugs
        assert "occ" in slugs
        assert "rate_of_surplus_value" in slugs
        assert "mass_of_profit" in slugs
        assert "credit_gdp_gap" in slugs

    def test_documentation_has_latex_formulas(self) -> None:
        mapper = ShaikhTonakMapper()
        docs = mapper.get_documentation()
        for doc in docs:
            assert doc.formula_latex, f"Missing LaTeX for {doc.slug}"
            assert "frac" in doc.formula_latex or "=" in doc.formula_latex

    def test_documentation_has_nipa_mappings(self) -> None:
        mapper = ShaikhTonakMapper()
        docs = mapper.get_documentation()
        for doc in docs:
            assert len(doc.mappings) > 0, f"Missing NIPA mappings for {doc.slug}"

    def test_documentation_has_citations(self) -> None:
        mapper = ShaikhTonakMapper()
        docs = mapper.get_documentation()
        for doc in docs:
            assert len(doc.citations) > 0, f"Missing citations for {doc.slug}"
            assert any("Shaikh" in c for c in doc.citations)


class TestKlimanMetadata:
    """Kliman mapper properties and documentation."""

    def test_name_and_slug(self) -> None:
        mapper = KlimanMapper()
        assert mapper.name == "Kliman TSSI"
        assert mapper.slug == "kliman"

    def test_get_required_series_has_historical_cost(self) -> None:
        mapper = KlimanMapper()
        series = mapper.get_required_series()
        assert isinstance(series, list)
        # Should have historical-cost series, not current-cost
        assert "K1NTOTL1SI000" not in series  # NOT current-cost
        # Has the equivalent historical-cost series
        assert any("HI" in s or "HIST" in s.upper() or "K1NTOTL1HI" in s for s in series)

    def test_get_documentation_has_kliman_citations(self) -> None:
        mapper = KlimanMapper()
        docs = mapper.get_documentation()
        assert len(docs) == 8
        for doc in docs:
            assert any("Kliman" in c for c in doc.citations)


class TestRegistryIntegration:
    """Both mappers registered and discoverable."""

    def test_both_mappers_registered(self) -> None:
        all_mappers = MethodologyRegistry.list_all()
        slugs = {m.slug for m in all_mappers}
        assert "shaikh-tonak" in slugs
        assert "kliman" in slugs

    def test_default_is_shaikh_tonak(self) -> None:
        default = MethodologyRegistry.default()
        assert default.slug == "shaikh-tonak"


# ---------------------------------------------------------------------------
# Productivity-wage gap (methodology-independent, on ABC default)
# ---------------------------------------------------------------------------


class TestProductivityWageGap:
    """Productivity-wage gap = ratio of productivity index to compensation index."""

    def test_productivity_wage_gap_over_window(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Output grows 10% (100->110), compensation 2% (100->102).

        Gap should increase: output index / comp index > 100.
        """
        mapper = MethodologyRegistry.default()
        result = mapper.compute_productivity_wage_gap(mock_nipa_data, window=1)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        # First period: both at base=100, gap=100
        assert result.iloc[0] == pytest.approx(100.0, rel=1e-2)
        # Last period: output 110%, comp 102% -> gap > 100
        assert result.iloc[-1] > 100.0


# ---------------------------------------------------------------------------
# Credit-GDP gap (methodology-independent, on ABC default)
# ---------------------------------------------------------------------------


class TestCreditGDPGap:
    """Credit-to-GDP gap via HP filter trend extraction."""

    def test_credit_gdp_gap_with_hp_filter(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """With 40 quarterly observations, HP filter should extract a trend.

        Gap = actual ratio - HP trend. Should not be all zeros.
        """
        mapper = MethodologyRegistry.default()
        result = mapper.compute_credit_gdp_gap(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 40
        # Gap should have non-trivial variation (not all zeros)
        assert result.std() > 0.004


# ---------------------------------------------------------------------------
# Financial-to-real ratio (methodology-independent, on ABC default)
# ---------------------------------------------------------------------------


class TestFinancialRealRatio:
    """Financial-to-real asset ratio with LOCF frequency alignment."""

    def test_financial_real_ratio_computes_correctly(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Quarterly financial_assets aligned against annual real_assets via LOCF.

        real_assets: 2020-12-31=60000, 2021-12-31=62000
        financial_assets: 8 quarters starting 2020-03-31

        After LOCF alignment, the annual year-end values (2020-12-31=60000,
        2021-12-31=62000) are forward-filled onto the quarterly index.
        Q1-Q3 2020 precede the first annual observation, so real_assets
        is NaN there and the ratio is NaN for those periods.
        """
        mapper = MethodologyRegistry.default()
        result = mapper.compute_financial_real_ratio(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 8
        # Q1-Q3 2020 have NaN (no prior annual observation to forward-fill)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])
        # Q4-2020 (2020-12-31): 33000 / 60000
        assert result.iloc[3] == pytest.approx(33000 / 60000, rel=1e-3)
        # Q3-2021 (2021-09-30): 36000 / 60000 (still ffill from 2020 annual)
        assert result.iloc[6] == pytest.approx(36000 / 60000, rel=1e-3)
        # Q4-2021 (2021-12-31): 37000 / 62000
        assert result.iloc[7] == pytest.approx(37000 / 62000, rel=1e-3)


# ---------------------------------------------------------------------------
# Debt service ratio (methodology-independent, on ABC default)
# ---------------------------------------------------------------------------


class TestDebtServiceRatio:
    """Corporate debt service ratio."""

    def test_debt_service_ratio_computes_correctly(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """debt_service=100, corporate_income=500 -> ratio=20%."""
        mapper = MethodologyRegistry.default()
        result = mapper.compute_debt_service_ratio(mock_nipa_data)

        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(100 / 500 * 100, rel=1e-3)


# ---------------------------------------------------------------------------
# Frequency alignment
# ---------------------------------------------------------------------------


class TestFrequencyAlignment:
    """LOCF frequency alignment for mixed-frequency inputs."""

    def test_locf_alignment_for_mixed_frequency(self) -> None:
        """Verify that LOCF strategy is used for mixed-frequency alignment."""
        from ecpm.indicators.definitions import FREQUENCY_STRATEGY

        assert FREQUENCY_STRATEGY == "LOCF"

    def test_financial_real_ratio_locf_alignment(self) -> None:
        """LOCF alignment: annual real_assets forward-fills onto quarterly index."""
        from ecpm.indicators.financial import compute_financial_real_ratio

        quarterly_idx = pd.date_range("2020-03-31", periods=4, freq="QE")
        annual_idx = pd.date_range("2020", periods=1, freq="YE")

        data = {
            "financial_assets": pd.Series(
                [10.0, 20.0, 30.0, 40.0], index=quarterly_idx
            ),
            "real_assets": pd.Series([100.0], index=annual_idx),
        }
        result = compute_financial_real_ratio(data)

        assert len(result) == 4
        # Q1 (2020-03-31) precedes the annual obs (2020-12-31), so NaN
        assert pd.isna(result.iloc[0])
        # Q4 (2020-12-31) and after: real_assets=100 via LOCF
        assert result.iloc[3] == pytest.approx(40.0 / 100.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Standalone financial.py function tests
# ---------------------------------------------------------------------------


class TestFinancialStandaloneFunctions:
    """Test standalone financial indicator functions from financial.py."""

    def test_compute_productivity_wage_gap_standalone(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Standalone function should produce same result as ABC default."""
        from ecpm.indicators.financial import compute_productivity_wage_gap

        result = compute_productivity_wage_gap(mock_nipa_data, window=1)
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[0] == pytest.approx(100.0, rel=1e-2)
        assert result.iloc[-1] > 100.0

    def test_compute_credit_gdp_gap_standalone(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Standalone function produces gap with non-trivial variation."""
        from ecpm.indicators.financial import compute_credit_gdp_gap

        result = compute_credit_gdp_gap(mock_nipa_data)
        assert isinstance(result, pd.Series)
        assert len(result) == 40
        assert result.std() > 0.004

    def test_compute_financial_real_ratio_standalone(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Standalone function computes financial/real ratio with LOCF alignment."""
        from ecpm.indicators.financial import compute_financial_real_ratio

        result = compute_financial_real_ratio(mock_nipa_data)
        assert isinstance(result, pd.Series)
        assert len(result) == 8
        # Q4-2020 (2020-12-31): 33000 / 60000
        assert result.iloc[3] == pytest.approx(33000 / 60000, rel=1e-3)

    def test_compute_debt_service_ratio_standalone(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """Standalone function computes debt service ratio in percent."""
        from ecpm.indicators.financial import compute_debt_service_ratio

        result = compute_debt_service_ratio(mock_nipa_data)
        assert isinstance(result, pd.Series)
        assert result.iloc[0] == pytest.approx(100 / 500 * 100, rel=1e-3)

    def test_abc_delegates_to_financial_module(
        self, mock_nipa_data: dict[str, pd.Series]
    ) -> None:
        """ABC default methods should delegate to financial.py functions."""
        from ecpm.indicators.financial import compute_financial_real_ratio

        mapper = MethodologyRegistry.default()
        mapper_result = mapper.compute_financial_real_ratio(mock_nipa_data)
        standalone_result = compute_financial_real_ratio(mock_nipa_data)

        pd.testing.assert_series_equal(mapper_result, standalone_result)


# ---------------------------------------------------------------------------
# Computation orchestrator tests
# ---------------------------------------------------------------------------


class TestComputationOrchestrator:
    """Test the computation orchestrator dispatch logic."""

    def test_get_indicator_dispatch_map(self) -> None:
        """Orchestrator should have a dispatch map for all indicator slugs."""
        from ecpm.indicators.computation import INDICATOR_DISPATCH

        from ecpm.indicators.definitions import IndicatorSlug

        for slug in IndicatorSlug:
            assert slug in INDICATOR_DISPATCH or slug.value in INDICATOR_DISPATCH, (
                f"Missing dispatch entry for {slug}"
            )
