"""BEA API client with exponential backoff retry.

Wraps the beaapi library for retrieving NIPA and Fixed Assets tables
with tenacity retry logic for resilient data retrieval.
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
    table_name = "unknown"
    if retry_state.args and len(retry_state.args) > 1:
        table_name = retry_state.args[1]
    elif retry_state.kwargs:
        table_name = retry_state.kwargs.get("table_name", "unknown")

    logger.warning(
        "bea_retry",
        table_name=table_name,
        attempt=retry_state.attempt_number,
    )


class BEAClient:
    """BEA API wrapper with exponential backoff retry.

    Handles both NIPA and FixedAssets datasets, which are separate
    API endpoints in the BEA system (pitfall #6 from research).

    Attributes:
        api_key: BEA API key for authentication.
        rate_limit_delay: Minimum seconds between consecutive API calls.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("BEA API key is required")
        self.api_key = api_key
        self.rate_limit_delay: float = 0.7  # BEA: 100 req/min
        self._last_call_time: float = 0.0

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
    def _api_request(
        self,
        dataset_name: str,
        table_name: str,
        frequency: str = "Q",
        year: str = "ALL",
    ) -> pd.DataFrame:
        """Make a BEA API request with retry logic.

        Uses beaapi library under the hood. Falls back to empty DataFrame
        on import issues.

        Args:
            dataset_name: BEA dataset ("NIPA" or "FixedAssets").
            table_name: Table name code (e.g., "T11200", "FAAt101").
            frequency: Frequency code ("Q", "A", "M").
            year: Year specification ("ALL" or specific year).

        Returns:
            DataFrame with BEA data.
        """
        self._throttle()

        try:
            import beaapi

            data = beaapi.get_data(
                self.api_key,
                datasetname=dataset_name,
                TableName=table_name,
                Frequency=frequency,
                Year=year,
            )
        except ImportError:
            # beaapi not installed -- use httpx as fallback
            import httpx

            params = {
                "UserID": self.api_key,
                "method": "GetData",
                "datasetname": dataset_name,
                "TableName": table_name,
                "Frequency": frequency,
                "Year": year,
                "ResultFormat": "JSON",
            }
            response = httpx.get(
                "https://apps.bea.gov/api/data/", params=params, timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            # Parse BEA JSON response
            bea_data = result.get("BEAAPI", {}).get("Results", {}).get("Data", [])
            if not bea_data:
                return pd.DataFrame(
                    columns=[
                        "LineNumber",
                        "LineDescription",
                        "DataValue",
                        "TimePeriod",
                    ]
                )
            data = pd.DataFrame(bea_data)

        logger.info(
            "bea_fetch_success",
            dataset=dataset_name,
            table_name=table_name,
            rows=len(data) if data is not None else 0,
        )
        return data

    def fetch_nipa_table(
        self,
        table_name: str,
        frequency: str = "Q",
        year: str = "ALL",
    ) -> pd.DataFrame:
        """Fetch a NIPA table from the BEA API.

        Args:
            table_name: NIPA table code (e.g., "T11200", "T61900").
            frequency: Data frequency ("Q" for quarterly, "A" for annual).
            year: Year to fetch ("ALL" for all available years).

        Returns:
            DataFrame with columns including LineNumber, DataValue, TimePeriod.
        """
        return self._api_request(
            dataset_name="NIPA",
            table_name=table_name,
            frequency=frequency,
            year=year,
        )

    def fetch_fixed_assets(
        self,
        table_name: str,
        year: str = "ALL",
    ) -> pd.DataFrame:
        """Fetch a Fixed Assets table from the BEA API.

        Uses datasetname='FixedAssets' -- separate from NIPA
        (BEA research pitfall #6).

        Args:
            table_name: Fixed assets table code (e.g., "FAAt101").
            year: Year to fetch ("ALL" for all available years).

        Returns:
            DataFrame with fixed assets data.
        """
        return self._api_request(
            dataset_name="FixedAssets",
            table_name=table_name,
            frequency="A",  # Fixed assets are annual
            year=year,
        )

    def discover_tables(self, dataset: str = "NIPA") -> pd.DataFrame:
        """Discover available table names for a BEA dataset.

        Useful for verifying table name codes before configuring ingestion.

        Args:
            dataset: BEA dataset name ("NIPA" or "FixedAssets").

        Returns:
            DataFrame listing available tables with descriptions.
        """
        try:
            import beaapi

            return beaapi.get_parameter_values(
                self.api_key, dataset, "TableName"
            )
        except ImportError:
            import httpx

            params = {
                "UserID": self.api_key,
                "method": "GetParameterValues",
                "datasetname": dataset,
                "ParameterName": "TableName",
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
            return pd.DataFrame(param_values)
