---
phase: 05-corporate-concentration-analysis
plan: 006
type: execute
subsystem: concentration-analysis

tags:
  - concentration
  - cr4
  - hhi
  - census-api
  - correlation
  - frontend
  - backend

dependency-graph:
  requires:
    - quick-004 (Phase 4 backend - structural analysis)
    - quick-005 (Phase 4 frontend - structural UI)
  provides:
    - Census Bureau API client
    - Concentration metrics computation (CR4, CR8, HHI)
    - Correlation engine for indicator mapping
    - 6 FastAPI endpoints at /api/concentration/*
    - 7 React components for concentration visualization
    - /concentration page routes with industry detail
    - Enabled sidebar navigation
  affects:
    - None (Phase 5 completes ECPM system)

tech-stack:
  added:
    - Census Bureau API integration
  patterns:
    - Concentration metric computation
    - Rolling correlation with lead-lag analysis
    - Department I/II aggregation using DEPT_I_CODES
    - Dual-axis time series visualization

key-files:
  created:
    - backend/ecpm/ingestion/census_client.py
    - backend/ecpm/models/concentration.py
    - backend/ecpm/concentration/__init__.py
    - backend/ecpm/concentration/metrics.py
    - backend/ecpm/concentration/correlation.py
    - backend/ecpm/schemas/concentration.py
    - backend/ecpm/api/concentration.py
    - backend/alembic/versions/004_concentration_tables.py
    - frontend/src/lib/concentration-api.ts
    - frontend/src/components/concentration/concentration-overview.tsx
    - frontend/src/components/concentration/industry-ranking-bars.tsx
    - frontend/src/components/concentration/correlation-heatmap.tsx
    - frontend/src/components/concentration/industry-indicator-chart.tsx
    - frontend/src/components/concentration/top-firms-table.tsx
    - frontend/src/components/concentration/confidence-breakdown.tsx
    - frontend/src/components/concentration/concentration-card.tsx
    - frontend/src/app/concentration/page.tsx
    - frontend/src/app/concentration/layout.tsx
    - frontend/src/app/concentration/loading.tsx
    - frontend/src/app/concentration/error.tsx
    - frontend/src/app/concentration/[naics]/page.tsx
    - frontend/src/app/concentration/[naics]/[indicator]/page.tsx
    - frontend/src/components/ui/slider.tsx
    - frontend/src/components/ui/tabs.tsx
  modified:
    - backend/ecpm/models/__init__.py
    - backend/ecpm/api/router.py
    - frontend/src/components/layout/sidebar.tsx
    - .env.example

decisions:
  - id: CONC-01
    description: Census Bureau API client uses httpx with tenacity retry, rate limited at 0.5s between calls
  - id: CONC-02
    description: HHI uses 0-10,000 scale with DoJ/FTC thresholds (1500 competitive, 2500 moderate, 7000+ monopoly)
  - id: CONC-03
    description: Lead-lag correlation tests at [0, 3, 6, 12, 18, 24] month offsets
  - id: CONC-04
    description: Confidence score formula combines correlation, sample size, and R-squared
  - id: CONC-05
    description: Removed Recharts tooltip formatter props due to strict typing in Recharts 3

metrics:
  duration: ~15min
  completed: 2026-03-24
---

# Quick Task 006: Phase 5 Corporate Concentration Analysis Summary

**One-liner:** Census API client, CR4/CR8/HHI computation, correlation engine mapping concentration to crisis indicators, 6 FastAPI endpoints, 7 React components, /concentration routes with sidebar navigation enabled.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Census Bureau API client and database models | aed8602 | census_client.py, concentration.py, __init__.py, 004_concentration_tables.py, .env.example |
| 2 | Concentration metrics computation module | b8ad1fd | metrics.py, __init__.py |
| 3 | Correlation engine for concentration-indicator mapping | 3e15979 | correlation.py, __init__.py |
| 4 | Pydantic schemas and FastAPI endpoints | f660ce6 | schemas/concentration.py, api/concentration.py, router.py |
| 5 | Frontend API client and components | be05711 | concentration-api.ts, 7 component files |
| 6 | /concentration page routes | 82b91f6 | page.tsx, layout.tsx, loading.tsx, error.tsx, [naics]/page.tsx, [naics]/[indicator]/page.tsx |
| 7 | Enable sidebar navigation and build fixes | be36279 | sidebar.tsx, slider.tsx, tabs.tsx, component fixes |

## Implementation Details

### Backend

**CensusClient (census_client.py):**
- httpx-based HTTP client with tenacity exponential backoff (5 attempts, 2-60s wait)
- Rate limited at 0.5s between calls (Census API is slower than BEA)
- Methods: fetch_concentration_data(), fetch_market_share_data(), aggregate_by_parent()
- Graceful degradation returns empty DataFrame on missing data

**Concentration Metrics (metrics.py):**
- compute_cr4(): Sum of top 4 market shares
- compute_cr8(): Sum of top 8 market shares
- compute_hhi(): Herfindahl-Hirschman Index (0-10,000 scale)
- compute_trend(): Linear regression with direction classification
- classify_concentration_level(): DoJ/FTC threshold classification
- aggregate_by_department(): Revenue-weighted Dept I/II aggregation using DEPT_I_CODES

**Correlation Engine (correlation.py):**
- compute_rolling_correlation(): Pearson/Spearman with configurable window
- compute_lead_lag_correlation(): Tests lags [0, 3, 6, 12, 18, 24] months
- compute_confidence_score(): Formula: |r| * 100 * sqrt(n/24) * R^2, clamped to 0-100
- map_concentration_to_indicators(): Maps industry to all 8 Phase 2 indicators
- find_strongest_correlations(): Top N industry-indicator pairs

**FastAPI Endpoints (api/concentration.py):**
1. GET /api/concentration/industries - List with optional department filter
2. GET /api/concentration/industry/{naics}/history - Time series CR4/CR8/HHI
3. GET /api/concentration/industry/{naics}/firms/{year} - Top firms table
4. GET /api/concentration/correlations/{naics} - Indicator correlations
5. GET /api/concentration/top-correlations - Top 20 by confidence
6. GET /api/concentration/overview - Dept I/II aggregates + highlights

### Frontend

**API Client (concentration-api.ts):**
- Types mirroring backend Pydantic schemas
- 6 fetch functions: fetchIndustries, fetchIndustryHistory, fetchFirms, fetchCorrelations, fetchTopCorrelations, fetchOverview

**Components (7 total):**
1. ConcentrationOverview - Dept I vs Dept II hero chart with dual Y-axis
2. IndustryRankingBars - Horizontal bar chart with HHI color gradient
3. CorrelationHeatmap - 2D grid with diverging red-white-blue colors
4. IndustryIndicatorChart - Dual-axis time series for concentration vs indicator
5. TopFirmsTable - Market share table with CR4 contributors highlighted
6. ConfidenceBreakdown - Component bars showing confidence factors
7. ConcentrationCard - Summary card with sparkline

**Page Routes:**
- /concentration - Overview with sort toggle, 60s auto-refresh
- /concentration/[naics] - Industry detail with tabs (History, Firms, Correlations)
- /concentration/[naics]/[indicator] - Dual-axis chart with confidence breakdown

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing UI components**
- Found during: Task 6 build verification
- Issue: Slider and Tabs UI components were not present in the project
- Fix: Created minimal implementations following shadcn/ui patterns
- Files created: slider.tsx, tabs.tsx
- Commit: be36279

**2. [Rule 1 - Bug] Recharts type errors**
- Found during: Task 7 build verification
- Issue: Recharts 3 has strict typing that rejects formatter functions with typed parameters
- Fix: Removed custom tooltip formatters to use defaults
- Files modified: industry-ranking-bars.tsx, industry-indicator-chart.tsx
- Commit: be36279

**3. [Rule 1 - Bug] Invalid Next.js import**
- Found during: Task 7 build verification
- Issue: unstable_retry is not exported from next/navigation in Next.js 16
- Fix: Removed the import (function was unused)
- Files modified: error.tsx
- Commit: be36279

## Verification Results

- Backend Python syntax: All files compile successfully
- Frontend build: Passes with all routes generated
- Sidebar: Concentration link enabled and visible
- Routes generated: /concentration, /concentration/[naics], /concentration/[naics]/[indicator]

## Next Phase Readiness

Phase 5 (Corporate Concentration Analysis) is now **COMPLETE**.

This completes the ECPM system implementation across all 5 phases:
1. Data Ingestion & Infrastructure
2. Marxist Indicator Computation
3. Time-Series Forecasting
4. Structural Analysis (Leontief I-O)
5. Corporate Concentration Analysis

The system is ready for:
- Census API key configuration (CENSUS_API_KEY in .env)
- Data ingestion via Celery tasks
- Production deployment
