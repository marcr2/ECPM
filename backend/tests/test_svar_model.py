"""Test scaffolds for SVAR model module -- MODL-03.

Tests structural VAR A-matrix construction (Marxist causal ordering)
and SVAR identification. All tests are skip-marked until
ecpm.modeling.svar_model is implemented.
"""

from __future__ import annotations

import pytest

svar_model = pytest.importorskip(
    "ecpm.modeling.svar_model",
    reason="ecpm.modeling.svar_model not yet implemented",
)


class TestSVARMatrixConstruction:
    """Verify A-matrix for Marxist causal ordering."""

    def test_svar_a_matrix_shape(self):
        """A matrix should be (8, 8) for 8 indicators."""
        import numpy as np

        a_matrix = svar_model.build_a_matrix(n_vars=8)

        assert a_matrix.shape == (8, 8), (
            f"Expected (8, 8), got {a_matrix.shape}"
        )
        # Diagonal should be 1s (normalization)
        np.testing.assert_array_equal(
            np.diag(a_matrix),
            np.ones(8),
            err_msg="Diagonal of A matrix should be all 1s",
        )

    def test_svar_a_matrix_lower_triangular(self):
        """Upper triangle (above diagonal) should be all zeros; lower has 'E' markers."""
        import numpy as np

        a_matrix = svar_model.build_a_matrix(n_vars=8)

        # Upper triangle (excluding diagonal) should be zero
        upper = np.triu(a_matrix, k=1)
        assert np.all(upper == 0), (
            "Upper triangle of A matrix should be all zeros"
        )

        # Lower triangle should have non-zero entries (free parameters)
        lower = np.tril(a_matrix, k=-1)
        assert np.any(lower != 0), (
            "Lower triangle should have non-zero free parameters"
        )


class TestSVARIdentification:
    """Verify SVAR identification on synthetic data."""

    def test_svar_identification(self, synthetic_indicators):
        """SVAR should fit without error on synthetic indicator data."""
        result = svar_model.fit_svar(synthetic_indicators)

        assert result is not None
        assert "irf" in result or "a_matrix_estimated" in result, (
            "SVAR result should contain impulse response functions or estimated A matrix"
        )
