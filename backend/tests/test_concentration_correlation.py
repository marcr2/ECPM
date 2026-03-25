"""Tests for concentration–indicator correlation (annual Census panels)."""

import pandas as pd

from ecpm.concentration.correlation import (
    _annual_observation_lag_correlation,
    _merge_concentration_with_indicator,
    map_concentration_to_indicators,
)


def test_merge_aligns_by_calendar_year() -> None:
    conc = pd.DataFrame(
        {
            "year": [2000, 2001, 2005],
            "cr4": [10.0, 20.0, 30.0],
        }
    )
    idx = pd.to_datetime(["2000-01-01", "2001-01-01", "2005-01-01"])
    ind = pd.Series([1.0, 2.0, 3.0], index=idx)
    m = _merge_concentration_with_indicator(conc, "cr4", ind)
    assert len(m) == 3
    assert list(m["concentration"]) == [10.0, 20.0, 30.0]
    assert list(m["indicator"]) == [1.0, 2.0, 3.0]


def test_short_panel_produces_nonzero_correlation() -> None:
    """Census-style ~6 points must still yield correlations (regression guard)."""
    conc = pd.DataFrame(
        {
            "year": [1997, 2002, 2007, 2012, 2017, 2022],
            "cr4": [20.0, 22.0, 25.0, 28.0, 30.0, 35.0],
        }
    )
    years = conc["year"]
    ind = pd.Series(
        (years - 1997).astype(float).values * 0.1,
        index=pd.to_datetime(years.astype(str), format="%Y"),
    )
    merged = _merge_concentration_with_indicator(conc, "cr4", ind)
    r, lag, n = _annual_observation_lag_correlation(merged)
    assert n >= 4
    assert r > 0.9
    assert lag == 0

    indicator_data = {"rate-of-profit": ind}
    out = map_concentration_to_indicators(conc, indicator_data, naics_code="311")
    rop = next(x for x in out if x["indicator_slug"] == "rate-of-profit")
    assert rop["correlation"] > 0.5
    assert rop["confidence"] > 0
