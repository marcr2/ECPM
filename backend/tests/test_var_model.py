"""Test scaffolds for VAR model module -- MODL-01, MODL-04.

Tests VAR lag selection, forecast shape, confidence intervals, and
indicator coverage. All tests are skip-marked until ecpm.modeling.var_model
is implemented.
"""

from __future__ import annotations

import pytest

var_model = pytest.importorskip(
    "ecpm.modeling.var_model",
    reason="ecpm.modeling.var_model not yet implemented",
)


class TestVARLagSelection:
    """Verify automatic lag order selection."""

    def test_var_lag_selection(self, synthetic_indicators):
        """Selected lag order should be reasonable (1-12) for quarterly data."""
        result = var_model.fit_var(synthetic_indicators)

        assert "lag_order" in result
        assert 1 <= result["lag_order"] <= 12, (
            f"Lag order {result['lag_order']} outside reasonable range 1-12"
        )


class TestVARForecast:
    """Verify forecast output structure and properties."""

    def test_var_forecast_shape(self, synthetic_indicators):
        """Forecast output should have shape (steps, n_variables)."""
        n_steps = 8  # 8-quarter forecast horizon
        result = var_model.fit_var(synthetic_indicators)
        forecasts = var_model.forecast(result, steps=n_steps)

        assert forecasts["point_forecasts"].shape == (
            n_steps,
            len(synthetic_indicators.columns),
        ), (
            f"Expected ({n_steps}, {len(synthetic_indicators.columns)}), "
            f"got {forecasts['point_forecasts'].shape}"
        )

    def test_forecast_confidence_intervals(self, synthetic_indicators):
        """68% CI should be narrower than 95% CI for all variables and horizons."""
        n_steps = 8
        result = var_model.fit_var(synthetic_indicators)
        forecasts = var_model.forecast(result, steps=n_steps)

        ci_68_width = forecasts["upper_68"] - forecasts["lower_68"]
        ci_95_width = forecasts["upper_95"] - forecasts["lower_95"]

        # 68% interval must be strictly narrower than 95% interval everywhere
        import numpy as np

        assert np.all(ci_68_width < ci_95_width), (
            "68% confidence interval should be narrower than 95% CI at all points"
        )

    def test_forecast_includes_all_indicators(self, synthetic_indicators):
        """Forecast dict should have entries for all 8 indicators."""
        result = var_model.fit_var(synthetic_indicators)
        indicator_forecasts = var_model.get_indicator_forecasts(result, steps=8)

        expected_indicators = set(synthetic_indicators.columns)
        actual_indicators = set(indicator_forecasts.keys())

        assert actual_indicators == expected_indicators, (
            f"Missing indicators: {expected_indicators - actual_indicators}"
        )
