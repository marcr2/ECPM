---
phase: 02-feature-engineering-and-core-dashboard
plan: 01
subsystem: api
tags: [abc, registry, pydantic, indicators, marxist-economics, nipa, plugin-architecture]

# Dependency graph
requires:
  - phase: 01-foundation-and-data-ingestion
    provides: "SQLAlchemy models (Observation, SeriesMetadata), Pydantic schema patterns, conftest.py test infrastructure, _align_frequency LOCF implementation"
provides:
  - "MethodologyMapper ABC with NIPAMapping and IndicatorDoc dataclasses"
  - "MethodologyRegistry class for mapper discovery (register/get/list_all/default/reset)"
  - "IndicatorSlug enum with 8 indicators and INDICATOR_DEFS metadata dict"
  - "FREQUENCY_STRATEGY constant documenting LOCF-only alignment"
  - "Pydantic v2 response schemas for all indicator API endpoints"
  - "Stub computation orchestrator (compute_indicator, compute_all_summaries)"
  - "Test scaffolds: 5 passing registry tests, 8 skipped computation tests, 4 skipped API tests"
  - "Mock NIPA data fixture with known values for formula verification"
affects: [02-02-PLAN, 02-03-PLAN, 02-04-PLAN, 02-05-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: ["ABC plugin architecture for methodology mappers", "Class-level registry with reset for test isolation", "StrEnum for URL-safe indicator slugs", "Default (non-abstract) methods on ABC for methodology-invariant computations"]

key-files:
  created:
    - backend/ecpm/indicators/__init__.py
    - backend/ecpm/indicators/base.py
    - backend/ecpm/indicators/registry.py
    - backend/ecpm/indicators/definitions.py
    - backend/ecpm/indicators/computation.py
    - backend/ecpm/schemas/indicators.py
    - backend/tests/test_methodology_registry.py
    - backend/tests/test_indicators.py
    - backend/tests/test_api_indicators.py
  modified: []

key-decisions:
  - "Productivity-wage gap, credit-GDP gap, financial-real ratio, and debt-service ratio have default (non-abstract) implementations on the ABC since they do not vary by Marxist methodology"
  - "One-sided HP filter implemented as recursive approximation in base.py for credit-to-GDP gap (BIS lambda=400,000)"
  - "StrEnum used for IndicatorSlug for direct string comparison in URL routing"

patterns-established:
  - "ABC + Registry: MethodologyMapper ABC defines interface, MethodologyRegistry provides class-level discovery with reset() for test isolation"
  - "Indicator definitions: IndicatorSlug StrEnum + INDICATOR_DEFS dict pattern for enumerating indicators with metadata"
  - "Test scaffolding: skip-marked tests with concrete assertions as specification for future implementation plans"

requirements-completed: [FEAT-01, FEAT-09]

# Metrics
duration: 4min
completed: 2026-03-23
---

# Phase 2 Plan 01: Interface Contracts Summary

**MethodologyMapper ABC plugin architecture with registry pattern, 8-indicator definitions, Pydantic API schemas, and comprehensive test scaffolds**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-23T20:21:07Z
- **Completed:** 2026-03-23T20:25:23Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- MethodologyMapper ABC defines complete NIPA-to-Marx translation interface with 6 abstract methods (core indicators + series/docs) and 4 default methods (financial indicators that are methodology-invariant)
- MethodologyRegistry with class-level storage, slug-based lookup, default methodology shortcut, and reset for test isolation
- IndicatorSlug StrEnum with 8 indicators (4 core + 4 financial) and INDICATOR_DEFS metadata dict with names, units, categories, descriptions
- Pydantic v2 response schemas defining full API contract: IndicatorDataPoint, IndicatorResponse, IndicatorSummary, IndicatorOverviewResponse, NIPAMappingDoc, IndicatorMethodologyDoc, MethodologyDocResponse
- 5 passing registry tests, 8 skipped computation tests with known-value assertions, 4 skipped API endpoint tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Create indicator package with ABC, registry, definitions, and schemas** - `b975e64` (feat)
2. **Task 2: Create test scaffolds with mock data fixtures** - `99f1f2b` (test)

## Files Created/Modified
- `backend/ecpm/indicators/__init__.py` - Public API re-exports for indicators package
- `backend/ecpm/indicators/base.py` - MethodologyMapper ABC, NIPAMapping/IndicatorDoc dataclasses, one-sided HP filter
- `backend/ecpm/indicators/registry.py` - MethodologyRegistry with register/get/list_all/default/reset
- `backend/ecpm/indicators/definitions.py` - IndicatorSlug StrEnum, INDICATOR_DEFS metadata, FREQUENCY_STRATEGY constant
- `backend/ecpm/indicators/computation.py` - Stub orchestrator (NotImplementedError for Plan 02-02)
- `backend/ecpm/schemas/indicators.py` - Pydantic v2 response models for all indicator endpoints
- `backend/tests/test_methodology_registry.py` - 5 passing tests for registry plugin pattern
- `backend/tests/test_indicators.py` - 8 skipped tests with mock NIPA data fixtures for indicator computation
- `backend/tests/test_api_indicators.py` - 4 skipped tests for indicator API endpoints

## Decisions Made
- Productivity-wage gap, credit-GDP gap, financial-real ratio, and debt-service ratio implemented as default (non-abstract) methods on the ABC since they are methodology-invariant -- only core Marxist indicators (rate of profit, OCC, rate of surplus value, mass of profit) vary by methodology
- One-sided HP filter implemented as recursive approximation directly in base.py rather than adding statsmodels dependency now (statsmodels can be added in Plan 02-02 or Phase 3 when needed for VAR models)
- Used Python StrEnum for IndicatorSlug for direct string comparison compatibility in URL routing and database queries

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All interface contracts established: MethodologyMapper ABC, MethodologyRegistry, IndicatorSlug, Pydantic schemas
- Plan 02-02 can implement concrete Shaikh/Tonak and Kliman mappers against the ABC
- Plan 02-04 can implement API endpoints using the Pydantic response schemas
- Test scaffolds provide specification-as-tests for Plans 02-02 and 02-04
- Full test suite: 23 passed, 24 skipped, 0 failed

## Self-Check: PASSED

All 10 created files verified present. Both task commits (b975e64, 99f1f2b) verified in git log.

---
*Phase: 02-feature-engineering-and-core-dashboard*
*Completed: 2026-03-23*
