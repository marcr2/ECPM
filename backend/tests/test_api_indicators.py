"""Tests for indicator API endpoints -- FEAT-01, FEAT-08, DASH-04, DASH-05.

These tests verify the FastAPI indicator endpoints implemented in Plan 02-04.
They follow the existing test pattern from test_api.py (sync TestClient with
dependency overrides), seeding the in-memory SQLite database with observation
data for the FRED series that the mappers need.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import tempfile
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

# Import guards
try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False

try:
    from ecpm.main import app as fastapi_app
    from ecpm.database import get_db
    from ecpm.models import Base
    from ecpm.models.series_metadata import SeriesMetadata
    from ecpm.models.observation import Observation
    from ecpm.indicators.registry import MethodologyRegistry
    from ecpm.indicators.shaikh_tonak import ShaikhTonakMapper
    from ecpm.indicators.kliman import KlimanMapper

    _HAS_APP = True
except ImportError:
    _HAS_APP = False

pytestmark = pytest.mark.skipif(
    not _HAS_APP, reason="ecpm.main not yet implemented"
)


# ---------------------------------------------------------------------------
# All FRED series IDs required by both mappers + financial indicators
# ---------------------------------------------------------------------------

# Core series used by Shaikh/Tonak and Kliman mappers
_CORE_SERIES = {
    "BEA:T11200:L1": ("National Income (NIPA T11200 L1)", "A", "BEA"),
    "A053RC1Q027SBEA": ("National Income", "Q", "FRED"),
    "A576RC1": ("Compensation of Employees", "Q", "FRED"),
    "K1NTOTL1SI000": ("Current-Cost Net Stock of Private Fixed Assets", "A", "FRED"),
    "K1NTOTL1HI000": ("Historical-Cost Net Stock of Private Fixed Assets", "A", "FRED"),
}

# Financial series (methodology-independent)
_FINANCIAL_SERIES = {
    "OPHNFB": ("Output Per Hour, Nonfarm Business", "Q", "FRED"),
    "PRS85006092": ("Real Compensation Per Hour", "Q", "FRED"),
    "BOGZ1FL073164003Q": ("Nonfinancial Corporate Debt Securities", "Q", "FRED"),
    "TFAABSNNCB": ("Nonfinancial Corporate Total Financial Assets", "Q", "FRED"),
    "K1PTOTL1ES000": ("Current-Cost Net Stock of Private Fixed Assets", "A", "FRED"),
    "GDP": ("Gross Domestic Product", "Q", "FRED"),
    "BOGZ1FU106130001Q": ("Interest and Miscellaneous Payments, NFCB", "Q", "FRED"),
    "A445RC1Q027SBEA": ("Net Operating Surplus", "Q", "FRED"),
}

_ALL_SERIES = {**_CORE_SERIES, **_FINANCIAL_SERIES}


def _seed_database_sync(engine):
    """Seed the test database with mock observation data for all required series.

    Creates SeriesMetadata rows and 5 annual observations per series with
    known values that the mappers can compute against.

    Uses raw SQL inserts to avoid SQLAlchemy sentinel-value mismatches
    with SQLite and timezone-aware datetime composite primary keys.
    """

    async def _seed():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_factory() as session:
            # Create SeriesMetadata for all required series
            for series_id, (name, freq, source) in _ALL_SERIES.items():
                meta = SeriesMetadata(
                    series_id=series_id,
                    source=source,
                    name=name,
                    frequency=freq,
                    fetch_status="ok",
                    observation_count=5,
                )
                session.add(meta)
            await session.flush()

            # Create observations with known values (5 annual periods)
            # Use naive datetimes to avoid SQLite tz-aware sentinel mismatch
            dates = [
                dt.datetime(2018, 1, 1),
                dt.datetime(2019, 1, 1),
                dt.datetime(2020, 1, 1),
                dt.datetime(2021, 1, 1),
                dt.datetime(2022, 1, 1),
            ]

            # Known values matching test_indicators.py style
            series_values = {
                "BEA:T11200:L1": [
                    900_000.0,
                    950_000.0,
                    1_000_000.0,
                    1_100_000.0,
                    1_200_000.0,
                ],
                "A053RC1Q027SBEA": [900.0, 950.0, 1000.0, 1100.0, 1200.0],
                "A576RC1": [540.0, 570.0, 600.0, 650.0, 700.0],
                "K1NTOTL1SI000": [2800.0, 2900.0, 3000.0, 3200.0, 3400.0],
                "K1NTOTL1HI000": [2300.0, 2400.0, 2500.0, 2700.0, 2900.0],
                "OPHNFB": [95.0, 97.5, 100.0, 105.0, 110.0],
                "PRS85006092": [98.0, 99.0, 100.0, 101.0, 102.0],
                "BOGZ1FL073164003Q": [4500.0, 4700.0, 5000.0, 5300.0, 5600.0],
                "TFAABSNNCB": [28000.0, 29000.0, 30000.0, 32000.0, 34000.0],
                "K1PTOTL1ES000": [55000.0, 57000.0, 60000.0, 62000.0, 65000.0],
                "GDP": [19000.0, 19500.0, 20000.0, 20500.0, 21000.0],
                "BOGZ1FU106130001Q": [85.0, 90.0, 100.0, 110.0, 120.0],
                "A445RC1Q027SBEA": [450.0, 475.0, 500.0, 550.0, 600.0],
            }

            # Insert observations one by one with individual flushes
            # to avoid SQLite sentinel-value batch insert issues
            from sqlalchemy import text

            for series_id, values in series_values.items():
                for date, value in zip(dates, values):
                    await session.execute(
                        text(
                            "INSERT INTO observations "
                            "(observation_date, series_id, value, gap_flag) "
                            "VALUES (:date, :sid, :val, 0)"
                        ),
                        {"date": date.isoformat(), "sid": series_id, "val": value},
                    )

            await session.commit()

    asyncio.run(_seed())


@pytest.fixture
def sync_client(monkeypatch):
    """Provide a synchronous TestClient backed by in-memory SQLite with seeded data.

    Overrides get_db and lifespan, seeds all required FRED series for indicator
    computation, and registers both methodology mappers.
    """
    try:
        from starlette.testclient import TestClient
    except ImportError:
        pytest.skip("starlette not installed")

    if not _HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")

    import ecpm.cache_manager as cache_manager

    _cache_tmp = Path(tempfile.mkdtemp()) / "indicators"
    monkeypatch.setattr(cache_manager, "CACHE_DIR", _cache_tmp)

    # Register mappers (needed for computation)
    MethodologyRegistry.reset()
    MethodologyRegistry.register(ShaikhTonakMapper())
    MethodologyRegistry.register(KlimanMapper())

    # Create in-memory async SQLite engine
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # Seed the database with all required series and observations
    _seed_database_sync(test_engine)

    test_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            yield session

    # Replace lifespan to avoid DB/Redis connection attempts
    @asynccontextmanager
    async def _test_lifespan(app):
        yield

    original_lifespan = fastapi_app.router.lifespan_context
    fastapi_app.router.lifespan_context = _test_lifespan
    fastapi_app.dependency_overrides[get_db] = _override_get_db

    client = TestClient(fastapi_app)
    yield client

    # Cleanup
    fastapi_app.dependency_overrides.clear()
    fastapi_app.router.lifespan_context = original_lifespan
    MethodologyRegistry.reset()
    # Re-register defaults for other tests
    MethodologyRegistry.register(ShaikhTonakMapper())
    MethodologyRegistry.register(KlimanMapper())
    asyncio.run(test_engine.dispose())


# ---------------------------------------------------------------------------
# Indicator Overview tests
# ---------------------------------------------------------------------------


class TestIndicatorOverview:
    """GET /api/indicators/ returns overview with all indicator summaries."""

    def test_overview_returns_all_indicators(self, sync_client) -> None:
        """Overview endpoint returns all 8 indicator summaries."""
        response = sync_client.get("/api/indicators/")
        assert response.status_code == 200

        data = response.json()
        assert "methodology" in data
        assert "indicators" in data
        assert len(data["indicators"]) == 8

    def test_overview_default_methodology(self, sync_client) -> None:
        """Default methodology is shaikh-tonak."""
        response = sync_client.get("/api/indicators/")
        assert response.status_code == 200
        data = response.json()
        assert data["methodology"] == "shaikh-tonak"

    def test_overview_each_summary_has_required_fields(self, sync_client) -> None:
        """Each indicator summary has slug, name, units fields."""
        response = sync_client.get("/api/indicators/")
        data = response.json()
        for indicator in data["indicators"]:
            assert "slug" in indicator
            assert "name" in indicator
            assert "units" in indicator


# ---------------------------------------------------------------------------
# Indicator Detail tests
# ---------------------------------------------------------------------------


class TestIndicatorDetail:
    """GET /api/indicators/{slug} returns time-series data."""

    def test_indicator_detail_returns_timeseries(self, sync_client) -> None:
        """Detail endpoint returns time-series with slug, name, data."""
        response = sync_client.get("/api/indicators/rate_of_profit")
        assert response.status_code == 200

        data = response.json()
        assert data["slug"] == "rate_of_profit"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_indicator_detail_has_methodology(self, sync_client) -> None:
        """Detail response includes methodology field."""
        response = sync_client.get("/api/indicators/rate_of_profit")
        data = response.json()
        assert data["methodology"] == "shaikh-tonak"

    def test_indicator_detail_kliman_returns_data(self, sync_client) -> None:
        """Kliman path maps FRED national income and computes successfully."""
        response = sync_client.get(
            "/api/indicators/rate_of_profit?methodology=kliman"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["methodology"] == "kliman"
        assert len(data["data"]) > 0

    def test_indicator_detail_data_has_date_value(self, sync_client) -> None:
        """Each data point has date and value."""
        response = sync_client.get("/api/indicators/rate_of_profit")
        data = response.json()
        for point in data["data"]:
            assert "date" in point
            assert "value" in point


# ---------------------------------------------------------------------------
# Methodology Documentation tests
# ---------------------------------------------------------------------------


class TestMethodologyDocs:
    """GET /api/indicators/methodology returns docs for all methodologies."""

    def test_methodology_docs_list_returned(self, sync_client) -> None:
        """Methodology endpoint returns list of documentation objects."""
        response = sync_client.get("/api/indicators/methodology")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # shaikh-tonak and kliman

    def test_methodology_docs_have_required_fields(self, sync_client) -> None:
        """Each methodology doc has slug, name, and indicators."""
        response = sync_client.get("/api/indicators/methodology")
        data = response.json()
        for doc in data:
            assert "methodology_slug" in doc
            assert "methodology_name" in doc
            assert "indicators" in doc
            # Each indicator doc has formula_latex and mappings
            for indicator in doc["indicators"]:
                assert "formula_latex" in indicator
                assert "mappings" in indicator

    def test_single_methodology_doc(self, sync_client) -> None:
        """GET /api/indicators/methodology/shaikh-tonak returns single doc."""
        response = sync_client.get("/api/indicators/methodology/shaikh-tonak")
        assert response.status_code == 200

        data = response.json()
        assert data["methodology_slug"] == "shaikh-tonak"
        assert len(data["indicators"]) == 8


# ---------------------------------------------------------------------------
# Compare endpoint tests
# ---------------------------------------------------------------------------


class TestIndicatorCompare:
    """GET /api/indicators/{slug}/compare returns multi-methodology comparison."""

    def test_compare_returns_multiple_methodologies(self, sync_client) -> None:
        """Compare endpoint returns same indicator under different methodologies."""
        response = sync_client.get("/api/indicators/rate_of_profit/compare")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Should have at least 2 methodology results
        assert len(data) >= 2
        slugs = {item["methodology"] for item in data}
        assert "shaikh-tonak" in slugs
        assert "kliman" in slugs


# ---------------------------------------------------------------------------
# Negative tests (404 cases)
# ---------------------------------------------------------------------------


class TestIndicatorNotFound:
    """Unknown slugs and methodologies return 404."""

    def test_unknown_indicator_slug_returns_404(self, sync_client) -> None:
        """GET /api/indicators/unknown-slug returns 404."""
        response = sync_client.get("/api/indicators/unknown-slug")
        assert response.status_code == 404

    def test_unknown_methodology_returns_404(self, sync_client) -> None:
        """GET /api/indicators/rate_of_profit?methodology=unknown returns 404."""
        response = sync_client.get(
            "/api/indicators/rate_of_profit?methodology=unknown"
        )
        assert response.status_code == 404
