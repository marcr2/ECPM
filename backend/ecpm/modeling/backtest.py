"""Historical backtesting against known crisis episodes.

Evaluates the Composite Crisis Index against 6 major historical
crisis episodes, checking 12-month and 24-month early-warning
capability.

Exports:
    run_episode       -- backtest a single crisis episode
    run_all_backtests -- backtest all 6 episodes
    CRISIS_EPISODES   -- list of episode definitions
"""

from __future__ import annotations

import pandas as pd
import structlog

from ecpm.modeling.crisis_index import compute as compute_crisis_index

logger = structlog.get_logger(__name__)


# Historical crisis episodes matching frontend/src/lib/crisis-episodes.ts
CRISIS_EPISODES: list[dict] = [
    {
        "name": "Great Depression",
        "start_date": "1929-10-01",
        "end_date": "1933-03-01",
    },
    {
        "name": "Oil/Stagflation",
        "start_date": "1973-11-01",
        "end_date": "1975-03-01",
    },
    {
        "name": "Volcker",
        "start_date": "1980-01-01",
        "end_date": "1982-11-01",
    },
    {
        "name": "Dot-com",
        "start_date": "2001-03-01",
        "end_date": "2001-11-01",
    },
    {
        "name": "GFC",
        "start_date": "2007-12-01",
        "end_date": "2009-06-01",
    },
    {
        "name": "COVID",
        "start_date": "2020-02-01",
        "end_date": "2020-04-01",
    },
]


def run_episode(
    indicators: pd.DataFrame,
    episode_name: str,
    start_date: str,
    end_date: str,
) -> dict:
    """Run a backtest for a single crisis episode.

    Computes the crisis index over a window from 3 years before
    start_date to end_date. Evaluates whether the composite index
    exceeded its 75th historical percentile in the 12-month and
    24-month windows before the crisis start.

    Parameters
    ----------
    indicators : pd.DataFrame
        Full indicator DataFrame (all available history).
    episode_name : str
        Name of the crisis episode.
    start_date : str
        Episode start date (ISO format).
    end_date : str
        Episode end date (ISO format).

    Returns
    -------
    dict
        Compatible with BacktestResult schema: episode_name, start_date,
        end_date, crisis_index_series, warning_12m, warning_24m,
        peak_value, peak_date.
    """
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    # Window: 3 years before start to end
    window_start = start_dt - pd.DateOffset(years=3)

    # Compute crisis index on the full available data
    crisis_result = compute_crisis_index(indicators)
    composite_history = crisis_result["history"]

    # Convert history to a Series for easier manipulation
    dates = pd.DatetimeIndex([entry["date"] for entry in composite_history])
    values = pd.Series(
        [entry["composite"] for entry in composite_history],
        index=dates,
    )

    # Check if data covers the episode window
    data_covers_episode = (
        len(values) > 0
        and values.index.min() <= window_start
        and values.index.max() >= start_dt
    )

    if not data_covers_episode:
        logger.warning(
            "backtest_insufficient_data",
            episode=episode_name,
            data_start=str(values.index.min()) if len(values) > 0 else "empty",
            data_end=str(values.index.max()) if len(values) > 0 else "empty",
            required_start=str(window_start),
        )
        # Still compute what we can with available data
        window_data = values
    else:
        window_data = values[
            (values.index >= window_start) & (values.index <= end_dt)
        ]

    # Historical 75th percentile (from all available data)
    threshold_75 = float(values.quantile(0.75)) if len(values) > 0 else 50.0

    # 12-month warning window: start_date - 12 months to start_date
    warning_12m_start = start_dt - pd.DateOffset(months=12)
    pre_12m = values[
        (values.index >= warning_12m_start) & (values.index < start_dt)
    ]
    warning_12m = bool((pre_12m > threshold_75).any()) if len(pre_12m) > 0 else False

    # 24-month warning window: start_date - 24 months to start_date
    warning_24m_start = start_dt - pd.DateOffset(months=24)
    pre_24m = values[
        (values.index >= warning_24m_start) & (values.index < start_dt)
    ]
    warning_24m = bool((pre_24m > threshold_75).any()) if len(pre_24m) > 0 else False

    # Peak value and date within the episode window
    episode_data = values[
        (values.index >= start_dt) & (values.index <= end_dt)
    ]

    if len(episode_data) > 0:
        peak_idx = episode_data.idxmax()
        peak_value = float(episode_data.max())
        peak_date = peak_idx.isoformat() if hasattr(peak_idx, "isoformat") else str(peak_idx)
    elif len(window_data) > 0:
        # Fallback: use window data if episode dates not covered
        peak_idx = window_data.idxmax()
        peak_value = float(window_data.max())
        peak_date = peak_idx.isoformat() if hasattr(peak_idx, "isoformat") else str(peak_idx)
    else:
        peak_value = 0.0
        peak_date = start_date

    # Crisis index series for the window (as list of dicts)
    crisis_index_series = [
        {
            "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
            "value": float(val),
        }
        for idx, val in window_data.items()
    ]

    logger.info(
        "backtest_episode_complete",
        episode=episode_name,
        warning_12m=warning_12m,
        warning_24m=warning_24m,
        peak_value=round(peak_value, 2),
    )

    return {
        "episode_name": episode_name,
        "start_date": start_date,
        "end_date": end_date,
        "crisis_index_series": crisis_index_series,
        "warning_12m": warning_12m,
        "warning_24m": warning_24m,
        "peak_value": peak_value,
        "peak_date": peak_date,
    }


def run_all_backtests(
    indicators: pd.DataFrame,
) -> list[dict]:
    """Run backtests for all 6 historical crisis episodes.

    Parameters
    ----------
    indicators : pd.DataFrame
        Full indicator DataFrame.

    Returns
    -------
    list[dict]
        List of BacktestResult-compatible dicts.
    """
    results = []
    for episode in CRISIS_EPISODES:
        result = run_episode(
            indicators,
            episode_name=episode["name"],
            start_date=episode["start_date"],
            end_date=episode["end_date"],
        )
        results.append(result)

    logger.info(
        "all_backtests_complete",
        n_episodes=len(results),
    )

    return results
