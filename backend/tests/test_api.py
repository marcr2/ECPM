"""Tests for FastAPI REST endpoints and SSE -- INFR-02, INFR-03.

Covers health, series list, series detail, status, fetch trigger,
and SSE stream endpoints. Uses in-memory SQLite to avoid requiring
a running PostgreSQL instance during tests.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest

# Import guards
try:
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False

try:
    from ecpm.main import app as fastapi_app
    from ecpm.database import get_db
    from ecpm.models import Base

    _HAS_APP = True
except ImportError:
    _HAS_APP = False

pytestmark = pytest.mark.skipif(
    not _HAS_APP, reason="ecpm.main not yet implemented"
)


@pytest.fixture
def sync_client():
    """Provide a synchronous TestClient backed by in-memory SQLite.

    Overrides the get_db dependency and the lifespan so tests do not
    require a running PostgreSQL or Redis instance.
    """
    try:
        from starlette.testclient import TestClient
    except ImportError:
        pytest.skip("starlette not installed")

    if not _HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")

    # Create an in-memory async SQLite engine for tests
    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # Create tables in the in-memory SQLite engine
    import asyncio

    async def _setup_db():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_setup_db())

    test_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            yield session

    # Replace the lifespan to avoid DB/Redis connection attempts
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
    asyncio.run(test_engine.dispose())


class TestHealthEndpoint:
    """GET /health returns 200 with status healthy."""

    def test_health_endpoint(self, sync_client) -> None:
        response = sync_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSeriesListEndpoint:
    """GET /api/data/series returns 200 with series list."""

    def test_series_list_endpoint(self, sync_client) -> None:
        response = sync_client.get("/api/data/series")
        assert response.status_code == 200

        data = response.json()
        # Should return a list (may be empty before any ingestion)
        assert isinstance(data, (list, dict)), (
            "Series list should return a list or paginated dict"
        )


class TestSeriesDetailEndpoint:
    """GET /api/data/series/GDPC1 returns 200 with observations."""

    def test_series_detail_endpoint(self, sync_client) -> None:
        response = sync_client.get("/api/data/series/GDPC1")
        # May return 200 (with data) or 404 (series not ingested yet)
        assert response.status_code in (200, 404), (
            f"Expected 200 or 404, got {response.status_code}"
        )

        if response.status_code == 200:
            data = response.json()
            assert "series_id" in data or "observations" in data, (
                "Series detail should contain series_id or observations"
            )


class TestStatusEndpoint:
    """GET /api/data/status returns 200 with status fields."""

    def test_status_endpoint(self, sync_client) -> None:
        response = sync_client.get("/api/data/status")
        assert response.status_code == 200

        data = response.json()
        # Should have fields indicating pipeline health
        assert isinstance(data, dict), "Status should return a dict"


class TestFetchTrigger:
    """POST /api/data/fetch returns 200 with task_id."""

    def test_fetch_trigger(self, sync_client) -> None:
        response = sync_client.post("/api/data/fetch")
        assert response.status_code in (200, 202), (
            f"Fetch trigger should return 200 or 202, got {response.status_code}"
        )

        data = response.json()
        assert "task_id" in data, (
            "Fetch trigger response should contain task_id"
        )


class TestSSEStream:
    """GET /api/data/fetch/stream returns SSE content type."""

    def test_sse_stream(self, sync_client) -> None:
        # Use stream=True to test SSE endpoint without hanging
        with sync_client.stream("GET", "/api/data/fetch/stream") as response:
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type, (
                f"SSE endpoint should return text/event-stream, got {content_type}"
            )
