---
phase: 02-feature-engineering-and-core-dashboard
plan: 04
subsystem: api
tags: [fastapi, rest, redis, indicators, methodology, caching]

# Dependency graph
requires:
  - phase: 02-01
    provides: "Pydantic schemas (IndicatorResponse, MethodologyDocResponse, etc.), ABC, registry, definitions"
  - phase: 02-02
    provides: "Computation orchestrator (compute_indicator, compute_all_summaries), Shaikh/Tonak + Kliman mappers"
provides:
  - "GET /api/indicators/ endpoint returning overview with all 8 indicator summaries"
  - "GET /api/indicators/{slug} endpoint returning indicator time-series data"
  - "GET /api/indicators/{slug}/compare endpoint returning multi-methodology comparison"
  - "GET /api/indicators/methodology endpoint returning self-documentation for all methodologies"
  - "GET /api/indicators/methodology/{slug} endpoint returning docs for one methodology"
affects: [02-05, frontend-dashboard, api-consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Methodology docs embedded in same router as indicator data (route ordering)"
    - "Per-indicator FRED-to-key mapping for financial indicators"
    - "Redis caching with 3600s TTL for data, 86400s TTL for docs"

key-files:
  created:
    - "backend/ecpm/api/indicators.py"
    - "backend/ecpm/api/methodology.py"
  modified:
    - "backend/ecpm/api/router.py"
    - "backend/ecpm/indicators/computation.py"
    - "backend/tests/test_api_indicators.py"

key-decisions:
  - "Merged methodology routes into indicators router to avoid FastAPI dynamic route capture conflict"
  - "Fixed per-indicator financial FRED-to-key mapping to resolve K1NTOTL1SI000 and BOGZ1FL073164003Q ambiguity"

patterns-established:
  - "Route ordering: static routes (methodology) before dynamic ({slug}) within same prefix"
  - "Per-indicator key mappings instead of global dict when FRED series IDs are reused across contexts"

requirements-completed: [FEAT-01, FEAT-08, DASH-04, DASH-05]

# Metrics
duration: 12min
completed: 2026-03-23
---

# Phase 2 Plan 4: Indicator API Endpoints Summary

**FastAPI REST endpoints for all 8 Marxist indicator time-series, multi-methodology comparison, and self-documenting methodology docs with Redis caching**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-23T20:50:12Z
- **Completed:** 2026-03-23T21:02:22Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created 5 API endpoints exposing computed Marxist indicators and methodology documentation
- Fixed FRED-to-key mapping collision in computation orchestrator that prevented core indicators from computing
- All 12 API integration tests pass; full backend suite green (86/86)
- Redis caching on all endpoints with appropriate TTLs (1h for data, 24h for docs)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create indicator data and methodology API endpoints** - `330c9fa` (feat)
2. **Task 2: Un-skip and pass API integration tests** - `6a979d5` (test)

## Files Created/Modified
- `backend/ecpm/api/indicators.py` - FastAPI router with 5 endpoints: overview, methodology list, methodology detail, indicator detail, indicator compare
- `backend/ecpm/api/methodology.py` - Documentation reference (routes consolidated into indicators.py for route ordering)
- `backend/ecpm/api/router.py` - Updated aggregate router to include indicators router
- `backend/ecpm/indicators/computation.py` - Fixed FRED-to-key mapping to use per-indicator dicts for financial indicators
- `backend/tests/test_api_indicators.py` - 12 integration tests: overview, detail, methodology docs, compare, 404 cases

## Decisions Made
- **Merged methodology routes into indicators router:** The separate methodology router at `/api/indicators/methodology` conflicted with the dynamic `/{slug}` route on the indicators router. FastAPI matched `/api/indicators/methodology` as `slug="methodology"` before checking the methodology router. Consolidating all routes into one router with correct ordering (static before dynamic) resolved this.
- **Per-indicator financial FRED-to-key mapping:** The global `_FINANCIAL_FRED_TO_KEY` dict had collisions (K1NTOTL1SI000 mapped to both "net_fixed_assets_current" and "real_assets"). Replaced with `_FINANCIAL_INDICATOR_MAPPINGS` dict-of-dicts keyed by indicator slug, so each financial indicator gets the correct key for its FRED series.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed FRED-to-key mapping collision in computation.py**
- **Found during:** Task 1 (endpoint implementation)
- **Issue:** `_FINANCIAL_FRED_TO_KEY` dict overwrote `_FRED_TO_KEY` entries when merged via `{**_FRED_TO_KEY, **_FINANCIAL_FRED_TO_KEY}`. K1NTOTL1SI000 mapped to "real_assets" instead of "net_fixed_assets_current" for core indicators, causing KeyError in Shaikh/Tonak mapper.
- **Fix:** Created `_FINANCIAL_INDICATOR_MAPPINGS` (per-indicator dict) and passed correct mapping to `_fetch_series_from_db` based on indicator type.
- **Files modified:** backend/ecpm/indicators/computation.py
- **Verification:** compute_indicator("rate_of_profit", "shaikh-tonak", ...) succeeds; all 86 tests pass
- **Committed in:** 330c9fa (Task 1 commit)

**2. [Rule 3 - Blocking] Consolidated methodology routes into indicators router**
- **Found during:** Task 1 (endpoint implementation)
- **Issue:** Separate methodology router's prefix `/api/indicators/methodology/` was not matched before the indicators router's `/{slug}` route captured "methodology" as a slug.
- **Fix:** Moved methodology endpoint definitions into indicators.py, placed before dynamic `{slug}` route definitions.
- **Files modified:** backend/ecpm/api/indicators.py, backend/ecpm/api/methodology.py, backend/ecpm/api/router.py
- **Verification:** GET /api/indicators/methodology returns 200 with methodology docs; GET /api/indicators/rate_of_profit still returns 200
- **Committed in:** 330c9fa (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both auto-fixes necessary for correct endpoint behavior. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All backend API endpoints for indicators and methodology docs are live
- Frontend plan (02-05) can consume these endpoints to build the interactive dashboard
- Redis caching is operational (degrades gracefully when Redis unavailable)

## Self-Check: PASSED

All 5 source files verified present. Both task commits (330c9fa, 6a979d5) verified in git log.

---
*Phase: 02-feature-engineering-and-core-dashboard*
*Completed: 2026-03-23*
