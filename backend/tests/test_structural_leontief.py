"""Tests for Leontief matrix computation functions.

Tests technical coefficient computation, Leontief inverse with stability checks,
and output multiplier extraction. Uses synthetic I-O fixtures with known solutions.
"""

from __future__ import annotations

import numpy as np
import pytest

# Skip if structural module not implemented yet
leontief = pytest.importorskip("ecpm.structural.leontief")


class TestComputeTechnicalCoefficients:
    """Tests for compute_technical_coefficients function."""

    def test_build_coefficients_shape(
        self, synthetic_use_matrix_3x3, synthetic_total_output_3x3
    ):
        """Technical coefficient matrix A should have same shape as Use matrix."""
        A = leontief.compute_technical_coefficients(
            synthetic_use_matrix_3x3, synthetic_total_output_3x3
        )
        assert A.shape == synthetic_use_matrix_3x3.shape

    def test_build_coefficients_values(
        self, synthetic_use_matrix_3x3, synthetic_total_output_3x3
    ):
        """A[i,j] = Z[i,j] / X[j] should hold for each element."""
        A = leontief.compute_technical_coefficients(
            synthetic_use_matrix_3x3, synthetic_total_output_3x3
        )
        # Manual check: first column, first row
        expected_a00 = (
            synthetic_use_matrix_3x3[0, 0] / synthetic_total_output_3x3[0]
        )
        assert np.isclose(A[0, 0], expected_a00)

    def test_build_coefficients_zero_output_handled(self):
        """Division by zero output should be handled (set to 0)."""
        use_matrix = np.array([[10.0, 5.0], [3.0, 8.0]])
        total_output = np.array([100.0, 0.0])  # Zero output in second sector
        A = leontief.compute_technical_coefficients(use_matrix, total_output)
        # Column with zero output should have coefficient 0 or handled gracefully
        assert not np.any(np.isnan(A))
        assert not np.any(np.isinf(A))


class TestComputeLeontiefInverse:
    """Tests for compute_leontief_inverse function."""

    def test_leontief_inverse_stable(
        self, synthetic_use_matrix_3x3, synthetic_total_output_3x3
    ):
        """Stable A matrix should produce valid Leontief inverse."""
        A = leontief.compute_technical_coefficients(
            synthetic_use_matrix_3x3, synthetic_total_output_3x3
        )
        L, diagnostics = leontief.compute_leontief_inverse(A)

        assert L is not None
        assert diagnostics["success"] is True
        assert diagnostics["convergent"] is True
        assert L.shape == A.shape

    def test_leontief_inverse_matches_expected(
        self,
        synthetic_use_matrix_3x3,
        synthetic_total_output_3x3,
        synthetic_leontief_inverse_3x3,
    ):
        """Computed Leontief inverse should match pre-computed analytical solution."""
        A = leontief.compute_technical_coefficients(
            synthetic_use_matrix_3x3, synthetic_total_output_3x3
        )
        L, _ = leontief.compute_leontief_inverse(A)

        # Compare with expected solution (tolerance for floating point)
        assert np.allclose(L, synthetic_leontief_inverse_3x3, rtol=1e-5)

    def test_leontief_inverse_singular_returns_none(self):
        """Singular matrix should return None with diagnostics."""
        # Singular matrix: rows are linearly dependent
        A = np.array([[0.5, 0.5], [0.5, 0.5]])
        L, diagnostics = leontief.compute_leontief_inverse(A)

        # Either L is None or diagnostics indicate failure
        # Implementation may handle singular matrix by returning None
        if L is None:
            assert diagnostics.get("success") is False or not diagnostics.get(
                "well_conditioned", True
            )
        else:
            # If it returns a matrix, condition number should be very high
            assert diagnostics["condition_number"] > 1e10

    def test_leontief_inverse_hawkins_simon_failure(self):
        """Matrix violating Hawkins-Simon should be flagged in diagnostics."""
        # Construct a matrix where (I-A) has a negative leading minor
        # This is when some diagonal of (I-A) is negative
        A = np.array([[1.5, 0.1], [0.1, 0.2]])  # A[0,0] > 1 violates HS
        _, diagnostics = leontief.compute_leontief_inverse(A)

        assert diagnostics["hawkins_simon"] is False
        assert diagnostics["hawkins_simon_failure_at"] == 1


class TestCheckStability:
    """Tests for check_stability function."""

    def test_stability_stable_matrix(
        self, synthetic_use_matrix_3x3, synthetic_total_output_3x3
    ):
        """Stable matrix should report is_stable=True."""
        A = leontief.compute_technical_coefficients(
            synthetic_use_matrix_3x3, synthetic_total_output_3x3
        )
        stability = leontief.check_stability(A)

        assert stability["is_stable"] is True
        assert stability["max_eigenvalue"] < 1.0
        assert stability["hawkins_simon"] is True

    def test_stability_unstable_matrix(self):
        """Unstable matrix (spectral radius >= 1) should report is_stable=False."""
        # Spectral radius > 1 when eigenvalue > 1
        A = np.array([[0.9, 0.5], [0.5, 0.9]])  # Eigenvalue > 1
        stability = leontief.check_stability(A)

        assert stability["is_stable"] is False
        assert stability["max_eigenvalue"] >= 1.0


class TestGetMultipliers:
    """Tests for get_multipliers function."""

    def test_get_multipliers_length(self, synthetic_leontief_inverse_3x3):
        """Output multipliers should have length equal to number of sectors."""
        multipliers = leontief.get_multipliers(synthetic_leontief_inverse_3x3)
        assert len(multipliers) == synthetic_leontief_inverse_3x3.shape[0]

    def test_get_multipliers_positive(self, synthetic_leontief_inverse_3x3):
        """Output multipliers should be positive for valid Leontief inverse."""
        multipliers = leontief.get_multipliers(synthetic_leontief_inverse_3x3)
        assert np.all(multipliers > 0)

    def test_get_multipliers_minimum_one(self, synthetic_leontief_inverse_3x3):
        """Output multipliers should be >= 1 (direct effect)."""
        multipliers = leontief.get_multipliers(synthetic_leontief_inverse_3x3)
        assert np.all(multipliers >= 1.0)


class TestGetOutputMultipliers:
    """Tests for get_output_multipliers function (with sector codes)."""

    def test_get_output_multipliers_indexed(self, synthetic_leontief_inverse_3x3):
        """Output multipliers should be a Series indexed by sector code."""
        import pandas as pd

        sector_codes = ["IND1", "IND2", "IND3"]
        multipliers = leontief.get_output_multipliers(
            synthetic_leontief_inverse_3x3, sector_codes
        )

        assert isinstance(multipliers, pd.Series)
        assert list(multipliers.index) == sector_codes or set(
            multipliers.index
        ) == set(sector_codes)

    def test_get_output_multipliers_sorted_descending(
        self, synthetic_leontief_inverse_3x3
    ):
        """Output multipliers Series should be sorted by value descending."""
        sector_codes = ["IND1", "IND2", "IND3"]
        multipliers = leontief.get_output_multipliers(
            synthetic_leontief_inverse_3x3, sector_codes
        )

        values = multipliers.values
        assert np.all(values[:-1] >= values[1:])
