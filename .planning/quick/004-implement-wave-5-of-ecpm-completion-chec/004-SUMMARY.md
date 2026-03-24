---
phase: quick
plan: 004
subsystem: structural-analysis
tags: [leontief, input-output, bea-api, fastapi, shock-simulation]
dependency-graph:
  requires: [01-02, 01-03, 02-01]
  provides: [structural-backend, leontief-inverse, shock-simulation, department-classification]
  affects: [wave-6-frontend]
tech-stack:
  added: []
  patterns: [structural-module, matrix-computation, department-classification]
key-files:
  created:
    - backend/ecpm/structural/__init__.py
    - backend/ecpm/structural/bea_io_client.py
    - backend/ecpm/structural/leontief.py
    - backend/ecpm/structural/shock.py
    - backend/ecpm/structural/departments.py
    - backend/ecpm/models/io_table.py
    - backend/alembic/versions/003_io_tables.py
    - backend/ecpm/schemas/structural.py
    - backend/ecpm/api/structural.py
    - backend/tests/test_structural_bea_io.py
    - backend/tests/test_structural_leontief.py
    - backend/tests/test_structural_shock.py
    - backend/tests/test_structural_departments.py
    - backend/tests/test_api_structural.py
  modified:
    - backend/ecpm/models/__init__.py
    - backend/ecpm/api/router.py
    - backend/tests/conftest.py
decisions:
  - id: quick-004-1
    summary: "Synthetic 3x3 I-O fixtures for deterministic testing"
    rationale: "Known analytical Leontief inverse enables exact verification of matrix computations"
  - id: quick-004-2
    summary: "DEPT_I_CODES static set for means-of-production classification"
    rationale: "NAICS codes for mining, utilities, construction, manufacturing capital goods assigned to Dept I"
  - id: quick-004-3
    summary: "Simplified c/v/s decomposition uses 60/40 labor/surplus split"
    rationale: "Proper decomposition requires GDPbyIndustry value-added data; placeholder until data integration"
  - id: quick-004-4
    summary: "Default BEA TableIDs cached (Use=259, Make=47)"
    rationale: "Avoid repeated API discovery calls; IDs stable at summary-level"
metrics:
  duration: ~12min
  tasks_completed: 6/6
  files_created: 15
  files_modified: 3
  tests_added: 5 test files with 50+ test cases
  completed: 2026-03-24
---

# Quick Task 004: Wave 5 Phase 4 Backend Summary

Implemented complete backend for structural analysis: BEA InputOutput API client, Leontief matrix computations with stability checks, shock propagation simulation, Department I/II classification with reproduction schema, and 5 FastAPI endpoints.

## What Was Built

### BEA InputOutput API Client
- `BEAIOClient` extends existing BEA client pattern for I-O tables
- `fetch_use_table(year)` / `fetch_make_table(year)` return pivoted matrices
- `discover_table_id(type)` with caching for summary-level table IDs
- `pivot_io_data()` converts flat BEA response to matrix format
- Rate limiting (0.7s) and tenacity retry logic

### Leontief Matrix Computations
- `compute_technical_coefficients(Z, X)`: A[i,j] = Z[i,j] / X[j]
- `compute_leontief_inverse(A)`: L = (I - A)^-1 with diagnostics
- `check_stability(A)`: quick stability assessment
- `get_output_multipliers(L, codes)`: sorted pd.Series by multiplier

Stability checks include:
- Hawkins-Simon conditions (leading principal minors > 0)
- Condition number threshold (< 1e10)
- Spectral radius (< 1.0 for convergence)

### Shock Propagation Simulation
- `simulate_shock(L, idx, magnitude, codes)`: single-sector impact
- `simulate_multi_sector_shock(L, shocks, codes)`: superposition
- `find_critical_sectors(L, codes, threshold)`: high-multiplier sectors
- `compute_backward_linkages(L, codes)`: column sums (demand pull)
- `compute_forward_linkages(L, codes)`: row sums (supply push)
- `find_weakest_link(L, codes, names)`: most vulnerable sector

### Department I/II Classification
- `DEPT_I_CODES`: static NAICS set for means of production
- `classify_departments(codes)`: NAICS -> Dept_I/Dept_II mapping
- `aggregate_by_department(Z, class, codes)`: 2x2 inter-dept flows
- `check_proportionality(c/v/s values)`: Marx's reproduction conditions
- `compute_reproduction_flows(Z, va, class, codes)`: full schema

### Database Schema
- `IOMetadata`: year, table_type, num_industries, source
- `IOCell`: year, row_code, col_code, value, descriptions
- Composite indexes for efficient year/type/row/col queries
- Alembic migration 003

### FastAPI Endpoints (5 total)
- `GET /api/structural/years`: available I-O table years
- `GET /api/structural/matrix/{year}?type=`: coefficients, inverse, flows
- `POST /api/structural/shock`: multi-sector simulation
- `GET /api/structural/reproduction/{year}`: Dept I/II schema + Sankey
- `GET /api/structural/critical-sectors/{year}`: critical sector list

### Test Infrastructure
- 5 test files with pytest.importorskip stubs
- Synthetic 3x3 I-O matrix fixtures with known Leontief inverse
- Mock BEA IO client fixture
- NAICS-to-Department classification fixture
- ~50 test cases covering all modules

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| quick-004-1 | Synthetic 3x3 fixtures | Known analytical inverse enables exact verification |
| quick-004-2 | Static DEPT_I_CODES set | NAICS-based classification for capital goods sectors |
| quick-004-3 | 60/40 labor/surplus split | Placeholder until GDPbyIndustry integration |
| quick-004-4 | Default BEA TableIDs cached | Stable summary-level IDs (Use=259, Make=47) |

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Type | Description |
|------|------|-------------|
| d21fb44 | test | Add test scaffolds and synthetic I-O fixtures |
| 9ceac5d | feat | Create BEA InputOutput API client |
| 32df1f8 | feat | Create database schema for I-O tables |
| 051532d | feat | Implement Leontief matrix computations |
| 15f9215 | feat | Implement shock propagation and Department I/II |
| a0243a0 | feat | Create FastAPI structural analysis endpoints |

## Next Steps

Wave 6 will implement the frontend visualization:
- Nivo HeatMapCanvas for 71x71 coefficient matrix
- Nivo Sankey for Department I/II flows
- Shock simulation UI with result bar charts
- Year selector dropdown for temporal analysis
