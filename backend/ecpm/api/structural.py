"""Structural analysis API endpoints for I-O data and computations.

Provides:
- GET /api/structural/years -- Available I-O table years
- GET /api/structural/matrix/{year} -- Technical coefficients or Leontief inverse
- POST /api/structural/shock -- Shock propagation simulation
- GET /api/structural/reproduction/{year} -- Department I/II flows and proportionality
- GET /api/structural/critical-sectors/{year} -- Critical sector identification
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Optional

import numpy as np
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.cache import build_cache_key, cache_get, cache_set
from ecpm.database import get_db
from ecpm.models.io_table import IOCell, IOMetadata
from ecpm.schemas.structural import (
    CriticalSector,
    CriticalSectorsResponse,
    DepartmentValues,
    MatrixResponse,
    ProportionalityCheck,
    ReproductionResponse,
    SankeyData,
    SankeyLink,
    SankeyNode,
    ShockImpact,
    ShockRequest,
    ShockResultResponse,
    YearsResponse,
)
from ecpm.structural import (
    check_stability,
    classify_departments,
    compute_backward_linkages,
    compute_forward_linkages,
    compute_leontief_inverse,
    compute_reproduction_flows,
    compute_technical_coefficients,
    find_critical_sectors,
    simulate_multi_sector_shock,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/structural", tags=["structural"])

# Cache TTLs (I-O data is annual, rarely changes)
_MATRIX_CACHE_TTL = 86400  # 24 hours
_SIMULATION_CACHE_TTL = 3600  # 1 hour


def _get_redis():
    """Return the Redis client from app state, or None if unavailable."""
    try:
        from ecpm.main import _redis_pool
        return _redis_pool
    except (ImportError, AttributeError):
        return None


async def _get_matrix_from_db(
    year: int,
    table_type: str,
    db: AsyncSession,
) -> tuple[np.ndarray, list[str], list[str]] | None:
    """Load matrix from database.

    Args:
        year: Year to load.
        table_type: Type of table ("use", "make", "coefficients").
        db: Database session.

    Returns:
        Tuple of (matrix, row_labels, col_labels) or None if not found.
    """
    # Query cells for this year and table type
    stmt = select(IOCell).where(
        IOCell.year == year,
        IOCell.table_type == table_type,
    )
    result = await db.execute(stmt)
    cells = result.scalars().all()

    if not cells:
        return None

    # Get unique row and column codes
    row_codes = sorted(set(c.row_code for c in cells))
    col_codes = sorted(set(c.col_code for c in cells))

    # Build matrix
    n_rows = len(row_codes)
    n_cols = len(col_codes)
    matrix = np.zeros((n_rows, n_cols))

    row_idx = {code: i for i, code in enumerate(row_codes)}
    col_idx = {code: i for i, code in enumerate(col_codes)}

    for cell in cells:
        i = row_idx.get(cell.row_code)
        j = col_idx.get(cell.col_code)
        if i is not None and j is not None:
            matrix[i, j] = cell.value

    return matrix, row_codes, col_codes


async def _get_available_years(db: AsyncSession) -> list[int]:
    """Get list of years with I-O data in database."""
    stmt = select(IOMetadata.year).distinct().order_by(IOMetadata.year.desc())
    result = await db.execute(stmt)
    years = [row[0] for row in result.fetchall()]
    return years


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/years", response_model=YearsResponse)
async def get_years(
    db: AsyncSession = Depends(get_db),
) -> YearsResponse:
    """Return list of years with available I-O data.

    Returns years sorted descending (newest first).
    """
    redis = _get_redis()
    cache_key = build_cache_key("structural/years", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.years.cache_hit", key=cache_key)
        return YearsResponse.model_validate_json(cached)

    # Query database
    years = await _get_available_years(db)

    # If no data in DB, return default range for API exploration
    if not years:
        # Return placeholder years (actual data requires BEA ingestion)
        years = list(range(2022, 1996, -1))

    response = YearsResponse(years=years)

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_MATRIX_CACHE_TTL, redis=redis
    )

    return response


@router.get("/matrix/{year}", response_model=MatrixResponse)
async def get_matrix(
    year: int,
    matrix_type: str = Query(
        "coefficients",
        alias="type",
        description="Matrix type: coefficients, inverse, or flows",
    ),
    db: AsyncSession = Depends(get_db),
) -> MatrixResponse:
    """Return I-O matrix for a given year.

    Matrix types:
    - coefficients: Technical coefficient matrix A
    - inverse: Leontief inverse L = (I - A)^-1 with diagnostics
    - flows: Department I/II aggregated 2x2 flows

    Returns 404 if year not found.
    """
    if matrix_type not in ("coefficients", "inverse", "flows"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid matrix type: {matrix_type}. Must be coefficients, inverse, or flows.",
        )

    redis = _get_redis()
    cache_key = build_cache_key(f"structural/matrix/{year}/{matrix_type}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.matrix.cache_hit", key=cache_key)
        return MatrixResponse.model_validate_json(cached)

    # Try to load from database
    data = await _get_matrix_from_db(year, "coefficients", db)

    if data is None:
        # No data for this year
        raise HTTPException(
            status_code=404,
            detail=f"No I-O data available for year {year}",
        )

    matrix, row_labels, col_labels = data
    diagnostics = None

    if matrix_type == "inverse":
        # Compute Leontief inverse
        L, diag = compute_leontief_inverse(matrix)
        if L is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to compute Leontief inverse (singular matrix)",
            )
        matrix = L
        diagnostics = diag

    elif matrix_type == "flows":
        # Aggregate to Department I/II
        classification = classify_departments(row_labels)
        # Create simple aggregation
        dept_i_rows = [i for i, c in enumerate(row_labels) if classification.get(c) == "Dept_I"]
        dept_ii_rows = [i for i, c in enumerate(row_labels) if classification.get(c) == "Dept_II"]

        flows = np.array([
            [matrix[np.ix_(dept_i_rows, dept_i_rows)].sum() if dept_i_rows else 0,
             matrix[np.ix_(dept_i_rows, dept_ii_rows)].sum() if dept_i_rows and dept_ii_rows else 0],
            [matrix[np.ix_(dept_ii_rows, dept_i_rows)].sum() if dept_ii_rows and dept_i_rows else 0,
             matrix[np.ix_(dept_ii_rows, dept_ii_rows)].sum() if dept_ii_rows else 0],
        ])

        matrix = flows
        row_labels = ["Dept_I", "Dept_II"]
        col_labels = ["Dept_I", "Dept_II"]

    response = MatrixResponse(
        year=year,
        matrix=matrix.tolist(),
        row_labels=row_labels,
        col_labels=col_labels,
        matrix_type=matrix_type,
        diagnostics=diagnostics,
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_MATRIX_CACHE_TTL, redis=redis
    )

    return response


@router.post("/shock", response_model=ShockResultResponse)
async def simulate_shock_endpoint(
    request: ShockRequest,
    db: AsyncSession = Depends(get_db),
) -> ShockResultResponse:
    """Simulate shock propagation through Leontief inverse.

    Accepts sector codes and shock magnitudes, computes economy-wide impacts.
    """
    redis = _get_redis()

    # Create cache key from request hash
    request_hash = hashlib.sha256(request.model_dump_json().encode()).hexdigest()[:16]
    cache_key = build_cache_key(f"structural/shock/{request_hash}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.shock.cache_hit", key=cache_key)
        return ShockResultResponse.model_validate_json(cached)

    # Load coefficient matrix for the year
    data = await _get_matrix_from_db(request.year, "coefficients", db)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No I-O data available for year {request.year}",
        )

    A, sector_codes, _ = data

    # Compute Leontief inverse
    L, diagnostics = compute_leontief_inverse(A)
    if L is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to compute Leontief inverse",
        )

    # Map sector codes to indices
    code_to_idx = {code: i for i, code in enumerate(sector_codes)}
    shocks_indexed = {}
    for code, magnitude in request.shocks.items():
        if code in code_to_idx:
            shocks_indexed[code_to_idx[code]] = magnitude

    if not shocks_indexed:
        raise HTTPException(
            status_code=400,
            detail="No valid sector codes found in shocks",
        )

    # Run simulation
    result = simulate_multi_sector_shock(
        L=L,
        shocks=shocks_indexed,
        sector_codes=sector_codes,
    )

    # Build response
    impacts = [
        ShockImpact(
            sector=item["sector"],
            code=item["code"],
            impact=item["impact"],
        )
        for item in result["ranked_impacts"]
    ]

    response = ShockResultResponse(
        year=request.year,
        impacts=impacts,
        total_impact=result["total_impact"],
        shocked_sectors=list(request.shocks.keys()),
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_SIMULATION_CACHE_TTL, redis=redis
    )

    return response


@router.get("/reproduction/{year}", response_model=ReproductionResponse)
async def get_reproduction_schema(
    year: int,
    db: AsyncSession = Depends(get_db),
) -> ReproductionResponse:
    """Return Department I/II reproduction schema for a year.

    Includes c/v/s decomposition, inter-department flows, and
    proportionality condition checks.
    """
    redis = _get_redis()
    cache_key = build_cache_key(f"structural/reproduction/{year}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.reproduction.cache_hit", key=cache_key)
        return ReproductionResponse.model_validate_json(cached)

    # Load matrix
    data = await _get_matrix_from_db(year, "coefficients", db)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No I-O data available for year {year}",
        )

    A, sector_codes, _ = data

    # Classify sectors
    classification = classify_departments(sector_codes)

    # Compute reproduction flows
    # Note: This uses simplified value-added approximation
    # Proper implementation would load value-added data from GDPbyIndustry
    n = A.shape[0]
    value_added = np.ones(n) * 100  # Placeholder - would come from actual data

    flows_result = compute_reproduction_flows(
        use_matrix=A,  # Using coefficients as proxy
        value_added=value_added,
        classification=classification,
        sector_codes=sector_codes,
    )

    # Build Sankey data
    sankey_nodes = [
        SankeyNode(id="Dept_I", label="Department I (Means of Production)"),
        SankeyNode(id="Dept_II", label="Department II (Means of Consumption)"),
    ]

    # Flows: I->II represents I(v+s), II->I represents II(c) demand
    prop = flows_result["proportionality"]
    condition_color = "green" if prop["condition_met"] else "red"

    sankey_links = [
        SankeyLink(
            source="Dept_I",
            target="Dept_II",
            value=prop["i_v_plus_s"],
            color=condition_color,
        ),
        SankeyLink(
            source="Dept_II",
            target="Dept_I",
            value=prop["ii_c"],
            color=condition_color,
        ),
    ]

    sankey_data = SankeyData(nodes=sankey_nodes, links=sankey_links)

    response = ReproductionResponse(
        year=year,
        dept_i=DepartmentValues(
            c=flows_result["dept_i"]["c"],
            v=flows_result["dept_i"]["v"],
            s=flows_result["dept_i"]["s"],
        ),
        dept_ii=DepartmentValues(
            c=flows_result["dept_ii"]["c"],
            v=flows_result["dept_ii"]["v"],
            s=flows_result["dept_ii"]["s"],
        ),
        flows=flows_result["flows"],
        proportionality=ProportionalityCheck(
            i_v_plus_s=prop["i_v_plus_s"],
            ii_c=prop["ii_c"],
            simple_reproduction_holds=prop["simple_reproduction_holds"],
            expanded_reproduction_holds=prop["expanded_reproduction_holds"],
            surplus_ratio=prop["surplus_ratio"],
            formula_display=prop["formula_display"],
            condition_met=prop["condition_met"],
        ),
        sankey_data=sankey_data,
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_MATRIX_CACHE_TTL, redis=redis
    )

    return response


@router.get("/critical-sectors/{year}", response_model=CriticalSectorsResponse)
async def get_critical_sectors(
    year: int,
    threshold: float = Query(0.1, description="Criticality threshold"),
    db: AsyncSession = Depends(get_db),
) -> CriticalSectorsResponse:
    """Identify critical sectors based on Leontief multipliers.

    Critical sectors have output multipliers significantly above average.
    """
    redis = _get_redis()
    cache_key = build_cache_key(f"structural/critical/{year}/{threshold}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.critical.cache_hit", key=cache_key)
        return CriticalSectorsResponse.model_validate_json(cached)

    # Load matrix
    data = await _get_matrix_from_db(year, "coefficients", db)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No I-O data available for year {year}",
        )

    A, sector_codes, _ = data

    # Compute Leontief inverse
    L, _ = compute_leontief_inverse(A)
    if L is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to compute Leontief inverse",
        )

    # Find critical sectors
    critical_result = find_critical_sectors(
        L=L,
        sector_codes=sector_codes,
        threshold=threshold,
    )

    # Compute linkages
    backward = compute_backward_linkages(L, sector_codes)
    forward = compute_forward_linkages(L, sector_codes)

    # Build response
    sectors = []
    for item in critical_result:
        code = item["code"]
        sectors.append(
            CriticalSector(
                code=code,
                name=item.get("name"),
                backward_linkage=float(backward.get(code, 0)),
                forward_linkage=float(forward.get(code, 0)),
                multiplier=item.get("multiplier"),
                critical=item["critical"],
            )
        )

    response = CriticalSectorsResponse(
        year=year,
        sectors=sectors,
        threshold=threshold,
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_MATRIX_CACHE_TTL, redis=redis
    )

    return response
