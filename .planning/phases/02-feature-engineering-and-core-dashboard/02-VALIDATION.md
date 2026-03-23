---
phase: 2
slug: feature-engineering-and-core-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio 0.24.x |
| **Config file** | backend/pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x --timeout=30` |
| **Full suite command** | `cd backend && python -m pytest tests/ --timeout=30 -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x --timeout=30`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ --timeout=30 -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | FEAT-01 | unit | `pytest tests/test_indicators.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | FEAT-02 | unit | `pytest tests/test_indicators.py::test_rate_of_profit -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | FEAT-03 | unit | `pytest tests/test_indicators.py::test_occ -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | FEAT-04 | unit | `pytest tests/test_indicators.py::test_rate_of_surplus_value -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | FEAT-05 | unit | `pytest tests/test_indicators.py::test_mass_of_profit -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | FEAT-06 | unit | `pytest tests/test_indicators.py::test_productivity_wage_gap -x` | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 1 | FEAT-07 | unit | `pytest tests/test_indicators.py::test_financial_fragility -x` | ❌ W0 | ⬜ pending |
| 02-01-08 | 01 | 1 | FEAT-09 | unit | `pytest tests/test_indicators.py::test_frequency_alignment -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | FEAT-08 | integration | `pytest tests/test_api_indicators.py::test_methodology_docs -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | DASH-04 | smoke | `pytest tests/test_api_indicators.py::test_overview_endpoint -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | DASH-01 | manual-only | Visual verification in browser | N/A | ⬜ pending |
| 02-03-02 | 03 | 2 | DASH-02 | manual-only | Visual verification in browser | N/A | ⬜ pending |
| 02-03-03 | 03 | 2 | DASH-03 | manual-only | Visual verification in browser | N/A | ⬜ pending |
| 02-03-04 | 03 | 2 | DASH-05 | manual-only | Visual verification in browser | N/A | ⬜ pending |
| 02-03-05 | 03 | 3 | DASH-08 | manual-only | Visual verification + error injection | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_indicators.py` — stubs for FEAT-01 through FEAT-07, FEAT-09 (indicator computation unit tests)
- [ ] `tests/test_api_indicators.py` — stubs for FEAT-08, DASH-04 (API endpoint integration tests)
- [ ] `tests/test_methodology_registry.py` — stubs for FEAT-01 (registry + plugin pattern)
- [ ] Shared fixtures: mock NIPA data (series dict with known values for verifying formulas)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Time-series charts render with zoom/pan/brush | DASH-01 | Recharts visual rendering | Load /indicators/{slug}, verify chart renders, test zoom/pan/brush interactions |
| Dual y-axis overlay | DASH-02 | Visual multi-axis alignment | On detail page, add overlay indicator, verify dual y-axes render correctly |
| Crisis annotations on charts | DASH-03 | Visual ReferenceArea rendering | Verify shaded regions appear at correct date ranges for all 6 crisis episodes |
| Methodology docs with KaTeX | DASH-05 | KaTeX formula rendering | Load /indicators/methodology, verify formulas render (fractions, subscripts, Greek) |
| Loading/error states | DASH-08 | UI state transitions | Test slow load, API failure, empty data scenarios |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
