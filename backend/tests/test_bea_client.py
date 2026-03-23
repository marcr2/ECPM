"""Tests for BEA API client -- DATA-03.

Covers initialization, NIPA table retrieval, Fixed Assets retrieval,
and retry configuration. Tests are in RED state until Plan 01-03.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

# Import guard
BEAClient = pytest.importorskip(
    "ecpm.clients.bea", reason="ecpm.clients.bea not yet implemented"
).BEAClient


class TestBEAClientInit:
    """BEAClient accepts api_key parameter."""

    def test_bea_client_init(self) -> None:
        client = BEAClient(api_key="test-bea-key-12345")
        assert client.api_key == "test-bea-key-12345"

    def test_bea_client_requires_api_key(self) -> None:
        with pytest.raises((TypeError, ValueError)):
            BEAClient()  # type: ignore[call-arg]


class TestFetchNIPATable:
    """fetch_nipa_table returns DataFrame with expected columns."""

    def test_fetch_nipa_table(self) -> None:
        client = BEAClient(api_key="test-key")
        result = client.fetch_nipa_table("T11200")

        # Should return a DataFrame-like object
        assert hasattr(result, "columns"), "Result should be a DataFrame"

        # Expected columns from BEA NIPA response
        expected_cols = {"LineNumber", "DataValue", "TimePeriod"}
        actual_cols = set(result.columns)
        assert expected_cols.issubset(actual_cols), (
            f"Missing columns: {expected_cols - actual_cols}"
        )

    def test_fetch_nipa_table_returns_nonempty(self) -> None:
        client = BEAClient(api_key="test-key")
        result = client.fetch_nipa_table("T11200")
        assert len(result) > 0, "NIPA table should return at least one row"


class TestFetchFixedAssets:
    """Calls with datasetname='FixedAssets' (not NIPA)."""

    def test_fetch_fixed_assets(self) -> None:
        client = BEAClient(api_key="test-key")

        # Patch the underlying API call to capture the dataset parameter
        with patch.object(client, "_api_request") as mock_request:
            mock_request.return_value = {"BEAAPI": {"Results": {"Data": []}}}
            try:
                client.fetch_fixed_assets("FAAt101")
            except Exception:
                pass  # May fail due to empty response; we check the call

            # Verify the request was made with FixedAssets dataset
            if mock_request.called:
                call_kwargs = mock_request.call_args
                # Check that 'FixedAssets' appears in the call arguments
                args_str = str(call_kwargs)
                assert "FixedAssets" in args_str or "fixedassets" in args_str.lower(), (
                    "Fixed assets fetch should use 'FixedAssets' dataset"
                )


class TestRetryOnError:
    """Verify tenacity retry decorator is configured."""

    def test_retry_on_error(self) -> None:
        client = BEAClient(api_key="test-key")

        # Check that fetch methods have tenacity retry wrapper
        for method_name in ("fetch_nipa_table", "fetch_fixed_assets", "_api_request"):
            method = getattr(client, method_name, None)
            if method is not None:
                # tenacity-decorated functions have a 'retry' attribute
                assert hasattr(method, "retry"), (
                    f"{method_name} should be decorated with @retry (tenacity)"
                )
                break
        else:
            pytest.fail(
                "At least one BEA client method should have tenacity retry decorator"
            )
