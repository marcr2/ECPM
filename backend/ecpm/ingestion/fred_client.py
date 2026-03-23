"""FRED API client with exponential backoff retry and rate limiting.

Wraps the fredapi library with tenacity retry logic for resilient data retrieval.
Handles authentication, retry on transient errors, and rate limit mitigation.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pandas as pd
import structlog
from fredapi import Fred
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
    series_id = "unknown"
    if retry_state.args and len(retry_state.args) > 1:
        series_id = retry_state.args[1]
    elif retry_state.kwargs:
        series_id = retry_state.kwargs.get("series_id", "unknown")

    logger.warning(
        "fred_retry",
        series_id=series_id,
        attempt=retry_state.attempt_number,
        wait=round(retry_state.next_action.sleep if retry_state.next_action else 0, 2),  # type: ignore[union-attr]
    )


class FredClient:
    """FRED API wrapper with exponential backoff retry and rate limiting.

    Attributes:
        api_key: FRED API key for authentication.
        rate_limit_delay: Minimum seconds between consecutive API calls (0.6s
            for FRED's 120 req/min limit).
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("FRED API key is required")
        self.api_key = api_key
        self.fred = Fred(api_key=api_key)
        self.rate_limit_delay: float = 0.6
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
    def _raw_fetch(self, series_id: str) -> tuple[pd.Series, dict[str, Any]]:
        """Fetch a FRED series with retry logic.

        This is the retried internal method. It calls fredapi synchronously
        and returns raw data + info.

        Args:
            series_id: FRED series identifier (e.g., "GDPC1").

        Returns:
            Tuple of (pandas Series of observations, dict of series metadata).
        """
        self._throttle()
        data = self.fred.get_series(series_id)
        self._throttle()
        info_raw = self.fred.get_series_info(series_id)

        # fredapi returns a pandas Series for info -- convert to dict
        if isinstance(info_raw, pd.Series):
            info = info_raw.to_dict()
        else:
            info = dict(info_raw) if info_raw is not None else {}

        # Ensure series_id is in the info dict
        if "id" not in info:
            info["id"] = series_id

        return data, info

    def fetch_series(self, series_id: str) -> tuple[pd.Series, dict[str, Any]]:
        """Fetch a FRED series synchronously with retry.

        Suitable for use in Celery workers or other synchronous contexts.

        Args:
            series_id: FRED series identifier.

        Returns:
            Tuple of (pandas Series of observations, dict of series metadata).
        """
        data, info = self._raw_fetch(series_id)
        logger.info(
            "fred_fetch_success",
            series_id=series_id,
            count=len(data) if data is not None else 0,
        )
        return data, info

    # Alias for explicit naming in sync contexts
    fetch_series_sync = fetch_series

    async def fetch_series_async(
        self, series_id: str
    ) -> tuple[pd.Series, dict[str, Any]]:
        """Fetch a FRED series asynchronously by running in a thread executor.

        fredapi is synchronous internally, so we run it in a thread pool
        to avoid blocking the asyncio event loop.

        Args:
            series_id: FRED series identifier.

        Returns:
            Tuple of (pandas Series of observations, dict of series metadata).
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_series, series_id)
