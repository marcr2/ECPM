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
    from ecpm.database import Base, get_db  # noqa: F401 -- used by downstream tests

    _HAS_ECPM_DB = True
except ImportError:
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
    if _HAS_ECPM_DB:
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
      - client.get_series("GDPC1") -> pandas Series
      - client.get_series_info("GDPC1") -> dict with metadata
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

    client.get_series.return_value = gdpc1_data
    client.get_series_info.return_value = gdpc1_info
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
