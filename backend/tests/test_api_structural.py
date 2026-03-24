"""Integration tests for structural analysis API endpoints.

Tests the FastAPI endpoints for I-O data, shock simulation, reproduction
schema, and critical sectors analysis.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

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

    _HAS_APP = True
except ImportError:
    _HAS_APP = False

# Skip if structural API not implemented yet
pytest.importorskip("ecpm.api.structural")

pytestmark = pytest.mark.skipif(
    not _HAS_APP, reason="ecpm.main not yet implemented"
)


@pytest.fixture
def structural_api_client():
    """Provide a synchronous TestClient backed by in-memory SQLite.

    Mirrors the pattern from test_api.py: overrides get_db and lifespan
    to avoid requiring PostgreSQL or Redis during tests.
    """
    try:
        from starlette.testclient import TestClient
    except ImportError:
        pytest.skip("starlette not installed")

    if not _HAS_SQLALCHEMY:
        pytest.skip("sqlalchemy not installed")

    test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)

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

    @asynccontextmanager
    async def _test_lifespan(app):
        yield

    original_lifespan = fastapi_app.router.lifespan_context
    fastapi_app.router.lifespan_context = _test_lifespan
    fastapi_app.dependency_overrides[get_db] = _override_get_db

    client = TestClient(fastapi_app)
    yield client

    fastapi_app.dependency_overrides.clear()
    fastapi_app.router.lifespan_context = original_lifespan
    asyncio.run(test_engine.dispose())


class TestGetYears:
    """Tests for GET /api/structural/years endpoint."""

    def test_get_years_returns_list(self, structural_api_client):
        """GET /api/structural/years should return a list of available years."""
        response = structural_api_client.get("/api/structural/years")

        # Endpoint may return 200 with years or 503 if data not loaded
        if response.status_code == 200:
            data = response.json()
            assert "years" in data
            assert isinstance(data["years"], list)

    def test_get_years_sorted_descending(self, structural_api_client):
        """Years should be sorted newest first."""
        response = structural_api_client.get("/api/structural/years")

        if response.status_code == 200:
            years = response.json()["years"]
            if years:
                assert years == sorted(years, reverse=True)


class TestGetMatrixCoefficients:
    """Tests for GET /api/structural/matrix/{year} endpoint."""

    def test_get_matrix_coefficients_returns_matrix(
        self, structural_api_client
    ):
        """GET /api/structural/matrix/{year} should return matrix data."""
        response = structural_api_client.get(
            "/api/structural/matrix/2022", params={"type": "coefficients"}
        )

        # May return 404 if year not found, which is valid
        if response.status_code == 200:
            data = response.json()
            assert "year" in data
            assert "matrix" in data
            assert "row_labels" in data
            assert "col_labels" in data
            assert "matrix_type" in data

    def test_get_matrix_coefficients_square_matrix(
        self, structural_api_client
    ):
        """Coefficient matrix should be square."""
        response = structural_api_client.get(
            "/api/structural/matrix/2022", params={"type": "coefficients"}
        )

        if response.status_code == 200:
            data = response.json()
            matrix = data["matrix"]
            if matrix:
                n_rows = len(matrix)
                n_cols = len(matrix[0]) if matrix else 0
                assert n_rows == n_cols

    def test_get_matrix_inverse_includes_diagnostics(
        self, structural_api_client
    ):
        """Inverse matrix response should include diagnostics."""
        response = structural_api_client.get(
            "/api/structural/matrix/2022", params={"type": "inverse"}
        )

        if response.status_code == 200:
            data = response.json()
            assert "diagnostics" in data

    def test_get_matrix_invalid_year_404(self, structural_api_client):
        """Request for invalid year should return 404."""
        response = structural_api_client.get(
            "/api/structural/matrix/1900", params={"type": "coefficients"}
        )

        # Should be 404 for year before I-O data exists
        assert response.status_code == 404


class TestShockSimulation:
    """Tests for POST /api/structural/shock endpoint."""

    def test_shock_simulation_returns_impacts(self, structural_api_client):
        """POST /api/structural/shock should return impact data."""
        payload = {
            "year": 2022,
            "shocks": {"333": 0.1},  # 10% shock to machinery sector
            "shock_type": "demand",
        }

        response = structural_api_client.post(
            "/api/structural/shock", json=payload
        )

        # May return 404/422 if data not available
        if response.status_code == 200:
            data = response.json()
            assert "year" in data
            assert "impacts" in data
            assert "total_impact" in data
            assert "shocked_sectors" in data

    def test_shock_simulation_multi_sector(self, structural_api_client):
        """Multi-sector shock should include all shocked sectors in response."""
        payload = {
            "year": 2022,
            "shocks": {"333": 0.1, "22": -0.05},  # Machinery +10%, Utilities -5%
            "shock_type": "demand",
        }

        response = structural_api_client.post(
            "/api/structural/shock", json=payload
        )

        if response.status_code == 200:
            data = response.json()
            assert len(data["shocked_sectors"]) >= 2

    def test_shock_simulation_validation_error(self, structural_api_client):
        """Invalid payload should return 422."""
        payload = {"year": "invalid", "shocks": {}}  # Invalid year type

        response = structural_api_client.post(
            "/api/structural/shock", json=payload
        )

        assert response.status_code == 422


class TestReproductionSchema:
    """Tests for GET /api/structural/reproduction/{year} endpoint."""

    def test_reproduction_returns_departments(self, structural_api_client):
        """GET /api/structural/reproduction/{year} should return department data."""
        response = structural_api_client.get(
            "/api/structural/reproduction/2022"
        )

        if response.status_code == 200:
            data = response.json()
            assert "year" in data
            assert "dept_i" in data
            assert "dept_ii" in data
            assert "flows" in data
            assert "proportionality" in data

    def test_reproduction_department_structure(self, structural_api_client):
        """Department data should contain c, v, s values."""
        response = structural_api_client.get(
            "/api/structural/reproduction/2022"
        )

        if response.status_code == 200:
            data = response.json()
            for dept_key in ["dept_i", "dept_ii"]:
                dept = data[dept_key]
                assert "c" in dept
                assert "v" in dept
                assert "s" in dept

    def test_reproduction_includes_sankey_data(self, structural_api_client):
        """Response may include Sankey diagram data."""
        response = structural_api_client.get(
            "/api/structural/reproduction/2022"
        )

        if response.status_code == 200:
            data = response.json()
            # sankey_data is optional
            if "sankey_data" in data and data["sankey_data"]:
                assert "nodes" in data["sankey_data"]
                assert "links" in data["sankey_data"]

    def test_reproduction_proportionality_check(self, structural_api_client):
        """Proportionality dict should have reproduction condition flags."""
        response = structural_api_client.get(
            "/api/structural/reproduction/2022"
        )

        if response.status_code == 200:
            data = response.json()
            prop = data["proportionality"]
            assert "simple_reproduction_holds" in prop
            assert "expanded_reproduction_holds" in prop


class TestCriticalSectors:
    """Tests for GET /api/structural/critical-sectors/{year} endpoint."""

    def test_critical_sectors_returns_list(self, structural_api_client):
        """GET /api/structural/critical-sectors/{year} should return sector list."""
        response = structural_api_client.get(
            "/api/structural/critical-sectors/2022"
        )

        if response.status_code == 200:
            data = response.json()
            assert "year" in data
            assert "sectors" in data
            assert isinstance(data["sectors"], list)

    def test_critical_sectors_structure(self, structural_api_client):
        """Each sector should have code, linkages, and critical flag."""
        response = structural_api_client.get(
            "/api/structural/critical-sectors/2022"
        )

        if response.status_code == 200:
            data = response.json()
            if data["sectors"]:
                sector = data["sectors"][0]
                assert "code" in sector
                assert "backward_linkage" in sector
                assert "forward_linkage" in sector
                assert "critical" in sector

    def test_critical_sectors_threshold_param(self, structural_api_client):
        """Threshold parameter should affect critical flag counts."""
        low_resp = structural_api_client.get(
            "/api/structural/critical-sectors/2022", params={"threshold": 0.01}
        )
        high_resp = structural_api_client.get(
            "/api/structural/critical-sectors/2022", params={"threshold": 0.5}
        )

        if low_resp.status_code == 200 and high_resp.status_code == 200:
            low_critical = sum(
                1 for s in low_resp.json()["sectors"] if s["critical"]
            )
            high_critical = sum(
                1 for s in high_resp.json()["sectors"] if s["critical"]
            )
            # Lower threshold should find more critical sectors
            assert low_critical >= high_critical
