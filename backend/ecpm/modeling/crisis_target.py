"""Continuous distance-to-crisis target variable from NBER USREC data.

Transforms the binary USREC recession indicator (1 = recession month,
0 = expansion) into a continuous 0.0-1.0 target measuring proximity
to recession.  For each month *t*, the target equals the fraction of
the next 12 months that fall inside a recession:

    target(t) = mean(USREC[t+1 : t+13])

This gives ~800 continuous training observations instead of 14 binary
crisis labels, making supervised learning viable.

Exports:
    build_crisis_target -- build target Series aligned to an indicator index
"""

from __future__ import annotations

import pandas as pd
import structlog

logger = structlog.get_logger(__name__)

LOOKAHEAD_MONTHS = 12


def build_crisis_target(
    usrec: pd.Series,
    target_index: pd.DatetimeIndex | None = None,
    lookahead: int = LOOKAHEAD_MONTHS,
) -> pd.Series:
    """Build a continuous distance-to-crisis target from USREC.

    Parameters
    ----------
    usrec : pd.Series
        Binary USREC series (1 = recession, 0 = expansion) with a
        DatetimeIndex.
    target_index : pd.DatetimeIndex or None
        If provided, reindex the result to this index (forward-fill).
    lookahead : int
        Number of months to look ahead (default 12).

    Returns
    -------
    pd.Series
        Continuous target in [0.0, 1.0].  NaN for the last ``lookahead``
        months where the forward window is incomplete.
    """
    usrec = usrec.sort_index().dropna()

    # Forward-looking rolling mean (shift so we don't include current month)
    target = (
        usrec
        .shift(-1)
        .rolling(window=lookahead, min_periods=lookahead)
        .mean()
    )

    target.name = "crisis_proximity"

    if target_index is not None:
        target = target.reindex(target_index, method="ffill")

    n_valid = target.notna().sum()
    logger.info(
        "crisis_target_built",
        total_obs=len(target),
        valid_obs=int(n_valid),
        lookahead_months=lookahead,
        recession_rate=round(float(target.mean()) if n_valid > 0 else 0.0, 4),
    )

    return target
