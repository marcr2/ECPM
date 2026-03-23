---
phase: 03-predictive-modeling-and-crisis-index
plan: 02
subsystem: modeling
tags: [statsmodels, var, svar, regime-switching, crisis-index, backtest, stationarity, markov]

# Dependency graph
requires:
  - phase: 03-predictive-modeling-and-crisis-index
    plan: 01
    provides: "Pydantic schemas, test scaffolds, synthetic fixtures, statsmodels dependency"
  - phase: 02-feature-engineering-and-core-dashboard
    provides: "IndicatorSlug enum, indicator definitions"
provides:
  - "ecpm.modeling.stationarity: dual ADF+KPSS stationarity test and ensure_stationarity preprocessing"
  - "ecpm.modeling.var_model: VAR fitting with AIC lag selection and 68%/95% CI forecast generation"
  - "ecpm.modeling.svar_model: SVAR identification with lower-triangular Marxist causal A matrix"
  - "ecpm.modeling.regime_switching: Markov regime-switching with 3-to-2 fallback"
  - "ecpm.modeling.crisis_index: Composite Crisis Probability Index (0-100) with TRPF/realization/financial decomposition"
  - "ecpm.modeling.backtest: Historical backtesting against 6 crisis episodes with warning windows"
affects: [03-03, 03-04, 03-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [global cross-sectional percentile normalization for crisis index, Markov regime fallback chain, inverse differencing for VAR forecasts]

key-files:
  created:
    - backend/ecpm/modeling/stationarity.py
    - backend/ecpm/modeling/var_model.py
    - backend/ecpm/modeling/svar_model.py
    - backend/ecpm/modeling/regime_switching.py
    - backend/ecpm/modeling/crisis_index.py
    - backend/ecpm/modeling/backtest.py
  modified:
    - backend/ecpm/modeling/__init__.py

key-decisions:
  - "Global cross-sectional percentile normalization for crisis index: ranks all indicator values across all columns together to preserve absolute level sensitivity when comparing scenarios with different profit rate levels"
  - "Markov regime transition matrix transposed from statsmodels convention (columns sum to 1) to standard convention (rows sum to 1) for intuitive interpretation"
  - "SVAR fitting wrapped in try/except with None return for graceful degradation when optimization fails to converge"

patterns-established:
  - "Global cross-sectional normalization: stack all columns, rank globally, unstack -- captures absolute level differences across independent compute calls"
  - "Regime fallback chain: attempt max_regimes down to 2, return first successful fit"
  - "Inverse differencing: cumsum forecasted differences and add last observed level to recover original scale"

requirements-completed: [MODL-01, MODL-02, MODL-03, MODL-04, MODL-05, MODL-06, MODL-07, MODL-08]

# Metrics
duration: 9min
completed: 2026-03-23
---

# Phase 3 Plan 2: Core Modeling Modules Summary

**6 econometric modeling modules implementing dual ADF/KPSS stationarity testing, VAR/SVAR forecasting with 68%/95% CI bands, Markov 3-regime switching with 2-regime fallback, composite crisis index with TRPF/realization/financial decomposition, and historical backtesting against 6 crisis episodes**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-23T21:18:05Z
- **Completed:** 2026-03-23T21:27:49Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Implemented dual ADF+KPSS stationarity test with conservative differencing strategy and VAR fitting with AIC-optimal lag selection producing forecasts with nested 68%/95% confidence interval bands
- Built SVAR structural identification using lower-triangular A matrix encoding the Marxist causal ordering (OCC -> rate of surplus value -> rate of profit -> mass of profit -> productivity-wage gap -> credit-GDP gap -> financial-real ratio -> debt service ratio)
- Implemented Markov regime-switching model detecting Normal/Stagnation/Crisis regimes with automatic 3-to-2 regime fallback on convergence failure
- Created Composite Crisis Probability Index (0-100 scale) using global cross-sectional percentile normalization with TRPF, realization, and financial sub-index decomposition
- Built historical backtesting framework evaluating 6 crisis episodes (Great Depression through COVID) with 12-month and 24-month early-warning window assessment

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement stationarity preprocessing, VAR fitting, and SVAR identification** - `5e151f7` (feat)
2. **Task 2: Implement regime-switching detection, crisis index computation, and historical backtesting** - `9505570` (feat)

## Files Created/Modified
- `backend/ecpm/modeling/stationarity.py` - Dual ADF+KPSS stationarity test and ensure_stationarity DataFrame preprocessing
- `backend/ecpm/modeling/var_model.py` - VAR fitting with lag selection, forecast generation with 68%/95% CI bands, inverse differencing
- `backend/ecpm/modeling/svar_model.py` - SVAR A matrix construction (Marxist causal ordering) and structural identification
- `backend/ecpm/modeling/regime_switching.py` - Markov regime-switching with 3-to-2 fallback, regime labeling by weighted mean, duration computation
- `backend/ecpm/modeling/crisis_index.py` - Composite Crisis Index with mechanism decomposition and global cross-sectional normalization
- `backend/ecpm/modeling/backtest.py` - Historical backtesting against 6 crisis episodes with warning window evaluation
- `backend/ecpm/modeling/__init__.py` - Updated with full public API exports for all 6 modeling modules

## Decisions Made
- Used global cross-sectional percentile normalization (rank all values across all columns together) instead of per-column percentile rank for crisis index. This preserves sensitivity to absolute indicator levels -- necessary for scenarios where profit rate levels differ between datasets while maintaining the same relative ordering within each column.
- Transposed Markov transition matrix from statsmodels convention (columns sum to 1, P[j|i] stored in column i) to standard convention (rows sum to 1) for intuitive API consumption.
- SVAR fitting wrapped in try/except returning None on failure, since SVAR optimization commonly fails to converge with real economic data. Callers must handle None gracefully.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed transition matrix nesting from 3D to 2D**
- **Found during:** Task 2 (regime-switching implementation)
- **Issue:** statsmodels `regime_transition` has shape (k, k, 1) not (k, k); `.T.tolist()` produced nested lists that `sum()` could not handle
- **Fix:** Applied `np.squeeze()` before transposing to remove trailing singleton dimension
- **Files modified:** backend/ecpm/modeling/regime_switching.py
- **Verification:** test_transition_matrix_rows_sum_to_one passes
- **Committed in:** 9505570 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed crisis index normalization for scale sensitivity**
- **Found during:** Task 2 (crisis index implementation)
- **Issue:** Per-column percentile rank normalization is invariant to uniform scaling, causing `test_inverted_profit_rate` to fail (halving all profit rates produces identical percentile ranks)
- **Fix:** Switched to global cross-sectional percentile normalization (stack all columns, rank globally, unstack) which captures absolute level differences
- **Files modified:** backend/ecpm/modeling/crisis_index.py
- **Verification:** test_inverted_profit_rate passes -- lower profit rate produces higher TRPF crisis signal
- **Committed in:** 9505570 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
- statsmodels installed at runtime since it was listed in pyproject.toml but not yet present in the Python environment. Resolved by installing the dependency (already declared in 03-01).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 6 modeling modules provide the computational backbone for Phase 3 downstream plans
- Celery tasks (03-03) can import and orchestrate these pure-function modules
- API endpoints (03-04) can call these modules to serve forecast/regime/crisis/backtest results
- Frontend visualization (03-05) has a defined API contract via Pydantic schemas from 03-01
- 23 modeling tests pass green, covering stationarity, VAR/SVAR, regime-switching, crisis index, and backtesting

## Self-Check: PASSED

- All 7 created/modified files exist on disk
- Commit 5e151f7 (Task 1) verified in git log
- Commit 9505570 (Task 2) verified in git log
- 23 modeling tests pass, 76 total tests pass

---
*Phase: 03-predictive-modeling-and-crisis-index*
*Completed: 2026-03-23*
