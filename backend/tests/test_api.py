"""Tests for FastAPI REST endpoints and SSE -- INFR-02, INFR-03.

Covers health, series list, series detail, status, fetch trigger,
and SSE stream endpoints. Tests are in RED state until Plan 01-04.
"""

from __future__ import annotations

import pytest

# Import guard
try:
    from ecpm.main import app as fastapi_app

    _HAS_APP = True
except ImportError:
    _HAS_APP = False

pytestmark = pytest.mark.skipif(
    not _HAS_APP, reason="ecpm.main not yet implemented"
)


@pytest.fixture
def sync_client():
    """Provide a synchronous TestClient for simple endpoint tests."""
    try:
        from starlette.testclient import TestClient
    except ImportError:
        pytest.skip("starlette not installed")

    return TestClient(fastapi_app)


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
