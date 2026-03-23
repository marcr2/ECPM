# Requirements: Economic Crisis Prediction Model (ECPM)

**Defined:** 2026-03-23
**Core Value:** Ingest real macroeconomic data and compute Marxist economic indicators visible in an interactive dashboard

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Ingestion

- [x] **DATA-01**: System can retrieve time-series data from FRED API with API key authentication
- [x] **DATA-02**: System caches all retrieved FRED series in TimescaleDB to avoid re-fetching
- [x] **DATA-03**: System can ingest BEA NIPA tables (corporate profits, national income, fixed assets, GDP by industry)
- [ ] **DATA-04**: System stores series metadata (units, frequency, seasonality, source, last updated) alongside data
- [x] **DATA-05**: System runs scheduled data fetches via Celery beat on configurable intervals
- [x] **DATA-06**: System handles missing data with explicit interpolation and frequency alignment strategies
- [ ] **DATA-07**: System stores all series at native frequency (monthly/quarterly/annual) without implicit resampling
- [x] **DATA-08**: System implements exponential backoff retry for API calls (FRED rate limit: 120 req/min)
- [ ] **DATA-09**: TimescaleDB schema includes vintage_date column for future revision tracking support

### Feature Engineering

- [ ] **FEAT-01**: System provides a configurable NIPA-to-Marx translation engine with at least one canonical methodology (Shaikh/Tonak)
- [ ] **FEAT-02**: System computes rate of profit: r = Surplus / (Constant Capital + Variable Capital) from NIPA proxies
- [ ] **FEAT-03**: System computes organic composition of capital: OCC = C/V from NIPA proxies
- [ ] **FEAT-04**: System computes rate of surplus value: s/v = (Value Added - Wages) / Wages from NIPA proxies
- [ ] **FEAT-05**: System computes mass of profit and tracks mass vs. rate of profit divergence over time
- [ ] **FEAT-06**: System computes productivity-wage gap (labor productivity growth vs. real wage growth) over rolling windows
- [ ] **FEAT-07**: System computes financial fragility indicators: credit-to-GDP gap, financial-to-real asset ratio, corporate debt service ratio
- [ ] **FEAT-08**: System documents every NIPA-to-Marx mapping with specific table/line item references and theoretical citations
- [ ] **FEAT-09**: System performs explicit frequency alignment at model-time with documented strategy parameter

### Predictive Modeling

- [ ] **MODL-01**: System runs VAR models on key Marxist indicators with proper lag selection (AIC/BIC/HQIC)
- [ ] **MODL-02**: System performs mandatory stationarity preprocessing (ADF + KPSS tests) before any VAR modeling
- [ ] **MODL-03**: System runs SVAR with theoretically motivated identification restrictions from Marxist causal ordering
- [ ] **MODL-04**: System produces forecasts with confidence intervals / uncertainty quantification
- [ ] **MODL-05**: System backtests against the 2007-2009 Global Financial Crisis (indicators should rise 12-24 months prior)
- [ ] **MODL-06**: System implements Markov regime-switching models to detect crisis vs. normal vs. stagnation regimes
- [ ] **MODL-07**: System produces a Composite Crisis Probability Index synthesizing TRPF, realization, and financial fragility indicators
- [ ] **MODL-08**: Crisis Probability Index is decomposable by crisis mechanism (shows which typology is driving the signal)

### Structural Analysis

- [ ] **STRC-01**: System ingests BEA input-output tables and computes Leontief technical coefficient matrix A
- [ ] **STRC-02**: System computes Leontief inverse (I-A)^-1 with numerical stability checks (condition number, Hawkins-Simon)
- [ ] **STRC-03**: System simulates shock propagation through inter-industry structure using Leontief inverse
- [ ] **STRC-04**: System aggregates sectors into Department I (means of production) and Department II (means of consumption)
- [ ] **STRC-05**: System checks proportionality conditions for expanded reproduction (Marx Capital Vol. II)

### Corporation Mapping

- [ ] **CORP-01**: System ingests market share data for top corporations by industry sector (using parent company, e.g., Alphabet not YouTube)
- [ ] **CORP-02**: System maps corporate concentration (market share of top N firms per sector) to crisis indicator trajectories over time
- [ ] **CORP-03**: System computes confidence scores for corporation-to-crisis correlations (indicating strength and reliability of the mapping)
- [ ] **CORP-04**: System tracks changes in corporate concentration over time as a proxy for monopoly/centralization of capital tendencies
- [ ] **CORP-05**: User can view corporation-to-crisis mappings on the dashboard with confidence scores and sector breakdowns

### Frontend Dashboard

- [ ] **DASH-01**: User can view interactive time-series line charts with zoom, pan, and date range selection
- [ ] **DASH-02**: User can overlay multiple indicators on the same chart with dual y-axes
- [ ] **DASH-03**: User can see crisis episode annotations (vertical lines/shaded regions) for known historical crises
- [ ] **DASH-04**: User can view an indicator overview/summary page showing current state of all computed indicators
- [ ] **DASH-05**: User can view methodology documentation explaining each NIPA-to-Marx mapping and its theoretical basis
- [ ] **DASH-06**: User can view the Composite Crisis Probability Index with mechanism decomposition gauge
- [ ] **DASH-07**: User can view a Leontief I-O reproduction schema visualization (heatmap + Sankey/chord diagram)
- [ ] **DASH-08**: Dashboard shows loading states and error boundaries for all data-dependent components

### Infrastructure

- [x] **INFR-01**: System runs via Docker Compose with TimescaleDB, Redis, Python backend, and Next.js frontend containers
- [x] **INFR-02**: FastAPI backend exposes REST endpoints for all data, features, model outputs
- [x] **INFR-03**: FastAPI uses SSE for streaming progress of long-running jobs (model training, backtesting)
- [x] **INFR-04**: Redis caches expensive computations (Leontief inverse, model predictions, dashboard state)
- [x] **INFR-05**: Docker Compose includes health checks and separate dev/prod configurations

## v2 Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Simulation

- **SIML-01**: Agent-based simulation of capitalist dynamics using Mesa framework
- **SIML-02**: Simulation control panel with adjustable parameters (exploitation rate, accumulation rate, credit expansion)
- **SIML-03**: Counterfactual scenario simulation ("what if wages kept pace with productivity?")

### Expanded Coverage

- **EXPD-01**: BLS data integration (real wages, labor productivity, unit labor costs)
- **EXPD-02**: World Bank / IMF / BIS data for imperialist displacement indicators
- **EXPD-03**: Imperialist displacement indicators: capital outflow ratios, terms of trade, peripheral debt-to-export
- **EXPD-04**: Cybernetic viability indicators (Beer): regulatory lag, planning horizon compression, feedback integrity
- **EXPD-05**: Data vintage/revision tracking with FRED ALFRED vintage retrieval
- **EXPD-06**: Extended historical calibration (1929, 1973, 1997, 2001, 2020 in addition to 2008)

### Advanced Dashboard

- **ADVD-01**: Theoretical annotation layer linking indicators to Marx/Luxemburg/Lenin/Beer source texts
- **ADVD-02**: Beer VSM cybernetic system diagram with dynamic data overlays
- **ADVD-03**: Data export (CSV/JSON) for all indicators and model outputs
- **ADVD-04**: Anomaly detection visualization (Isolation Forest crisis fingerprints)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time streaming data | Macro data is quarterly/monthly with lags; no meaningful stream to consume |
| Multi-user / authentication | Single-user personal research tool |
| LLM-powered "crisis chat" | Hallucination risk undermines rigorous theoretical framework |
| Automated trading signals | Misunderstands purpose; Marxist crisis theory operates on multi-year timescales |
| Mobile-responsive design | Dense economic visualizations require desktop screen real estate |
| Cloud deployment / SaaS | Local Docker Compose only; no hosting costs or security concerns |
| Custom no-code indicator builder | NIPA-to-Marx translation requires economic expertise, not drag-and-drop |
| Multi-country support | Each country has different statistical agencies and data formats; US-only for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Pending |
| DATA-05 | Phase 1 | Complete |
| DATA-06 | Phase 1 | Complete |
| DATA-07 | Phase 1 | Pending |
| DATA-08 | Phase 1 | Complete |
| DATA-09 | Phase 1 | Pending |
| FEAT-01 | Phase 2 | Pending |
| FEAT-02 | Phase 2 | Pending |
| FEAT-03 | Phase 2 | Pending |
| FEAT-04 | Phase 2 | Pending |
| FEAT-05 | Phase 2 | Pending |
| FEAT-06 | Phase 2 | Pending |
| FEAT-07 | Phase 2 | Pending |
| FEAT-08 | Phase 2 | Pending |
| FEAT-09 | Phase 2 | Pending |
| MODL-01 | Phase 3 | Pending |
| MODL-02 | Phase 3 | Pending |
| MODL-03 | Phase 3 | Pending |
| MODL-04 | Phase 3 | Pending |
| MODL-05 | Phase 3 | Pending |
| MODL-06 | Phase 3 | Pending |
| MODL-07 | Phase 3 | Pending |
| MODL-08 | Phase 3 | Pending |
| STRC-01 | Phase 4 | Pending |
| STRC-02 | Phase 4 | Pending |
| STRC-03 | Phase 4 | Pending |
| STRC-04 | Phase 4 | Pending |
| STRC-05 | Phase 4 | Pending |
| CORP-01 | Phase 5 | Pending |
| CORP-02 | Phase 5 | Pending |
| CORP-03 | Phase 5 | Pending |
| CORP-04 | Phase 5 | Pending |
| CORP-05 | Phase 5 | Pending |
| DASH-01 | Phase 2 | Pending |
| DASH-02 | Phase 2 | Pending |
| DASH-03 | Phase 2 | Pending |
| DASH-04 | Phase 2 | Pending |
| DASH-05 | Phase 2 | Pending |
| DASH-06 | Phase 3 | Pending |
| DASH-07 | Phase 4 | Pending |
| DASH-08 | Phase 2 | Pending |
| INFR-01 | Phase 1 | Complete |
| INFR-02 | Phase 1 | Complete |
| INFR-03 | Phase 1 | Complete |
| INFR-04 | Phase 1 | Complete |
| INFR-05 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 49 total
- Mapped to phases: 49
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation*
