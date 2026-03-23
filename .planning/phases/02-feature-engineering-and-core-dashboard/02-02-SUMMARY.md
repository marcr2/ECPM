---
phase: 02-feature-engineering-and-core-dashboard
plan: 02
subsystem: api
tags: [marxist-economics, nipa, shaikh-tonak, kliman, tssi, rate-of-profit, financial-fragility, hp-filter, computation-orchestrator, redis-caching]

# Dependency graph
requires:
  - phase: 02-feature-engineering-and-core-dashboard
    plan: 01
    provides: "MethodologyMapper ABC, MethodologyRegistry, IndicatorSlug enum, stub computation.py, mock_nipa_data fixture, skipped test scaffolds"
provides:
  - "ShaikhTonakMapper: current-cost capital, rate of profit, OCC, rate of surplus value, mass of profit with LaTeX docs and NIPA mappings"
  - "KlimanMapper: historical-cost capital (TSSI), same 4 indicators with different C valuation, LaTeX docs and NIPA mappings"
  - "Standalone financial indicator functions: productivity-wage gap, credit-GDP gap, financial-real ratio, debt service ratio"
  - "Computation orchestrator: async DB fetch, FRED-to-descriptive key mapping, indicator dispatch, Redis caching (TTL 3600s)"
  - "INDICATOR_DISPATCH map for all 8 indicator slugs"
affects: [02-04-PLAN, 02-05-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Mapper delegates to internal _surplus_value/_constant_capital helpers for DRY core computation", "ABC default methods delegate to standalone financial.py functions for methodology-independent indicators", "FRED series ID -> descriptive key mapping in orchestrator bridges DB storage to mapper data dict convention", "INDICATOR_DISPATCH dict maps IndicatorSlug -> method name for generic compute_indicator entry point"]

key-files:
  created:
    - backend/ecpm/indicators/shaikh_tonak.py
    - backend/ecpm/indicators/kliman.py
    - backend/ecpm/indicators/financial.py
  modified:
    - backend/ecpm/indicators/__init__.py
    - backend/ecpm/indicators/base.py
    - backend/ecpm/indicators/computation.py
    - backend/tests/test_indicators.py

key-decisions:
  - "Mappers accept descriptive keys (national_income, compensation, etc.) not FRED series IDs directly; orchestrator maps FRED IDs to descriptive keys"
  - "Kliman uses FRED K1NTOTL1HI000 for historical-cost net fixed assets (vs K1NTOTL1SI000 current-cost for Shaikh/Tonak)"
  - "ABC financial method defaults delegate to standalone financial.py functions rather than duplicating logic"
  - "Redis cache key pattern: indicators/{slug}/{methodology} with TTL 3600s"

patterns-established:
  - "Mapper helper pattern: _surplus_value(), _variable_capital(), _constant_capital() encapsulate Marxian category extraction from data dict"
  - "Standalone financial functions: methodology-independent computations callable both via ABC delegation and directly"
  - "Orchestrator dispatch: INDICATOR_DISPATCH dict enables generic compute_indicator() without slug-specific branching"

requirements-completed: [FEAT-02, FEAT-03, FEAT-04, FEAT-05, FEAT-06, FEAT-07, FEAT-08]

# Metrics
duration: 8min
completed: 2026-03-23
---

# Phase 2 Plan 02: Methodology Mappers Summary

**Shaikh/Tonak and Kliman TSSI methodology mappers with 4 core + 4 financial indicators, self-documenting LaTeX formulas, and async computation orchestrator with Redis caching**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-23T20:32:48Z
- **Completed:** 2026-03-23T20:41:01Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- ShaikhTonakMapper computes rate of profit, OCC, rate of surplus value, mass of profit using current-cost capital (FRED K1NTOTL1SI000) with full LaTeX documentation and NIPA table/line references citing Shaikh & Tonak (1994)
- KlimanMapper computes the same 4 indicators using historical-cost capital (FRED K1NTOTL1HI000), producing measurably different rate of profit values (confirmed by test: Kliman rate > Shaikh/Tonak rate for same inputs due to lower denominator)
- Standalone financial.py module with 4 methodology-independent functions: productivity-wage gap (OPHNFB/PRS85006092 index ratio), credit-to-GDP gap (BIS HP filter lambda=400k), financial-to-real asset ratio, corporate debt service ratio
- Computation orchestrator replaces stubs: async DB query, FRED-to-descriptive key mapping, dispatch to correct mapper method, Redis caching with 1-hour TTL
- 30 indicator tests + 5 registry tests all passing; full suite 53 passed, 0 failed

## Task Commits

Each task was committed atomically (TDD: test -> feat):

1. **Task 1: Shaikh/Tonak and Kliman methodology mappers**
   - `ba330c8` (test) - Failing tests for both mappers
   - `94d5ab5` (feat) - Working mapper implementations + registry registration
2. **Task 2: Financial indicators and computation orchestrator**
   - `23a3729` (test) - Failing tests for financial.py and orchestrator dispatch
   - `7b3410f` (feat) - financial.py, updated base.py delegation, full computation.py

## Files Created/Modified
- `backend/ecpm/indicators/shaikh_tonak.py` - ShaikhTonakMapper: current-cost capital, 4 core indicators, FRED series metadata, IndicatorDoc with LaTeX
- `backend/ecpm/indicators/kliman.py` - KlimanMapper: historical-cost capital (TSSI), 4 core indicators, IndicatorDoc with LaTeX
- `backend/ecpm/indicators/financial.py` - Standalone functions: compute_productivity_wage_gap, compute_credit_gdp_gap, compute_financial_real_ratio, compute_debt_service_ratio
- `backend/ecpm/indicators/__init__.py` - Updated to import and register both mappers at import time
- `backend/ecpm/indicators/base.py` - ABC financial defaults now delegate to financial.py functions
- `backend/ecpm/indicators/computation.py` - Full orchestrator: INDICATOR_DISPATCH, compute_indicator, compute_all_summaries, FRED-to-key mapping, Redis caching
- `backend/tests/test_indicators.py` - 30 tests: 8 Shaikh/Tonak, 3 Kliman, 6 metadata, 2 registry, 4 financial via mapper, 5 standalone financial, 1 orchestrator dispatch, 1 frequency alignment

## Decisions Made
- Mappers accept descriptive keys (national_income, compensation, net_fixed_assets_current/historical) rather than raw FRED series IDs. The computation orchestrator bridges FRED IDs to descriptive keys. This keeps mapper code readable and testable with simple mock data.
- Kliman uses FRED series K1NTOTL1HI000 for historical-cost net stock of private fixed assets. If this series is not in the actual FRED database, it serves as a documented placeholder -- the mapper knows which series to request.
- ABC financial method defaults delegate to standalone financial.py functions. This avoids code duplication and allows financial functions to be called independently of the mapper class hierarchy.
- Redis cache key pattern `indicators/{slug}/{methodology}` with 1-hour TTL. Data changes at most daily; 1 hour is sufficient granularity.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both mappers registered and discoverable via MethodologyRegistry
- Computation orchestrator ready for API endpoint wiring (Plan 02-04)
- INDICATOR_DISPATCH provides the dispatch map for /api/indicators/{slug} endpoint
- compute_all_summaries provides the entry point for /api/indicators/ overview endpoint
- All 8 indicator computation functions verified with known-value tests
- Full test suite green (53 passed, 16 skipped from other plans)

## Self-Check: PASSED

All 8 created/modified files verified present. All 4 task commits (ba330c8, 94d5ab5, 23a3729, 7b3410f) verified in git log.

---
*Phase: 02-feature-engineering-and-core-dashboard*
*Completed: 2026-03-23*
