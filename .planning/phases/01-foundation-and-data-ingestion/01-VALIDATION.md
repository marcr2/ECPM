---
phase: 1
slug: foundation-and-data-ingestion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 + pytest-asyncio >= 0.23 |
| **Config file** | `backend/pyproject.toml` [tool.pytest.ini_options] — Wave 0 installs |
| **Quick run command** | `docker compose exec backend pytest tests/ -x --timeout=30` |
| **Full suite command** | `docker compose exec backend pytest tests/ -v --timeout=60` |
| **Estimated runtime** | ~30 seconds (quick) / ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec backend pytest tests/ -x --timeout=30`
- **After every plan wave:** Run `docker compose exec backend pytest tests/ -v --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFR-01 | smoke | `docker compose up -d && docker compose ps --format json` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | INFR-05 | smoke | `docker compose ps --format json \| jq '.[] .Health'` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | DATA-01 | integration | `pytest tests/test_fred_client.py -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | DATA-08 | unit | `pytest tests/test_fred_client.py::test_retry_backoff -x` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | DATA-03 | integration | `pytest tests/test_bea_client.py -x` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 1 | DATA-02 | integration | `pytest tests/test_ingestion_pipeline.py::test_fred_persistence -x` | ❌ W0 | ⬜ pending |
| 01-02-05 | 02 | 1 | DATA-06 | unit | `pytest tests/test_ingestion_pipeline.py::test_gap_handling -x` | ❌ W0 | ⬜ pending |
| 01-02-06 | 02 | 1 | DATA-07 | unit | `pytest tests/test_ingestion_pipeline.py::test_native_frequency -x` | ❌ W0 | ⬜ pending |
| 01-02-07 | 02 | 1 | DATA-04 | unit | `pytest tests/test_models.py::test_metadata_fields -x` | ❌ W0 | ⬜ pending |
| 01-02-08 | 02 | 1 | DATA-09 | unit | `pytest tests/test_models.py::test_vintage_date_column -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | DATA-05 | integration | `pytest tests/test_tasks.py::test_scheduled_fetch -x` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | INFR-02 | integration | `pytest tests/test_api.py -x` | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 2 | INFR-03 | integration | `pytest tests/test_api.py::test_sse_stream -x` | ❌ W0 | ⬜ pending |
| 01-03-04 | 03 | 2 | INFR-04 | integration | `pytest tests/test_cache.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/pyproject.toml` — pytest + pytest-asyncio + pytest-timeout configuration
- [ ] `backend/tests/conftest.py` — async session fixtures, test database, mock API clients
- [ ] `backend/tests/test_fred_client.py` — covers DATA-01, DATA-08
- [ ] `backend/tests/test_bea_client.py` — covers DATA-03
- [ ] `backend/tests/test_ingestion_pipeline.py` — covers DATA-02, DATA-06, DATA-07
- [ ] `backend/tests/test_models.py` — covers DATA-04, DATA-09
- [ ] `backend/tests/test_tasks.py` — covers DATA-05
- [ ] `backend/tests/test_api.py` — covers INFR-02, INFR-03
- [ ] `backend/tests/test_cache.py` — covers INFR-04
- [ ] Framework install: `pip install pytest pytest-asyncio pytest-timeout` — none detected

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker Compose starts all 4 containers | INFR-01 | Requires Docker runtime | Run `docker compose up -d`, verify 4 containers with `docker compose ps` |
| Health checks pass | INFR-05 | Requires running containers | Check `docker compose ps` shows "healthy" for all services |
| Next.js frontend loads | INFR-01 | Visual verification | Open `http://localhost:3000` and verify skeleton page renders |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
