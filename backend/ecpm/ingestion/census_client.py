"""Census Bureau API client with exponential backoff retry.

Wraps httpx for retrieving Economic Census data including
County Business Patterns (CBP) and Economic Census concentration data.
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
    year = "unknown"
    if retry_state.args and len(retry_state.args) > 1:
        year = retry_state.args[1]
    elif retry_state.kwargs:
        year = retry_state.kwargs.get("year", "unknown")

    logger.warning(
        "census_retry",
        year=year,
        attempt=retry_state.attempt_number,
    )


class CensusClient:
    """Census Bureau API wrapper with exponential backoff retry.

    Handles County Business Patterns (CBP) and Economic Census datasets
    for corporate concentration data retrieval.

    Attributes:
        api_key: Census API key for authentication.
        rate_limit_delay: Minimum seconds between consecutive API calls.
    """

    BASE_URL = "https://api.census.gov/data"

    def __init__(self, api_key: str) -> None:
        """Initialize Census client.

        Args:
            api_key: Census Bureau API key (get from census.gov/developers).

        Raises:
            ValueError: If api_key is empty.
        """
        if not api_key:
            raise ValueError("Census API key is required")
        self.api_key = api_key
        self.rate_limit_delay: float = 0.5  # Census API is slower than BEA
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
        dataset: str,
        year: int,
        variables: list[str],
        predicates: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """Make a Census API request with retry logic.

        Args:
            dataset: Census dataset path (e.g., "cbp", "ecnbasic").
            year: Data year.
            variables: List of variable names to retrieve.
            predicates: Query predicates (e.g., {"NAICS2017": "31-33"}).

        Returns:
            DataFrame with Census data.
        """
        self._throttle()

        import httpx

        # Build URL - Census API uses year/dataset format
        url = f"{self.BASE_URL}/{year}/{dataset}"

        # Build query params
        params: dict[str, str] = {
            "get": ",".join(variables),
            "key": self.api_key,
        }

        # Add predicates
        if predicates:
            for key, value in predicates.items():
                params[key] = value

        response = httpx.get(url, params=params, timeout=30.0)

        if response.status_code == 404:
            logger.warning(
                "census_no_data",
                year=year,
                dataset=dataset,
            )
            return pd.DataFrame()

        response.raise_for_status()
        result = response.json()

        if not result or len(result) < 2:
            return pd.DataFrame()

        # First row is headers, rest is data
        headers = result[0]
        data = result[1:]

        df = pd.DataFrame(data, columns=headers)

        logger.info(
            "census_fetch_success",
            dataset=dataset,
            year=year,
            rows=len(df),
        )

        return df

    def fetch_concentration_data(
        self,
        year: int,
        naics_code: str,
    ) -> dict[str, Any]:
        """Fetch concentration data for a NAICS industry.

        Retrieves establishment counts by employment size class,
        which can be used to compute concentration approximations.

        Args:
            year: Census year (e.g., 2017, 2022).
            naics_code: 2-6 digit NAICS code.

        Returns:
            Dict with concentration-related metrics, or empty dict if unavailable.
        """
        try:
            # Use County Business Patterns for establishment data
            variables = [
                "NAICS2017",
                "NAICS2017_LABEL",
                "ESTAB",
                "EMP",
                "PAYANN",
            ]

            predicates = {
                "for": "us:*",
                "NAICS2017": naics_code,
            }

            df = self._api_request(
                dataset="cbp",
                year=year,
                variables=variables,
                predicates=predicates,
            )

            if df.empty:
                return {}

            # Parse results
            row = df.iloc[0]
            return {
                "naics_code": str(row.get("NAICS2017", naics_code)),
                "naics_name": str(row.get("NAICS2017_LABEL", "")),
                "num_establishments": int(row.get("ESTAB", 0) or 0),
                "employment": int(row.get("EMP", 0) or 0),
                "annual_payroll": float(row.get("PAYANN", 0) or 0),
                "year": year,
            }

        except Exception as e:
            logger.warning(
                "census_concentration_error",
                year=year,
                naics_code=naics_code,
                error=str(e),
            )
            return {}

    def fetch_market_share_data(
        self,
        year: int,
        industry: str,
    ) -> pd.DataFrame:
        """Fetch market share data for an industry.

        Uses Economic Census data when available, falls back to
        CBP establishment size class distribution.

        Note: True firm-level market share data requires Economic Census
        microdata which is not publicly available. This returns establishment
        size distributions as a proxy.

        Args:
            year: Census year (1997, 2002, 2007, 2012, 2017, 2022).
            industry: NAICS industry code.

        Returns:
            DataFrame with firm/establishment market share approximations,
            or empty DataFrame if unavailable.
        """
        try:
            # Try Economic Census basic data
            variables = [
                "NAICS2017",
                "NAICS2017_LABEL",
                "RCPTOT",  # Total receipts
                "ESTAB",
                "EMP",
            ]

            predicates = {
                "for": "us:*",
                "NAICS2017": industry,
            }

            df = self._api_request(
                dataset="ecnbasic",
                year=year,
                variables=variables,
                predicates=predicates,
            )

            if df.empty:
                # Fall back to CBP
                df = self._api_request(
                    dataset="cbp",
                    year=year,
                    variables=[
                        "NAICS2017",
                        "NAICS2017_LABEL",
                        "ESTAB",
                        "EMP",
                        "PAYANN",
                    ],
                    predicates=predicates,
                )

            if df.empty:
                return pd.DataFrame(
                    columns=[
                        "naics_code",
                        "naics_name",
                        "firm_name",
                        "parent_company",
                        "revenue",
                        "market_share_pct",
                        "rank",
                    ]
                )

            return df

        except Exception as e:
            logger.warning(
                "census_market_share_error",
                year=year,
                industry=industry,
                error=str(e),
            )
            return pd.DataFrame()

    def aggregate_by_parent(self, firms_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate firm data by parent company.

        Groups subsidiaries under parent companies and sums revenues.

        Args:
            firms_df: DataFrame with firm-level data including
                'parent_company' and 'revenue' columns.

        Returns:
            DataFrame aggregated by parent company with total revenue
            and recalculated market shares.
        """
        if firms_df.empty:
            return firms_df

        if "parent_company" not in firms_df.columns:
            return firms_df

        # Group by parent company
        parent_col = "parent_company"
        revenue_col = "revenue" if "revenue" in firms_df.columns else "RCPTOT"

        if revenue_col not in firms_df.columns:
            return firms_df

        # Convert revenue to numeric
        firms_df[revenue_col] = pd.to_numeric(firms_df[revenue_col], errors="coerce")

        aggregated = (
            firms_df.groupby(parent_col, as_index=False)
            .agg({revenue_col: "sum"})
            .rename(columns={revenue_col: "total_revenue"})
        )

        # Calculate market share
        total = aggregated["total_revenue"].sum()
        if total > 0:
            aggregated["market_share_pct"] = (
                aggregated["total_revenue"] / total * 100
            )
        else:
            aggregated["market_share_pct"] = 0.0

        # Rank by market share
        aggregated = aggregated.sort_values("market_share_pct", ascending=False)
        aggregated["rank"] = range(1, len(aggregated) + 1)

        return aggregated
