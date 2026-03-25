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
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecpm.middleware.rate_limit import RATE_READ, RATE_WRITE, limiter

from ecpm.cache import build_cache_key, cache_get, cache_set
from ecpm.database import get_db
from ecpm.models.io_table import IOCell
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
) -> tuple[np.ndarray, list[str], list[str], list[str], list[str]] | None:
    """Load matrix from database.

    Args:
        year: Year to load.
        table_type: Type of table ("use", "make", "coefficients").
        db: Database session.

    Returns:
        Tuple of (matrix, row_labels, col_labels, row_display, col_display)
        or None if not found. Display lists use BEA descriptions when stored.
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
    row_codes = sorted(set(str(c.row_code) for c in cells))
    col_codes = sorted(set(str(c.col_code) for c in cells))

    row_desc_first: dict[str, str] = {}
    col_desc_first: dict[str, str] = {}
    for cell in cells:
        rc = str(cell.row_code)
        cc = str(cell.col_code)
        if cell.row_description and rc not in row_desc_first:
            row_desc_first[rc] = str(cell.row_description).strip()
        if cell.col_description and cc not in col_desc_first:
            col_desc_first[cc] = str(cell.col_description).strip()

    row_display = [row_desc_first.get(r, r) for r in row_codes]
    col_display = [col_desc_first.get(c, c) for c in col_codes]

    # Build matrix
    n_rows = len(row_codes)
    n_cols = len(col_codes)
    matrix = np.zeros((n_rows, n_cols))

    row_idx = {code: i for i, code in enumerate(row_codes)}
    col_idx = {code: i for i, code in enumerate(col_codes)}

    for cell in cells:
        rc = str(cell.row_code)
        cc = str(cell.col_code)
        i = row_idx.get(rc)
        j = col_idx.get(cc)
        if i is not None and j is not None:
            matrix[i, j] = cell.value

    return matrix, row_codes, col_codes, row_display, col_display


async def _get_available_years(db: AsyncSession) -> list[int]:
    """Years that have stored coefficient matrix cells (same source as matrix/shock/critical)."""
    stmt = (
        select(IOCell.year)
        .where(IOCell.table_type == "coefficients")
        .distinct()
        .order_by(IOCell.year.desc())
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]


def _square_matrix(
    matrix: np.ndarray,
    row_labels: list[str],
    col_labels: list[str],
) -> tuple[np.ndarray, list[str]]:
    """Extract the square submatrix using codes common to both rows and cols.

    BEA Use tables are non-square (e.g., 80 commodity rows x 92 industry cols).
    Leontief inverse requires a square matrix, so we intersect row/col codes.
    """
    common = [c for c in row_labels if c in set(col_labels)]
    if not common:
        return matrix, row_labels

    row_idx = {c: i for i, c in enumerate(row_labels)}
    col_idx = {c: i for i, c in enumerate(col_labels)}

    ri = [row_idx[c] for c in common]
    ci = [col_idx[c] for c in common]

    return matrix[np.ix_(ri, ci)], common


def _axis_display_for_common(
    common: list[str],
    ordered_codes: list[str],
    axis_display: list[str],
) -> list[str]:
    """Reorder per-axis display strings to match ``common`` (square submatrix)."""
    idx = {c: i for i, c in enumerate(ordered_codes)}
    out: list[str] = []
    for code in common:
        i = idx.get(code)
        if i is None or i >= len(axis_display):
            out.append(code)
        else:
            out.append(axis_display[i])
    return out


def _looks_like_coefficient_matrix(matrix: np.ndarray) -> bool:
    """Return True if values look like a technical-coefficient matrix, not dollar flows.

    BEA summary Use tables in millions of dollars have many cells well above 1.
    Coefficients are bounded (typically well below 2 per cell). Mis-labeled
    coefficient data stored as ``table_type="use"`` would otherwise be treated
    as dollars and confuse c vs v/s units.
    """
    if matrix.size == 0:
        return True
    return bool(np.nanmax(np.abs(matrix)) <= 2.0 + 1e-9)


async def _load_value_added(
    year: int,
    n_sectors: int,
    db: AsyncSession,
    *,
    use_millions: bool = True,
) -> np.ndarray:
    """Load aggregate value-added data and distribute across sectors.

    Queries FRED compensation (A576RC1) and net operating surplus
    (W209RC1Q156SBEA) for the nearest available year, then distributes
    proportionally across sectors using the I-O coefficient column sums
    as weights. Falls back to uniform distribution if no data is available.

    Args:
        use_millions: If True, scale FRED billions to millions (for BEA Use tables
            in millions of dollars). If False, keep billions per sector.

    Returns:
        n-vector of per-sector value added estimates.
    """
    import datetime as dt

    from ecpm.models.observation import Observation

    compensation_total = None
    surplus_total = None

    # Find the closest observation to the target year for each series
    target_start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
    target_end = dt.datetime(year, 12, 31, tzinfo=dt.timezone.utc)

    for series_id, attr in [("A576RC1", "compensation"), ("W209RC1Q156SBEA", "surplus")]:
        stmt = (
            select(Observation.value)
            .where(
                Observation.series_id == series_id,
                Observation.observation_date >= target_start,
                Observation.observation_date <= target_end,
                Observation.value.is_not(None),
            )
            .order_by(Observation.observation_date.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            # Try the closest year before
            stmt_fallback = (
                select(Observation.value)
                .where(
                    Observation.series_id == series_id,
                    Observation.observation_date <= target_end,
                    Observation.value.is_not(None),
                )
                .order_by(Observation.observation_date.desc())
                .limit(1)
            )
            result_fb = await db.execute(stmt_fallback)
            row = result_fb.scalar_one_or_none()

        if row is not None:
            if attr == "compensation":
                compensation_total = float(row)
            else:
                surplus_total = float(row)

    if compensation_total is not None and surplus_total is not None:
        total_va_billions = compensation_total + surplus_total
        scale = 1000.0 if use_millions else 1.0
        total_va = total_va_billions * scale
        value_added = np.full(n_sectors, total_va / n_sectors)
    else:
        logger.warning(
            "structural.reproduction.value_added_fallback",
            year=year,
            compensation_available=compensation_total is not None,
            surplus_available=surplus_total is not None,
        )
        value_added = np.ones(n_sectors) * 100

    return value_added


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/years", response_model=YearsResponse)
@limiter.limit(RATE_READ)
async def get_years(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> YearsResponse:
    """Return years that have coefficient I-O cells (newest first).

    Empty when no BEA I-O ingestion has been run. No placeholder years.
    """
    redis = _get_redis()
    cache_key = build_cache_key("structural/years/v2", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.years.cache_hit", key=cache_key)
        return YearsResponse.model_validate_json(cached)

    years = await _get_available_years(db)
    response = YearsResponse(years=years)

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_MATRIX_CACHE_TTL, redis=redis
    )

    return response


@router.get("/matrix/{year}", response_model=MatrixResponse)
@limiter.limit(RATE_READ)
async def get_matrix(
    request: Request,
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

    matrix, row_labels, col_labels, row_disp, col_disp = data
    diagnostics = None

    if matrix_type == "inverse":
        # BEA Use tables may be non-square; square for Leontief inverse
        sq_matrix, sq_codes = _square_matrix(matrix, row_labels, col_labels)
        L, diag = compute_leontief_inverse(sq_matrix)
        if L is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to compute Leontief inverse (singular matrix)",
            )
        matrix = L
        row_labels = sq_codes
        col_labels = sq_codes
        row_disp = _axis_display_for_common(sq_codes, data[1], data[3])
        col_disp = _axis_display_for_common(sq_codes, data[2], data[4])
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
        _dept_labels = [
            "Department I (means of production)",
            "Department II (means of consumption)",
        ]
        row_disp = list(_dept_labels)
        col_disp = list(_dept_labels)

    response = MatrixResponse(
        year=year,
        matrix=matrix.tolist(),
        row_labels=row_labels,
        col_labels=col_labels,
        matrix_type=matrix_type,
        diagnostics=diagnostics,
        row_display_labels=row_disp,
        col_display_labels=col_disp,
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_MATRIX_CACHE_TTL, redis=redis
    )

    return response


@router.post("/shock", response_model=ShockResultResponse)
@limiter.limit(RATE_WRITE)
async def simulate_shock_endpoint(
    request: Request,
    shock_request: ShockRequest,
    db: AsyncSession = Depends(get_db),
) -> ShockResultResponse:
    """Simulate shock propagation through Leontief inverse.

    Accepts sector codes and shock magnitudes, computes economy-wide impacts.
    """
    redis = _get_redis()

    # Create cache key from request hash
    request_hash = hashlib.sha256(shock_request.model_dump_json().encode()).hexdigest()[:16]
    cache_key = build_cache_key(f"structural/shock/{request_hash}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.shock.cache_hit", key=cache_key)
        return ShockResultResponse.model_validate_json(cached)

    # Load coefficient matrix for the year
    data = await _get_matrix_from_db(shock_request.year, "coefficients", db)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No I-O data available for year {shock_request.year}",
        )

    A_raw, row_labels, col_labels, _, _ = data

    # BEA Use tables may be non-square; square for Leontief inverse
    A, sector_codes = _square_matrix(A_raw, row_labels, col_labels)

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
    for code, magnitude in shock_request.shocks.items():
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
        year=shock_request.year,
        impacts=impacts,
        total_impact=result["total_impact"],
        shocked_sectors=list(shock_request.shocks.keys()),
    )

    # Cache the response
    await cache_set(
        cache_key, response.model_dump_json(), ttl=_SIMULATION_CACHE_TTL, redis=redis
    )

    return response


@router.get("/reproduction/{year}", response_model=ReproductionResponse)
@limiter.limit(RATE_READ)
async def get_reproduction_schema(
    request: Request,
    year: int,
    db: AsyncSession = Depends(get_db),
) -> ReproductionResponse:
    """Return Department I/II reproduction schema for a year.

    Includes c/v/s decomposition, inter-department flows, and
    proportionality condition checks.
    """
    redis = _get_redis()
    cache_key = build_cache_key(f"structural/reproduction/v2/{year}", {})

    # Try cache first
    cached = await cache_get(cache_key, redis=redis)
    if cached is not None:
        logger.debug("structural.reproduction.cache_hit", key=cache_key)
        return ReproductionResponse.model_validate_json(cached)

    # Prefer the dollar-flow Use table for c and flows in millions of dollars.
    # Reject rows that look like technical coefficients (mis-ingested data).
    # Fall back to the coefficient matrix if needed.
    use_data = await _get_matrix_from_db(year, "use", db)
    coeff_data = await _get_matrix_from_db(year, "coefficients", db)

    if use_data is None and coeff_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No I-O data available for year {year}",
        )

    use_matrix_raw = use_data[0] if use_data else None
    use_is_dollar = (
        use_data is not None and not _looks_like_coefficient_matrix(use_matrix_raw)
    )
    if use_data is not None and not use_is_dollar:
        logger.warning(
            "structural.reproduction.use_table_looks_like_coefficients",
            year=year,
            max_cell=float(np.nanmax(np.abs(use_matrix_raw))),
        )

    is_dollar_flows = use_is_dollar
    if is_dollar_flows:
        raw_matrix, row_labels, col_labels = (
            use_data[0],
            use_data[1],
            use_data[2],
        )
    else:
        if coeff_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No coefficient I-O data available for year {year}",
            )
        raw_matrix, row_labels, col_labels = (
            coeff_data[0],
            coeff_data[1],
            coeff_data[2],
        )

    # BEA Use tables may be non-square; square for analysis
    sq_matrix, sector_codes = _square_matrix(raw_matrix, row_labels, col_labels)

    # Classify sectors
    classification = classify_departments(sector_codes)

    # Value added: millions when paired with dollar Use; billions when using A only.
    n = sq_matrix.shape[0]
    value_added = await _load_value_added(
        year, n, db, use_millions=is_dollar_flows
    )

    flows_result = compute_reproduction_flows(
        use_matrix=sq_matrix,
        value_added=value_added,
        classification=classification,
        sector_codes=sector_codes,
        is_dollar_flows=is_dollar_flows,
    )

    # Build Sankey data with 4 nodes (produced / bought split per department)
    # to avoid circular links, which Sankey diagrams cannot represent.
    sankey_nodes = [
        SankeyNode(id="I_prod", label="Machinery & Materials produced"),
        SankeyNode(id="II_prod", label="Consumer Goods produced"),
        SankeyNode(id="I_buy", label="Bought by Dept I"),
        SankeyNode(id="II_buy", label="Bought by Dept II"),
    ]

    flow_matrix = flows_result["flows"]
    sankey_links = [
        l
        for l in [
            SankeyLink(source="I_prod", target="I_buy", value=flow_matrix[0][0]),
            SankeyLink(source="I_prod", target="II_buy", value=flow_matrix[0][1]),
            SankeyLink(source="II_prod", target="I_buy", value=flow_matrix[1][0]),
            SankeyLink(source="II_prod", target="II_buy", value=flow_matrix[1][1]),
        ]
        if l.value > 0
    ]

    sankey_data = SankeyData(nodes=sankey_nodes, links=sankey_links)

    prop = flows_result["proportionality"]
    if is_dollar_flows:
        c_unit = "millions_of_dollars"
        vs_unit = "millions_of_dollars"
    else:
        c_unit = "coefficient_column_sum"
        vs_unit = "billions_of_dollars"

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
        constant_capital_unit=c_unit,
        labor_and_surplus_unit=vs_unit,
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
@limiter.limit(RATE_READ)
async def get_critical_sectors(
    request: Request,
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

    A, row_labels, col_labels, _, _ = data

    # BEA Use tables may be non-square; extract square submatrix
    A_sq, sector_codes = _square_matrix(A, row_labels, col_labels)

    # Compute Leontief inverse
    L, _ = compute_leontief_inverse(A_sq)
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
