---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Active
stopped_at: Completed quick-005-PLAN.md
last_updated: "2026-03-24T01:30:00.000Z"
last_activity: 2026-03-24 -- Completed quick-005-PLAN.md (Wave 6 - Phase 4 Frontend)
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 17
  completed_plans: 15
  percent: 88
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** Ingest real macroeconomic data (FRED/BEA) and compute Marxist economic indicators visible in an interactive dashboard
**Current focus:** Phase 4 Complete: Structural Analysis (Backend + Frontend)

## Current Position

Phase: 4 of 5 (Structural Analysis) - COMPLETE
Plan: Phase 4 complete (quick-004 backend + quick-005 frontend)
Status: Active
Last activity: 2026-03-24 -- Completed quick-005-PLAN.md (Wave 6 - Phase 4 Frontend)

Progress: [█████████░] 88%

### Quick Tasks
- quick-001: Wave 2 ECPM completion (Celery pipeline + forecasting API) - COMPLETE
- quick-002: Wave 3 Frontend forecasting UI - COMPLETE
- quick-003: Wave 4 Phase 3 Integration (forecast overlay, sidebar, auto-retrain) - COMPLETE
- quick-004: Wave 5 Phase 4 Backend (structural analysis, Leontief, shock propagation) - COMPLETE
- quick-005: Wave 6 Phase 4 Frontend (Nivo heatmap, Sankey, shock simulation UI) - COMPLETE

## Performance Metrics

**Velocity:**
- Total plans completed: 14
- Average duration: ~5min
- Total execution time: ~1.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 7 | ~33min | ~5min |
| 02 | 5 | ~30min | ~6min |
| 03 | 1 | ~4min | ~4min |

**Recent Trend:**
- Last 5 plans: 02-02, 02-03, 02-04, 03-01, quick-005
- Trend: Steady

*Updated after each plan completion*
| Phase 01 P03 | 8min | 2 tasks | 16 files |
| Phase 01 P05 | 5min | 3 tasks | 22 files |
| Phase 01 P06 | 3min | 2 tasks | 4 files |
| Phase 02 P01 | 4min | 2 tasks | 9 files |
| Phase 02 P02 | 8min | 2 tasks | 7 files |
| Phase 02 P03 | 6min | 2 tasks | 9 files |
| Phase 02 P04 | 12min | 2 tasks | 5 files |
| Phase 03 P01 | 4min | 2 tasks | 11 files |
| Phase 03 P02 | 9min | 2 tasks | 7 files |
| quick-005 | 8min | 5 tasks | 14 files |

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
- [03-01]: pytest.importorskip at module level for clean skip-marking of unimplemented modeling modules
- [03-01]: numpy default_rng(42) for reproducible synthetic data (modern Generator API)
- [03-01]: Synthetic indicator data uses realistic economic trends for domain validity in tests
- [Phase 03-02]: Global cross-sectional percentile normalization for crisis index to preserve absolute level sensitivity
- [Phase 03-02]: Markov transition matrix transposed to standard convention (rows sum to 1) from statsmodels convention (columns sum to 1)
- [Phase 03-02]: SVAR fitting returns None on convergence failure for graceful degradation
- [quick-001]: Versioned Redis keys (ecpm:forecasts:v{timestamp}) with 3600s TTL for data, no TTL for 'latest' pointers
- [quick-001]: Sync redis.StrictRedis in Celery tasks (not async - Celery workers are synchronous)
- [quick-001]: Progress channel 'ecpm:training:progress' for pubsub-based SSE streaming
- [quick-002]: SSE subscription pattern returns EventSource for caller cleanup
- [quick-002]: Removed Recharts Tooltip formatter props due to Recharts 3 strict typing
- [quick-003]: Recharts Area with [lower, upper] array format for CI band gradient rendering
- [quick-003]: Forecast toggle uses per-page useState with lazy fetch on enable
- [quick-003]: Auto-retrain hardcoded 5 minute offset from data refresh schedule
- [quick-004]: Synthetic 3x3 I-O fixtures with known analytical Leontief inverse for deterministic testing
- [quick-004]: DEPT_I_CODES static set for means-of-production NAICS classification
- [quick-004]: Simplified c/v/s decomposition uses 60/40 labor/surplus split (placeholder until GDPbyIndustry integration)
- [quick-004]: Default BEA TableIDs cached (Use=259, Make=47) to avoid repeated API discovery
- [quick-005]: HeatMapCanvas over HeatMap for 71x71 matrix performance
- [quick-005]: Build sankey flows from 2x2 matrix when sankey_data is null
- [quick-005]: Native HTML select for year selector (simpler than Base UI Select)

### Pending Todos

None yet.

### Blockers/Concerns

- FRED API key and BEA API key required before Phase 1 execution
- Phase 2 planning needs domain research into Shaikh/Tonak and Kliman NIPA methodologies
- Phase 3 planning needs SVAR cross-validation protocol against R

## Session Continuity

Last session: 2026-03-24T01:30:00.000Z
Stopped at: Completed quick-005-PLAN.md
Resume file: None
