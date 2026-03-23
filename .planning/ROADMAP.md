# Roadmap: Economic Crisis Prediction Model (ECPM)

## Overview

ECPM delivers a working pipeline from raw US macroeconomic data (FRED/BEA) through Marxist economic indicator computation, econometric forecasting, structural analysis, and corporate concentration mapping, all visible in an interactive Next.js dashboard. The build order follows hard data dependencies: nothing downstream works without data in the database, no model runs without computed indicators, no structural analysis without I-O tables, and no corporation-crisis mapping without both indicators and market data. Each phase delivers an independently verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation and Data Ingestion** - Docker stack, TimescaleDB schema, FRED/BEA data pipeline, FastAPI/Next.js skeletons
- [ ] **Phase 2: Feature Engineering and Core Dashboard** - NIPA-to-Marx translation engine, all Marxist indicators, interactive time-series dashboard
- [ ] **Phase 3: Predictive Modeling and Crisis Index** - VAR/SVAR forecasting, regime-switching detection, Composite Crisis Probability Index, historical backtesting
- [ ] **Phase 4: Structural Analysis** - Leontief I-O ingestion, inverse computation, shock propagation, reproduction schema visualization
- [ ] **Phase 5: Corporate Concentration Analysis** - Corporation market share ingestion, concentration-to-crisis mapping, dashboard integration

## Phase Details

### Phase 1: Foundation and Data Ingestion
**Goal**: User can start the system with Docker Compose and see real FRED/BEA macroeconomic data stored and accessible through API endpoints
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07, DATA-08, DATA-09, INFR-01, INFR-02, INFR-03, INFR-04, INFR-05
**Success Criteria** (what must be TRUE):
  1. User can run `docker compose up` and all four containers (TimescaleDB, Redis, Python backend, Next.js frontend) start with passing health checks
  2. User can trigger a data fetch that retrieves real FRED series and BEA NIPA tables, with results persisted in TimescaleDB at native frequency
  3. User can query FastAPI endpoints and receive stored time-series data with metadata (units, frequency, source, last updated)
  4. System automatically re-fetches data on a configurable schedule without manual intervention, with exponential backoff on API failures
  5. User can see the Next.js frontend loads and connects to the backend API (skeleton page, no visualizations yet)
**Plans:** 6 plans

Plans:
- [ ] 01-00-PLAN.md -- Wave 0 test infrastructure (all test scaffold files and conftest)
- [ ] 01-01-PLAN.md -- Docker Compose stack, Dockerfiles, env template, pyproject.toml
- [ ] 01-02-PLAN.md -- Python backend package, models, Alembic migrations, series config
- [ ] 01-03-PLAN.md -- FRED/BEA ingestion clients, pipeline orchestrator, Celery scheduling, CLI
- [ ] 01-04-PLAN.md -- FastAPI REST endpoints, Redis caching, SSE streaming, status monitoring
- [ ] 01-05-PLAN.md -- Next.js frontend skeleton, dark theme, navigation shell, data overview table

### Phase 2: Feature Engineering and Core Dashboard
**Goal**: User can explore computed Marxist economic indicators (rate of profit, OCC, rate of surplus value, productivity-wage gap, financial fragility) in an interactive dashboard with documented methodology
**Depends on**: Phase 1
**Requirements**: FEAT-01, FEAT-02, FEAT-03, FEAT-04, FEAT-05, FEAT-06, FEAT-07, FEAT-08, FEAT-09, DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-08
**Success Criteria** (what must be TRUE):
  1. User can view the rate of profit, organic composition of capital, and rate of surplus value as interactive time-series charts with zoom, pan, and date range selection
  2. User can overlay multiple indicators on the same chart (e.g., rate of profit vs. mass of profit) with dual y-axes to see divergence patterns
  3. User can see historical crisis episodes (1929, 1973, 2008, etc.) as annotations on all time-series charts for visual pattern matching
  4. User can view an indicator overview page showing the current state of all computed indicators at a glance
  5. User can read methodology documentation explaining each NIPA-to-Marx mapping with specific table/line item references and theoretical citations
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD
- [ ] 02-03: TBD

### Phase 3: Predictive Modeling and Crisis Index
**Goal**: User can see econometric forecasts of Marxist indicators, detect crisis regimes, and monitor a Composite Crisis Probability Index that decomposes by crisis mechanism
**Depends on**: Phase 2
**Requirements**: MODL-01, MODL-02, MODL-03, MODL-04, MODL-05, MODL-06, MODL-07, MODL-08, DASH-06
**Success Criteria** (what must be TRUE):
  1. User can view VAR/SVAR forecasts of key Marxist indicators with confidence intervals extending into the future
  2. User can see the Composite Crisis Probability Index gauge on the dashboard, decomposed by crisis mechanism (TRPF, realization, financial fragility)
  3. User can run a backtest against the 2007-2009 crisis and see that crisis indicators rise 12-24 months prior to the event
  4. User can see regime-switching detection results showing whether the current period is classified as crisis, normal, or stagnation
  5. User can monitor long-running model training jobs via streaming progress updates (SSE) without the dashboard freezing
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Structural Analysis
**Goal**: User can explore inter-industry structure through Leontief input-output analysis, simulate sectoral shock propagation, and verify Marx's expanded reproduction conditions
**Depends on**: Phase 1
**Requirements**: STRC-01, STRC-02, STRC-03, STRC-04, STRC-05, DASH-07
**Success Criteria** (what must be TRUE):
  1. User can view the Leontief technical coefficient matrix as a heatmap showing inter-industry dependencies
  2. User can simulate a shock to any sector and see how it propagates through the inter-industry structure via the Leontief inverse
  3. User can see sectors aggregated into Department I (means of production) and Department II (means of consumption) with proportionality condition checks
  4. User can view a Sankey or chord diagram showing material flows between sectors in the reproduction schema
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Corporate Concentration Analysis
**Goal**: User can see how corporate concentration maps to crisis indicator trajectories, connecting macro-level Marxist categories to firm-level monopolization tendencies
**Depends on**: Phase 2
**Requirements**: CORP-01, CORP-02, CORP-03, CORP-04, CORP-05
**Success Criteria** (what must be TRUE):
  1. User can view top corporations by market share for each industry sector, with concentration ratios tracked over time
  2. User can see corporation-to-crisis indicator correlations with confidence scores indicating strength and reliability
  3. User can view sector-level breakdowns showing how monopoly/centralization trends relate to rate of profit, realization gaps, and financial fragility
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order. Phase 4 depends on Phase 1 (not Phase 3), so Phases 3, 4, and 5 could theoretically overlap, but sequential execution is recommended.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Data Ingestion | 0/6 | Not started | - |
| 2. Feature Engineering and Core Dashboard | 0/3 | Not started | - |
| 3. Predictive Modeling and Crisis Index | 0/3 | Not started | - |
| 4. Structural Analysis | 0/2 | Not started | - |
| 5. Corporate Concentration Analysis | 0/2 | Not started | - |
