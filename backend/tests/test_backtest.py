"""Test scaffolds for historical backtesting module -- MODL-05.

Tests backtest execution for the GFC episode, result structure validation,
and crisis index series coverage. All tests are skip-marked until
ecpm.modeling.backtest is implemented.
"""

from __future__ import annotations

import pytest

backtest = pytest.importorskip(
    "ecpm.modeling.backtest",
    reason="ecpm.modeling.backtest not yet implemented",
)


class TestGFCBacktest:
    """Verify backtesting against the 2007-2009 Great Financial Crisis."""

    def test_gfc_backtest(self, synthetic_indicators):
        """GFC backtest should produce a result with all required fields."""
        result = backtest.run_episode(
            synthetic_indicators,
            episode_name="GFC",
            start_date="2006-01-01",
            end_date="2009-12-31",
        )

        assert result["episode_name"] == "GFC"
        assert "start_date" in result
        assert "end_date" in result
        assert "crisis_index_series" in result
        assert "warning_12m" in result
        assert "warning_24m" in result
        assert "peak_value" in result
        assert "peak_date" in result


class TestBacktestResultStructure:
    """Verify BacktestResult Pydantic schema validation."""

    def test_backtest_result_structure(self, synthetic_indicators):
        """Backtest output should validate against BacktestResult schema."""
        from ecpm.modeling.schemas import BacktestResult

        result = backtest.run_episode(
            synthetic_indicators,
            episode_name="GFC",
            start_date="2006-01-01",
            end_date="2009-12-31",
        )

        # Should not raise ValidationError
        validated = BacktestResult.model_validate(result)
        assert validated.episode_name == "GFC"
        assert isinstance(validated.warning_12m, bool)
        assert isinstance(validated.warning_24m, bool)
        assert isinstance(validated.peak_value, float)


class TestBacktestCrisisIndexSeries:
    """Verify crisis index time series within backtest results."""

    def test_backtest_crisis_index_series(self, synthetic_indicators):
        """Crisis index series should cover the episode time range."""
        result = backtest.run_episode(
            synthetic_indicators,
            episode_name="GFC",
            start_date="2006-01-01",
            end_date="2009-12-31",
        )

        series = result["crisis_index_series"]
        assert len(series) > 0, "Crisis index series should not be empty"

        # Each entry should have date and value
        for entry in series:
            assert "date" in entry, "Each entry should have a 'date' field"
            assert "value" in entry, "Each entry should have a 'value' field"
