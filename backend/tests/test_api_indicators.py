"""Tests for indicator API endpoints -- FEAT-08, DASH-04.

These tests verify the FastAPI indicator endpoints once they are
implemented in Plan 02-04. They follow the existing test pattern
from test_api.py (sync TestClient with dependency overrides).
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="Awaiting Plan 02-04 API endpoints")
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


@pytest.mark.skip(reason="Awaiting Plan 02-04 API endpoints")
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


@pytest.mark.skip(reason="Awaiting Plan 02-04 API endpoints")
class TestMethodologyDocs:
    """GET /api/indicators/methodology returns docs for all methodologies."""

    def test_methodology_docs_returned(self, sync_client) -> None:
        """Methodology endpoint returns documentation with mappings."""
        response = sync_client.get("/api/indicators/methodology")
        assert response.status_code == 200

        data = response.json()
        assert "methodology_slug" in data
        assert "indicators" in data
        # Each indicator doc has formula_latex and mappings
        for indicator in data["indicators"]:
            assert "formula_latex" in indicator
            assert "mappings" in indicator


@pytest.mark.skip(reason="Awaiting Plan 02-04 API endpoints")
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
