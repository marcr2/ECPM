"""Tests for shock propagation simulation functions.

Tests single-sector and multi-sector shock simulation, critical sector
identification, and backward/forward linkage computation.
"""

from __future__ import annotations

import numpy as np
import pytest

# Skip if structural module not implemented yet
shock = pytest.importorskip("ecpm.structural.shock")


class TestSimulateShock:
    """Tests for simulate_shock function."""

    def test_single_sector_shock_returns_dict(self, synthetic_leontief_inverse_3x3):
        """simulate_shock should return a dict with impact data."""
        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.simulate_shock(
            L=synthetic_leontief_inverse_3x3,
            shock_industry_idx=0,
            shock_magnitude=10.0,
            sector_codes=sector_codes,
        )

        assert isinstance(result, dict)
        assert "impact_vector" in result
        assert "ranked_impacts" in result
        assert "total_impact" in result

    def test_single_sector_shock_impact_vector_length(
        self, synthetic_leontief_inverse_3x3
    ):
        """Impact vector should have length equal to number of sectors."""
        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.simulate_shock(
            L=synthetic_leontief_inverse_3x3,
            shock_industry_idx=0,
            shock_magnitude=10.0,
            sector_codes=sector_codes,
        )

        assert len(result["impact_vector"]) == 3

    def test_single_sector_shock_ranked_impacts_sorted(
        self, synthetic_leontief_inverse_3x3
    ):
        """Ranked impacts should be sorted by absolute impact descending."""
        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.simulate_shock(
            L=synthetic_leontief_inverse_3x3,
            shock_industry_idx=0,
            shock_magnitude=10.0,
            sector_codes=sector_codes,
        )

        ranked = result["ranked_impacts"]
        impacts = [abs(r["impact"]) for r in ranked]
        assert impacts == sorted(impacts, reverse=True)

    def test_single_sector_shock_total_impact_positive(
        self, synthetic_leontief_inverse_3x3
    ):
        """Total impact of positive shock should be positive."""
        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.simulate_shock(
            L=synthetic_leontief_inverse_3x3,
            shock_industry_idx=0,
            shock_magnitude=10.0,
            sector_codes=sector_codes,
        )

        assert result["total_impact"] > 0


class TestSimulateMultiSectorShock:
    """Tests for simulate_multi_sector_shock function."""

    def test_multi_sector_shock_returns_dict(self, synthetic_leontief_inverse_3x3):
        """simulate_multi_sector_shock should return a dict with impact data."""
        sector_codes = ["IND1", "IND2", "IND3"]
        shocks = {0: 10.0, 2: -5.0}  # Positive shock to IND1, negative to IND3

        result = shock.simulate_multi_sector_shock(
            L=synthetic_leontief_inverse_3x3,
            shocks=shocks,
            sector_codes=sector_codes,
        )

        assert isinstance(result, dict)
        assert "impact_vector" in result
        assert "ranked_impacts" in result
        assert "total_impact" in result

    def test_multi_sector_shock_superposition(self, synthetic_leontief_inverse_3x3):
        """Multi-sector shock should be linear superposition of individual shocks."""
        sector_codes = ["IND1", "IND2", "IND3"]

        # Individual shocks
        result1 = shock.simulate_shock(
            L=synthetic_leontief_inverse_3x3,
            shock_industry_idx=0,
            shock_magnitude=10.0,
            sector_codes=sector_codes,
        )
        result2 = shock.simulate_shock(
            L=synthetic_leontief_inverse_3x3,
            shock_industry_idx=1,
            shock_magnitude=5.0,
            sector_codes=sector_codes,
        )

        # Combined shock
        combined = shock.simulate_multi_sector_shock(
            L=synthetic_leontief_inverse_3x3,
            shocks={0: 10.0, 1: 5.0},
            sector_codes=sector_codes,
        )

        # Superposition: combined impact should equal sum of individual impacts
        expected_impact = np.array(result1["impact_vector"]) + np.array(
            result2["impact_vector"]
        )
        actual_impact = np.array(combined["impact_vector"])

        assert np.allclose(actual_impact, expected_impact)


class TestFindCriticalSectors:
    """Tests for find_critical_sectors function."""

    def test_find_critical_sectors_returns_list(self, synthetic_leontief_inverse_3x3):
        """find_critical_sectors should return a list of dicts."""
        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.find_critical_sectors(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
            threshold=0.1,
        )

        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)
            assert "code" in result[0]
            assert "multiplier" in result[0]
            assert "critical" in result[0]

    def test_find_critical_sectors_threshold(self, synthetic_leontief_inverse_3x3):
        """Higher threshold should result in fewer critical sectors."""
        sector_codes = ["IND1", "IND2", "IND3"]

        low_threshold = shock.find_critical_sectors(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
            threshold=0.01,
        )
        high_threshold = shock.find_critical_sectors(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
            threshold=0.5,
        )

        critical_low = sum(1 for s in low_threshold if s["critical"])
        critical_high = sum(1 for s in high_threshold if s["critical"])

        assert critical_low >= critical_high


class TestComputeBackwardLinkages:
    """Tests for compute_backward_linkages function."""

    def test_backward_linkages_returns_series(self, synthetic_leontief_inverse_3x3):
        """compute_backward_linkages should return a pd.Series."""
        import pandas as pd

        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.compute_backward_linkages(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_backward_linkages_column_sums(self, synthetic_leontief_inverse_3x3):
        """Backward linkages should equal column sums of Leontief inverse."""
        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.compute_backward_linkages(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
        )

        expected = synthetic_leontief_inverse_3x3.sum(axis=0)
        assert np.allclose(result.values, expected)


class TestComputeForwardLinkages:
    """Tests for compute_forward_linkages function."""

    def test_forward_linkages_returns_series(self, synthetic_leontief_inverse_3x3):
        """compute_forward_linkages should return a pd.Series."""
        import pandas as pd

        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.compute_forward_linkages(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
        )

        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_forward_linkages_row_sums(self, synthetic_leontief_inverse_3x3):
        """Forward linkages should equal row sums of Leontief inverse."""
        sector_codes = ["IND1", "IND2", "IND3"]
        result = shock.compute_forward_linkages(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
        )

        expected = synthetic_leontief_inverse_3x3.sum(axis=1)
        assert np.allclose(result.values, expected)


class TestFindWeakestLink:
    """Tests for find_weakest_link function."""

    def test_find_weakest_link_returns_dict(self, synthetic_leontief_inverse_3x3):
        """find_weakest_link should return a dict with explanation."""
        sector_codes = ["IND1", "IND2", "IND3"]
        sector_names = ["Industry 1", "Industry 2", "Industry 3"]

        result = shock.find_weakest_link(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
            sector_names=sector_names,
        )

        assert isinstance(result, dict)
        assert "weakest_sector" in result
        assert "weakest_index" in result
        assert "multiplier" in result
        assert "explanation" in result
        assert "vulnerability_ranking" in result

    def test_find_weakest_link_highest_multiplier(self, synthetic_leontief_inverse_3x3):
        """Weakest link should be sector with highest output multiplier."""
        sector_codes = ["IND1", "IND2", "IND3"]
        sector_names = ["Industry 1", "Industry 2", "Industry 3"]

        result = shock.find_weakest_link(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
            sector_names=sector_names,
        )

        # Calculate multipliers manually
        multipliers = synthetic_leontief_inverse_3x3.sum(axis=0)
        max_idx = np.argmax(multipliers)

        assert result["weakest_index"] == max_idx
        assert np.isclose(result["multiplier"], multipliers[max_idx])

    def test_find_weakest_link_explanation_complete(
        self, synthetic_leontief_inverse_3x3
    ):
        """Explanation dict should contain all required fields."""
        sector_codes = ["IND1", "IND2", "IND3"]
        sector_names = ["Industry 1", "Industry 2", "Industry 3"]

        result = shock.find_weakest_link(
            L=synthetic_leontief_inverse_3x3,
            sector_codes=sector_codes,
            sector_names=sector_names,
        )

        explanation = result["explanation"]
        assert "output_multiplier" in explanation
        assert "backward_linkage" in explanation
        assert "forward_linkage" in explanation
        assert "dependency_count" in explanation
