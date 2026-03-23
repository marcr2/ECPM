"""Shared test fixtures for ECPM backend test suite.

Provides mock API clients, async database session, test configuration,
FastAPI test client, and mock Redis. All production code imports are
guarded so conftest loads even before production code exists.
"""

from __future__ import annotations

import datetime
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Import guards: wrap production-code imports so conftest loads even when
# the backend package has not been created yet.
# ---------------------------------------------------------------------------

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False

try:
    import pandas as pd

    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False

try:
    from ecpm.models import Base  # noqa: F401 -- used by downstream tests

    _HAS_ECPM_MODELS = True
except ImportError:
    _HAS_ECPM_MODELS = False

try:
    from ecpm.database import get_db  # noqa: F401 -- used by downstream tests

    _HAS_ECPM_DB = True
except (ImportError, Exception):
    _HAS_ECPM_DB = False

try:
    from ecpm.main import app as fastapi_app  # noqa: F401

    _HAS_ECPM_APP = True
except ImportError:
    _HAS_ECPM_APP = False


# ---------------------------------------------------------------------------
# Async SQLAlchemy test session (sqlite+aiosqlite for unit tests)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[Any, None]:
    """Provide an async SQLAlchemy session backed by in-memory SQLite.

    Requires aiosqlite. If unavailable the test is skipped.
    """
    if not _HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")

    try:
        import aiosqlite  # noqa: F401 -- ensure driver is available
    except ImportError:
        pytest.skip("aiosqlite not installed")

    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # If production models are available, create tables
    if _HAS_ECPM_MODELS:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        yield session

    await engine.dispose()


# ---------------------------------------------------------------------------
# Mock FRED API client
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_fred_client() -> MagicMock:
    """Return a mock FRED API client with canned data for GDPC1.

    The mock exposes:
      - client.fetch_series(series_id) -> (pandas Series, dict) matching FredClient interface
    """
    client = MagicMock()

    if _HAS_PANDAS:
        gdpc1_data = pd.Series(
            [18_000.0, 18_200.0, 18_500.0, 18_300.0, 18_700.0],
            index=pd.to_datetime(
                ["2023-01-01", "2023-04-01", "2023-07-01", "2023-10-01", "2024-01-01"]
            ),
            name="GDPC1",
        )
    else:
        gdpc1_data = [18_000.0, 18_200.0, 18_500.0, 18_300.0, 18_700.0]

    gdpc1_info = {
        "id": "GDPC1",
        "title": "Real Gross Domestic Product",
        "units": "Billions of Chained 2017 Dollars",
        "frequency": "Quarterly",
        "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
        "last_updated": "2024-01-26",
        "observation_start": "1947-01-01",
        "observation_end": "2023-10-01",
    }

    client.fetch_series.return_value = (gdpc1_data, gdpc1_info)
    return client


# ---------------------------------------------------------------------------
# Mock BEA API client
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bea_client() -> MagicMock:
    """Return a mock BEA API client with canned NIPA T11200 data.

    The mock exposes:
      - client.fetch_nipa_table("T11200") -> DataFrame
    """
    client = MagicMock()

    if _HAS_PANDAS:
        nipa_data = pd.DataFrame(
            {
                "LineNumber": [1, 2, 3],
                "DataValue": [25000.0, 12000.0, 13000.0],
                "TimePeriod": ["2023Q1", "2023Q1", "2023Q1"],
                "LineDescription": [
                    "National income",
                    "Compensation of employees",
                    "Proprietors' income",
                ],
            }
        )
    else:
        nipa_data = {
            "LineNumber": [1, 2, 3],
            "DataValue": [25000.0, 12000.0, 13000.0],
            "TimePeriod": ["2023Q1", "2023Q1", "2023Q1"],
        }

    client.fetch_nipa_table.return_value = nipa_data
    client.fetch_fixed_assets.return_value = nipa_data  # simplified
    return client


# ---------------------------------------------------------------------------
# Test series configuration
# ---------------------------------------------------------------------------


@pytest.fixture
def test_series_config() -> dict[str, Any]:
    """Minimal series configuration: 2 FRED series, 1 BEA table."""
    return {
        "fred": {
            "series": [
                {
                    "id": "GDPC1",
                    "name": "Real GDP",
                    "frequency": "quarterly",
                    "category": "gdp",
                },
                {
                    "id": "UNRATE",
                    "name": "Unemployment Rate",
                    "frequency": "monthly",
                    "category": "labor",
                },
            ],
        },
        "bea": {
            "tables": [
                {
                    "id": "T11200",
                    "name": "National Income by Type of Income",
                    "dataset": "NIPA",
                    "frequency": "quarterly",
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# FastAPI TestClient (httpx async)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[Any, None]:
    """Provide an httpx.AsyncClient wired to the FastAPI app.

    Skips if the production app or httpx is not available.
    """
    if not _HAS_ECPM_APP:
        pytest.skip("ecpm.main.app not available")

    try:
        from httpx import ASGITransport, AsyncClient
    except ImportError:
        pytest.skip("httpx not installed")

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# Mock Redis client
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redis() -> MagicMock:
    """Dict-backed mock Redis client for unit tests.

    Supports get/set/delete with optional TTL tracking.
    """
    store: dict[str, tuple[Any, float | None]] = {}

    redis = MagicMock()

    async def _set(key: str, value: Any, ex: int | None = None) -> None:
        ttl = float(ex) if ex is not None else None
        store[key] = (value, ttl)

    async def _get(key: str) -> Any | None:
        entry = store.get(key)
        return entry[0] if entry else None

    async def _delete(key: str) -> int:
        return 1 if store.pop(key, None) is not None else 0

    redis.set = AsyncMock(side_effect=_set)
    redis.get = AsyncMock(side_effect=_get)
    redis.delete = AsyncMock(side_effect=_delete)
    redis._store = store  # expose for test introspection
    return redis


# ---------------------------------------------------------------------------
# Synthetic indicator fixtures for modeling tests (Phase 3)
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_indicators():
    """Generate a deterministic DataFrame of 8 economic indicators over 124 quarters.

    Uses numpy random seed 42 for reproducibility. Columns correspond to
    IndicatorSlug values. Rows span 1993Q1 to 2023Q4 (124 quarters).

    Produces realistic-looking time series:
      - rate_of_profit: declining trend (~0.15 to ~0.08)
      - occ: rising trend (~3.0 to ~5.5)
      - rate_of_surplus_value: gently rising (~1.5 to ~2.0)
      - mass_of_profit: strongly rising (~500 to ~2000)
      - productivity_wage_gap: rising (~100 to ~160)
      - credit_gdp_gap: oscillating around 0 with structural breaks (-10 to +15)
      - financial_real_ratio: rising (~1.2 to ~3.5)
      - debt_service_ratio: oscillating (~10 to ~20%)
    """
    if not _HAS_PANDAS:
        pytest.skip("pandas not installed")

    import numpy as np

    rng = np.random.default_rng(42)
    n = 124
    t = np.arange(n)

    dates = pd.date_range("1993-01-01", periods=n, freq="QS")

    # Declining trend with noise
    rate_of_profit = 0.15 - 0.07 * (t / n) + rng.normal(0, 0.005, n)

    # Rising trend
    occ = 3.0 + 2.5 * (t / n) + rng.normal(0, 0.1, n)

    # Gently rising
    rate_of_surplus_value = 1.5 + 0.5 * (t / n) + rng.normal(0, 0.03, n)

    # Strongly rising
    mass_of_profit = 500 + 1500 * (t / n) + rng.normal(0, 30, n)

    # Rising index
    productivity_wage_gap = 100 + 60 * (t / n) + rng.normal(0, 2, n)

    # Oscillating with structural breaks
    credit_gdp_gap = (
        5 * np.sin(2 * np.pi * t / 40)
        + 3 * np.where(t > 60, 1, 0)  # structural break at ~2008
        + rng.normal(0, 1.5, n)
    )

    # Rising
    financial_real_ratio = 1.2 + 2.3 * (t / n) + rng.normal(0, 0.08, n)

    # Oscillating
    debt_service_ratio = 15 + 4 * np.sin(2 * np.pi * t / 48) + rng.normal(0, 0.8, n)

    df = pd.DataFrame(
        {
            "rate_of_profit": rate_of_profit,
            "occ": occ,
            "rate_of_surplus_value": rate_of_surplus_value,
            "mass_of_profit": mass_of_profit,
            "productivity_wage_gap": productivity_wage_gap,
            "credit_gdp_gap": credit_gdp_gap,
            "financial_real_ratio": financial_real_ratio,
            "debt_service_ratio": debt_service_ratio,
        },
        index=dates,
    )

    return df


@pytest.fixture
def synthetic_regime_series():
    """Generate a pd.Series with 3 distinct volatility regimes.

    Uses numpy random seed 42 for reproducibility. Returns 300 data points
    with three segments:
      - Regime 0 (normal): low volatility, positive mean
      - Regime 1 (stagnation): medium volatility, near-zero mean
      - Regime 2 (crisis): high volatility, negative mean
    """
    if not _HAS_PANDAS:
        pytest.skip("pandas not installed")

    import numpy as np

    rng = np.random.default_rng(42)
    n = 300

    series = np.empty(n)

    # Regime 0: normal (quarters 0-119)
    series[:120] = 0.5 + rng.normal(0, 0.3, 120)

    # Regime 1: stagnation (quarters 120-219)
    series[120:220] = 0.05 + rng.normal(0, 0.8, 100)

    # Regime 2: crisis (quarters 220-299)
    series[220:] = -0.8 + rng.normal(0, 1.5, 80)

    dates = pd.date_range("1948-01-01", periods=n, freq="QS")
    return pd.Series(series, index=dates, name="regime_test")
