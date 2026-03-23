"""Test scaffolds for crisis index computation -- MODL-07, MODL-08.

Tests composite index range, mechanism decomposition, default and custom
weights, and the profit-rate inversion relationship. All tests are
skip-marked until ecpm.modeling.crisis_index is implemented.
"""

from __future__ import annotations

import pytest

crisis_index = pytest.importorskip(
    "ecpm.modeling.crisis_index",
    reason="ecpm.modeling.crisis_index not yet implemented",
)


class TestCompositeIndex:
    """Verify composite crisis index calculation."""

    def test_composite_index(self, synthetic_indicators):
        """Composite index should be bounded in [0, 100]."""
        result = crisis_index.compute(synthetic_indicators)

        assert 0 <= result["current_value"] <= 100, (
            f"Crisis index {result['current_value']} outside [0, 100] range"
        )

    def test_mechanism_decomposition(self, synthetic_indicators):
        """All three mechanism components should be present and separate."""
        result = crisis_index.compute(synthetic_indicators)

        assert "trpf_component" in result
        assert "realization_component" in result
        assert "financial_component" in result

        # Components should be numeric
        assert isinstance(result["trpf_component"], (int, float))
        assert isinstance(result["realization_component"], (int, float))
        assert isinstance(result["financial_component"], (int, float))


class TestCrisisWeights:
    """Verify weighting behavior of crisis index components."""

    def test_equal_weights_default(self, synthetic_indicators):
        """Default weights should be 1/3 each."""
        result = crisis_index.compute(synthetic_indicators)

        # With equal weights, composite should be close to mean of components
        expected = (
            result["trpf_component"]
            + result["realization_component"]
            + result["financial_component"]
        ) / 3.0

        assert abs(result["current_value"] - expected) < 0.01, (
            f"Default (equal) weights: composite {result['current_value']} "
            f"should be ~{expected}"
        )

    def test_custom_weights(self, synthetic_indicators):
        """Custom weights should change the composite index value."""
        result_default = crisis_index.compute(synthetic_indicators)
        result_custom = crisis_index.compute(
            synthetic_indicators,
            weights={"trpf": 0.7, "realization": 0.2, "financial": 0.1},
        )

        # With different weights, composite should differ (unless all components equal)
        # At minimum, verify both produce valid results
        assert 0 <= result_custom["current_value"] <= 100
        # If components differ, the weighted result should differ from equal-weight
        if not (
            abs(result_default["trpf_component"] - result_default["realization_component"]) < 0.01
            and abs(result_default["trpf_component"] - result_default["financial_component"]) < 0.01
        ):
            assert result_default["current_value"] != result_custom["current_value"], (
                "Custom weights should produce a different composite value"
            )


class TestProfitRateInversion:
    """Verify TRPF crisis signal relationship with profit rate."""

    def test_inverted_profit_rate(self, synthetic_indicators):
        """Lower profit rate should produce higher TRPF crisis signal."""
        import pandas as pd

        # Create two DataFrames with different profit rates
        low_profit = synthetic_indicators.copy()
        high_profit = synthetic_indicators.copy()

        low_profit["rate_of_profit"] = low_profit["rate_of_profit"] * 0.5
        high_profit["rate_of_profit"] = high_profit["rate_of_profit"] * 1.5

        result_low = crisis_index.compute(low_profit)
        result_high = crisis_index.compute(high_profit)

        assert result_low["trpf_component"] > result_high["trpf_component"], (
            "Lower profit rate should produce higher TRPF crisis signal: "
            f"low={result_low['trpf_component']}, high={result_high['trpf_component']}"
        )
