# Phase 3: Predictive Modeling and Crisis Index - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver econometric forecasting (VAR/SVAR), Markov regime-switching detection, a Composite Crisis Probability Index with mechanism decomposition, and historical backtesting against known crisis episodes. All displayed on a dedicated /forecasting dashboard section. Indicator computation (Phase 2), structural analysis (Phase 4), and corporate concentration (Phase 5) are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Forecast visualization
- Forecast toggle button on each indicator chart from Phase 2 — off by default, chart looks exactly like Phase 2 when disabled
- When toggled on: dashed forecast line extending from end of historical data, with nested semi-transparent CI bands (darker 68%, lighter 95%)
- User-adjustable forecast horizon via dropdown: 4Q, 8Q, 12Q, 16Q — default 8 quarters (2 years)
- All Marxist indicators computed in Phase 2 get forecast toggles — VAR model includes all as endogenous variables

### Crisis Index gauge
- Horizontal stacked bar showing Composite Crisis Probability Index (0-100%), decomposed by mechanism: TRPF, realization crisis, financial fragility — each segment colored by mechanism type
- Sparkline below the bar showing composite index trend over last 5-10 years
- Regime classification badge (green 'Normal', amber 'Stagnation', red 'Crisis') on the gauge card corner — from Markov regime-switching model
- Lives as hero element on dedicated /forecasting page, with forecast charts below
- Separate regime detail section further down the page: transition probability matrix, regime duration stats, historical regime timeline

### Backtest presentation
- Interactive timeline chart for each crisis episode: shows composite Crisis Index over the period, crisis episode as shaded region, vertical marker at 12-month and 24-month warning windows
- Per-mechanism decomposition: stacked area beneath the composite line showing TRPF, realization, and financial fragility contributions — see which mechanism "called" each crisis
- All 6 crisis episodes from Phase 2 annotations available: Great Depression (1929), Oil/Stagflation (1973), Volcker (1980), Dot-com (2001), GFC (2007-09), COVID (2020) — user selects which to view
- Pre-computed during model training pipeline — results cached, always available after training completes, no manual trigger needed

### Model training UX
- Auto-retrain triggered after data refresh (daily Celery beat from Phase 1), plus manual "Train Models" button on /forecasting page
- Progress bar + collapsible live log stream via SSE: shows overall step progress (stationarity tests → lag selection → VAR → SVAR → regime-switching → backtests) with checkmarks, plus detailed diagnostic output
- Non-blocking: dashboard stays fully usable during training. Old forecasts remain visible until new results replace them. Persistent training status card on /forecasting page
- Detailed diagnostics on failure: which step failed, error message, diagnostic context (e.g., stationarity test failures, convergence issues). Researcher needs to understand why

### Claude's Discretion
- VAR/SVAR implementation details (lag selection criteria weights, identification restrictions)
- Markov regime-switching model specification (number of regimes, transition assumptions)
- Crisis Index weighting scheme for combining TRPF, realization, and financial fragility sub-indices
- Exact stacked bar color palette and sparkline styling
- API endpoint structure for forecasts, backtest results, and training status
- Celery task chaining for the training pipeline
- Redis caching strategy for model outputs and backtest results

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Recharts library (Phase 2): extend for forecast CI bands, backtest timelines, and stacked bar gauge
- Crisis episode annotations (Phase 2): same 6 episodes used for both chart annotations and backtest targets
- Card component (frontend/src/components/ui/card.tsx): for gauge card, training status card, regime detail cards
- Skeleton component (frontend/src/components/ui/skeleton.tsx): loading states for forecast data
- api.ts client (frontend/src/lib/api.ts): extend for forecast/training/backtest endpoints
- Redis caching (backend/ecpm/cache.py): cache model predictions, backtest results
- Celery task infrastructure (backend/ecpm/tasks/): extend for model training pipeline tasks
- SSE streaming (backend): already set up for long-running jobs in Phase 1 — reuse for training progress
- LOCF frequency alignment (backend/ecpm/api/data.py): reuse for model input data preparation

### Established Patterns
- Async SQLAlchemy with FastAPI dependency injection (get_db)
- Pydantic response schemas with model_validate
- Redis cache with sha256 key hashing and configurable TTL
- structlog for structured logging
- shadcn/ui + Tailwind CSS dark theme
- Next.js App Router with page.tsx per route
- Sidebar navigation with section-based routing

### Integration Points
- Sidebar nav (frontend/src/components/layout/sidebar.tsx): "Forecasting" link at /forecasting currently disabled — enable and add sub-navigation
- API router (backend/ecpm/api/router.py): mount new forecast, training, and backtest endpoints
- Phase 2 indicator charts: add forecast toggle button that fetches forecast data from new endpoints
- Phase 2 computed indicators in TimescaleDB: source data for all VAR/SVAR models
- Celery beat schedule: add auto-retrain task after data ingestion completes

</code_context>

<specifics>
## Specific Ideas

- Forecast toggle keeps Phase 2 charts clean by default — predictive content is opt-in, not forced
- Stacked bar gauge directly encodes mechanism decomposition — no need to click through to see what's driving the signal
- Sparkline + regime badge on gauge card gives "at a glance" assessment: probability level + trend direction + regime classification
- Progress bar + log stream pattern borrowed from CI/CD dashboards — researcher can monitor at any depth
- Pre-computed backtests mean results are always ready when you navigate to them — no waiting

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-predictive-modeling-and-crisis-index*
*Context gathered: 2026-03-23*
