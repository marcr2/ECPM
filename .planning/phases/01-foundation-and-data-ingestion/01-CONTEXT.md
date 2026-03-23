# Phase 1: Foundation and Data Ingestion - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a working Docker Compose stack (TimescaleDB, Redis, Python/FastAPI backend, Next.js frontend) with an automated FRED/BEA data ingestion pipeline. User can start the system, trigger data fetches, query stored time-series via API endpoints, and see ingested data in a skeleton dashboard. No indicator computation, no visualizations beyond a data overview table.

</domain>

<decisions>
## Implementation Decisions

### Initial data scope
- Shaikh/Tonak methodology drives series selection (most widely cited Marxist NIPA mapping)
- BEA NIPA tables to ingest: Corporate profits (Table 6.19), National income (Table 1.12), Fixed assets (FAT Tables), GDP by industry (Tables 1.3/1.15)
- Broad FRED coverage (~50-80 series): Phase 2 essentials plus GDP components, interest rates, money supply, unemployment, industrial production, housing
- Series list managed via configuration file (YAML/JSON), not hardcoded — easy to add/remove without touching code

### Missing data handling
- Store all series at native frequency (monthly/quarterly/annual) — no implicit resampling
- Frequency alignment happens at query time with explicit strategy parameter
- Interpolation: LOCF (last observation carried forward) only — most conservative, no synthetic data points
- Gaps: flag explicitly with null values and metadata markers, do not interpolate across gaps — let downstream consumers decide
- Log warnings when gaps are detected during ingestion
- Vintage tracking: schema includes vintage_date column per DATA-09, but no ALFRED vintage retrieval pipeline (that's v2 EXPD-05)

### Scheduling and refresh
- Daily automatic re-fetch via Celery beat
- Manual trigger available via both FastAPI endpoint (POST /api/data/fetch) and CLI command (python -m ecpm fetch)
- API keys (FRED, BEA) provided via .env file, with .env.example template committed to repo
- Structured JSON logging for all fetch attempts (series, status, error, retry count)
- /api/data/status endpoint showing last fetch time, failures, and next scheduled run

### Frontend skeleton
- Full navigation shell with sidebar placeholder links for all 5 phases: Data Overview (active), Indicators (Phase 2), Forecasting (Phase 3), Structural Analysis (Phase 4), Concentration (Phase 5) — disabled/greyed out
- Dark theme, data-dense aesthetic (Bloomberg Terminal / Grafana feel) — research tool, not consumer app
- Data overview page with full metadata table: Series ID, Name, Source (FRED/BEA), Frequency, Last Updated, Observation Count, Status (OK/stale/error) — sortable and searchable

### Claude's Discretion
- Exact TimescaleDB schema design (table structure, indexes, hypertable configuration)
- FastAPI project structure and endpoint naming conventions
- Next.js component library choice (shadcn/ui, etc.)
- Docker Compose networking and health check specifics
- Celery configuration details
- Redis caching strategy for API responses

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- None — patterns will be established in this phase

### Integration Points
- FRED API (api.stlouisfed.org) — requires API key, 120 req/min rate limit
- BEA API (apps.bea.gov/api) — requires API key
- Docker Compose orchestrates all four services

</code_context>

<specifics>
## Specific Ideas

- Navigation shell should give a sense of the full system even in Phase 1 — greyed-out links for future phases
- Data overview table should immediately prove the pipeline works end-to-end
- Dark, data-dense aesthetic throughout — this is a research instrument, not a consumer product
- Config-driven series list so the researcher can expand coverage without code changes

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-and-data-ingestion*
*Context gathered: 2026-03-23*
