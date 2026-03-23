"""Tests for FRED API client -- DATA-01, DATA-08.

Covers authentication, data retrieval, retry/backoff, and rate limiting.
All API calls are mocked to avoid hitting the real FRED API.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Import guard -- skip collection cleanly if production module missing
FredClient = pytest.importorskip(
    "ecpm.clients.fred", reason="ecpm.clients.fred not yet implemented"
).FredClient


class TestFredClientInit:
    """FredClient accepts api_key parameter."""

    def test_fred_client_init(self) -> None:
        client = FredClient(api_key="test-api-key-12345")
        assert client.api_key == "test-api-key-12345"

    def test_fred_client_requires_api_key(self) -> None:
        with pytest.raises((TypeError, ValueError)):
            FredClient()  # type: ignore[call-arg]


class TestFetchSeries:
    """fetch_series returns (DataFrame, dict) tuple."""

    def test_fetch_series_returns_data(self) -> None:
        client = FredClient(api_key="test-key")

        # Mock the underlying fredapi calls
        mock_data = pd.Series(
            [18_000.0, 18_200.0, 18_500.0],
            index=pd.to_datetime(["2023-01-01", "2023-04-01", "2023-07-01"]),
            name="GDPC1",
        )
        mock_info = pd.Series({
            "id": "GDPC1",
            "title": "Real Gross Domestic Product",
            "units": "Billions of Chained 2017 Dollars",
            "frequency": "Quarterly",
            "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
            "last_updated": "2024-01-26",
        })

        with patch.object(client.fred, "get_series", return_value=mock_data), \
             patch.object(client.fred, "get_series_info", return_value=mock_info):
            result = client.fetch_series("GDPC1")

        # Should return a tuple of (data, info_dict)
        assert isinstance(result, tuple)
        assert len(result) == 2

        data, info = result
        # data should be a pandas object (Series or DataFrame)
        assert hasattr(data, "index"), "Data should have an index (pandas-like)"
        # info should be a dict with metadata
        assert isinstance(info, dict)
        assert "id" in info or "series_id" in info


class TestRetryBackoff:
    """Mock fredapi to raise ConnectionError, verify tenacity retries."""

    def test_retry_backoff(self) -> None:
        client = FredClient(api_key="test-key")

        # Track calls to the underlying fredapi
        call_count = 0

        def failing_get_series(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection refused")
            # Third call succeeds
            return pd.Series(
                [18_000.0],
                index=pd.to_datetime(["2023-01-01"]),
                name="GDPC1",
            )

        mock_info = pd.Series({"id": "GDPC1", "title": "Real GDP"})

        with patch.object(client.fred, "get_series", side_effect=failing_get_series), \
             patch.object(client.fred, "get_series_info", return_value=mock_info):
            result = client.fetch_series("GDPC1")

        # Verify retry was attempted (at least 2 calls before success on 3rd)
        assert call_count >= 3, (
            f"Expected at least 3 attempts (2 retries + success), got {call_count}"
        )
        # Should have eventually succeeded
        assert isinstance(result, tuple)


class TestRateLimitDelay:
    """Verify rate limiting exists between consecutive API calls."""

    def test_rate_limit_delay(self) -> None:
        client = FredClient(api_key="test-key")

        # Check that the client has a rate limit configuration
        # FRED allows 120 req/min => ~0.5s between calls; we use 0.6s
        assert hasattr(client, "rate_limit_delay") or hasattr(
            client, "_rate_limiter"
        ), "Client should have rate limiting mechanism"

        # If rate_limit_delay attribute exists, verify it is >= 0.5s
        if hasattr(client, "rate_limit_delay"):
            assert client.rate_limit_delay >= 0.5, (
                f"Rate limit delay should be >= 0.5s, got {client.rate_limit_delay}"
            )
