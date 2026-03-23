"""Tests for BEA API client -- DATA-03.

Covers initialization, NIPA table retrieval, Fixed Assets retrieval,
and retry configuration. All API calls are mocked.
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
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

        mock_df = pd.DataFrame({
            "LineNumber": [1, 2, 3],
            "DataValue": [25000.0, 12000.0, 13000.0],
            "TimePeriod": ["2023Q1", "2023Q1", "2023Q1"],
            "LineDescription": [
                "National income",
                "Compensation of employees",
                "Proprietors' income",
            ],
        })

        with patch.object(client, "_api_request", return_value=mock_df):
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

        mock_df = pd.DataFrame({
            "LineNumber": [1],
            "DataValue": [25000.0],
            "TimePeriod": ["2023Q1"],
            "LineDescription": ["National income"],
        })

        with patch.object(client, "_api_request", return_value=mock_df):
            result = client.fetch_nipa_table("T11200")
        assert len(result) > 0, "NIPA table should return at least one row"


class TestFetchFixedAssets:
    """Calls with datasetname='FixedAssets' (not NIPA)."""

    def test_fetch_fixed_assets(self) -> None:
        client = BEAClient(api_key="test-key")

        # Patch _api_request to capture the dataset parameter
        with patch.object(client, "_api_request") as mock_request:
            mock_request.return_value = pd.DataFrame(
                columns=["LineNumber", "DataValue", "TimePeriod"]
            )
            client.fetch_fixed_assets("FAAt101")

            # Verify the request was made with FixedAssets dataset
            assert mock_request.called, "_api_request should have been called"
            call_args = mock_request.call_args
            # The first positional arg or 'dataset_name' kwarg should be 'FixedAssets'
            args_str = str(call_args)
            assert "FixedAssets" in args_str, (
                "Fixed assets fetch should use 'FixedAssets' dataset"
            )


class TestRetryOnError:
    """Verify tenacity retry decorator is configured."""

    def test_retry_on_error(self) -> None:
        client = BEAClient(api_key="test-key")

        # Check that at least one fetch method has tenacity retry wrapper
        has_retry = False
        for method_name in ("fetch_nipa_table", "fetch_fixed_assets", "_api_request"):
            method = getattr(client, method_name, None)
            if method is not None and hasattr(method, "retry"):
                has_retry = True
                break

        assert has_retry, (
            "At least one BEA client method should have tenacity retry decorator"
        )
