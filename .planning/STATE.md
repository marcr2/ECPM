---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Active
stopped_at: Completed 02-04-PLAN.md
last_updated: "2026-03-23T21:02:22Z"
last_activity: 2026-03-23 -- Completed 02-04-PLAN.md (Indicator data and methodology documentation API endpoints)
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 12
  completed_plans: 12
  percent: 86
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** Ingest real macroeconomic data (FRED/BEA) and compute Marxist economic indicators visible in an interactive dashboard
**Current focus:** Phase 2 in progress: Feature Engineering and Core Dashboard

## Current Position

Phase: 2 of 5 (Feature Engineering and Core Dashboard)
Plan: 5 of 5 in current phase (02-01, 02-02, 02-03, 02-04 COMPLETE)
Status: Active
Last activity: 2026-03-23 -- Completed 02-04-PLAN.md (Indicator data and methodology documentation API endpoints)

Progress: [████████░░] 86%

## Performance Metrics

**Velocity:**
- Total plans completed: 12
- Average duration: ~5min
- Total execution time: ~0.8 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 7 | ~33min | ~5min |
| 02 | 5 | ~30min | ~6min |

**Recent Trend:**
- Last 5 plans: 02-01, 02-02, 02-03, 02-04
- Trend: Steady

*Updated after each plan completion*
| Phase 01 P03 | 8min | 2 tasks | 16 files |
| Phase 01 P05 | 5min | 3 tasks | 22 files |
| Phase 01 P06 | 3min | 2 tasks | 4 files |
| Phase 02 P01 | 4min | 2 tasks | 9 files |
| Phase 02 P02 | 8min | 2 tasks | 7 files |
| Phase 02 P03 | 6min | 2 tasks | 9 files |
| Phase 02 P04 | 12min | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 5-phase structure derived from requirement dependencies; Phases 3/4/5 can proceed semi-independently after Phase 2
- [Roadmap]: Research flags Phase 2 (NIPA-to-Marx mapping) and Phase 3 (SVAR identification) as needing domain-specific research during planning
- [01-04]: Redis cache keys use sha256 hash of sorted params for deterministic deduplication
- [01-04]: LOCF frequency alignment groups by period, keeps latest observation per period
- [01-04]: Celery task import wrapped in try/except for graceful fallback when Plan 01-03 incomplete
- [01-04]: Test fixture overrides get_db and lifespan for in-memory SQLite testing
- [Phase 01]: Canonical ingestion code in ecpm/ingestion/ with re-export modules at ecpm/clients/ and ecpm/pipeline for test import compatibility
- [Phase 01]: Pipeline uses session.merge() for SQLite-compatible upsert in tests, works with PG in production
- [Phase 01]: BEA series stored as BEA:{table}:L{line_number} for unique identification per table line item
- [01-05]: shadcn/ui component library for consistent dark-themed data-dense UI matching Bloomberg/Grafana aesthetic
- [01-05]: TanStack React Table for sortable/searchable/filterable series metadata table
- [01-05]: Auto-refresh polling every 30s instead of WebSocket for simplicity (macro data changes infrequently)
- [01-06]: Separated _HAS_ECPM_MODELS from _HAS_ECPM_DB in conftest to allow table creation without asyncpg
- [02-01]: Financial indicators (productivity-wage gap, credit-GDP gap, financial-real ratio, debt-service ratio) have default implementations on ABC -- methodology-invariant
- [02-01]: One-sided HP filter recursive approximation in base.py for credit-to-GDP gap (BIS lambda=400,000)
- [02-01]: StrEnum for IndicatorSlug for direct string comparison in URL routing
- [02-02]: Mappers accept descriptive keys (national_income, compensation, etc.) not FRED series IDs; orchestrator maps FRED IDs to descriptive keys
- [02-02]: Kliman uses FRED K1NTOTL1HI000 for historical-cost net fixed assets (vs K1NTOTL1SI000 current-cost for Shaikh/Tonak)
- [02-02]: ABC financial method defaults delegate to standalone financial.py functions rather than duplicating logic
- [02-02]: Redis cache key pattern indicators/{slug}/{methodology} with TTL 3600s
- [02-03]: ComposedChart (not LineChart) for indicator charts to support mixing Line + ReferenceArea children
- [02-03]: KaTeX renderToString directly (no react-katex wrapper) for React 19 compatibility
- [02-03]: Next.js 16 error.tsx uses unstable_retry (not reset) per framework docs
- [02-04]: Methodology routes merged into indicators router to prevent FastAPI dynamic route capture conflict
- [02-04]: Per-indicator financial FRED-to-key mappings replace global dict to resolve K1NTOTL1SI000/BOGZ1FL073164003Q ambiguity

### Pending Todos

None yet.

### Blockers/Concerns

- FRED API key and BEA API key required before Phase 1 execution
- Phase 2 planning needs domain research into Shaikh/Tonak and Kliman NIPA methodologies
- Phase 3 planning needs SVAR cross-validation protocol against R

## Session Continuity

Last session: 2026-03-23T21:02:22Z
Stopped at: Completed 02-04-PLAN.md
Resume file: None
