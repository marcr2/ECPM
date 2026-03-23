"""Indicator computation orchestrator (stub).

Provides async entry points for computing individual and summary indicators.
These stubs will be implemented in Plan 02-02 when methodology mappers exist.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession


async def compute_indicator(
    slug: str, methodology_slug: str, db: AsyncSession
) -> pd.Series:
    """Compute a single indicator time-series.

    Args:
        slug: Indicator slug (e.g., 'rate_of_profit').
        methodology_slug: Methodology to use (e.g., 'shaikh-tonak').
        db: Async database session for querying observations.

    Returns:
        pd.Series of computed values indexed by date.

    Raises:
        NotImplementedError: Always -- implementation in Plan 02-02.
    """
    raise NotImplementedError("Implementation in Plan 02-02")


async def compute_all_summaries(
    methodology_slug: str, db: AsyncSession
) -> list[dict]:
    """Compute summary statistics for all indicators.

    Args:
        methodology_slug: Methodology to use (e.g., 'shaikh-tonak').
        db: Async database session for querying observations.

    Returns:
        List of dicts with slug, latest_value, latest_date, trend, sparkline.

    Raises:
        NotImplementedError: Always -- implementation in Plan 02-02.
    """
    raise NotImplementedError("Implementation in Plan 02-02")
