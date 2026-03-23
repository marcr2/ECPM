"""Test scaffolds for stationarity testing module -- MODL-02.

Tests the dual ADF/KPSS stationarity check and the ensure_stationarity
transformation that differences non-stationary series. All tests are
skip-marked until ecpm.modeling.stationarity is implemented.
"""

from __future__ import annotations

import pytest

stationarity = pytest.importorskip(
    "ecpm.modeling.stationarity",
    reason="ecpm.modeling.stationarity not yet implemented",
)


class TestDualStationarityCheck:
    """Verify dual ADF + KPSS stationarity assessment."""

    def test_dual_stationarity_stationary_series(self, synthetic_indicators):
        """A stationary series should be identified as stationary by both tests."""
        import numpy as np

        # First-differenced series should be stationary
        diff_series = synthetic_indicators["rate_of_profit"].diff().dropna()

        result = stationarity.check_stationarity(diff_series)

        assert result["is_stationary"] is True
        assert "adf_pvalue" in result
        assert "kpss_pvalue" in result
        assert result["adf_pvalue"] < 0.05  # ADF rejects unit root
        assert result["kpss_pvalue"] > 0.05  # KPSS fails to reject stationarity

    def test_dual_stationarity_nonstationary_series(self, synthetic_indicators):
        """A random walk should be detected as non-stationary."""
        import numpy as np

        rng = np.random.default_rng(99)
        random_walk = np.cumsum(rng.normal(0, 1, 200))
        import pandas as pd

        rw_series = pd.Series(random_walk)

        result = stationarity.check_stationarity(rw_series)

        assert result["is_stationary"] is False


class TestEnsureStationarity:
    """Verify automatic differencing to achieve stationarity."""

    def test_ensure_stationarity_differences_when_needed(self, synthetic_indicators):
        """Non-stationary columns should be differenced; diff_orders reported."""
        result_df, diff_orders = stationarity.ensure_stationarity(synthetic_indicators)

        # Result should have same columns
        assert list(result_df.columns) == list(synthetic_indicators.columns)
        # At least some series need differencing (trending series)
        assert any(d > 0 for d in diff_orders.values()), (
            "Expected at least one series to require differencing"
        )
        # diff_orders should have an entry for each column
        assert set(diff_orders.keys()) == set(synthetic_indicators.columns)

    def test_ensure_stationarity_preserves_stationary(self):
        """Already-stationary DataFrame should not be differenced."""
        import numpy as np
        import pandas as pd

        rng = np.random.default_rng(42)
        # White noise is stationary
        stationary_df = pd.DataFrame(
            {
                "a": rng.normal(0, 1, 200),
                "b": rng.normal(0, 1, 200),
            }
        )

        result_df, diff_orders = stationarity.ensure_stationarity(stationary_df)

        assert all(d == 0 for d in diff_orders.values()), (
            "Stationary series should not be differenced"
        )
        assert len(result_df) == len(stationary_df)
