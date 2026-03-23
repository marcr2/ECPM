---
phase: 4
slug: structural-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `backend/pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `cd backend && python -m pytest tests/test_structural*.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_structural*.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 0 | STRC-01, STRC-02, STRC-03, STRC-04, STRC-05, DASH-07 | scaffold | `pytest tests/test_structural*.py --collect-only` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | STRC-01 | unit | `pytest tests/test_structural_leontief.py::test_build_coefficients -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | STRC-02 | unit | `pytest tests/test_structural_leontief.py::test_leontief_inverse -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | STRC-03 | unit | `pytest tests/test_structural_shock.py -x` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 2 | STRC-04 | unit | `pytest tests/test_structural_departments.py::test_classification -x` | ❌ W0 | ⬜ pending |
| 04-03-03 | 03 | 2 | STRC-05 | unit | `pytest tests/test_structural_departments.py::test_proportionality -x` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 2 | DASH-07 | integration | `pytest tests/test_api_structural.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_structural_leontief.py` — stubs for STRC-01, STRC-02 (matrix construction, inverse, stability checks)
- [ ] `tests/test_structural_shock.py` — stubs for STRC-03 (shock propagation, multi-sector scenarios, weakest link)
- [ ] `tests/test_structural_departments.py` — stubs for STRC-04, STRC-05 (Dept I/II classification, proportionality conditions)
- [ ] `tests/test_api_structural.py` — stubs for DASH-07 (I-O data endpoints, shock simulation endpoint, reproduction schema endpoint)
- [ ] Synthetic I-O fixtures in conftest.py (small 3x3 or 5x5 matrices with known analytical solutions)
- [ ] No new framework install needed (pytest already configured)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Heatmap renders 71x71 matrix with drill-down | DASH-07 | Visual rendering in browser | Load /structural, verify heatmap displays, click cell to drill into sub-sectors |
| Sankey diagram shows Dept I/II flows at 3 depth levels | DASH-07 | Visual rendering in browser | Load /structural, toggle between department-only, dept+sub-sectors, full 71-sector views |
| Year selector updates both heatmap and Sankey | DASH-07 | UI interaction | Select different years, verify data changes in both visualizations |
| Shock propagation highlights path on heatmap | DASH-07 | Visual rendering in browser | Run a shock simulation, verify bar chart + heatmap highlight appear side by side |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
