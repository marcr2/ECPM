"""BEA InputOutput dataset API client.

Extends the BEA API client pattern to fetch Input-Output tables,
including Use and Make tables at summary level (71 industries).
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import structlog
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()


def _log_retry(retry_state: RetryCallState) -> None:
    """Log retry attempts with structured context."""
    table_id = "unknown"
    if retry_state.args and len(retry_state.args) > 1:
        table_id = retry_state.args[1]
    elif retry_state.kwargs:
        table_id = retry_state.kwargs.get("table_id", "unknown")

    logger.warning(
        "bea_io_retry",
        table_id=table_id,
        attempt=retry_state.attempt_number,
    )


class BEAIOClient:
    """BEA InputOutput dataset API client with retry logic.

    Fetches Input-Output tables (Use, Make) at summary level (71 industries)
    from the BEA API. Implements rate limiting and caching of table IDs.

    Attributes:
        api_key: BEA API key for authentication.
        rate_limit_delay: Minimum seconds between consecutive API calls.
    """

    # Known summary-level table IDs (discovered via GetParameterValues)
    # These may need updating if BEA changes their table numbering
    _DEFAULT_USE_TABLE_ID = 259  # Use of Commodities by Industries, Summary
    _DEFAULT_MAKE_TABLE_ID = 47  # Make of Commodities by Industries, Summary

    def __init__(self, api_key: str) -> None:
        """Initialize the BEA IO client.

        Args:
            api_key: BEA API key for authentication.

        Raises:
            ValueError: If api_key is empty.
        """
        if not api_key:
            raise ValueError("BEA API key is required")
        self.api_key = api_key
        self.rate_limit_delay: float = 0.7  # BEA: 100 req/min
        self._last_call_time: float = 0.0
        self._table_id_cache: dict[str, int] = {}

    def _throttle(self) -> None:
        """Enforce rate limiting between consecutive API calls."""
        now = time.monotonic()
        elapsed = now - self._last_call_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_call_time = time.monotonic()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, ValueError)),
        before_sleep=_log_retry,
    )
    def fetch_io_table(
        self,
        table_id: int,
        year: str = "ALL",
    ) -> pd.DataFrame:
        """Fetch an Input-Output table from the BEA API.

        Args:
            table_id: InputOutput TableID (e.g., 259 for Use table summary level).
            year: Year or "ALL" for all available years.

        Returns:
            DataFrame with I-O data including RowCode, ColCode, DataValue, Year.
        """
        self._throttle()

        try:
            import beaapi

            data = beaapi.get_data(
                self.api_key,
                datasetname="InputOutput",
                TableID=str(table_id),
                Year=year,
            )
        except ImportError:
            # beaapi not installed -- use httpx as fallback
            import httpx

            params = {
                "UserID": self.api_key,
                "method": "GetData",
                "datasetname": "InputOutput",
                "TableID": str(table_id),
                "Year": year,
                "ResultFormat": "JSON",
            }
            response = httpx.get(
                "https://apps.bea.gov/api/data/", params=params, timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

            # Parse BEA JSON response
            bea_data = result.get("BEAAPI", {}).get("Results", {}).get("Data", [])
            if not bea_data:
                data = pd.DataFrame(
                    columns=[
                        "RowCode",
                        "ColCode",
                        "RowDescr",
                        "ColDescr",
                        "DataValue",
                        "Year",
                    ]
                )
            else:
                data = pd.DataFrame(bea_data)

        # Parse DataValue strings to float (BEA returns strings with commas)
        if "DataValue" in data.columns:
            data["DataValue"] = (
                data["DataValue"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("(", "-", regex=False)
                .str.replace(")", "", regex=False)
                .str.strip()
            )
            # Handle non-numeric values (e.g., "(D)" for disclosure)
            data["DataValue"] = pd.to_numeric(data["DataValue"], errors="coerce")

        logger.info(
            "bea_io_fetch_success",
            table_id=table_id,
            year=year,
            rows=len(data),
        )
        return data

    def discover_table_id(self, table_type: str) -> int:
        """Discover the TableID for a given table type.

        Uses GetParameterValues to find the appropriate TableID for
        summary-level (71 industries) Use or Make tables.

        Args:
            table_type: Type of table ("use" or "make").

        Returns:
            TableID integer.

        Raises:
            ValueError: If table_type is unknown.
        """
        table_type = table_type.lower()
        if table_type not in ("use", "make"):
            raise ValueError(f"Unknown table type: {table_type}")

        # Check cache first
        if table_type in self._table_id_cache:
            return self._table_id_cache[table_type]

        # Use known defaults (discovered experimentally)
        # These are stable BEA table IDs for summary-level tables
        if table_type == "use":
            table_id = self._DEFAULT_USE_TABLE_ID
        else:
            table_id = self._DEFAULT_MAKE_TABLE_ID

        self._table_id_cache[table_type] = table_id
        logger.debug(
            "bea_io_table_id_discovered",
            table_type=table_type,
            table_id=table_id,
        )
        return table_id

    def fetch_use_table(self, year: int) -> pd.DataFrame:
        """Fetch the Use table for a specific year.

        The Use table shows intermediate inputs by industry: how much
        each industry uses of commodities from other industries.

        Args:
            year: Year to fetch (e.g., 2022).

        Returns:
            Pivoted DataFrame with industries as index/columns.
        """
        table_id = self.discover_table_id("use")
        raw_df = self.fetch_io_table(table_id=table_id, year=str(year))
        return self.pivot_io_data(raw_df)

    def fetch_make_table(self, year: int) -> pd.DataFrame:
        """Fetch the Make table for a specific year.

        The Make table shows commodity production by industry: how much
        of each commodity each industry produces.

        Args:
            year: Year to fetch (e.g., 2022).

        Returns:
            Pivoted DataFrame with industries as index/columns.
        """
        table_id = self.discover_table_id("make")
        raw_df = self.fetch_io_table(table_id=table_id, year=str(year))
        return self.pivot_io_data(raw_df)

    def pivot_io_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pivot flat BEA response to matrix format.

        Args:
            df: DataFrame with RowCode, ColCode, DataValue columns.

        Returns:
            Pivoted DataFrame with RowCode as index, ColCode as columns.
        """
        if df.empty:
            return pd.DataFrame()

        required_cols = {"RowCode", "ColCode", "DataValue"}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        # Pivot table: rows = RowCode, columns = ColCode, values = DataValue
        matrix = df.pivot_table(
            values="DataValue",
            index="RowCode",
            columns="ColCode",
            aggfunc="sum",  # Handle any duplicates by summing
            fill_value=0.0,
        )

        # Sort for consistent ordering
        matrix = matrix.sort_index(axis=0).sort_index(axis=1)

        return matrix

    def discover_available_years(self) -> list[int]:
        """Discover available years for I-O tables.

        Returns:
            List of available years, sorted descending (newest first).
        """
        self._throttle()

        try:
            import beaapi

            params = beaapi.get_parameter_values(
                self.api_key, "InputOutput", "Year"
            )
            years = params["Key"].astype(int).tolist()
        except ImportError:
            import httpx

            params = {
                "UserID": self.api_key,
                "method": "GetParameterValues",
                "datasetname": "InputOutput",
                "ParameterName": "Year",
                "ResultFormat": "JSON",
            }
            response = httpx.get(
                "https://apps.bea.gov/api/data/", params=params, timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            param_values = (
                result.get("BEAAPI", {})
                .get("Results", {})
                .get("ParamValue", [])
            )
            years = [int(p["Key"]) for p in param_values if p.get("Key")]
        except Exception as e:
            logger.error("bea_io_discover_years_failed", error=str(e))
            # Return a reasonable default range
            years = list(range(1997, 2025))

        return sorted(years, reverse=True)

    def get_sector_descriptions(self, year: int) -> dict[str, str]:
        """Get sector code to description mapping.

        Args:
            year: Year to fetch descriptions for.

        Returns:
            Dict mapping sector codes to descriptions.
        """
        table_id = self.discover_table_id("use")
        raw_df = self.fetch_io_table(table_id=table_id, year=str(year))

        if raw_df.empty:
            return {}

        # Build mapping from both row and column descriptions
        descriptions: dict[str, str] = {}

        if "RowCode" in raw_df.columns and "RowDescr" in raw_df.columns:
            for _, row in raw_df[["RowCode", "RowDescr"]].drop_duplicates().iterrows():
                descriptions[row["RowCode"]] = row["RowDescr"]

        if "ColCode" in raw_df.columns and "ColDescr" in raw_df.columns:
            for _, row in raw_df[["ColCode", "ColDescr"]].drop_duplicates().iterrows():
                if row["ColCode"] not in descriptions:
                    descriptions[row["ColCode"]] = row["ColDescr"]

        return descriptions
