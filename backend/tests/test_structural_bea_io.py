"""Tests for BEA InputOutput API client.

Tests fetch_use_table, fetch_make_table, and discover_table_id methods.
Uses pytest.importorskip for graceful skip-marking of unimplemented modules.
"""

from __future__ import annotations

import pytest

# Skip if structural module not implemented yet
bea_io_client = pytest.importorskip("ecpm.structural.bea_io_client")


class TestDiscoverTableId:
    """Tests for BEAIOClient.discover_table_id method."""

    def test_discover_table_id_use_returns_int(self, mock_bea_io_client):
        """discover_table_id('use') should return an integer TableID."""
        table_id = mock_bea_io_client.discover_table_id("use")
        assert isinstance(table_id, int)
        assert table_id > 0

    def test_discover_table_id_make_returns_int(self, mock_bea_io_client):
        """discover_table_id('make') should return an integer TableID."""
        table_id = mock_bea_io_client.discover_table_id("make")
        assert isinstance(table_id, int)
        assert table_id > 0

    def test_discover_table_id_caches_result(self, mock_bea_io_client):
        """TableID discovery should cache results to avoid repeated API calls."""
        # First call
        table_id_1 = mock_bea_io_client.discover_table_id("use")
        # Second call should use cached value
        table_id_2 = mock_bea_io_client.discover_table_id("use")
        assert table_id_1 == table_id_2

    def test_discover_table_id_invalid_type_raises(self, mock_bea_io_client):
        """discover_table_id with unknown table type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown table type"):
            mock_bea_io_client.discover_table_id("invalid")


class TestFetchUseTable:
    """Tests for BEAIOClient.fetch_use_table method."""

    def test_fetch_use_table_returns_dataframe(
        self, mock_bea_io_client, synthetic_use_matrix_3x3
    ):
        """fetch_use_table should return a pivoted DataFrame."""
        import pandas as pd

        df = mock_bea_io_client.fetch_use_table(2022)
        assert isinstance(df, pd.DataFrame)
        # Matrix should be square for Use table
        assert df.shape[0] == df.shape[1]

    def test_fetch_use_table_values_numeric(
        self, mock_bea_io_client, synthetic_use_matrix_3x3
    ):
        """fetch_use_table values should be float, not strings."""
        df = mock_bea_io_client.fetch_use_table(2022)
        assert df.dtypes.apply(lambda x: x == float or x == "float64").all()


class TestFetchMakeTable:
    """Tests for BEAIOClient.fetch_make_table method."""

    def test_fetch_make_table_returns_dataframe(self, mock_bea_io_client):
        """fetch_make_table should return a pivoted DataFrame."""
        import pandas as pd

        df = mock_bea_io_client.fetch_make_table(2022)
        assert isinstance(df, pd.DataFrame)


class TestFetchIOTable:
    """Tests for BEAIOClient.fetch_io_table raw data method."""

    def test_fetch_io_table_has_required_columns(self, mock_bea_io_client):
        """fetch_io_table raw response should have RowCode, ColCode, DataValue."""
        df = mock_bea_io_client.fetch_io_table(table_id=259, year="2022")
        required_cols = {"RowCode", "ColCode", "DataValue"}
        assert required_cols.issubset(set(df.columns))


class TestPivotIOData:
    """Tests for BEAIOClient.pivot_io_data helper."""

    def test_pivot_io_data_creates_matrix(self, mock_bea_io_client):
        """pivot_io_data should convert flat data to matrix format."""
        import pandas as pd

        flat_df = pd.DataFrame(
            {
                "RowCode": ["A", "A", "B", "B"],
                "ColCode": ["X", "Y", "X", "Y"],
                "DataValue": [1.0, 2.0, 3.0, 4.0],
            }
        )
        matrix = mock_bea_io_client.pivot_io_data(flat_df)
        assert matrix.shape == (2, 2)
        assert matrix.loc["A", "X"] == 1.0
        assert matrix.loc["B", "Y"] == 4.0
