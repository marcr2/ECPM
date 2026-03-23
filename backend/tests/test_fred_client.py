"""Tests for FRED API client -- DATA-01, DATA-08.

Covers authentication, data retrieval, retry/backoff, and rate limiting.
Tests are written in RED state: they will fail until production code is
implemented in Plan 01-03.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

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

        # Patch the underlying HTTP call to raise ConnectionError
        call_count = 0

        def failing_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection refused")
            # Third call succeeds
            return MagicMock()

        with patch.object(client, "_raw_fetch", side_effect=failing_call):
            try:
                client.fetch_series("GDPC1")
            except ConnectionError:
                pass  # May exhaust retries depending on config

        # Verify retry was attempted (at least 2 calls)
        assert call_count >= 2, (
            f"Expected at least 2 attempts (retry), got {call_count}"
        )


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
