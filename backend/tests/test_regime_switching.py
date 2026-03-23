"""Test scaffolds for regime-switching model -- MODL-06.

Tests Markov-switching regime detection, probability normalization,
transition matrix properties, and fallback behavior. All tests are
skip-marked until ecpm.modeling.regime_switching is implemented.
"""

from __future__ import annotations

import pytest

regime_switching = pytest.importorskip(
    "ecpm.modeling.regime_switching",
    reason="ecpm.modeling.regime_switching not yet implemented",
)


class TestRegimeDetection:
    """Verify regime identification on synthetic data."""

    def test_regime_detection(self, synthetic_regime_series):
        """Model should identify multiple regimes in synthetic series."""
        result = regime_switching.fit_regime_model(synthetic_regime_series)

        assert result["n_regimes"] >= 2, (
            f"Expected at least 2 regimes, got {result['n_regimes']}"
        )
        assert "current_regime" in result
        assert "smoothed_probabilities" in result

    def test_regime_fallback_to_2_regimes(self, synthetic_regime_series):
        """If 3-regime model fails convergence, should fall back to 2 regimes."""
        import numpy as np

        # Use a shorter, noisier series that may cause 3-regime to fail
        rng = np.random.default_rng(123)
        import pandas as pd

        short_series = pd.Series(rng.normal(0, 1, 50))

        result = regime_switching.fit_regime_model(short_series, max_regimes=3)

        # Should still produce a result (possibly with 2 regimes as fallback)
        assert result["n_regimes"] >= 2


class TestRegimeProbabilities:
    """Verify probability properties of regime model output."""

    def test_regime_probabilities_sum_to_one(self, synthetic_regime_series):
        """Smoothed probabilities should sum to ~1.0 at each time point."""
        import numpy as np

        result = regime_switching.fit_regime_model(synthetic_regime_series)
        smoothed = result["smoothed_probabilities"]

        # Each row of smoothed probabilities should sum to ~1.0
        for i, row in enumerate(smoothed):
            prob_values = [v for k, v in row.items() if k != "date"]
            total = sum(prob_values)
            assert abs(total - 1.0) < 0.01, (
                f"Smoothed probabilities at index {i} sum to {total}, expected ~1.0"
            )

    def test_transition_matrix_rows_sum_to_one(self, synthetic_regime_series):
        """Each row of the transition matrix should sum to ~1.0."""
        import numpy as np

        result = regime_switching.fit_regime_model(synthetic_regime_series)
        trans_matrix = result["transition_matrix"]

        for i, row in enumerate(trans_matrix):
            row_sum = sum(row)
            assert abs(row_sum - 1.0) < 0.01, (
                f"Transition matrix row {i} sums to {row_sum}, expected ~1.0"
            )
