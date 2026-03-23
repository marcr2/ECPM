# Phase 4: Structural Analysis - Research

**Researched:** 2026-03-23
**Domain:** Leontief input-output analysis, BEA I-O table ingestion, matrix computation, interactive heatmap/Sankey visualization
**Confidence:** MEDIUM-HIGH

## Summary

Phase 4 adds inter-industry structural analysis to ECPM: ingesting BEA Input-Output tables via the existing BEA API client, computing the Leontief technical coefficient matrix and its inverse, simulating shock propagation through the production network, and aggregating sectors into Marx's Department I/II reproduction schema with proportionality condition checks. The frontend delivers an interactive heatmap (71x71 technical coefficients), shock simulation controls with result visualization, and a Sankey diagram for reproduction schema flows.

The BEA API exposes I-O data through its `InputOutput` dataset, which accepts `TableID` and `Year` parameters. The project already has a working BEA client with httpx fallback and retry logic that can be extended with a new `fetch_io_table()` method. The backend computation stack is NumPy (already installed) for matrix operations. The frontend uses React 19.2.4 + Next.js 16.2.1 + shadcn/ui dark theme; Nivo 0.99.0 (supports React 19) provides both HeatMapCanvas (canvas-rendered, performant for 71x71 = 5041 cells) and Sankey components with theming support.

**Primary recommendation:** Extend the existing BEA client for InputOutput dataset queries, build a dedicated `ecpm/structural/` backend module for I-O computation (matrix construction, Leontief inverse, shock simulation, Department classification), expose via new FastAPI endpoints under `/api/structural/`, and use Nivo HeatMapCanvas + Nivo Sankey for frontend visualization with the established shadcn/ui dark theme.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Detailed 71-sector BEA I-O tables (not summary 15-sector)
- All available annual tables (~1997 onward) for time-series of structural change
- Extend existing BEA API client (`backend/ecpm/clients/bea.py`) using BEA InputOutput dataset endpoint
- Built-in canonical 71-to-2 Department I/II classification based on NAICS codes (manufacturing/mining/construction to Dept I, consumer goods/services to Dept II). Pre-defined, documented, not user-editable
- Aggregated overview (~15 sector groups) by default for heatmap, click a cell to drill down into detailed sub-sectors within that group
- Sequential single-hue color scale (dark to bright on dark theme) for coefficient magnitude
- Year selector dropdown to switch between annual I-O tables
- Hover tooltips showing exact coefficient value + sector names
- Three shock modes: (1) Multi-sector scenario builder, (2) Automatic "weakest link" with explanation of WHY that sector was chosen
- Shock results: ranked bar chart (largest impact first) + highlighted heatmap showing propagation path, side by side layout
- All computation server-side via backend API (NumPy/SciPy) -- frontend sends shock params, receives results
- Sankey diagram for Department I / Department II material flows
- Three toggleable depth levels for Sankey: (1) department-only (2 nodes), (2) department + top sub-sectors (default), (3) full 71-sector view
- Proportionality conditions (e.g., I(v+s) >= II(c)) displayed inline on the Sankey -- flows colored green/red based on whether conditions hold, with formula shown as tooltip
- Year selector dropdown on Sankey (same pattern as heatmap)

### Claude's Discretion
- Heatmap library choice (D3, Nivo, canvas-based -- prioritize rendering performance)
- Sankey library choice
- Backend module structure for I-O computation (matrix storage, caching strategy)
- API endpoint design for I-O data, shock simulation, and reproduction schema
- Exact NAICS-to-Department mapping table
- Numerical stability checks for Leontief inverse (condition number thresholds, Hawkins-Simon)
- Redis caching strategy for computed matrices and simulation results
- Sector ordering/grouping logic for the aggregated heatmap view

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STRC-01 | Ingest BEA input-output tables and compute Leontief technical coefficient matrix A | BEA InputOutput API (TableID/Year params), existing BEA client extension, NumPy A[i,j] = Z[i,j] / X[j] formula |
| STRC-02 | Compute Leontief inverse (I-A)^-1 with numerical stability checks (condition number, Hawkins-Simon) | numpy.linalg.inv + numpy.linalg.cond, Hawkins-Simon determinant check, spectral radius validation |
| STRC-03 | Simulate shock propagation through inter-industry structure using Leontief inverse | Delta_x = L @ Delta_d formula, output multiplier computation, multi-sector + weakest-link modes |
| STRC-04 | Aggregate sectors into Department I (means of production) and Department II (means of consumption) | NAICS-based 71-to-2 canonical mapping, BEA summary-level industry codes |
| STRC-05 | Check proportionality conditions for expanded reproduction (Marx Capital Vol. II) | Simple: c2 = v1+s1; Expanded: v1+s1 > c2; green/red flow coloring |
| DASH-07 | User can view Leontief I-O reproduction schema visualization (heatmap + Sankey/chord diagram) | Nivo HeatMapCanvas for 71x71 heatmap, Nivo Sankey for reproduction schema, React 19 compatible |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| NumPy | >=2.0 (already installed via pandas) | Matrix operations: technical coefficients, Leontief inverse, shock propagation | Standard for numerical linear algebra in Python; numpy.linalg.inv, numpy.linalg.cond |
| @nivo/heatmap | 0.99.0 | Canvas-rendered heatmap for 71x71 technical coefficient matrix | Canvas rendering handles 5041 cells without DOM overhead; React 19 compatible; built-in theming |
| @nivo/sankey | 0.99.0 | Sankey diagram for Department I/II material flows | D3-sankey based; React component with theming; same ecosystem as heatmap |
| Recharts | 3.8.0 (already installed) | Bar charts for shock simulation results | Already in project; consistent with Phase 2 patterns |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27 (already installed) | BEA API InputOutput dataset queries | Extend existing BEA client fallback path |
| beaapi | >=0.0.4 (already installed) | BEA API InputOutput dataset queries (primary) | Primary path in BEA client |
| Redis | (already configured) | Cache computed matrices and simulation results | Cache Leontief inverse (expensive), I-O tables, simulation results |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Nivo HeatMapCanvas | D3 custom canvas | D3 gives maximum control but requires hand-building tooltips, axes, interactions; Nivo provides these out of the box with React integration |
| Nivo HeatMapCanvas | ECharts | ECharts has excellent canvas/WebGL performance but is not already in the project ecosystem and has a different theming approach |
| Nivo Sankey | Recharts Sankey | Recharts Sankey exists but is less mature and has limited customization for link coloring (green/red conditions) |
| Nivo Sankey | D3-sankey direct | More flexible but requires manual React integration; Nivo wraps d3-sankey with React bindings |
| NumPy linalg.inv | SciPy sparse | For 71x71 dense matrix, NumPy dense inversion is fine; SciPy sparse would only help at 400+ sector detail level |

**Installation:**
```bash
# Backend: NumPy already available via pandas dependency. No new packages needed.
# Verify numpy is available:
python -c "import numpy; print(numpy.__version__)"

# Frontend:
cd frontend && npm install @nivo/heatmap@0.99.0 @nivo/sankey@0.99.0 @nivo/core@0.99.0
```

**Note on React 19 compatibility:** Nivo 0.99.0 officially supports React 19. The project uses React 19.2.4. If peer dependency warnings appear during install, they are safe to override -- the maintainer confirmed React 19 compatibility (GitHub issue #2618).

## Architecture Patterns

### Recommended Backend Module Structure
```
backend/ecpm/
├── structural/                 # NEW - I-O analysis module
│   ├── __init__.py             # Public API exports
│   ├── bea_io_client.py        # BEA InputOutput dataset fetching (extends BEAClient pattern)
│   ├── leontief.py             # Core computation: tech coefficients, inverse, stability checks
│   ├── shock.py                # Shock propagation: multi-sector, weakest-link
│   ├── departments.py          # Dept I/II classification, proportionality conditions
│   └── schemas.py              # Pydantic response models for I-O endpoints
├── api/
│   ├── structural.py           # NEW - FastAPI router for /api/structural/*
│   └── router.py               # MODIFIED - mount structural router
└── models/
    └── io_table.py             # NEW - SQLAlchemy model for I-O table storage
```

### Recommended Frontend Structure
```
frontend/src/
├── app/
│   └── structural/             # NEW - /structural route
│       ├── page.tsx            # Main structural analysis page (tab-based)
│       ├── layout.tsx          # Layout with year selector context
│       ├── loading.tsx         # Skeleton loading state
│       └── error.tsx           # Error boundary
├── components/
│   └── structural/             # NEW - structural analysis components
│       ├── coefficient-heatmap.tsx       # Nivo HeatMapCanvas wrapper
│       ├── heatmap-drill-down.tsx        # Detail view when cell clicked
│       ├── shock-simulator.tsx           # Shock mode controls
│       ├── shock-results.tsx             # Bar chart + highlighted heatmap
│       ├── reproduction-sankey.tsx       # Nivo Sankey wrapper
│       ├── proportionality-badge.tsx     # Green/red condition indicators
│       └── year-selector.tsx             # Year dropdown (reusable)
└── lib/
    └── structural.ts           # NEW - API client functions for structural endpoints
```

### Pattern 1: BEA InputOutput API Extension
**What:** Extend existing BEAClient to fetch InputOutput dataset tables
**When to use:** All I-O data ingestion
**Example:**
```python
# Source: BEA API User Guide (Feb 2026), existing BEAClient pattern
class BEAClient:
    # ... existing methods ...

    def fetch_io_table(
        self,
        table_id: int,
        year: str = "ALL",
    ) -> pd.DataFrame:
        """Fetch an Input-Output table from the BEA API.

        Args:
            table_id: InputOutput TableID (e.g., 259 for Use table summary level).
            year: Year or "ALL" for all available years.

        Returns:
            DataFrame with I-O data including RowCode, ColCode, DataValue, Year.
        """
        return self._api_request_io(
            table_id=table_id,
            year=year,
        )

    def _api_request_io(self, table_id: int, year: str) -> pd.DataFrame:
        """Make BEA InputOutput API request with retry logic."""
        self._throttle()
        try:
            import beaapi
            data = beaapi.get_data(
                self.api_key,
                datasetname="InputOutput",
                TableID=str(table_id),
                Year=year,
            )
        except ImportError:
            import httpx
            params = {
                "UserID": self.api_key,
                "method": "GetData",
                "datasetname": "InputOutput",
                "TableID": str(table_id),
                "Year": year,
                "ResultFormat": "JSON",
            }
            response = httpx.get(
                "https://apps.bea.gov/api/data/", params=params, timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            bea_data = result.get("BEAAPI", {}).get("Results", {}).get("Data", [])
            data = pd.DataFrame(bea_data) if bea_data else pd.DataFrame()
        return data
```

### Pattern 2: Leontief Computation Pipeline
**What:** Build technical coefficient matrix from Use table, compute inverse with stability checks
**When to use:** After ingesting I-O table data
**Example:**
```python
# Source: QuantEcon Input-Output Models, NumPy docs
import numpy as np

def build_technical_coefficients(use_matrix: np.ndarray, total_output: np.ndarray) -> np.ndarray:
    """Compute technical coefficient matrix A where A[i,j] = Z[i,j] / X[j].

    Args:
        use_matrix: n x n intermediate use matrix (Z)
        total_output: n-vector of total industry output (X)

    Returns:
        n x n technical coefficient matrix A
    """
    # Avoid division by zero for industries with zero output
    safe_output = np.where(total_output > 0, total_output, 1.0)
    A = use_matrix / safe_output[np.newaxis, :]
    return A


def compute_leontief_inverse(A: np.ndarray) -> tuple[np.ndarray, dict]:
    """Compute Leontief inverse L = (I - A)^{-1} with stability checks.

    Returns:
        Tuple of (Leontief inverse matrix, diagnostics dict)
    """
    n = A.shape[0]
    I = np.eye(n)
    B = I - A

    diagnostics = {}

    # Hawkins-Simon condition: all leading principal minors of (I-A) must be positive
    for k in range(1, n + 1):
        minor_det = np.linalg.det(B[:k, :k])
        if minor_det <= 0:
            diagnostics["hawkins_simon"] = False
            diagnostics["hawkins_simon_failure_at"] = k
            break
    else:
        diagnostics["hawkins_simon"] = True

    # Condition number check
    cond = np.linalg.cond(B)
    diagnostics["condition_number"] = float(cond)
    diagnostics["well_conditioned"] = cond < 1e10  # threshold for 71x71

    # Spectral radius of A must be < 1
    eigenvalues = np.linalg.eigvals(A)
    spectral_radius = float(np.max(np.abs(eigenvalues)))
    diagnostics["spectral_radius"] = spectral_radius
    diagnostics["convergent"] = spectral_radius < 1.0

    # Compute inverse
    L = np.linalg.inv(B)
    diagnostics["success"] = True

    return L, diagnostics
```

### Pattern 3: Shock Simulation
**What:** Compute impact of demand shocks through Leontief inverse
**When to use:** Multi-sector scenario and weakest-link modes
**Example:**
```python
# Source: QuantEcon I-O Models
def simulate_shock(
    L: np.ndarray,
    shock_vector: np.ndarray,
    sector_names: list[str],
) -> dict:
    """Simulate shock propagation through Leontief inverse.

    Args:
        L: Leontief inverse matrix (n x n)
        shock_vector: demand shock vector (n,) -- negative for contraction
        sector_names: list of sector names for labeling

    Returns:
        Dict with impact_vector, ranked_impacts, output_multipliers
    """
    impact = L @ shock_vector

    # Rank by absolute impact
    ranked_indices = np.argsort(np.abs(impact))[::-1]
    ranked_impacts = [
        {"sector": sector_names[i], "impact": float(impact[i])}
        for i in ranked_indices
    ]

    # Output multipliers (column sums of L)
    multipliers = L.sum(axis=0)

    return {
        "impact_vector": impact.tolist(),
        "ranked_impacts": ranked_impacts,
        "output_multipliers": multipliers.tolist(),
    }


def find_weakest_link(L: np.ndarray, sector_names: list[str]) -> dict:
    """Identify most vulnerable sector via Leontief inverse multipliers.

    The sector with the highest output multiplier propagates shocks
    most widely through the production network.
    """
    multipliers = L.sum(axis=0)
    vulnerability_ranking = np.argsort(multipliers)[::-1]

    # Also compute backward linkage (row sums) and forward linkage (col sums)
    backward_linkage = L.sum(axis=1)  # how much sector i depends on others
    forward_linkage = L.sum(axis=0)   # how much others depend on sector i

    weakest_idx = vulnerability_ranking[0]

    return {
        "weakest_sector": sector_names[weakest_idx],
        "weakest_index": int(weakest_idx),
        "multiplier": float(multipliers[weakest_idx]),
        "explanation": {
            "output_multiplier": float(multipliers[weakest_idx]),
            "backward_linkage": float(backward_linkage[weakest_idx]),
            "forward_linkage": float(forward_linkage[weakest_idx]),
            "dependency_count": int(np.sum(L[:, weakest_idx] > 0.01)),
        },
        "vulnerability_ranking": [
            {
                "sector": sector_names[i],
                "multiplier": float(multipliers[i]),
            }
            for i in vulnerability_ranking[:10]  # top 10
        ],
    }
```

### Pattern 4: Department I/II Classification
**What:** Map 71 BEA summary sectors to Department I (means of production) or Department II (means of consumption) and check proportionality conditions
**When to use:** Reproduction schema analysis
**Example:**
```python
# Department I: Industries producing means of production
# Department II: Industries producing means of consumption
# Based on BEA summary-level industry codes (NAICS-derived)

DEPT_I_CODES = {
    # Mining
    "211", "212", "213",
    # Utilities (power generation infrastructure)
    "22",
    # Construction
    "23",
    # Manufacturing - durable goods (machinery, equipment, metals)
    "321", "327", "331", "332", "333", "334", "335", "336",
    # Manufacturing - chemicals, plastics (industrial inputs)
    "325", "326",
    # Wholesale trade (intermediate distribution)
    "42",
    # Transportation and warehousing (means of circulation)
    "481", "482", "483", "484", "485", "486", "487OS", "493",
    # Information (telecommunications infrastructure)
    "511", "512", "513", "514",
}
# Department II: Everything not in Department I
# Consumer-facing services, retail, food, healthcare, education, etc.


def check_proportionality(
    dept_i_c: float, dept_i_v: float, dept_i_s: float,
    dept_ii_c: float, dept_ii_v: float, dept_ii_s: float,
) -> dict:
    """Check Marx's reproduction schema proportionality conditions.

    Simple reproduction: I(v+s) = II(c)
    Expanded reproduction: I(v+s) > II(c)

    Args:
        dept_i_c, dept_i_v, dept_i_s: Constant capital, variable capital,
            surplus value for Department I
        dept_ii_c, dept_ii_v, dept_ii_s: Same for Department II
    """
    i_vs = dept_i_v + dept_i_s
    ii_c = dept_ii_c

    return {
        "i_v_plus_s": float(i_vs),
        "ii_c": float(ii_c),
        "simple_reproduction_holds": abs(i_vs - ii_c) / max(ii_c, 1) < 0.05,
        "expanded_reproduction_holds": i_vs > ii_c,
        "surplus_ratio": float(i_vs / ii_c) if ii_c > 0 else None,
        "formula_display": f"I(v+s) = {i_vs:.1f}, II(c) = {ii_c:.1f}",
        "condition_met": i_vs >= ii_c,
    }
```

### Anti-Patterns to Avoid
- **SVG heatmap for 71x71:** 5041 DOM elements will cause sluggish interaction. Use canvas rendering (HeatMapCanvas).
- **Client-side matrix computation:** Sending raw I-O tables to the browser and computing Leontief inverse in JavaScript. Keep all matrix operations server-side.
- **Fetching all years at once from BEA:** BEA rate limits at 100 req/min with 1-hour timeout on violation. Fetch one year at a time with throttling; cache aggressively.
- **Storing raw BEA API responses in DB:** Parse into structured matrix format at ingestion time. The raw response has flat row/column data that needs reshaping.
- **Hard-coding sector ordering:** Use BEA's industry code ordering as canonical; derive groupings programmatically from the codes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Matrix inversion | Custom Gauss-Jordan elimination | `numpy.linalg.inv` | Numerically optimized LAPACK backend; handles edge cases |
| Condition number | Manual SVD computation | `numpy.linalg.cond` | Single function call with multiple norm support |
| Sankey diagram layout | Custom force-directed node positioning | `@nivo/sankey` (wraps d3-sankey) | Iterative relaxation algorithm with proper link ordering |
| Heatmap canvas rendering | Custom HTML5 Canvas drawing | `@nivo/heatmap` HeatMapCanvas | Built-in tooltips, axes, color scales, cell interactions |
| BEA API rate limiting | Custom rate limiter | Existing `_throttle()` method in BEAClient | Already battle-tested; 0.7s delay between calls |
| Color scale mapping | Manual value-to-color interpolation | Nivo's built-in sequential color schemes | Perceptually uniform scales, dark theme compatible |

**Key insight:** The Leontief model is standard linear algebra. The complexity is in data wrangling (BEA response format to matrix), proper stability checks, and visualization UX -- not in the math itself.

## Common Pitfalls

### Pitfall 1: BEA InputOutput Dataset Parameter Discovery
**What goes wrong:** The BEA API User Guide does not include the InputOutput appendix with TableID values. You must discover them programmatically via `GetParameterValues`.
**Why it happens:** The InputOutput dataset documentation is incomplete in the published PDF guide.
**How to avoid:** At development time, call `beaapi.get_parameter_values(key, "InputOutput", "TableID")` to discover available table IDs. The Use table at summary (71-industry) level is the key table needed. Cache the discovered table IDs.
**Warning signs:** Empty DataFrames returned, API errors about invalid TableID.

### Pitfall 2: BEA I-O Data Format Reshaping
**What goes wrong:** BEA API returns I-O data in long/flat format (one row per cell: RowCode, ColCode, DataValue). Building the 71x71 matrix requires pivoting.
**Why it happens:** API responses are flat tabular data, not matrix format.
**How to avoid:** Pivot using `pd.pivot_table(data, values='DataValue', index='RowCode', columns='ColCode')`. Handle missing cells (zero entries) explicitly. Parse DataValue strings to float (BEA returns strings with commas).
**Warning signs:** DataValue column contains strings like "1,234.5" not numeric floats.

### Pitfall 3: BEA API Rate Limiting (1-hour Timeout)
**What goes wrong:** Exceeding 100 req/min or 100MB/min results in HTTP 429 with a 1-hour timeout.
**Why it happens:** Fetching all years (~27 tables) in rapid succession without throttling.
**How to avoid:** Existing BEAClient has 0.7s rate limit delay. For bulk ingestion, add extra delay between year requests. Implement 429 detection with Retry-After header parsing. Cache all fetched data to avoid re-fetching.
**Warning signs:** HTTP 429 status code, Retry-After: 3600 header.

### Pitfall 4: Singular or Ill-Conditioned (I-A) Matrix
**What goes wrong:** `numpy.linalg.inv` raises `LinAlgError` or returns numerically garbage results.
**Why it happens:** Some sectors may have zero output in certain years, or data quality issues create near-singular matrices.
**How to avoid:** Check condition number before inversion (threshold ~1e10 for 71x71). Verify Hawkins-Simon conditions. Check spectral radius of A < 1. For borderline cases, use `numpy.linalg.solve` instead of explicit inversion.
**Warning signs:** Condition number > 1e12, negative values in Leontief inverse, Hawkins-Simon failure.

### Pitfall 5: Nivo Peer Dependency Warnings with React 19
**What goes wrong:** npm install shows peer dependency conflict warnings.
**Why it happens:** Nivo 0.99.0 peer dependency declarations may not explicitly list React 19.2.x even though it works.
**How to avoid:** Use `--legacy-peer-deps` flag if needed. Nivo maintainer confirmed React 19 compatibility (GitHub issue #2618). Test rendering before proceeding.
**Warning signs:** npm ERESOLVE errors during installation.

### Pitfall 6: Department I/II Classification Ambiguity
**What goes wrong:** Some industries don't clearly fit either department (e.g., agriculture produces both food and raw materials).
**Why it happens:** Marx's two-department model is an analytical abstraction; real NAICS codes don't map 1:1.
**How to avoid:** Document the classification table explicitly with rationale for each assignment. Make the mapping a static data structure, not computed. Accept that some assignments are judgment calls -- document these.
**Warning signs:** User confusion about why a sector is in Dept I vs II.

### Pitfall 7: Heatmap Performance with Year Switching
**What goes wrong:** Switching years reloads 71x71 matrix, causing visible lag if not cached.
**Why it happens:** Each year requires a fresh API call and matrix recomputation.
**How to avoid:** Pre-compute and Redis-cache the technical coefficient matrix and Leontief inverse for all available years during ingestion. Year switching just fetches from cache. Set long TTL (24h+) since I-O tables are annual and rarely revised.
**Warning signs:** Multi-second delay when switching years in the dropdown.

## Code Examples

### Nivo HeatMapCanvas Data Format
```typescript
// Source: Nivo docs (nivo.rocks/heatmap/)
// HeatMapCanvas expects data in this format:
interface HeatMapDatum {
  id: string;  // row label
  data: Array<{
    x: string;  // column label
    y: number | null;  // cell value
  }>;
}

// Example transformation from API response:
function transformToHeatmapData(
  matrix: number[][],
  sectorNames: string[]
): HeatMapDatum[] {
  return sectorNames.map((rowName, i) => ({
    id: rowName,
    data: sectorNames.map((colName, j) => ({
      x: colName,
      y: matrix[i][j],
    })),
  }));
}
```

### Nivo Sankey Data Format
```typescript
// Source: Nivo docs (nivo.rocks/sankey/)
interface SankeyData {
  nodes: Array<{ id: string; /* optional color, label */ }>;
  links: Array<{
    source: string;  // node id
    target: string;  // node id
    value: number;
    // Custom: startColor/endColor for green/red conditions
  }>;
}

// Department-level Sankey example:
const departmentSankey: SankeyData = {
  nodes: [
    { id: "Dept I (Means of Production)" },
    { id: "Dept II (Means of Consumption)" },
  ],
  links: [
    { source: "Dept I", target: "Dept II", value: deptI_vs },
    { source: "Dept II", target: "Dept I", value: deptII_c },
  ],
};
```

### FastAPI Endpoint Pattern
```python
# Source: Existing ecpm/api/indicators.py pattern
from fastapi import APIRouter, Depends, Query
from ecpm.database import get_db
from ecpm.cache import build_cache_key, cache_get, cache_set

router = APIRouter(prefix="/api/structural", tags=["structural"])

@router.get("/coefficients")
async def get_coefficients(
    year: int = Query(..., ge=1997, le=2024),
    level: str = Query("summary", regex="^(sector|summary)$"),
    db: AsyncSession = Depends(get_db),
):
    """Return technical coefficient matrix for a given year."""
    cache_key = build_cache_key("structural/coefficients", {"year": year, "level": level})
    cached = await cache_get(cache_key, redis=_get_redis())
    if cached:
        return json.loads(cached)
    # ... compute and return ...

@router.post("/shock")
async def simulate_shock(
    request: ShockRequest,
    db: AsyncSession = Depends(get_db),
):
    """Simulate shock propagation through Leontief inverse."""
    # ...

@router.get("/reproduction")
async def get_reproduction_schema(
    year: int = Query(..., ge=1997, le=2024),
    depth: str = Query("sub_sectors", regex="^(departments|sub_sectors|full)$"),
    db: AsyncSession = Depends(get_db),
):
    """Return Department I/II flows for Sankey visualization."""
    # ...
```

### SQLAlchemy Model for I-O Table Storage
```python
# Source: Existing ecpm/models patterns
from sqlalchemy import Float, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from ecpm.models import Base

class IOCoefficient(Base):
    """Stores individual cells of the technical coefficient matrix.

    One row per (year, row_sector, col_sector) triple.
    """
    __tablename__ = "io_coefficients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    row_code: Mapped[str] = mapped_column(String(10), nullable=False)
    col_code: Mapped[str] = mapped_column(String(10), nullable=False)
    row_name: Mapped[str] = mapped_column(String(200), nullable=False)
    col_name: Mapped[str] = mapped_column(String(200), nullable=False)
    coefficient: Mapped[float] = mapped_column(Float, nullable=False)
    table_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "use", "make", "requirements"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

## BEA InputOutput API Details

### API Endpoint
```
GET https://apps.bea.gov/api/data/
  ?UserID={key}
  &method=GetData
  &datasetname=InputOutput
  &TableID={id}
  &Year={year}
  &ResultFormat=JSON
```

### Key Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| TableID | integer | Yes | Table identifier (discover via GetParameterValues) |
| Year | string | No | Comma-delimited years, or "ALL" (default varies) |

### Discovering TableID Values
```python
# At development/setup time, run this to get available tables:
import beaapi
tables = beaapi.get_parameter_values(api_key, "InputOutput", "TableID")
# Returns DataFrame with Key (TableID) and Desc (table description)
# Key tables to identify:
# - Use of Commodities by Industries, Summary level (71 industries)
# - Make of Commodities by Industries, Summary level
# - Total Requirements, Summary level
```

### Known TableID Values (from documentation examples)
| TableID | Description | Level |
|---------|-------------|-------|
| 2 | Use of Commodities by Industries, Before Redefinitions (Producer's Prices) | Sector (15) |
| 46 | Make of Commodities by Industries, Before Redefinitions | Sector (15) |
| 47 | Make of Commodities by Industries, Before Redefinitions | Summary (71) |

**IMPORTANT:** The full TableID list must be discovered programmatically via `GetParameterValues`. The above are confirmed from documentation examples only. The summary-level (71 industry) Use table TableID must be discovered at implementation time.

### BEA Industry Detail Levels
| Level | Industry Groups | Available Years | Notes |
|-------|----------------|----------------|-------|
| Sector | 15 | 1997-2024 | Aggregated view, good for overview heatmap |
| Summary | 71 | 1997-2024 | Target level for detailed analysis |
| Underlying Summary | 138 | 1997-2024 | More detail than needed |
| Detail | 402 | Benchmark years (2007, 2012, 2017, 2022) only | Too sparse for time series |

### Data Format
BEA API returns flat rows with dimensions: RowCode, ColCode, RowDescr, ColDescr, DataValue, Year. DataValue is a string that may contain commas (e.g., "1,234.5") and must be parsed to float.

### Rate Limits (Updated Feb 2026)
- 100 requests per minute
- 100 MB data volume per minute
- 30 errors per minute
- **Violation penalty: 1-hour timeout** (HTTP 429, Retry-After: 3600)
- Existing BEAClient rate_limit_delay of 0.7s provides adequate spacing for single-threaded access

## Marx's Reproduction Schema: Mathematical Reference

### Department Structure
- **Department I:** Produces means of production (constant capital goods)
- **Department II:** Produces means of consumption (consumer goods)

Each department's output decomposes into: c (constant capital consumed) + v (variable capital / wages) + s (surplus value)

### Simple Reproduction Condition
For the economy to reproduce at the same scale:
```
I(v + s) = II(c)
```
Department I's newly created value (wages + surplus) must equal Department II's demand for means of production.

### Expanded Reproduction Condition
For growth (capital accumulation):
```
I(v + s) > II(c)
```
Department I must produce more means of production than Department II consumes, providing the surplus for investment.

### Additional Conditions
```
I(c + v + s) > I(c) + II(c)        # Total means of production > replacement needs
II(c + v + s) > I(v + sv) + II(v + sv)  # Where sv = consumed portion of surplus
```

### Practical Mapping from I-O Tables
- Department I output = sum of output from Dept I classified industries
- Department II output = sum of output from Dept II classified industries
- Inter-department flows = sum of I-O coefficients between cross-department industry pairs
- c, v, s decomposition approximated from: c = intermediate inputs, v = compensation of employees, s = gross operating surplus (from BEA value-added data)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SVG heatmaps for large matrices | Canvas-rendered heatmaps (Nivo HeatMapCanvas) | ~2022+ | Eliminates DOM bottleneck at 5000+ cells |
| Manual D3 Sankey integration | Nivo Sankey (React-native wrapper) | Nivo 0.80+ | Built-in theming, tooltips, React lifecycle |
| beaapi-only BEA access | beaapi + httpx fallback | Existing in project | Resilient to beaapi import issues |
| Separate React state per viz | Shared year context via layout | Next.js App Router pattern | Year selector affects all visualizations consistently |

**Deprecated/outdated:**
- Nivo versions < 0.88.0 do not support React 19
- BEA API `GetParameterValuesFiltered` does NOT work with InputOutput dataset (returns error "not implemented")
- Old BEA table naming (pre-2018) used different TableID numbers; always discover dynamically

## Open Questions

1. **Exact TableID for summary-level Use table**
   - What we know: TableID=2 is sector-level (15 industries) Use table. TableID=47 is summary-level (71 industries) Make table.
   - What's unclear: The exact TableID for the summary-level (71 industries) Use table.
   - Recommendation: Discover programmatically via `beaapi.get_parameter_values(key, "InputOutput", "TableID")` as the first task in implementation. This is a one-time discovery step.

2. **Value-added decomposition for c/v/s**
   - What we know: I-O tables provide intermediate inputs (proxy for c). BEA also publishes value-added by industry (compensation = v proxy, gross operating surplus = s proxy).
   - What's unclear: Whether value-added data is available in the same InputOutput dataset or requires a separate GDPbyIndustry dataset query.
   - Recommendation: Check if the InputOutput dataset includes value-added rows, or plan to join with GDPbyIndustry data for the c/v/s decomposition.

3. **Nivo HeatMapCanvas cell click interaction for drill-down**
   - What we know: HeatMapCanvas supports onClick handler per cell. The aggregated (15-sector) overview needs to drill into a 71-sector sub-view.
   - What's unclear: Whether Nivo's onClick provides the cell data needed for drill-down, or if custom event handling is needed.
   - Recommendation: Implement drill-down as a conditional render: show aggregated matrix by default, on cell click filter the full 71x71 to the sub-sectors within that group, display in a detail panel/modal.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `backend/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `cd backend && python -m pytest tests/test_structural.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STRC-01 | Ingest BEA I-O tables, compute tech coefficient matrix A | unit | `pytest tests/test_structural_leontief.py::test_build_coefficients -x` | Wave 0 |
| STRC-02 | Compute Leontief inverse with stability checks | unit | `pytest tests/test_structural_leontief.py::test_leontief_inverse -x` | Wave 0 |
| STRC-03 | Simulate shock propagation via Leontief inverse | unit | `pytest tests/test_structural_shock.py -x` | Wave 0 |
| STRC-04 | Aggregate sectors into Dept I / Dept II | unit | `pytest tests/test_structural_departments.py::test_classification -x` | Wave 0 |
| STRC-05 | Check proportionality conditions | unit | `pytest tests/test_structural_departments.py::test_proportionality -x` | Wave 0 |
| DASH-07 | API endpoints return correct heatmap/sankey data | integration | `pytest tests/test_api_structural.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_structural*.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_structural_leontief.py` -- covers STRC-01, STRC-02 (matrix construction, inverse, stability)
- [ ] `tests/test_structural_shock.py` -- covers STRC-03 (shock propagation, weakest link)
- [ ] `tests/test_structural_departments.py` -- covers STRC-04, STRC-05 (classification, proportionality)
- [ ] `tests/test_api_structural.py` -- covers DASH-07 (API endpoints)
- [ ] Synthetic I-O fixtures in conftest.py (small 3x3 or 5x5 matrices with known solutions)
- [ ] No new framework install needed (pytest already configured)

## Sources

### Primary (HIGH confidence)
- [BEA API User Guide (PDF, Feb 6 2026)](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf) - API structure, InputOutput dataset params, rate limits (100 req/min, 1h penalty)
- [QuantEcon Input-Output Models](https://intro.quantecon.org/input_output.html) - Leontief inverse computation, Hawkins-Simon conditions, shock propagation formulas, Python/NumPy code
- [NumPy linalg.inv docs](https://numpy.org/doc/stable/reference/generated/numpy.linalg.inv.html) - Matrix inversion API
- [NumPy linalg.cond docs](https://numpy.org/doc/stable/reference/generated/numpy.linalg.cond.html) - Condition number computation
- [beaapi Python library docs](https://us-bea.github.io/beaapi/README.html) - get_data, get_parameter_values functions, auto-throttling

### Secondary (MEDIUM confidence)
- [BEA Guide to Interactive I-O Tables](https://www.bea.gov/resources/guide-interactive-industry-input-output-accounts-tables) - Industry detail levels (sector=15, summary=71, underlying=138, detail=402), table types
- [BEA Input-Output Accounts Data](https://www.bea.gov/industry/input-output-accounts-data) - Available years 1997-2024, data organization
- [Nivo GitHub Issue #2618](https://github.com/plouc/nivo/issues/2618) - React 19 support confirmed, resolved
- [Marx's Reproduction Schema (thenextrecession)](https://thenextrecession.wordpress.com/2021/07/06/marxs-reproduction-schema/) - Simple and expanded reproduction conditions
- [Marx Capital Vol II Ch 21](https://www.marxists.org/archive/marx/works/1885-c2/ch21_01.htm) - Original expanded reproduction formulas
- [pyBEA User Guide (notebook.community)](https://notebook.community/davidrpugh/pyBEA/examples/user-guide) - InputOutput TableID examples (2=Use sector, 46/47=Make sector/summary)

### Tertiary (LOW confidence)
- TableID numbers beyond 2, 46, 47 need programmatic discovery -- documentation is incomplete
- Exact summary-level Use table TableID: not found in any documentation; must discover via API
- Department I/II NAICS mapping: based on economic theory judgment, not a published standard

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - NumPy for computation is standard; Nivo confirmed React 19 compatible
- Architecture: HIGH - follows established project patterns (FastAPI router, Pydantic schemas, Redis cache)
- BEA API specifics: MEDIUM - TableID discovery needed at implementation time; rate limits and response format well-documented
- Leontief math: HIGH - standard textbook linear algebra, well-documented in QuantEcon
- Department I/II mapping: MEDIUM - theoretical judgment call, not a published standard mapping
- Pitfalls: HIGH - based on official BEA documentation and library issue trackers

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable domain; BEA API changes infrequently)
