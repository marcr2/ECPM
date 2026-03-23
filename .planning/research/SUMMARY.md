# Project Research Summary

**Project:** Economic Crisis Prediction Model (ECPM)
**Domain:** Macroeconomic crisis prediction platform — Marxist political economy
**Researched:** 2026-03-23
**Confidence:** HIGH (stack, architecture, pitfalls) / MEDIUM (features — niche domain, no direct competitors)

## Executive Summary

ECPM is a single-user research platform that automates the empirical work Marxist economists currently do manually in spreadsheets: translating US national accounts (NIPA/BEA) into Marxist economic categories, computing the rate of profit and organic composition of capital, running econometric forecasts, and visualizing results through an interactive dashboard. The recommended approach is a strict four-layer pipeline — data ingestion, feature engineering, predictive modeling, and presentation — where each layer communicates exclusively through a shared TimescaleDB database and a FastAPI REST layer. No existing tool does this; the closest analogues are static spreadsheets circulated in academic papers by researchers like Michael Roberts and Anwar Shaikh.

The recommended stack centers on Python 3.12 (hard requirement from Mesa 3.5), FastAPI, TimescaleDB, and Next.js 16. Key technology substitutions versus the original architecture document: replace Polars with pandas-only (all downstream econometric libraries expect pandas DataFrames), replace hmmlearn with statsmodels' built-in MarkovAutoregression, skip Airflow/Dagster in favor of Celery beat, and replace Plotly.js with Nivo + D3 (Plotly is 3.5MB and conflicts with React's virtual DOM). The NIPA-to-Marxist category translation engine is the intellectual core and the highest-risk component; it must be configurable and multi-methodology from the start, not hardcoded to a single formula.

The three risks that must be designed against from day one are: (1) look-ahead bias in historical calibration — the TimescaleDB schema must include a `vintage_date` column even if MVP only fetches latest values; (2) mixed-frequency data corruption — all series must be stored at their native frequency and aligned only at model-time; and (3) VAR/SVAR misspecification — a mandatory stationarity preprocessing pipeline (ADF/KPSS tests, lag selection by information criteria) must precede any econometric modeling. Retrofitting any of these three properties after the fact carries HIGH recovery cost.

---

## Key Findings

### Recommended Stack

Python 3.12 is a hard constraint imposed by Mesa 3.5 (the ABM framework), overriding the architecture document's "Python 3.10+" specification. All other scientific libraries confirm 3.12 compatibility. The overall backend stack is well-understood and uses established, actively maintained libraries; the only medium-confidence choice is Celery for task scheduling (APScheduler would also work for single-user use, but Celery handles long-running simulation tasks better). The frontend stack uses Next.js 16.2 LTS with Nivo + D3 for visualization; the D3 dependency is non-negotiable because the Beer VSM diagram, Leontief I-O matrix view, and sectoral dependency graph are too custom for any pre-built chart library.

**Core technologies:**
- Python 3.12: backend runtime — hard requirement from Mesa 3.5; avoid 3.13/3.14 (incomplete scientific library wheels)
- FastAPI ~0.135 + Uvicorn: REST API — async-native, auto-generates OpenAPI docs, native SSE for long-running jobs
- TimescaleDB 2.25 (PostgreSQL 17): time-series storage — hypertable compression, continuous aggregates, native multi-frequency handling
- Redis 7.4: caching and Celery broker — caches Leontief inverses, model predictions, job status
- pandas 3.0 + NumPy 2.4 + SciPy 1.17: data manipulation and linear algebra — all econometric libraries expect pandas DataFrames; SciPy handles sparse I-O matrix math
- statsmodels ~0.14.6: econometrics — only Python library with full SVAR identification restrictions, VECM, and built-in MarkovAutoregression
- scikit-learn ~1.8.0: anomaly detection — IsolationForest sufficient for MVP; defer PyOD
- Mesa ~3.5.1: agent-based modeling — target 3.5.x only; Mesa 4.0 alpha has breaking API changes
- Celery ~5.5 + celery-beat: task scheduling — scheduled data pulls, background model runs, simulation execution
- Next.js 16.2 + React 19 + TypeScript ~5.7: frontend — Turbopack stable, React Compiler stable
- Nivo (latest) + D3 ~7.x: visualization — Canvas rendering for dense time-series, Sankey for I-O flows, D3 for fully custom diagrams
- Zustand: frontend state — 1.1kB, zero boilerplate, handles simulation parameters and chart state
- uv: Python package management — 10-100x faster than pip, lockfile support

See `.planning/research/STACK.md` for full version table, installation commands, and alternatives considered.

### Expected Features

The feature landscape divides cleanly into three tiers by dependency depth. Data ingestion is the absolute foundation; nothing else works without it. The NIPA-to-Marxist translation engine is the critical bottleneck that gates all indicator computation. Modeling and advanced visualization (ABM, Leontief, Beer VSM) are semi-independent workstreams that can be developed in parallel once the foundation is stable.

**Must have (P1 — core pipeline and basic visualization):**
- FRED API + BEA NIPA data ingestion with caching and scheduled fetching
- Missing data handling with explicit frequency alignment (not implicit resampling)
- NIPA-to-Marx translation engine with at least one canonical methodology (Shaikh/Tonak recommended), configurable
- Rate of profit, organic composition of capital (OCC), rate of surplus value computation
- Productivity-wage gap indicator
- Basic VAR forecasting on key indicators
- Historical backtesting against 2008 crisis
- Interactive time-series dashboard with multi-series overlay, date range selection, crisis episode annotations
- Indicator overview/summary page
- Methodology documentation (in-app or linked)
- Docker Compose deployment

**Should have (P2 — advanced modeling and richer dashboard, after core validates):**
- Mass vs. rate of profit divergence tracking
- Markov regime-switching crisis detection (statsmodels MarkovAutoregression)
- Composite Crisis Probability Index decomposable by crisis mechanism
- Theoretical annotation layer linking indicators to Marx/Luxemburg/Lenin source texts
- Financial fragility indicators (credit expansion, debt-to-equity, fictitious capital proxies)
- Crisis probability gauge with mechanism decomposition
- Data export (CSV/JSON)

**Defer to v2+:**
- Leontief I-O reproduction schema analysis and interactive visualizer (separate data source, high complexity)
- Agent-based simulation with Mesa (significant modeling effort, separate workstream)
- Beer VSM cybernetic system diagram
- Counterfactual scenario simulation
- Imperialist displacement indicators (requires World Bank/IMF/BIS data)
- Data vintage/revision tracking (schema must support it from day one, but fetching vintage data is deferred)
- Multi-country support

**Deliberate anti-features (do not build):** real-time streaming (macro data is quarterly/monthly, no stream to consume), multi-user/collaborative features, LLM-powered analysis (hallucination risk undermines rigorous theoretical framework), automated trading signals, mobile-responsive design.

See `.planning/research/FEATURES.md` for full dependency graph, competitor analysis, and prioritization matrix.

### Architecture Approach

A strict four-layer pipeline where data flows downward through ingestion (Module A), feature engineering (Module B), predictive modeling (Module C), and presentation (Module D / Next.js). The database is the integration layer between modules — Module B never imports Module A code; it reads from tables Module A populated. This decoupling means each module can be tested independently, partial pipeline reruns are trivial, and the architecture supports future scaling without rewriting module logic. The FastAPI application server sits horizontally, serving all layers via REST endpoints and SSE for long-running jobs. All four containers in Docker Compose (TimescaleDB, Redis, backend Python process, Next.js frontend); no separate scheduler service.

**Major components:**
1. Module A (Data Ingestion): pulls FRED/BEA/BLS, validates, normalizes, stores at native frequency in TimescaleDB `raw_series` hypertables; Celery beat for scheduling
2. Module B (Feature Engineering): reads `raw_series`, computes all Marxist economic categories, writes to `computed_features` hypertables; the NIPA-to-Marx translation engine lives here
3. Module C (Predictive Modeling): reads `computed_features`, runs VAR/SVAR, anomaly detection, Leontief analysis, Mesa ABM, produces composite crisis index; writes to `model_outputs`; expensive results cached in Redis
4. FastAPI: exposes all data, features, model outputs, and simulation controls as REST; manages long-running job lifecycle via SSE; single Python process containing all modules plus Celery workers
5. Module D (Next.js Dashboard): renders interactive visualizations, accepts simulation parameters, displays crisis probability; never touches database directly

See `.planning/research/ARCHITECTURE.md` for full data flow diagrams, schema examples, anti-patterns, and Docker Compose layout.

### Critical Pitfalls

1. **Look-ahead bias in historical calibration** — Use FRED ALFRED vintage retrieval (`get_series_as_of_date()`); include `vintage_date` column in TimescaleDB schema from day one; BEA vintage data requires `datapungibea` or manual archiving (not available via official API). Prevention phase: Phase 1.

2. **NIPA-to-Marxist translation is methodologically contested** — Make the translation configurable via a `TranslationConfig` object specifying NIPA line item mappings; implement at least two methodological variants (Shaikh/Tonak and Kliman); document every mapping decision with theoretical citations. Rushing this produces a tool any Marxist economist would immediately question. Prevention phase: Phase 2.

3. **Mixed-frequency data alignment corruption** — Store all series at native frequency in TimescaleDB; never resample on ingestion; create explicit alignment functions invoked at model-time with a documented strategy parameter; track publication dates separately from observation dates. Schema error here has HIGH recovery cost. Prevention phase: Phase 1 (schema) + Phase 2 (alignment functions).

4. **VAR/SVAR misspecification cascade** — Mandatory preprocessing: ADF + KPSS stationarity tests, information-criteria lag selection (AIC/BIC/HQIC), VECM consideration for I(1) series. Note: statsmodels SVAR has known bugs (GitHub issue #6537); validate against R's `vars` package for at least one test case. Prevention phase: Phase 3.

5. **FRED/BEA API fragility** — Implement exponential backoff retry from day one (FRED rate-limits at 120 req/min); cache all raw API responses immediately; build a series metadata registry with freshness monitoring; never re-fetch data already stored. Prevention phase: Phase 1.

See `.planning/research/PITFALLS.md` for Leontief numerical stability, chart performance traps, Docker volume issues, and the full "looks done but isn't" checklist.

---

## Implications for Roadmap

Research across all four files converges on a five-phase structure matching the architecture document's build order. The ordering is driven by hard data dependencies, not arbitrary scheduling choices.

### Phase 1: Foundation and Data Ingestion

**Rationale:** Nothing in the system works without data in the database. This phase must also make schema decisions that are expensive to retrofit later: `vintage_date` column, native-frequency storage, series metadata registry, Docker Compose health checks. All three HIGH-cost pitfalls (look-ahead bias, mixed-frequency corruption, API fragility) are prevented here or never.

**Delivers:** TimescaleDB schema with hypertables, FRED + BEA NIPA ingestion with retry/backoff, Celery beat scheduling, series metadata registry, Docker Compose stack (4 containers), FastAPI skeleton with raw data endpoints, Next.js skeleton connected to API.

**Addresses features:** FRED API data retrieval, BEA NIPA ingestion, automated scheduled fetching, data caching and persistence, series metadata management, missing data handling (schema-level), Docker Compose deployment.

**Avoids pitfalls:** API fragility (retry from day one), mixed-frequency corruption (native-frequency schema), look-ahead bias (vintage_date column in schema even if not yet populated), Docker deployment issues (separate dev/prod compose files, health checks).

**Research flag:** Standard patterns, well-documented. No phase-level research needed. Use FRED ALFRED documentation and TimescaleDB hypertable docs directly.

### Phase 2: Feature Engineering and Marxist Indicators

**Rationale:** The NIPA-to-Marx translation engine is the intellectual core and the primary source of methodological risk. It must be built carefully, with configurable methodology, before any modeling work begins. This phase delivers independently valuable output: a working rate of profit chart is useful before any prediction exists.

**Delivers:** Configurable `TranslationConfig` abstraction, rate of profit (at least Shaikh/Tonak methodology), OCC, rate of surplus value, productivity-wage gap, basic time-series dashboard with multi-series overlay, indicator overview page, methodology documentation, crisis episode annotations.

**Addresses features:** NIPA-to-Marx translation engine, all three fundamental Marxist indicators, productivity-wage gap, interactive dashboard, data export skeleton.

**Avoids pitfalls:** NIPA translation methodology (configurable from day one, at least two variants, every formula documented with NIPA table/line mappings and theoretical citations), mixed-frequency alignment (explicit alignment functions with documented strategies).

**Research flag:** NEEDS deeper research during planning. The NIPA-to-Marxist category mapping choices (productive vs. unproductive labor, current-cost vs. historical-cost capital stock, specific NIPA table and line item selections for each methodology) are domain-specific and not derivable from software documentation. Reference sources: Shaikh & Tonak (1994), Kliman (2012), BEA NIPA Handbook Chapter 13, Roberts world rate of profit empirical work.

### Phase 3: Predictive Modeling and Crisis Index

**Rationale:** VAR/SVAR and anomaly detection are well-established methods that prove the modeling layer works before attempting complex structural analysis. Composite crisis index requires at least TRPF and realization indicators to be computed, which come from Phase 2. The stationarity preprocessing pipeline must be built before the models, not after.

**Delivers:** ADF/KPSS preprocessing pipeline, VAR/SVAR forecasting with lag selection by information criteria, Markov regime-switching detection, IsolationForest anomaly detection, composite Crisis Probability Index with mechanism decomposition, historical backtesting against 2008, crisis probability gauge on dashboard.

**Addresses features:** VAR/SVAR forecasting, historical backtesting, confidence intervals, regime-switching detection, Composite Crisis Probability Index, financial fragility indicators, theoretical annotation layer.

**Avoids pitfalls:** VAR/SVAR misspecification (mandatory stationarity tests, information-criteria lag selection, VECM consideration, validate against R `vars` package), composite index shown with confidence intervals not just point estimates.

**Research flag:** NEEDS deeper research during planning for the SVAR identification restrictions. The A and B matrix structure for SVAR must be derived from Marxist crisis theory's causal ordering; this is domain-specific theoretical work, not a software question. Also: statsmodels SVAR known bugs require a validation step against R.

### Phase 4: Structural Analysis and Simulation

**Rationale:** Leontief I-O analysis requires BEA I-O tables (a separate data source from NIPA, published every 5 years with annual estimates). Mesa ABM is the most complex module and should be built last. Both are semi-independent workstreams that can proceed in parallel once Phase 3 is stable.

**Delivers:** BEA I-O table ingestion with Hawkins-Simon validation, Leontief inverse computation with condition number check, reproduction schema visualizer (Nivo heatmap + D3 Sankey), Mesa ABM with configurable agents and behaviors, simulation control panel, counterfactual scenario support.

**Addresses features:** Leontief I-O reproduction schema analysis and visualizer, agent-based simulation, simulation control panel, counterfactual scenarios.

**Avoids pitfalls:** Leontief numerical failure (condition number check before inversion, `np.linalg.solve` not `np.linalg.inv`, Hawkins-Simon validation, output non-negativity assertion), chart performance with 71x71 matrix (aggregate to ~15 major sectors for interactive view, full matrix as downloadable CSV), ABM simulation parameter validation server-side (max agents, max steps, parameter bounds to prevent OOM).

**Research flag:** NEEDS deeper research during planning. Mesa 3.5 ABM design for capitalist dynamics (agent types, accumulation behaviors, crisis emergence mechanisms) is a novel modeling problem with no established implementation to copy. Also: BEA I-O table structure and the specific BEA API calls for I-O data differ significantly from NIPA ingestion.

### Phase 5: Enrichment and Expanded Coverage

**Rationale:** Additional data sources, imperialist displacement indicators, Beer VSM diagram, and vintage data fetching do not change the architecture. They add series to Module A and computations to Module B. They belong after the core pipeline is proven and stable.

**Delivers:** BLS data integration, World Bank/IMF/BIS data for imperialist displacement indicators, data vintage/revision tracking with ALFRED retrieval, Beer VSM cybernetic system diagram, extended historical calibration against multiple crisis episodes (1929, 1973, 2001, 2008).

**Addresses features:** Imperialist displacement indicators, Beer VSM diagram, data vintage/revision tracking, comprehensive historical backtesting.

**Research flag:** Standard patterns for data ingestion extensions. Beer VSM diagram implementation is primarily a D3 visualization design problem. Vintage data retrieval uses documented ALFRED API.

### Phase Ordering Rationale

- Phase 1 before everything: no data in the database means nothing downstream works; schema decisions here (vintage_date, native frequency, metadata registry) are expensive to retrofit.
- Phase 2 before Phase 3: models require computed Marxist indicators as inputs; the rate of profit chart is independently valuable before any prediction exists; feature engineering exposes methodological problems early when recovery cost is lower.
- Phase 3 before Phase 4: VAR/SVAR and Markov models are simpler and better-documented than Leontief or ABM; proving the modeling layer works on known methods before building novel structural models reduces risk; Leontief requires a different, more complex data source.
- Phase 4 before Phase 5: ABM and Leontief are the most complex modules; enrichment and expansion are additive and should not compete with core complexity.
- This ordering directly mirrors the feature dependency graph in FEATURES.md and the build order in ARCHITECTURE.md.

### Research Flags

Phases needing deeper research during planning:
- **Phase 2 (Feature Engineering):** NIPA-to-Marxist category mapping requires domain-specific research into Shaikh/Tonak and Kliman methodologies; specific NIPA table/line item selections for variable capital, constant capital, and surplus value must be validated against published empirical work.
- **Phase 3 (Predictive Modeling):** SVAR identification restrictions for a Marxist crisis theory causal ordering are domain-specific; statsmodels SVAR known bugs require a cross-validation protocol against R.
- **Phase 4 (Structural Analysis + ABM):** Mesa ABM agent design for capitalist dynamics is a novel modeling problem; BEA I-O table API structure differs from NIPA and needs specific research.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** FRED API, TimescaleDB hypertables, FastAPI, Docker Compose — all well-documented with established patterns.
- **Phase 5 (Enrichment):** Additive extensions to Module A and Module B; no new architectural patterns.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI, official docs, and release notes as of March 2026. Key substitutions (Mesa requiring Python 3.12, Nivo over Plotly, statsmodels over hmmlearn) are well-supported by evidence. |
| Features | MEDIUM | No direct competitors exist. Features synthesized from adjacent platforms (Macrobond, FRED, IMF EWS tools) and academic literature. The Marxist-specific features (ROP, OCC, six-typology decomposition) have no software precedent to validate against. |
| Architecture | HIGH | Four-layer pipeline is a well-established pattern for data analysis platforms. Database-boundary module pattern is standard in data engineering. TimescaleDB + FastAPI + Next.js integration is documented. The specific Marxist application is novel but the structural pattern is sound. |
| Pitfalls | HIGH (technical) / MEDIUM (domain) | API fragility, mixed-frequency issues, VAR misspecification, Leontief numerical stability, and Docker issues are all well-documented. The NIPA-to-Marx methodology contestation is domain-specific knowledge confirmed by published academic debates, not software documentation. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Exact NIPA line item mappings for Marxist categories:** The research identifies that multiple methodologies exist and must be configurable, but does not prescribe the exact NIPA table/line item selections for each methodology. This requires consulting Shaikh & Tonak (1994), BEA NIPA Handbook Chapter 13, and published empirical work (Roberts, Kliman) during Phase 2 planning.

- **Mesa ABM agent design:** The research confirms Mesa 3.5 is the correct framework and provides architectural guidance, but the specific agent types, behavioral rules, and crisis emergence mechanisms for a Marxist capitalist dynamics model are an open research question. This needs domain-specific design work before Phase 4 planning.

- **BEA vintage data access:** The official BEA API does not provide vintage data. The `datapungibea` package is identified as an alternative but is less well-documented than `beaapi`. This gap affects the look-ahead bias prevention strategy and must be resolved before Phase 5 (or earlier if historical calibration requires vintage data in Phase 3).

- **SVAR identification cross-validation protocol:** statsmodels SVAR has known bugs. A specific cross-validation protocol against R's `vars` package must be designed before Phase 3 begins. The research flags this but does not provide the protocol.

---

## Sources

### Primary (HIGH confidence)

- Mesa PyPI (v3.5.1, March 2026) — Python 3.12 hard requirement
- FastAPI releases (v0.135.1, March 2026) — version verification
- TimescaleDB releases (v2.25, January 2026) — PostgreSQL 17 compatibility
- statsmodels PyPI (v0.14.6, December 2025) — VAR/SVAR/Markov capabilities
- pandas 3.0 release notes (January 2026) — version verification
- Next.js 16.2 blog (March 2026) — Turbopack stable, LTS confirmation
- BEA API User Guide (November 2024) — API capabilities and limitations
- FRED API documentation — rate limits, vintage retrieval via ALFRED
- TimescaleDB Python integration docs — hypertable patterns
- statsmodels SVAR issue #6537 — known bug documentation

### Secondary (MEDIUM confidence)

- IMF Early Warning Systems paper — EWS methodology and regime-switching validation approach
- APScheduler vs. Celery Beat comparison — scheduler selection rationale
- Macrobond, CEIC, Trading Economics — feature benchmarking for commercial macro platforms
- QuantEcon Input-Output lecture — Leontief implementation patterns in Python
- Basu & Manolakos (RRPE) — econometric TRPF testing methodology
- Springer: Predicting financial crises with ML — crisis indicator methodology

### Tertiary (LOW confidence — needs validation during implementation)

- datapungibea (BEA vintage data) — limited documentation; must validate capability before relying on it
- Mesa 4.0 alpha release notes — informational only; explicitly excluded from recommended stack
- Freeman new approach to rate of profit — one of multiple contested methodological positions

---
*Research completed: 2026-03-23*
*Ready for roadmap: yes*
