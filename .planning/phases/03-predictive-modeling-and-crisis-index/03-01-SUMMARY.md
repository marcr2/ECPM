---
phase: 03-predictive-modeling-and-crisis-index
plan: 01
subsystem: modeling, testing
tags: [statsmodels, pydantic, pytest, var, svar, regime-switching, crisis-index, backtest]

# Dependency graph
requires:
  - phase: 02-feature-engineering-and-core-dashboard
    provides: "IndicatorSlug enum, Pydantic schema patterns, conftest fixtures"
provides:
  - "ecpm.modeling package with 9 Pydantic v2 response schemas"
  - "28 skip-marked test scaffolds across 7 files as executable specifications"
  - "Synthetic indicator fixtures: 124-quarter 8-column deterministic DataFrame"
  - "Synthetic regime series fixture: 300-point 3-regime volatility data"
  - "statsmodels>=0.14.6 as project dependency"
affects: [03-02, 03-03, 03-04, 03-05]

# Tech tracking
tech-stack:
  added: [statsmodels]
  patterns: [importorskip for deferred module testing, synthetic time-series fixtures with fixed seeds]

key-files:
  created:
    - backend/ecpm/modeling/__init__.py
    - backend/ecpm/modeling/schemas.py
    - backend/tests/test_stationarity.py
    - backend/tests/test_var_model.py
    - backend/tests/test_svar_model.py
    - backend/tests/test_regime_switching.py
    - backend/tests/test_crisis_index.py
    - backend/tests/test_backtest.py
    - backend/tests/test_api_forecasting.py
  modified:
    - backend/pyproject.toml
    - backend/tests/conftest.py

key-decisions:
  - "pytest.importorskip for skip-marking: cleaner than @skipif for module-level skipping"
  - "numpy default_rng(42) over legacy np.random.seed for modern reproducible RNG"
  - "Synthetic data with realistic economic trends (declining profit rate, rising OCC) for domain validity"

patterns-established:
  - "importorskip pattern: test files use pytest.importorskip at module level for deferred implementation modules"
  - "Synthetic fixture pattern: conftest provides synthetic_indicators (8-col, 124-row DataFrame) and synthetic_regime_series (300-point 3-regime)"

requirements-completed: [MODL-01, MODL-02, MODL-03, MODL-04, MODL-05, MODL-06, MODL-07, MODL-08, DASH-06]

# Metrics
duration: 4min
completed: 2026-03-23
---

# Phase 3 Plan 1: Modeling Foundation Summary

**Pydantic v2 modeling schemas (9 response models) and 28 skip-marked test scaffolds with deterministic synthetic indicator fixtures for VAR/SVAR forecasting, regime-switching, crisis index, and backtesting**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-23T21:10:51Z
- **Completed:** 2026-03-23T21:15:17Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Created ecpm/modeling/ package with 9 Pydantic v2 response schemas defining the complete API contract for forecasts, regimes, crisis index, backtests, and training status
- Scaffolded 28 skip-marked tests across 7 files serving as executable specifications for all Phase 3 modeling modules
- Added synthetic_indicators fixture (124 quarters, 8 economic indicators with realistic trends) and synthetic_regime_series fixture (300-point 3-regime volatility data)
- Added statsmodels>=0.14.6 as project dependency

## Task Commits

Each task was committed atomically:

1. **Task 1: Add statsmodels dependency and create modeling package with Pydantic schemas** - `ba04816` (feat)
2. **Task 2: Create test scaffolds with synthetic data fixtures for all modeling modules** - `9c09150` (test)

## Files Created/Modified
- `backend/pyproject.toml` - Added statsmodels>=0.14.6 dependency
- `backend/ecpm/modeling/__init__.py` - Package marker with public schema exports
- `backend/ecpm/modeling/schemas.py` - 9 Pydantic v2 response models (ForecastPoint, IndicatorForecast, RegimeResult, CrisisIndex, BacktestResult, TrainingStatus, TrainingStep, ForecastsResponse, BacktestsResponse)
- `backend/tests/conftest.py` - Added synthetic_indicators and synthetic_regime_series fixtures
- `backend/tests/test_stationarity.py` - 4 tests: ADF/KPSS dual check, auto-differencing
- `backend/tests/test_var_model.py` - 4 tests: lag selection, forecast shape, CI ordering, indicator coverage
- `backend/tests/test_svar_model.py` - 3 tests: A-matrix shape, lower-triangular structure, SVAR identification
- `backend/tests/test_regime_switching.py` - 4 tests: regime detection, probability sums, transition matrix, fallback
- `backend/tests/test_crisis_index.py` - 5 tests: composite bounds, decomposition, equal weights, custom weights, profit-rate inversion
- `backend/tests/test_backtest.py` - 3 tests: GFC episode, schema validation, crisis index series
- `backend/tests/test_api_forecasting.py` - 5 tests: forecasts, regime, crisis-index, backtests, training endpoints

## Decisions Made
- Used `pytest.importorskip` at module level for clean skip-marking (cleaner than `@skipif` decorators for entire files)
- Used `numpy.random.default_rng(42)` (modern Generator API) instead of legacy `np.random.seed` for reproducible synthetic data
- Synthetic indicator data uses realistic economic trends (declining rate of profit ~0.15 to ~0.08, rising OCC ~3.0 to ~5.5) for domain validity in tests

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 9 Pydantic schemas define the API contract for backend-to-frontend communication
- 28 skip-marked tests serve as executable specifications for implementation plans 03-02 through 03-05
- Synthetic fixtures provide deterministic test data for all modeling modules
- statsmodels dependency ready for import by implementation code

---
*Phase: 03-predictive-modeling-and-crisis-index*
*Completed: 2026-03-23*
