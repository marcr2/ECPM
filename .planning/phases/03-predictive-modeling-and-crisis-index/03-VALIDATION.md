---
phase: 3
slug: predictive-modeling-and-crisis-index
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio 0.24.x |
| **Config file** | backend/pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -v --timeout=60` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `cd /home/marcellinor/Desktop/ECPM/backend && python -m pytest tests/ -v --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | MODL-02 | unit | `pytest tests/test_stationarity.py::test_dual_stationarity -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | MODL-01 | unit | `pytest tests/test_var_model.py::test_var_lag_selection -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | MODL-04 | unit | `pytest tests/test_var_model.py::test_forecast_confidence_intervals -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | MODL-03 | unit | `pytest tests/test_svar_model.py::test_svar_identification -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | MODL-06 | unit | `pytest tests/test_regime_switching.py::test_regime_detection -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 1 | MODL-07 | unit | `pytest tests/test_crisis_index.py::test_composite_index -x` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 1 | MODL-08 | unit | `pytest tests/test_crisis_index.py::test_mechanism_decomposition -x` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 2 | MODL-05 | integration | `pytest tests/test_backtest.py::test_gfc_backtest -x` | ❌ W0 | ⬜ pending |
| 03-05-01 | 05 | 2 | DASH-06 | integration | `pytest tests/test_api_forecasting.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_stationarity.py` — stubs for MODL-02 (ADF + KPSS dual test)
- [ ] `tests/test_var_model.py` — stubs for MODL-01, MODL-04 (VAR fitting, forecasts with CIs)
- [ ] `tests/test_svar_model.py` — stubs for MODL-03 (SVAR identification)
- [ ] `tests/test_regime_switching.py` — stubs for MODL-06 (Markov regime detection)
- [ ] `tests/test_crisis_index.py` — stubs for MODL-07, MODL-08 (composite index, decomposition)
- [ ] `tests/test_backtest.py` — stubs for MODL-05 (GFC backtest)
- [ ] `tests/test_api_forecasting.py` — stubs for DASH-06 (API endpoints)
- [ ] `tests/conftest.py` additions — mock indicator data fixtures (synthetic time series)
- [ ] Framework install: `pip install statsmodels>=0.14.6` (add to pyproject.toml dependencies)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SSE streaming progress updates don't freeze dashboard | DASH-06 | Requires browser + real WebSocket connection | Open dashboard, trigger model training, verify progress bar animates without UI freezing |
| Forecast chart renders CI bands correctly | MODL-04 | Visual rendering correctness | Inspect forecast chart, verify dashed line + shaded 68%/95% bands render properly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
